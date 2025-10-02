from __future__ import annotations
import json
import os
from typing import Optional, Any, Dict
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.tool_context import ToolContext
from app.utils.llmproxy import GeminiLLM
LLM = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))        
LLM_FLASH = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))
LLM_LITE = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))
MCP_SSE_URL = os.getenv("BROWSER_MCP", "localhost")
toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SSE_URL,
    )
)
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "20"))
def finish(
    summary: Optional[str] = None,
    reason: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    tool_context: ToolContext = None,
) -> Dict[str, Any]:
    if tool_context:
        if summary:
            tool_context.state["final_summary"] = summary
        if reason:
            tool_context.state["final_reason"] = reason
        if data is not None:
            tool_context.state["final_data"] = data
        tool_context.actions.escalate = True
    return {"status": "ok", "escalated": True}
fake_urgency_ingest_agent = Agent(
    name="fake_urgency_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Fake Urgency' - ложных таймеров и срочности.",
    instruction=(
        "Ты — Ingest агент для детектирования FAKE URGENCY паттерна. Создай план тестирования ложных таймеров.\n\n"
        "Схема FakeUrgencyPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Fake Urgency pattern - timers and deadlines that reset or are client-side only\",\n'
        '  \"target_site\": string,\n'
        '  \"test_duration_minutes\": 15,\n'
        '  \"success_criteria\": [\n'
        '    \"Identify countdown timers and urgency messages\",\n'
        '    \"Test timer behavior on page reload\",\n'
        '    \"Test timer behavior in new session/incognito\",\n'
        '    \"Check for server-side validation of deadlines\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"timers_found\": [],\n'
        '    \"timer_resets_on_reload\": [],\n'
        '    \"timer_resets_on_new_session\": [],\n'
        '    \"urgency_messages\": [],\n'
        '    \"server_validation_present\": false,\n'
        '    \"fake_urgency_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find pages with timers/urgency\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Document initial timer states\", \"track\": \"baseline_timers\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test reload behavior\", \"track\": \"reload_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test new session behavior\", \"track\": \"session_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze timer authenticity\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: countdown timers, 'Only today', 'Limited time', 'Hurry up'.\n"
        "2) Тестировать: перезагрузка страницы, новая сессия, инкогнито режим.\n"
        "3) Проверять: есть ли серверная валидация дедлайнов.\n"
        "4) Пороги: таймер сбрасывается при reload/new session = fake urgency.\n"
        "5) Только чистый JSON.\n"
    ),
    output_key="plan",
)
fake_urgency_decider_agent = Agent(
    name="fake_urgency_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Fake Urgency паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования FAKE URGENCY паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- urgency_metrics: {urgency_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"discovery\"|\"baseline\"|\"reload_test\"|\"session_test\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда протестированы таймеры на reload И new session И проверена серверная валидация.\n"
        "- parse: когда завершена одна из фаз тестирования и нужно проанализировать результаты.\n"
        "- act: когда нужно взаимодействовать с таймерами, делать перезагрузки, открывать новые сессии.\n"
        "- navigate: когда нужно найти страницы с таймерами или переключиться между вкладками.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'discovery': найти страницы с countdown timers, urgency messages.\n"
        "- Фаза 'baseline': зафиксировать начальные значения таймеров и сообщений.\n"
        "- Фаза 'reload_test': перезагрузить страницу и сравнить состояния таймеров.\n"
        "- Фаза 'session_test': открыть новую вкладку/инкогнито и сравнить таймеры.\n"
        "- Записывать точное время каждого измерения для корректного сравнения.\n\n"
        "Если таймер сбрасывается при reload ≥2 раза — вызови finish с отчетом о fake urgency.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
fake_urgency_navigator_agent = Agent(
    name="fake_urgency_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска и тестирования таймеров срочности.",
    instruction=(
        "Ты — Навигатор для детектирования FAKE URGENCY паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК И НАВИГАЦИЯ ПО ТАЙМЕРАМ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) ПОИСК СТРАНИЦ С URGENCY ЭЛЕМЕНТАМИ:\n"
        "   • Landing pages с 'Limited time offers'\n"
        "   • Checkout pages с countdown timers\n"
        "   • Product pages с 'Only X left in stock'\n"
        "   • Promotional pages с 'Sale ends soon'\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Ищи ключевые слова: 'countdown', 'timer', 'expires', 'limited time'\n"
        "   • Прокрутка для поиска таймеров внизу страницы\n"
        "   • Hover над элементами для активации таймеров\n"
        "D) УПРАВЛЕНИЕ СЕССИЯМИ ДЛЯ ТЕСТИРОВАНИЯ:\n"
        "   • browser_tabs { action: \"create\" } для новых сессий\n"
        "   • Инкогнито через browser_tabs с параметрами\n"
        "   • Сравнение таймеров между вкладками\n"
        "E) ОЖИДАНИЕ И НАБЛЮДЕНИЕ: browser_wait_for { time: 30-60 } для естественного изменения таймеров\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с актуальными таймерами\n\n"
        "ФИКСАЦИЯ ТАЙМЕРОВ:\n"
        "На каждой странице записывай в state:\n"
        "- Найденные таймеры с их текущими значениями\n"
        "- Urgency сообщения и их содержание\n"
        "- Timestamp наблюдения\n"
        "- URL страницы для повторных проверок\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
fake_urgency_form_filler_agent = Agent(
    name="fake_urgency_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Выполняет тесты перезагрузки и новых сессий для проверки таймеров.",
    instruction=(
        "Ты — агент тестирования для FAKE URGENCY. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "МЕТОДИЧНОЕ ТЕСТИРОВАНИЕ ТАЙМЕРОВ:\n"
        "1) browser_snapshot — фиксация текущих таймеров ДО теста\n"
        "2) ИЗВЛЕЧЕНИЕ ЗНАЧЕНИЙ ТАЙМЕРОВ:\n"
        "   • Ищи элементы с числовыми значениями времени\n"
        "   • Записывай точные значения: 'XX:YY:ZZ', 'X hours left', 'Y minutes'\n"
        "   • Фиксируй timestamp измерения\n"
        "3) ТЕСТЫ ПЕРЕЗАГРУЗКИ (фаза 'reload_test'):\n"
        "   • browser_navigate с тем же URL (hard reload)\n"
        "   • browser_wait_for { time: 3 } для загрузки\n"
        "   • browser_snapshot и сравнение новых значений таймеров\n"
        "   • Повторить 2-3 раза для подтверждения\n"
        "4) ТЕСТЫ НОВОЙ СЕССИИ (фаза 'session_test'):\n"
        "   • browser_tabs { action: \"create\" } — новая вкладка\n"
        "   • browser_navigate на тот же URL в новой вкладке\n"
        "   • browser_snapshot и сравнение таймеров\n"
        "   • Тест инкогнито: browser_tabs с incognito если поддерживается\n"
        "5) АНАЛИЗ NETWORK REQUESTS:\n"
        "   • browser_network_requests для поиска серверных запросов таймеров\n"
        "   • Искать API calls к endpoint'ам типа /timer, /deadline, /offer-expiry\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • timer_values_before vs timer_values_after для каждого теста\n"
        "   • reset_detected: boolean для каждого таймера\n"
        "   • server_requests: наличие серверной валидации\n"
        "7) SNAPSHOT ПОСЛЕ ТЕСТОВ: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ FAKE URGENCY:\n"
        "- Если таймер показывает то же или большее значение после reload — FAKE\n"
        "- Если таймер идентичен в новой сессии — FAKE\n"
        "- Если нет серверных запросов для валидации времени — подозрительно\n\n"
        "Возвращай только текст снапшота. Результаты тестов пиши в state."
    ),
    output_key="last_page_text",
)
fake_urgency_parser_agent = Agent(
    name="fake_urgency_parser_agent",
    model=LLM_FLASH,
    description="Анализирует аутентичность таймеров и urgency элементов.",
    instruction=(
        "Ты — парсер для FAKE URGENCY анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, urgency_state={urgency_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ АУТЕНТИЧНОСТИ ТАЙМЕРОВ:\n"
        "1) Извлеки из state все результаты тестирования таймеров.\n"
        "2) Сравни значения до и после каждого теста.\n"
        "3) Определи паттерны поведения каждого таймера.\n"
        "4) Оцени наличие серверной валидации.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"timers_analyzed\": [\n'
        '      {\n'
        '        \"timer_id\": \"countdown_1\",\n'
        '        \"initial_value\": \"23:45:12\",\n'
        '        \"after_reload_value\": \"23:45:12\",\n'
        '        \"after_new_session_value\": \"23:45:12\",\n'
        '        \"resets_on_reload\": boolean,\n'
        '        \"resets_on_new_session\": boolean,\n'
        '        \"appears_server_validated\": boolean,\n'
        '        \"fake_urgency_score\": number\n'
        '      }\n'
        '    ],\n'
        '    \"total_timers_found\": number,\n'
        '    \"fake_timers_detected\": number,\n'
        '    \"urgency_messages\": [\"Limited time offer\", \"Only today\"],\n'
        '    \"server_validation_detected\": boolean,\n'
        '    \"fake_urgency_pattern_detected\": boolean,\n'
        '    \"overall_fake_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание поведения каждого таймера и признаков fake urgency\"\n'
        "}\n\n"
        "КРИТЕРИИ FAKE URGENCY ДЕТЕКТИРОВАНИЯ:\n"
        "- fake_urgency_pattern_detected = true, если ≥1 таймер сбрасывается при reload\n"
        "- ИЛИ если все таймеры идентичны в новых сессиях\n"
        "- ИЛИ если отсутствуют серверные запросы валидации времени\n"
        "- fake_urgency_score = (fake_timers / total_timers) * reset_frequency * validation_penalty"
    ),
    output_key="parsed",
)
fake_urgency_critic_agent = Agent(
    name="fake_urgency_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Fake Urgency анализа.",
    instruction=(
        "Ты — критик для FAKE URGENCY детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдены и зафиксированы таймеры/urgency элементы.\n"
        "2) Проведены тесты перезагрузки для каждого таймера.\n"
        "3) Проведены тесты новой сессии/инкогнито.\n"
        "4) Проверено наличие серверной валидации.\n"
        "5) Рассчитаны показатели fake urgency для каждого элемента.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет об аутентичности найденных таймеров и urgency элементов\n"
        "- reason: количество fake таймеров, паттерны сбросов, отсутствие серверной валидации\n"
        "- data: parsed.extracted со всеми деталями тестирования\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Таймеры, которые сбрасываются при reload — явный fake urgency\n"
        "- Идентичные значения в разных сессиях — подозрительно\n"
        "- Отсутствие network requests к серверу — клиентский fake\n"
        "- Urgency сообщения без временной привязки — потенциально misleading\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти таймеры или провести больше тестов\"}"
    ),
    output_key="critic_json",
)
fake_urgency_result_agent = Agent(
    name="fake_urgency_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Fake Urgency анализа.",
    instruction=(
        "Ты — Result агент для FAKE URGENCY паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ fake urgency анализ завершен:\n"
        "Сформируй отчет о Fake Urgency:\n"
        "- Найдены ли поддельные таймеры срочности\n"
        "- Поведение таймеров при перезагрузках и новых сессиях\n"
        "- Наличие/отсутствие серверной валидации дедлайнов\n"
        "- Влияние fake urgency на принятие решений\n"
        "- Категории найденных urgency элементов\n"
        "- Рекомендации по обеспечению аутентичности\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если таймеры не найдены → should_retry=true с поиском в других разделах\n"
        "- Сайт не использует urgency elements → should_retry=false\n"
        "- Технические проблемы с тестированием → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность временных ограничений и их влияние на поведение пользователя."
    ),
    output_key="result_json",
)
def fake_urgency_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("⏰ FAKE URGENCY PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        total_timers = extracted.get("total_timers_found", 0)
        fake_timers = extracted.get("fake_timers_detected", 0)
        detected = extracted.get("fake_urgency_pattern_detected", False)
        fake_score = extracted.get("overall_fake_score", 0)
        server_validation = extracted.get("server_validation_detected", False)
        pieces.append(f"📊 АНАЛИЗ ТАЙМЕРОВ СРОЧНОСТИ:")
        pieces.append(f"  • Всего таймеров найдено: {total_timers}")
        pieces.append(f"  • Поддельных таймеров: {fake_timers}")
        pieces.append(f"  • Серверная валидация: {'✅ обнаружена' if server_validation else '❌ отсутствует'}")
        pieces.append(f"  • Fake Urgency Score: {fake_score:.2f}")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        timers = extracted.get("timers_analyzed", [])
        if timers:
            pieces.append("🔍 ДЕТАЛИ ТАЙМЕРОВ:")
            for i, timer in enumerate(timers[:3]):  # Показываем первые 3
                resets_reload = timer.get("resets_on_reload", False)
                resets_session = timer.get("resets_on_new_session", False)
                server_val = timer.get("appears_server_validated", False)
                pieces.append(f"  {i+1}. Timer {timer.get('timer_id', 'unknown')}:")
                pieces.append(f"      • Сбрасывается при reload: {'❌ да' if resets_reload else '✅ нет'}")
                pieces.append(f"      • Сбрасывается в новой сессии: {'❌ да' if resets_session else '✅ нет'}")
                pieces.append(f"      • Серверная валидация: {'✅ да' if server_val else '❌ нет'}")
        messages = extracted.get("urgency_messages", [])
        if messages:
            pieces.append(f"📢 НАЙДЕНЫ URGENCY СООБЩЕНИЯ: {', '.join(messages[:3])}")
    reason = state.get("final_reason") or critic.get("reason")
    if reason:
        pieces.append(f"Статус: {reason}")
    if isinstance(result, dict) and "should_retry" in result:
        sr = "да" if result.get("should_retry") else "нет"
        rr = result.get("retry_reason") or "—"
        pieces.append(f"Повторить анализ: {sr}")
        if rr != "—":
            pieces.append(f"Причина: {rr}")
    text = "\n\n".join(pieces)
    return types.Content(role="model", parts=[types.Part(text=text)])
fake_urgency_browser_loop = LoopAgent(
    name="fake_urgency_browser_loop",
    description="Итеративное тестирование Fake Urgency: таймеры и дедлайны, которые сбрасываются.",
    sub_agents=[
        fake_urgency_decider_agent,
        fake_urgency_navigator_agent,
        fake_urgency_form_filler_agent,
        fake_urgency_parser_agent,
        fake_urgency_critic_agent,
        fake_urgency_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=fake_urgency_after_loop_callback,
)
fake_urgency_root_agent = SequentialAgent(
    name="fake_urgency_pipeline",
    description="Полный пайплайн для детектирования Fake Urgency паттерна (поддельные таймеры срочности).",
    sub_agents=[
        fake_urgency_ingest_agent,
        fake_urgency_browser_loop,
    ],
)