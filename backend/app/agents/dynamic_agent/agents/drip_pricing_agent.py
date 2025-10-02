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
drip_pricing_ingest_agent = Agent(
    name="drip_pricing_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Drip Pricing' - скрытых комиссий и доплат.",
    instruction=(
        "Ты — Ingest агент для детектирования DRIP PRICING паттерна. Создай план тестирования скрытых комиссий.\n\n"
        "Схема DripPricingPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Drip Pricing pattern - hidden fees and late price increases\",\n'
        '  \"target_site\": string,\n'
        '  \"product_service\": string|null,\n'
        '  \"success_criteria\": [\n'
        '    \"Complete checkout flow to final step\",\n'
        '    \"Track price changes at each step\",\n'
        '    \"Test different delivery/payment options\",\n'
        '    \"Document all fee additions and timing\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"initial_advertised_price\": 0.0,\n'
        '    \"step_prices\": [],\n'
        '    \"final_total_price\": 0.0,\n'
        '    \"price_increases\": [],\n'
        '    \"hidden_fees\": [],\n'
        '    \"fee_disclosure_timing\": [],\n'
        '    \"delta_percentage\": 0.0,\n'
        '    \"drip_pricing_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find product/service page\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Add to cart and note initial price\", \"track\": \"price_step_1\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Proceed through checkout steps\", \"track\": \"price_tracking\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test delivery/payment options changes\", \"track\": \"option_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze price progression and hidden fees\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Цель: полный чекаут до последнего шага (без реальной оплаты).\n"
        "2) Фиксировать цену на КАЖДОМ шаге: товар→корзина→доставка→оплата→итог.\n"
        "3) Тестировать изменения: разные способы доставки и оплаты.\n"
        "4) Пороги: Δtotal > 10% от начальной цены без раскрытия = drip pricing.\n"
        "5) Только чистый JSON.\n"
    ),
    output_key="plan",
)
drip_pricing_decider_agent = Agent(
    name="drip_pricing_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Drip Pricing паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования DRIP PRICING паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- pricing_metrics: {pricing_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"product_selection\"|\"cart\"|\"checkout\"|\"payment\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда прошли полный чекаут И зафиксировали все изменения цен.\n"
        "- parse: когда завершена одна из фаз чекаута и нужно зафиксировать цены.\n"
        "- act: когда нужно взаимодействовать с формами, выбрать опции, добавить в корзину.\n"
        "- navigate: когда нужно перейти между этапами чекаута или на страницы товаров.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ ПО ФАЗАМ:\n"
        "- Фаза 'product_selection': найти товар, зафиксировать базовую цену.\n"
        "- Фаза 'cart': добавить в корзину, проверить изменения, найти скрытые доплаты.\n"
        "- Фаза 'checkout': заполнить адрес доставки, тестировать разные варианты.\n"
        "- Фаза 'payment': выбрать способы оплаты, отслеживать финальные комиссии.\n"
        "- При каждом изменении цены: записывать timestamp, размер изменения, причину.\n\n"
        "Если Δtotal > 15% И скрытые комиссии появились только на поздних этапах — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
drip_pricing_navigator_agent = Agent(
    name="drip_pricing_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация через чекаут для отслеживания Drip Pricing.",
    instruction=(
        "Ты — Навигатор для детектирования DRIP PRICING паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "НАВИГАЦИЯ ПО ЧЕКАУТУ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущих цен\n"
        "B) ПЕРЕХОДЫ МЕЖДУ ЭТАПАМИ ЧЕКАУТА:\n"
        "   • Каталог → Страница товара → Корзина → Чекаут → Способы доставки → Способы оплаты → Подтверждение\n"
        "   • Использовать: browser_navigate { url: \"...\" }\n"
        "   • Кнопки продолжения: найти \"Add to Cart\", \"Proceed\", \"Continue\", \"Next\"\n"
        "   • Возврат назад: browser_navigate_back {} для тестирования изменений\n"
        "C) СПЕЦИАЛЬНЫЕ НАВИГАЦИОННЫЕ ЗАДАЧИ:\n"
        "   • Поиск товаров с \"от X руб.\" или \"starting at\"\n"
        "   • Переход между разными категориями доставки (Express, Standard, Free)\n"
        "   • Тестирование различных регионов доставки\n"
        "D) ОЖИДАНИЕ ЗАГРУЗКИ ЦЕН: browser_wait_for { text: \"Total\" или time: 3-5 }\n"
        "E) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с обновленными ценами\n\n"
        "ФИКСАЦИЯ ЦЕН:\n"
        "На каждом этапе записывай в state:\n"
        "- Текущая фаза (product/cart/checkout/payment)\n"
        "- Видимая цена/итог на этом этапе\n"
        "- Timestamp перехода\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
drip_pricing_form_filler_agent = Agent(
    name="drip_pricing_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Заполняет формы чекаута и отслеживает изменения цен.",
    instruction=(
        "Ты — агент форм для DRIP PRICING тестирования. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ОТСЛЕЖИВАНИЕ ЦЕН ПРИ КАЖДОМ ДЕЙСТВИИ:\n"
        "1) browser_snapshot — фиксация текущих цен ДО действия\n"
        "2) ПАРСИНГ ЦЕН из snapshot:\n"
        "   • Ищи: \"Total\", \"Subtotal\", \"Tax\", \"Shipping\", \"Service fee\", \"Grand Total\"\n"
        "   • Извлекай числовые значения и валюту\n"
        "   • Записывай в state[current_phase + '_price']\n"
        "3) ВЫПОЛНЕНИЕ ДЕЙСТВИЯ:\n"
        "   • Добавление в корзину: browser_click с кнопкой \"Add to Cart\"\n"
        "   • Заполнение адреса: browser_type с тестовыми данными (НЕ реальные!)\n"
        "   • Выбор доставки: browser_select_option или browser_click с radio buttons\n"
        "   • Способ оплаты: выбор без ввода реальных карт\n"
        "4) ТЕСТИРОВАНИЕ ОПЦИЙ:\n"
        "   • Переключение между Standard/Express доставкой\n"
        "   • Изменение региона доставки (локальный/международный)\n"
        "   • Разные способы оплаты (карта/наличные/PayPal)\n"
        "   • Дополнительные услуги (страховка, упаковка)\n"
        "5) ЗАПИСЬ ИЗМЕНЕНИЙ:\n"
        "   • Если цена изменилась: зафиксировать размер изменения и причину\n"
        "   • Новые комиссии: добавить в hidden_fees с описанием\n"
        "   • Timestamp каждого изменения\n"
        "6) ОЖИДАНИЕ: browser_wait_for для загрузки обновленных цен\n"
        "7) SNAPSHOT ПОСЛЕ: browser_snapshot для фиксации новых цен\n\n"
        "КРИТИЧЕСКИ ВАЖНО:\n"
        "- НЕ вводить реальные личные данные или банковские карты\n"
        "- Использовать тестовые данные: test@example.com, Test Address 123\n"
        "- НЕ совершать реальную покупку\n\n"
        "Возвращай только текст снапшота. Метрики цен пиши в state."
    ),
    output_key="last_page_text",
)
drip_pricing_parser_agent = Agent(
    name="drip_pricing_parser_agent",
    model=LLM_FLASH,
    description="Анализирует прогрессию цен и скрытые комиссии.",
    instruction=(
        "Ты — парсер для DRIP PRICING анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, pricing_state={pricing_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ ЦЕНОВОЙ ПРОГРЕССИИ:\n"
        "1) Извлеки из state все зафиксированные цены по этапам.\n"
        "2) Рассчитай изменения между этапами (Δ в % и абсолютных значениях).\n"
        "3) Идентифицируй скрытые комиссии: fees, которые появились поздно.\n"
        "4) Оцени прозрачность раскрытия: когда комиссия стала видна.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"initial_advertised_price\": number,\n'
        '    \"final_total_price\": number,\n'
        '    \"total_price_increase\": number,\n'
        '    \"price_increase_percentage\": number,\n'
        '    \"price_progression\": [\n'
        '      {\"step\": \"product\", \"price\": number, \"timestamp\": \"...\"},\n'
        '      {\"step\": \"cart\", \"price\": number, \"timestamp\": \"...\"},\n'
        '      {\"step\": \"checkout\", \"price\": number, \"timestamp\": \"...\"},\n'
        '      {\"step\": \"payment\", \"price\": number, \"timestamp\": \"...\"}\n'
        '    ],\n'
        '    \"hidden_fees_detected\": [\n'
        '      {\"name\": \"Shipping Fee\", \"amount\": number, \"introduced_at_step\": \"checkout\"},\n'
        '      {\"name\": \"Service Fee\", \"amount\": number, \"introduced_at_step\": \"payment\"}\n'
        '    ],\n'
        '    \"late_disclosure_fees\": number,\n'
        '    \"drip_pricing_score\": number,\n'
        '    \"drip_pricing_detected\": boolean\n'
        '  },\n'
        '  \"notes\": \"Описание найденных скрытых комиссий и их появления\"\n'
        "}\n\n"
        "ПОРОГИ DRIP PRICING ДЕТЕКТИРОВАНИЯ:\n"
        "- drip_pricing_detected = true, если price_increase_percentage > 15%\n"
        "- И если >50% увеличения происходит на последних двух этапах (checkout/payment)\n"
        "- ИЛИ если есть комиссии, появившиеся только после ввода личных данных\n"
        "- drip_pricing_score = (late_fees_amount / initial_price) * steps_delay_factor"
    ),
    output_key="parsed",
)
drip_pricing_critic_agent = Agent(
    name="drip_pricing_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Drip Pricing анализа.",
    instruction=(
        "Ты — критик для DRIP PRICING детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Пройден полный путь чекаута (минимум 4 этапа).\n"
        "2) Зафиксированы цены на каждом этапе с timestamp.\n"
        "3) Протестированы различные опции доставки/оплаты.\n"
        "4) Рассчитан общий процент увеличения цены.\n"
        "5) Идентифицированы скрытые комиссии и момент их раскрытия.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о найденных скрытых комиссиях и их влиянии на цену\n"
        "- reason: процент увеличения, количество поздних комиссий, этапы раскрытия\n"
        "- data: parsed.extracted с полной прогрессией цен\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Если >20% увеличения цены происходит после ввода контактных данных — серьезный drip pricing\n"
        "- Комиссии, появляющиеся только на этапе payment — красный флаг\n"
        "- Отсутствие предупреждения о дополнительных сборах — нарушение прозрачности\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно завершить чекаут или протестировать больше опций\"}"
    ),
    output_key="critic_json",
)
drip_pricing_result_agent = Agent(
    name="drip_pricing_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Drip Pricing анализа.",
    instruction=(
        "Ты — Result агент для DRIP PRICING паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ drip pricing анализ завершен:\n"
        "Сформируй отчет о Drip Pricing:\n"
        "- Обнаружены ли скрытые комиссии\n"
        "- Процент увеличения от заявленной цены\n"
        "- На каких этапах появились дополнительные сборы\n"
        "- Прозрачность раскрытия комиссий\n"
        "- Влияние на принятие решения покупателем\n"
        "- Рекомендации по улучшению прозрачности\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если не удалось дойти до финальных этапов чекаута → should_retry=true\n"
        "- Требуется реальная оплата для завершения → should_retry=false\n"
        "- Технические проблемы (таймауты, ошибки) → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: поведенческие аспекты раскрытия цен, влияние на пользовательский опыт."
    ),
    output_key="result_json",
)
def drip_pricing_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("💰 DRIP PRICING PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        initial_price = extracted.get("initial_advertised_price", 0)
        final_price = extracted.get("final_total_price", 0)
        increase_pct = extracted.get("price_increase_percentage", 0)
        hidden_fees = extracted.get("hidden_fees_detected", [])
        detected = extracted.get("drip_pricing_detected", False)
        score = extracted.get("drip_pricing_score", 0)
        pieces.append(f"📊 ЦЕНОВАЯ ПРОГРЕССИЯ:")
        pieces.append(f"  • Начальная цена: {initial_price}")
        pieces.append(f"  • Финальная цена: {final_price}")
        pieces.append(f"  • Увеличение: {increase_pct:.1f}%")
        pieces.append(f"  • Drip Pricing Score: {score:.2f}")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        if hidden_fees:
            pieces.append("💸 СКРЫТЫЕ КОМИССИИ:")
            for fee in hidden_fees[:3]:  # Показываем первые 3
                pieces.append(f"  • {fee.get('name', 'Unknown')}: +{fee.get('amount', 0)} (этап: {fee.get('introduced_at_step', 'unknown')})")
        progression = extracted.get("price_progression", [])
        if progression:
            pieces.append("📈 ЭТАПЫ ЧЕКАУТА:")
            for step in progression:
                pieces.append(f"  • {step.get('step', 'unknown')}: {step.get('price', 0)}")
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
drip_pricing_browser_loop = LoopAgent(
    name="drip_pricing_browser_loop",
    description="Итеративное тестирование Drip Pricing: скрытые комиссии в процессе чекаута.",
    sub_agents=[
        drip_pricing_decider_agent,
        drip_pricing_navigator_agent,
        drip_pricing_form_filler_agent,
        drip_pricing_parser_agent,
        drip_pricing_critic_agent,
        drip_pricing_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=drip_pricing_after_loop_callback,
)
drip_pricing_root_agent = SequentialAgent(
    name="drip_pricing_pipeline",
    description="Полный пайплайн для детектирования Drip Pricing паттерна (скрытые поздние комиссии).",
    sub_agents=[
        drip_pricing_ingest_agent,
        drip_pricing_browser_loop,
    ],
)