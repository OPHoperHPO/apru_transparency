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
LLM = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))        # планирование/критика/итоги
LLM_FLASH = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))
LLM_LITE = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))
MCP_SSE_URL = os.getenv("BROWSER_MCP", "localhost")
toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SSE_URL,
    )
)
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "15"))
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
roach_motel_ingest_agent = Agent(
    name="roach_motel_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Roach Motel' - асимметрии между подпиской и отменой.",
    instruction=(
        "Ты — Ingest агент для детектирования паттерна ROACH MOTEL. На основе запроса пользователя создай план тестирования асимметрии действий.\n\n"
        "Схема RoachMotelPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Roach Motel pattern - asymmetry between subscription and cancellation\",\n'
        '  \"target_site\": string,\n'
        '  \"test_service\": string|null,\n'
        '  \"success_criteria\": [\n'
        '    \"Subscribe flow completed with step count recorded\",\n'
        '    \"Cancel flow attempted with step count recorded\",\n'
        '    \"SAR (Steps Asymmetry Ratio) calculated\",\n'
        '    \"Time to Subscribe (TTS) and Time to Cancel (TTC) measured\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"subscribe_steps\": 0,\n'
        '    \"cancel_steps\": 0,\n'
        '    \"subscribe_time_seconds\": 0,\n'
        '    \"cancel_time_seconds\": 0,\n'
        '    \"sar_ratio\": 0.0,\n'
        '    \"requires_support_contact\": false,\n'
        '    \"menu_depth_to_cancel\": 0\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Go to target site\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Complete subscription flow\", \"track\": \"subscribe_metrics\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Attempt cancellation flow\", \"track\": \"cancel_metrics\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Calculate asymmetry ratios and detect pattern\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Если в запросе указан конкретный сервис/сайт — используй его как target_site.\n"
        "2) success_criteria должны включать измерение шагов подписки vs отмены.\n"
        "3) Обязательно отслеживать: количество шагов, время выполнения, глубину меню.\n"
        "4) Флаг тревоги: SAR >= 3 (отмена в 3+ раза сложнее подписки).\n"
        "5) Только чистый JSON без комментариев.\n"
    ),
    output_key="plan",
)
roach_motel_decider_agent = Agent(
    name="roach_motel_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Roach Motel паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования ROACH MOTEL паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- metrics: {roach_motel_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"subscribe\"|\"cancel\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда собраны метрики подписки И отмены, рассчитан SAR >= 3.\n"
        "- parse: когда завершена одна из фаз (подписка/отмена) и нужно извлечь данные.\n"
        "- act: когда нужно выполнить действие (подписку или отмену).\n"
        "- navigate: когда нужно перейти на страницу или обновить снимок.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'subscribe': ищи кнопки 'Sign up', 'Subscribe', 'Get started', считай клики до завершения.\n"
        "- Фаза 'cancel': ищи 'Account settings', 'Billing', 'Cancel', 'Unsubscribe', отслеживай глубину меню.\n"
        "- Зафиксируй, если отмена требует звонка в поддержку или email.\n"
        "- Измеряй время: начало фазы → завершение фазы.\n\n"
        "Если SAR рассчитан И SAR >= 3 — вызови finish с детальным отчетом.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
roach_motel_navigator_agent = Agent(
    name="roach_motel_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для тестирования Roach Motel паттерна.",
    instruction=(
        "Ты — Навигатор для детектирования ROACH MOTEL паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "Иначе выполняй навигацию с учетом текущей фазы тестирования:\n"
        "A) SNAPSHOT для синхронизации: browser_snapshot\n"
        "B) НАВИГАЦИЯ согласно action_instructions и фазе:\n"
        "   • subscribe фаза: ищи pricing/signup страницы\n"
        "   • cancel фаза: ищи account/settings/billing страницы\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "   • Назад: browser_navigate_back {}\n"
        "   • Вкладки: browser_tabs { action: \"create\"|\"select\"|\"close\" }\n"
        "C) ОЖИДАНИЕ стабилизации: browser_wait_for { text: \"..\" или time: 2-5 }\n"
        "D) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot\n\n"
        "ВАЖНО: При переходе между фазами (подписка→отмена) записывай временные метки в state.\n"
        "Возвращай только сырой текст последнего browser_snapshot."
    ),
    output_key="last_page_text",
)
roach_motel_form_filler_agent = Agent(
    name="roach_motel_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Выполняет действия для тестирования Roach Motel паттерна, считает шаги.",
    instruction=(
        "Ты — агент действий для ROACH MOTEL тестирования. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "СЧЕТЧИК ШАГОВ — КРИТИЧЕСКИ ВАЖНО:\n"
        "1) Перед каждым действием: увеличь счетчик текущей фазы в state.\n"
        "2) Фазы: 'subscribe' или 'cancel' из decider_json.current_phase.\n"
        "3) Каждый клик/ввод/выбор = +1 шаг.\n\n"
        "АЛГОРИТМ:\n"
        "1) browser_snapshot — проверка элементов.\n"
        "2) НАЙДИ целевой элемент из snapshot.\n"
        "3) ВЫПОЛНИ действие:\n"
        "   • subscribe фаза: клики по 'Sign up', 'Choose plan', заполнение email (Реальные данные)\n"
        "   • cancel фаза: поиск 'Account', 'Settings', 'Billing', 'Cancel subscription'\n"
        "4) ЗАПИШИ ШАГ: обнови state[f'{current_phase?}_steps'] += 1\n"
        "5) ОЖИДАНИЕ: browser_wait_for\n"
        "6) ИТОГОВЫЙ SNAPSHOT: browser_snapshot\n\n"
        "ОСОБЕННОСТИ ОТМЕНЫ:\n"
        "- Считай глубину меню (сколько уровней до кнопки Cancel)\n"
        "- Фиксируй, если требуется контакт с поддержкой\n"
        "- Ищи скрытые ссылки, мелкий текст\n\n"
        "Возвращай только текст снапшота. Метрики пиши в state."
    ),
    output_key="last_page_text",
)
roach_motel_parser_agent = Agent(
    name="roach_motel_parser_agent",
    model=LLM_FLASH,
    description="Извлекает и рассчитывает метрики Roach Motel паттерна.",
    instruction=(
        "Ты — парсер для ROACH MOTEL анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, state_metrics={roach_motel_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "РАСЧЕТ МЕТРИК:\n"
        "1) Извлеки из state: subscribe_steps, cancel_steps, subscribe_time, cancel_time.\n"
        "2) Рассчитай SAR = cancel_steps / subscribe_steps (если subscribe_steps > 0).\n"
        "3) Рассчитай временной коэффициент TTC/TTS.\n"
        "4) Определи, требует ли отмена контакта с поддержкой (ищи 'contact support', 'call us').\n"
        "5) Измерь глубину навигации до Cancel (количество кликов от главной).\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"subscribe_steps\": number,\n'
        '    \"cancel_steps\": number,\n'
        '    \"sar_ratio\": number,\n'
        '    \"time_ratio_ttc_tts\": number,\n'
        '    \"requires_support_contact\": boolean,\n'
        '    \"menu_depth_to_cancel\": number,\n'
        '    \"roach_motel_detected\": boolean\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных признаков или их отсутствия\"\n'
        "}\n\n"
        "ПОРОГИ ДЕТЕКТИРОВАНИЯ:\n"
        "- roach_motel_detected = true, если SAR >= 3 ИЛИ TTC >= 180 сек при TTS <= 30 сек\n"
        "- Дополнительные красные флаги: requires_support_contact=true, menu_depth >= 4"
    ),
    output_key="parsed",
)
roach_motel_critic_agent = Agent(
    name="roach_motel_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Roach Motel анализа.",
    instruction=(
        "Ты — критик для ROACH MOTEL детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Собраны метрики подписки (subscribe_steps > 0).\n"
        "2) Собраны метрики отмены (cancel_steps > 0 ИЛИ зафиксирована невозможность self-service отмены).\n"
        "3) Рассчитан SAR (Steps Asymmetry Ratio).\n"
        "4) Определен результат детектирования (roach_motel_detected).\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: краткий отчет о найденной/отсутствующей асимметрии\n"
        "- reason: перечисли подтвержденные критерии и ключевые метрики (SAR, TTC/TTS)\n"
        "- data: parsed.extracted\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"что ещё требуется собрать\"}"
    ),
    output_key="critic_json",
)
roach_motel_result_agent = Agent(
    name="roach_motel_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Roach Motel анализа.",
    instruction=(
        "Ты — Result агент для ROACH MOTEL паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ все метрики собраны:\n"
        "Сформируй отчет о Roach Motel паттерне:\n"
        "- Обнаружен ли паттерн (SAR >= 3, TTC >> TTS, требует поддержки)\n"
        "- Конкретные цифры асимметрии\n"
        "- Рекомендации по улучшению UX\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Временные проблемы (загрузка, таймауты) → should_retry=true\n"
        "- Нужна регистрация/оплата для доступа к функциям отмены → should_retry=false\n"
        "- Верни JSON с рекомендацией ретрая\n\n"
        "ФОКУС: детектирование именно поведенческих барьеров в UI/UX, не правовых аспектов."
    ),
    output_key="result_json",
)
def roach_motel_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🔍 ROACH MOTEL PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        sar = extracted.get("sar_ratio", 0)
        subscribe_steps = extracted.get("subscribe_steps", 0)
        cancel_steps = extracted.get("cancel_steps", 0)
        detected = extracted.get("roach_motel_detected", False)
        pieces.append(f"📊 МЕТРИКИ АСИММЕТРИИ:")
        pieces.append(f"  • Шагов подписки: {subscribe_steps}")
        pieces.append(f"  • Шагов отмены: {cancel_steps}")
        pieces.append(f"  • SAR (коэффициент асимметрии): {sar:.2f}")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        if extracted.get("requires_support_contact"):
            pieces.append("  • ⚠️ Отмена требует обращения в поддержку")
        menu_depth = extracted.get("menu_depth_to_cancel", 0)
        if menu_depth >= 3:
            pieces.append(f"  • ⚠️ Глубина меню до отмены: {menu_depth} уровней")
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
roach_motel_browser_loop = LoopAgent(
    name="roach_motel_browser_loop",
    description="Итеративное тестирование Roach Motel паттерна: асимметрии между подпиской и отменой.",
    sub_agents=[
        roach_motel_decider_agent,
        roach_motel_navigator_agent,
        roach_motel_form_filler_agent,
        roach_motel_parser_agent,
        roach_motel_critic_agent,
        roach_motel_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=roach_motel_after_loop_callback,
)
roach_motel_root_agent = SequentialAgent(
    name="roach_motel_pipeline",
    description="Полный пайплайн для детектирования Roach Motel паттерна (асимметрия подписка/отмена).",
    sub_agents=[
        roach_motel_ingest_agent,
        roach_motel_browser_loop,
    ],
)