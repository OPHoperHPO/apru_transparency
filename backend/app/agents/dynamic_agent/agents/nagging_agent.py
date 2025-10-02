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
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "20"))  # Больше итераций для отслеживания повторов
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
nagging_ingest_agent = Agent(
    name="nagging_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Nagging' - назойливых повторяющихся попапов.",
    instruction=(
        "Ты — Ingest агент для детектирования NAGGING паттерна. Создай план тестирования повторяющихся интерстициалов.\n\n"
        "Схема NaggingPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Nagging pattern - repetitive popups and interstitials without proper opt-out\",\n'
        '  \"target_site\": string,\n'
        '  \"navigation_actions_count\": 15,\n'
        '  \"observation_time_minutes\": 10,\n'
        '  \"success_criteria\": [\n'
        '    \"Navigate through different pages/sections\",\n'
        '    \"Track popup appearances with timestamps\",\n'
        '    \"Test rejection persistence (does it remember No?)\",\n'
        '    \"Check for Don\'t show again options\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"popup_appearances\": [],\n'
        '    \"rejection_attempts\": 0,\n'
        '    \"persistent_rejections\": false,\n'
        '    \"has_dont_show_again\": false,\n'
        '    \"time_between_shows_seconds\": [],\n'
        '    \"nagging_score\": 0\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Go to target site\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Perform navigation tour (10-15 actions)\", \"track\": \"popup_tracking\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test rejection persistence\", \"track\": \"rejection_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze nagging patterns and frequency\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Цель: 10-15 навигационных действий по разным страницам для вызова попапов.\n"
        "2) Отслеживать: время появления, содержание, наличие опции 'Не показывать снова'.\n"
        "3) Тестировать: запоминается ли отказ между страницами/сессиями.\n"
        "4) Пороги: ≥3 показа одного предложения за ≤10 минут = nagging.\n"
        "5) Только чистый JSON.\n"
    ),
    output_key="plan",
)
nagging_decider_agent = Agent(
    name="nagging_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Nagging паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования NAGGING паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- nagging_metrics: {nagging_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"exploration\"|\"rejection_test\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда собрано ≥3 появления попапов И протестирована персистентность отказа.\n"
        "- parse: когда завершена навигационная сессия и нужно проанализировать паттерны.\n"
        "- act: когда нужно кликнуть, отказаться от попапа, или продолжить навигацию.\n"
        "- navigate: когда нужно перейти на новую страницу/раздел для триггера попапов.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'exploration': переходи между разными разделами (Home→About→Products→Contact→Blog).\n"
        "- Фаза 'rejection_test': отклоняй попапы и проверяй, появляются ли они снова.\n"
        "- При каждом попапе: записывай timestamp, содержание, наличие 'Don't show again'.\n"
        "- Ищи паттерны: один и тот же попап через короткие интервалы.\n\n"
        "Если зафиксировано ≥3 повтора за ≤10 минут — вызови finish с отчетом о nagging.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
nagging_navigator_agent = Agent(
    name="nagging_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для провокации и тестирования Nagging паттерна.",
    instruction=(
        "Ты — Навигатор для детектирования NAGGING паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "СТРАТЕГИЯ НАВИГАЦИИ ДЛЯ ПРОВОКАЦИИ ПОПАПОВ:\n"
        "A) SNAPSHOT: browser_snapshot для текущего состояния\n"
        "B) НАВИГАЦИОННЫЕ ПАТТЕРНЫ:\n"
        "   • Переходы между разными разделами: Home→About→Products→Pricing→Contact→Blog\n"
        "   • Прокрутка вниз/вверх страниц (может триггерить scroll-based попапы)\n"
        "   • Симуляция \"намерения ухода\" (движение мыши к краю экрана/табу)\n"
        "   • Использование: browser_navigate { url: \"...\" }\n"
        "   • Возврат: browser_navigate_back {}\n"
        "   • Новые вкладки: browser_tabs { action: \"create\" }\n"
        "C) ТРИГГЕРЫ ПОПАПОВ:\n"
        "   • Время на странице (browser_wait_for { time: 5-10 })\n"
        "   • Скроллинг до определенного места\n"
        "   • Hover над ссылками выхода\n"
        "D) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot\n\n"
        "ФИКСАЦИЯ ПОПАПОВ:\n"
        "Если в snapshot появился modal/popup/overlay — запиши в state:\n"
        "- Время появления (timestamp)\n"
        "- Тип попапа (newsletter, discount, notification)\n"
        "- Текст предложения\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
nagging_form_filler_agent = Agent(
    name="nagging_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Взаимодействует с попапами для тестирования Nagging паттерна.",
    instruction=(
        "Ты — агент взаимодействия для NAGGING тестирования. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ОБРАБОТКА ПОПАПОВ — КЛЮЧЕВАЯ ЗАДАЧА:\n"
        "1) browser_snapshot — обнаружение попапов/модалов\n"
        "2) ИДЕНТИФИКАЦИЯ ПОПАПА:\n"
        "   • Ищи селекторы: modal, popup, overlay, dialog, banner\n"
        "   • Распознавай тип: newsletter signup, discount offer, cookie consent, notification\n"
        "3) АНАЛИЗ ОПЦИЙ ОТКАЗА:\n"
        "   • Есть ли кнопка \"No thanks\", \"Close\", \"X\"?\n"
        "   • Есть ли checkbox \"Don't show this again\"?\n"
        "   • Размер/видимость кнопки отказа vs согласия?\n"
        "4) ДЕЙСТВИЕ:\n"
        "   • Первый показ: отказаться через browser_click с элементом отказа\n"
        "   • Повторный показ: пометить как nagging, попробовать \"Don't show again\"\n"
        "   • browser_handle_dialog если это системный alert\n"
        "5) ЗАПИСЬ МЕТРИК:\n"
        "   • Увеличить rejection_attempts в state\n"
        "   • Записать время и тип попапа\n"
        "6) ПРОДОЛЖЕНИЕ НАВИГАЦИИ:\n"
        "   • После закрытия попапа — продолжить исследование сайта\n"
        "   • browser_wait_for для наблюдения за повторными появлениями\n"
        "7) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot\n\n"
        "ВАЖНО: фиксируй каждое появление попапа с timestamp для расчета частоты.\n"
        "Возвращай только текст снапшота."
    ),
    output_key="last_page_text",
)
nagging_parser_agent = Agent(
    name="nagging_parser_agent",
    model=LLM_FLASH,
    description="Анализирует паттерны назойливости попапов.",
    instruction=(
        "Ты — парсер для NAGGING анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, nagging_state={nagging_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ NAGGING ПАТТЕРНОВ:\n"
        "1) Извлеки из state: popup_appearances, rejection_attempts, время между показами.\n"
        "2) Рассчитай частоту: сколько показов одного и того же попапа за период времени.\n"
        "3) Оцени качество отказа: размер кнопок, наличие \"Don't show again\".\n"
        "4) Проверь персистентность: запоминается ли отказ между страницами.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"total_popup_appearances\": number,\n'
        '    \"unique_popup_types\": [\"newsletter\", \"discount\", ...],\n'
        '    \"rejection_attempts\": number,\n'
        '    \"avg_time_between_shows_seconds\": number,\n'
        '    \"min_time_between_shows_seconds\": number,\n'
        '    \"has_dont_show_again_option\": boolean,\n'
        '    \"rejection_persistence\": boolean,\n'
        '    \"nagging_score\": number,\n'
        '    \"nagging_detected\": boolean\n'
        '  },\n'
        '  \"popup_details\": [\n'
        '    {\n'
        '      \"timestamp\": \"...\",\n'
        '      \"type\": \"newsletter|discount|notification\",\n'
        '      \"content_summary\": \"...\",\n'
        '      \"dismiss_options\": [\"X\", \"No thanks\", \"Don\'t show again\"]\n'
        '    }\n'
        '  ],\n'
        '  \"notes\": \"Детальное описание обнаруженных паттернов назойливости\"\n'
        "}\n\n"
        "ПОРОГИ NAGGING ДЕТЕКТИРОВАНИЯ:\n"
        "- nagging_detected = true, если ≥3 появления одного попапа за ≤10 минут\n"
        "- ИЛИ если отказ не запоминается (rejection_persistence = false)\n"
        "- ИЛИ если нет опции \"Don't show again\" для часто показываемых попапов\n"
        "- nagging_score = (appearances * rejection_attempts) / time_span_minutes"
    ),
    output_key="parsed",
)
nagging_critic_agent = Agent(
    name="nagging_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Nagging анализа.",
    instruction=(
        "Ты — критик для NAGGING детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Выполнено достаточно навигационных действий (≥10 переходов).\n"
        "2) Зафиксированы появления попапов с временными метками.\n"
        "3) Протестирована персистентность отказов.\n"
        "4) Рассчитан nagging_score и определен результат детектирования.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: краткий отчет о найденных/отсутствующих nagging паттернах\n"
        "- reason: количество попапов, частота, персистентность отказов\n"
        "- data: parsed.extracted + popup_details\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Если nagging_score > 2.0 И rejection_persistence = false — это явный nagging\n"
        "- Если отсутствует \"Don't show again\" для часто появляющихся попапов — красный флаг\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно больше навигации или попапов не обнаружено\"}"
    ),
    output_key="critic_json",
)
nagging_result_agent = Agent(
    name="nagging_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Nagging анализа.",
    instruction=(
        "Ты — Result агент для NAGGING паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ nagging анализ завершен:\n"
        "Сформируй отчет о Nagging паттерне:\n"
        "- Обнаружен ли назойливый паттерн\n"
        "- Частота появлений попапов\n"
        "- Качество опций отказа\n"
        "- Персистентность (запоминается ли \"нет\")\n"
        "- Рекомендации по улучшению UX\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если попапы не появлялись — попробовать другие триггеры\n"
        "- Временные проблемы (таймауты, загрузка) → should_retry=true\n"
        "- Сайт не использует попапы → should_retry=false\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: именно на UX-навязчивости, не на содержании предложений."
    ),
    output_key="result_json",
)
def nagging_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🔔 NAGGING PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        total_popups = extracted.get("total_popup_appearances", 0)
        rejection_attempts = extracted.get("rejection_attempts", 0)
        avg_time = extracted.get("avg_time_between_shows_seconds", 0)
        has_dont_show = extracted.get("has_dont_show_again_option", False)
        persistent = extracted.get("rejection_persistence", True)
        nagging_score = extracted.get("nagging_score", 0)
        detected = extracted.get("nagging_detected", False)
        pieces.append(f"📊 МЕТРИКИ НАЗОЙЛИВОСТИ:")
        pieces.append(f"  • Всего появлений попапов: {total_popups}")
        pieces.append(f"  • Попыток отказа: {rejection_attempts}")
        pieces.append(f"  • Среднее время между показами: {avg_time}с")
        pieces.append(f"  • Есть 'Не показывать снова': {'✅ да' if has_dont_show else '❌ нет'}")
        pieces.append(f"  • Отказ запоминается: {'✅ да' if persistent else '❌ нет'}")
        pieces.append(f"  • Назойливость (score): {nagging_score:.2f}")
        pieces.append(f"  • Nagging паттерн: {'❌ ОБНАРУЖЕН' if detected else '✅ НЕ ОБНАРУЖЕН'}")
    popup_details = parsed.get("popup_details", []) if isinstance(parsed, dict) else []
    if popup_details:
        pieces.append("📋 ДЕТАЛИ ПОПАПОВ:")
        for i, popup in enumerate(popup_details[:3]):  # Показываем первые 3
            pieces.append(f"  {i+1}. {popup.get('type', 'unknown')} - {popup.get('content_summary', 'N/A')}")
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
nagging_browser_loop = LoopAgent(
    name="nagging_browser_loop",
    description="Итеративное тестирование Nagging паттерна: назойливые повторяющиеся попапы.",
    sub_agents=[
        nagging_decider_agent,
        nagging_navigator_agent,
        nagging_form_filler_agent,
        nagging_parser_agent,
        nagging_critic_agent,
        nagging_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=nagging_after_loop_callback,
)
nagging_root_agent = SequentialAgent(
    name="nagging_pipeline",
    description="Полный пайплайн для детектирования Nagging паттерна (назойливые интерстициалы).",
    sub_agents=[
        nagging_ingest_agent,
        nagging_browser_loop,
    ],
)