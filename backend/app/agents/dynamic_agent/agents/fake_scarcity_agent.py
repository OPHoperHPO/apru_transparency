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
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "18"))
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
fake_scarcity_ingest_agent = Agent(
    name="fake_scarcity_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Fake Scarcity' - ложных индикаторов дефицита.",
    instruction=(
        "Ты — Ingest агент для детектирования FAKE SCARCITY паттерна. Создай план тестирования ложных индикаторов дефицита.\n\n"
        "Схема FakeScarcityPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Fake Scarcity pattern - false stock indicators and fake social proof\",\n'
        '  \"target_site\": string,\n'
        '  \"test_duration_minutes\": 20,\n'
        '  \"success_criteria\": [\n'
        '    \"Identify stock/availability indicators\",\n'
        '    \"Test stock numbers across page reloads\",\n'
        '    \"Check social proof notifications (recent buyers)\",\n'
        '    \"Verify authenticity of scarcity claims\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"stock_indicators_found\": [],\n'
        '    \"stock_changes_on_reload\": [],\n'
        '    \"social_proof_notifications\": [],\n'
        '    \"notification_patterns\": [],\n'
        '    \"scarcity_authenticity_score\": 0.0,\n'
        '    \"fake_scarcity_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find product pages with stock info\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Document stock indicators and social proof\", \"track\": \"baseline_scarcity\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test reload behavior of stock numbers\", \"track\": \"stock_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Monitor social proof patterns\", \"track\": \"social_proof_analysis\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze scarcity authenticity\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: 'Only X left', 'Y people bought', 'Z viewing now', recent purchase notifications.\n"
        "2) Тестировать: изменения числовых индикаторов при reload и между разными товарами.\n"
        "3) Анализировать: паттерны социальных уведомлений (регулярность, шаблонность).\n"
        "4) Пороги: неубедительные колебания stock'а, шаблонные social proof = fake scarcity.\n"
        "5) Только чистый JSON.\n"
    ),
    output_key="plan",
)
fake_scarcity_decider_agent = Agent(
    name="fake_scarcity_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Fake Scarcity паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования FAKE SCARCITY паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- scarcity_metrics: {scarcity_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"discovery\"|\"baseline\"|\"stock_testing\"|\"social_monitoring\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда протестированы stock indicators И social proof notifications И выявлены паттерны подделки.\n"
        "- parse: когда завершена одна из фаз сбора данных и нужно проанализировать паттерны.\n"
        "- act: когда нужно отслеживать изменения stock'а, мониторить уведомления, тестировать разные товары.\n"
        "- navigate: когда нужно найти страницы с индикаторами дефицита или переключаться между товарами.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'discovery': найти продуктовые страницы с stock indicators и social proof.\n"
        "- Фаза 'baseline': зафиксировать начальные значения всех индикаторов.\n"
        "- Фаза 'stock_testing': тестировать изменения stock numbers при reload и между товарами.\n"
        "- Фаза 'social_monitoring': отслеживать паттерны social proof уведомлений по времени.\n"
        "- Записывать точные значения и timestamps для выявления искусственности.\n\n"
        "Если stock неубедительно колеблется ИЛИ social proof следует шаблонным паттернам — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
fake_scarcity_navigator_agent = Agent(
    name="fake_scarcity_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска и анализа индикаторов дефицита.",
    instruction=(
        "Ты — Навигатор для детектирования FAKE SCARCITY паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК ИНДИКАТОРОВ ДЕФИЦИТА:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО ПРОДУКТАМ С SCARCITY ЭЛЕМЕНТАМИ:\n"
        "   • Product pages с stock counters\n"
        "   • Category pages с availability info\n"
        "   • Popular/trending sections\n"
        "   • Sale/clearance pages\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК РАЗНЫХ ТИПОВ ТОВАРОВ:\n"
        "   • Переключение между категориями для сравнения stock patterns\n"
        "   • Разные ценовые сегменты (дешевые vs дорогие товары)\n"
        "   • Новые vs популярные товары\n"
        "D) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Ищи текст: 'left in stock', 'people bought', 'viewing this item'\n"
        "   • Прокрутка для поиска social proof notifications\n"
        "   • Ожидание появления live notifications\n"
        "E) ОЖИДАНИЕ ДЛЯ МОНИТОРИНГА: browser_wait_for { time: 60-120 } для наблюдения социальных уведомлений\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с актуальными индикаторами\n\n"
        "ФИКСАЦИЯ SCARCITY ЭЛЕМЕНТОВ:\n"
        "На каждой странице записывай в state:\n"
        "- Stock numbers с точными значениями\n"
        "- Social proof messages с timestamp\n"
        "- Product IDs/URLs для повторных проверок\n"
        "- Notification frequency и содержание\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
fake_scarcity_form_filler_agent = Agent(
    name="fake_scarcity_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Отслеживает и тестирует изменения индикаторов дефицита.",
    instruction=(
        "Ты — агент мониторинга для FAKE SCARCITY. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "МЕТОДИЧНОЕ ТЕСТИРОВАНИЕ SCARCITY ИНДИКАТОРОВ:\n"
        "1) browser_snapshot — фиксация текущих индикаторов\n"
        "2) ИЗВЛЕЧЕНИЕ STOCK ДАННЫХ:\n"
        "   • Ищи числовые значения: 'Only 3 left', '15 in stock', 'Last one!'\n"
        "   • Записывай точные числа и их контекст\n"
        "   • Фиксируй timestamp каждого измерения\n"
        "3) ТЕСТИРОВАНИЕ STOCK CONSISTENCY:\n"
        "   • browser_navigate с тем же URL (reload)\n"
        "   • Сравнение stock numbers до и после\n"
        "   • Переход к другому товару той же категории\n"
        "   • Возврат к первому товару и повторная проверка\n"
        "4) МОНИТОРИНГ SOCIAL PROOF NOTIFICATIONS:\n"
        "   • browser_wait_for { time: 30-90 } между наблюдениями\n"
        "   • Запись каждого уведомления: содержание, время появления\n"
        "   • Поиск паттернов: одинаковые имена, регулярные интервалы\n"
        "5) АНАЛИЗ NETWORK ACTIVITY:\n"
        "   • browser_network_requests для поиска API calls\n"
        "   • Ищи requests к endpoints типа /stock, /notifications, /social-proof\n"
        "   • Проверка, обновляются ли данные с сервера или генерируются клиентом\n"
        "6) ЗАПИСЬ ПАТТЕРНОВ:\n"
        "   • stock_fluctuations: изменения без логики\n"
        "   • social_proof_regularity: фиксированные интервалы уведомлений\n"
        "   • template_detection: шаблонные имена и локации\n"
        "7) SNAPSHOT ПОСЛЕ НАБЛЮДЕНИЙ: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ FAKE SCARCITY:\n"
        "- Stock numbers не зависят от времени или действий — подозрительно\n"
        "- Social proof уведомления с фиксированными интервалами — fake\n"
        "- Одинаковые имена покупателей или шаблонные локации — red flag\n\n"
        "Возвращай только текст снапшота. Данные мониторинга пиши в state."
    ),
    output_key="last_page_text",
)
fake_scarcity_parser_agent = Agent(
    name="fake_scarcity_parser_agent",
    model=LLM_FLASH,
    description="Анализирует аутентичность индикаторов дефицита и социальных доказательств.",
    instruction=(
        "Ты — парсер для FAKE SCARCITY анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, scarcity_state={scarcity_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ АУТЕНТИЧНОСТИ ДЕФИЦИТА:\n"
        "1) Извлеки из state все stock measurements и social proof observations.\n"
        "2) Проанализируй паттерны изменений stock numbers.\n"
        "3) Выяви регулярность и шаблонность social proof notifications.\n"
        "4) Оцени наличие серверной синхронизации данных.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"stock_indicators_analyzed\": [\n'
        '      {\n'
        '        \"product_id\": \"prod_123\",\n'
        '        \"initial_stock\": 5,\n'
        '        \"stock_after_reload\": 5,\n'
        '        \"stock_changes_detected\": boolean,\n'
        '        \"stock_change_logic\": \"none|realistic|suspicious\",\n'
        '        \"fake_stock_score\": number\n'
        '      }\n'
        '    ],\n'
        '    \"social_proof_analysis\": {\n'
        '      \"total_notifications_observed\": number,\n'
        '      \"avg_interval_seconds\": number,\n'
        '      \"template_names_detected\": boolean,\n'
        '      \"template_locations_detected\": boolean,\n'
        '      \"notification_authenticity_score\": number\n'
        '    },\n'
        '    \"server_data_validation\": {\n'
        '      \"stock_api_calls_detected\": boolean,\n'
        '      \"social_proof_api_calls_detected\": boolean,\n'
        '      \"client_side_generation_suspected\": boolean\n'
        '    },\n'
        '    \"fake_scarcity_detected\": boolean,\n'
        '    \"overall_fake_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных признаков fake scarcity\"\n'
        "}\n\n"
        "КРИТЕРИИ FAKE SCARCITY ДЕТЕКТИРОВАНИЯ:\n"
        "- fake_scarcity_detected = true, если stock numbers не изменяются реалистично\n"
        "- ИЛИ если social proof notifications следуют регулярным паттернам\n"
        "- ИЛИ если обнаружены шаблонные имена/локации в уведомлениях\n"
        "- ИЛИ если отсутствуют серверные calls для обновления scarcity данных"
    ),
    output_key="parsed",
)
fake_scarcity_critic_agent = Agent(
    name="fake_scarcity_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Fake Scarcity анализа.",
    instruction=(
        "Ты — критик для FAKE SCARCITY детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдены и протестированы stock indicators на нескольких товарах.\n"
        "2) Отслежены social proof notifications в течение достаточного времени.\n"
        "3) Проанализированы паттерны изменений stock numbers.\n"
        "4) Выявлены признаки шаблонности или искусственности.\n"
        "5) Проверено наличие серверной валидации scarcity данных.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет об аутентичности найденных индикаторов дефицита\n"
        "- reason: stock behavior patterns, social proof regularity, server validation\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Stock numbers, которые не изменяются со временем — подозрительно\n"
        "- Social proof с фиксированными интервалами — явный fake\n"
        "- Шаблонные имена (John from NY, Mary from TX) — red flag\n"
        "- Отсутствие API calls для stock updates — клиентская генерация\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти больше scarcity элементов или продлить мониторинг\"}"
    ),
    output_key="critic_json",
)
fake_scarcity_result_agent = Agent(
    name="fake_scarcity_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Fake Scarcity анализа.",
    instruction=(
        "Ты — Result агент для FAKE SCARCITY паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ fake scarcity анализ завершен:\n"
        "Сформируй отчет о Fake Scarcity:\n"
        "- Найдены ли поддельные индикаторы дефицита\n"
        "- Аутентичность stock counters и их поведение\n"
        "- Анализ social proof notifications и их паттернов\n"
        "- Обнаружение шаблонных или искусственных элементов\n"
        "- Влияние fake scarcity на принятие решений\n"
        "- Рекомендации по обеспечению честности scarcity индикаторов\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если scarcity элементы не найдены → should_retry=true с поиском в других разделах\n"
        "- Сайт не использует scarcity tactics → should_retry=false\n"
        "- Нужно больше времени для мониторинга паттернов → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность представления доступности товаров и социальных доказательств."
    ),
    output_key="result_json",
)
def fake_scarcity_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("📦 FAKE SCARCITY PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        stock_indicators = extracted.get("stock_indicators_analyzed", [])
        social_proof = extracted.get("social_proof_analysis", {})
        server_validation = extracted.get("server_data_validation", {})
        detected = extracted.get("fake_scarcity_detected", False)
        fake_score = extracted.get("overall_fake_score", 0)
        pieces.append(f"📊 АНАЛИЗ ИНДИКАТОРОВ ДЕФИЦИТА:")
        pieces.append(f"  • Проанализировано товаров: {len(stock_indicators)}")
        pieces.append(f"  • Fake Scarcity Score: {fake_score:.2f}")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        if stock_indicators:
            suspicious_stock = sum(1 for item in stock_indicators if item.get("stock_change_logic") == "suspicious")
            pieces.append(f"📈 STOCK ИНДИКАТОРЫ:")
            pieces.append(f"  • Подозрительное поведение stock: {suspicious_stock}/{len(stock_indicators)}")
        if social_proof:
            total_notifications = social_proof.get("total_notifications_observed", 0)
            avg_interval = social_proof.get("avg_interval_seconds", 0)
            template_names = social_proof.get("template_names_detected", False)
            template_locations = social_proof.get("template_locations_detected", False)
            pieces.append(f"👥 SOCIAL PROOF:")
            pieces.append(f"  • Всего уведомлений: {total_notifications}")
            pieces.append(f"  • Средний интервал: {avg_interval}с")
            pieces.append(f"  • Шаблонные имена: {'❌ да' if template_names else '✅ нет'}")
            pieces.append(f"  • Шаблонные локации: {'❌ да' if template_locations else '✅ нет'}")
        if server_validation:
            stock_api = server_validation.get("stock_api_calls_detected", False)
            social_api = server_validation.get("social_proof_api_calls_detected", False)
            client_gen = server_validation.get("client_side_generation_suspected", False)
            pieces.append(f"🔍 СЕРВЕРНАЯ ВАЛИДАЦИЯ:")
            pieces.append(f"  • Stock API calls: {'✅ обнаружены' if stock_api else '❌ отсутствуют'}")
            pieces.append(f"  • Social proof API: {'✅ обнаружены' if social_api else '❌ отсутствуют'}")
            pieces.append(f"  • Клиентская генерация: {'❌ подозревается' if client_gen else '✅ не обнаружена'}")
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
fake_scarcity_browser_loop = LoopAgent(
    name="fake_scarcity_browser_loop",
    description="Итеративное тестирование Fake Scarcity: ложные индикаторы дефицита и социальные доказательства.",
    sub_agents=[
        fake_scarcity_decider_agent,
        fake_scarcity_navigator_agent,
        fake_scarcity_form_filler_agent,
        fake_scarcity_parser_agent,
        fake_scarcity_critic_agent,
        fake_scarcity_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=fake_scarcity_after_loop_callback,
)
fake_scarcity_root_agent = SequentialAgent(
    name="fake_scarcity_pipeline",
    description="Полный пайплайн для детектирования Fake Scarcity паттерна (ложные индикаторы дефицита).",
    sub_agents=[
        fake_scarcity_ingest_agent,
        fake_scarcity_browser_loop,
    ],
)