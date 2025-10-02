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
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "16"))
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
sneak_into_basket_ingest_agent = Agent(
    name="sneak_into_basket_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Sneak Into Basket' - предвыбранных платных опций.",
    instruction=(
        "Ты — Ingest агент для детектирования SNEAK INTO BASKET паттерна. Создай план тестирования предварительно выбранных опций.\n\n"
        "Схема SneakIntoBasketPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Sneak Into Basket pattern - preselected paid options and auto-added services\",\n'
        '  \"target_site\": string,\n'
        '  \"product_service\": string|null,\n'
        '  \"success_criteria\": [\n'
        '    \"Identify base service/product selection\",\n'
        '    \"Check for preselected additional options\",\n'
        '    \"Test impact of unchecking preselected items\",\n'
        '    \"Document default states of all checkboxes/options\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"base_service_price\": 0.0,\n'
        '    \"preselected_options\": [],\n'
        '    \"preselected_total_cost\": 0.0,\n'
        '    \"after_unchecking_price\": 0.0,\n'
        '    \"hidden_preselections\": [],\n'
        '    \"opt_out_difficulty\": 0,\n'
        '    \"sneak_detected_options\": [],\n'
        '    \"sneak_into_basket_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find service/product selection page\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Select basic service and note default options\", \"track\": \"default_state\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test unchecking preselected options\", \"track\": \"option_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze preselection patterns and pricing impact\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Цель: найти базовую услугу и проанализировать все дополнительные опции.\n"
        "2) Отслеживать: какие чекбоксы/опции включены по умолчанию.\n"
        "3) Тестировать: изменение итоговой суммы при отключении опций.\n"
        "4) Искать: скрытые или плохо заметные предварительные выборы.\n"
        "5) Пороги: если предвыбранные платные опции увеличивают цену >0% без явного согласия.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
sneak_into_basket_decider_agent = Agent(
    name="sneak_into_basket_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Sneak Into Basket паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования SNEAK INTO BASKET паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- basket_metrics: {basket_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"product_selection\"|\"option_analysis\"|\"uncheck_testing\"|\"final_check\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда проанализированы все предвыбранные опции И проверено влияние их отключения.\n"
        "- parse: когда нужно проанализировать текущие состояния чекбоксов и цены.\n"
        "- act: когда нужно взаимодействовать с опциями, чекбоксами, переключателями.\n"
        "- navigate: когда нужно перейти на страницы выбора услуг или в корзину.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'product_selection': найти базовый продукт/услугу, зафиксировать стартовую цену.\n"
        "- Фаза 'option_analysis': проверить все дополнительные опции, страховки, услуги.\n"
        "- Фаза 'uncheck_testing': методично отключать предвыбранные опции и отслеживать ценовые изменения.\n"
        "- Фаза 'final_check': проверить корзину/итоговую страницу на предмет скрытых добавлений.\n"
        "- При каждом чекбоксе: фиксировать default state (checked/unchecked), cost impact, visibility.\n\n"
        "Если найдены платные предвыбранные опции БЕЗ явного согласия — вызови finish с детализацией.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
sneak_into_basket_navigator_agent = Agent(
    name="sneak_into_basket_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска и анализа предвыбранных опций.",
    instruction=(
        "Ты — Навигатор для детектирования SNEAK INTO BASKET паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "НАВИГАЦИЯ ПО ОПЦИЯМ И УСЛУГАМ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) ПОИСК СТРАНИЦ С ОПЦИЯМИ:\n"
        "   • Страницы выбора тарифов/планов\n"
        "   • Страницы дополнительных услуг (insurance, warranty, premium support)\n"
        "   • Корзина с возможными автодополнениями\n"
        "   • Checkout страницы с доп. опциями\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Ищи разделы: \"Additional Options\", \"Extras\", \"Add-ons\", \"Insurance\"\n"
        "   • Прокрутка до секций с чекбоксами: browser_scroll или Page Down\n"
        "   • Переход между табами опций\n"
        "D) ОЖИДАНИЕ ЗАГРУЗКИ ОПЦИЙ: browser_wait_for { text: \"Options\" или time: 3 }\n"
        "E) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с видимыми опциями\n\n"
        "ФИКСАЦИЯ ОПЦИЙ:\n"
        "На каждой странице записывай в state:\n"
        "- Количество видимых чекбоксов/переключателей\n"
        "- Их текущие состояния (checked/unchecked)\n"
        "- Цены или влияние на итог\n"
        "- Видимость и размещение (заметные/скрытые)\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
sneak_into_basket_form_filler_agent = Agent(
    name="sneak_into_basket_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Взаимодействует с чекбоксами и опциями для тестирования предварительных выборов.",
    instruction=(
        "Ты — агент опций для SNEAK INTO BASKET тестирования. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "МЕТОДИЧНОЕ ТЕСТИРОВАНИЕ ОПЦИЙ:\n"
        "1) browser_snapshot — анализ всех видимых опций\n"
        "2) ИНВЕНТАРИЗАЦИЯ ЧЕКБОКСОВ:\n"
        "   • Найти все input[type='checkbox'], radio buttons, toggle switches\n"
        "   • Идентифицировать их текущие состояния (checked/unchecked)\n"
        "   • Прочитать labels и связанные цены\n"
        "3) ФИКСАЦИЯ DEFAULT СОСТОЯНИЙ:\n"
        "   • Записать в state каждую опцию: name, default_state, price, visibility_score\n"
        "   • Особо отметить предвыбранные платные опции\n"
        "4) ТЕСТИРОВАНИЕ ПЕРЕКЛЮЧЕНИЙ:\n"
        "   • Для каждого checked по умолчанию чекбокса:\n"
        "     - browser_click для отключения\n"
        "     - browser_wait_for для обновления цены\n"
        "     - Зафиксировать изменение итога\n"
        "   • Для unchecked опций: попробовать включить и проверить цену\n"
        "5) ПОИСК СКРЫТЫХ ПРЕДВАРИТЕЛЬНЫХ ВЫБОРОВ:\n"
        "   • Мелкий текст с предвыбранными услугами\n"
        "   • Dropdown'ы с не-базовыми default значениями\n"
        "   • Скрытые input fields со значениями\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • sneak_options: список найденных предвыбранных платных опций\n"
        "   • price_impact: изменение цены при отключении каждой опции\n"
        "   • visibility_issues: плохо заметные или введающие в заблуждение опции\n"
        "7) SNAPSHOT ПОСЛЕ ИЗМЕНЕНИЙ: browser_snapshot\n\n"
        "ВНИМАНИЕ К ДЕТАЛЯМ:\n"
        "- Ищи предвыбранные страховки, расширенные гарантии, premium поддержку\n"
        "- Отмечай размер шрифта и контрастность чекбоксов отказа\n"
        "- Фиксируй, если отключение опции \"скрыто\" или требует дополнительных кликов\n\n"
        "Возвращай только текст снапшота. Детали опций пиши в state."
    ),
    output_key="last_page_text",
)
sneak_into_basket_parser_agent = Agent(
    name="sneak_into_basket_parser_agent",
    model=LLM_FLASH,
    description="Анализирует предвыбранные опции и их влияние на цену.",
    instruction=(
        "Ты — парсер для SNEAK INTO BASKET анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, basket_state={basket_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ ПРЕДВАРИТЕЛЬНЫХ ВЫБОРОВ:\n"
        "1) Извлеки из state все найденные опции с их default states.\n"
        "2) Рассчитай общую стоимость предвыбранных платных опций.\n"
        "3) Оцени сложность отказа от каждой опции (клики, видимость).\n"
        "4) Определи category каждой опции (insurance, premium, addon, etc.).\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"base_service_price\": number,\n'
        '    \"total_preselected_cost\": number,\n'
        '    \"preselected_options_found\": [\n'
        '      {\n'
        '        \"name\": \"Premium Support\",\n'
        '        \"cost\": number,\n'
        '        \"default_state\": \"checked\"|\"unchecked\",\n'
        '        \"category\": \"premium|insurance|addon|upgrade\",\n'
        '        \"opt_out_difficulty\": number,\n'
        '        \"visibility_score\": number,\n'
        '        \"sneaky_indicators\": [\"small_font\", \"hidden_checkbox\", \"misleading_label\"]\n'
        '      }\n'
        '    ],\n'
        '    \"total_sneak_cost\": number,\n'
        '    \"cost_increase_percentage\": number,\n'
        '    \"avg_opt_out_difficulty\": number,\n'
        '    \"sneak_into_basket_detected\": boolean,\n'
        '    \"severity_score\": number\n'
        '  },\n'
        '  \"notes\": \"Описание найденных предварительных выборов и их воздействия\"\n'
        "}\n\n"
        "КРИТЕРИИ SNEAKING ДЕТЕКТИРОВАНИЯ:\n"
        "- sneak_into_basket_detected = true, если найдены платные предвыбранные опции БЕЗ явного согласия пользователя\n"
        "- ИЛИ если cost_increase_percentage > 5% от базовой цены за счет defaults\n"
        "- ИЛИ если avg_opt_out_difficulty > 2 (сложно отключить)\n"
        "- severity_score = (sneak_cost / base_cost) * difficulty_multiplier * visibility_penalty"
    ),
    output_key="parsed",
)
sneak_into_basket_critic_agent = Agent(
    name="sneak_into_basket_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Sneak Into Basket анализа.",
    instruction=(
        "Ты — критик для SNEAK INTO BASKET детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдена и проанализирована базовая услуга/продукт.\n"
        "2) Проверены все дополнительные опции на предмет предварительного выбора.\n"
        "3) Протестировано отключение предвыбранных опций.\n"
        "4) Рассчитано ценовое влияние предварительных выборов.\n"
        "5) Оценена сложность отказа от каждой опции.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о найденных предварительных выборах и их влиянии\n"
        "- reason: количество sneaky опций, общая стоимость, сложность отказа\n"
        "- data: parsed.extracted со всеми деталями опций\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Предвыбранные страховки/гарантии без явного согласия — серьезное нарушение\n"
        "- Скрытые или плохо заметные чекбоксы отказа — red flag\n"
        "- Увеличение цены >10% за счет предвыборов — значительный sneak\n"
        "- Опции, которые сложно отключить (>3 кликов) — препятствие для пользователя\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно протестировать больше опций или страниц\"}"
    ),
    output_key="critic_json",
)
sneak_into_basket_result_agent = Agent(
    name="sneak_into_basket_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Sneak Into Basket анализа.",
    instruction=(
        "Ты — Result агент для SNEAK INTO BASKET паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ анализ предварительных выборов завершен:\n"
        "Сформируй отчет о Sneak Into Basket:\n"
        "- Обнаружены ли предвыбранные платные опции\n"
        "- Категории найденных предварительных выборов\n"
        "- Влияние на итоговую цену\n"
        "- Сложность отказа от навязанных опций\n"
        "- Видимость и честность представления опций\n"
        "- Рекомендации по улучшению прозрачности\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если не найдены страницы с опциями → should_retry=true с другими разделами\n"
        "- Сайт не использует дополнительные опции → should_retry=false\n"
        "- Технические проблемы → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность и прозрачность предварительных выборов, влияние на решение пользователя."
    ),
    output_key="result_json",
)
def sneak_into_basket_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🛒 SNEAK INTO BASKET PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        base_price = extracted.get("base_service_price", 0)
        sneak_cost = extracted.get("total_sneak_cost", 0)
        increase_pct = extracted.get("cost_increase_percentage", 0)
        options = extracted.get("preselected_options_found", [])
        detected = extracted.get("sneak_into_basket_detected", False)
        severity = extracted.get("severity_score", 0)
        avg_difficulty = extracted.get("avg_opt_out_difficulty", 0)
        pieces.append(f"📊 АНАЛИЗ ПРЕДВАРИТЕЛЬНЫХ ВЫБОРОВ:")
        pieces.append(f"  • Базовая цена: {base_price}")
        pieces.append(f"  • Стоимость предвыборов: {sneak_cost}")
        pieces.append(f"  • Увеличение цены: {increase_pct:.1f}%")
        pieces.append(f"  • Сложность отказа (ср.): {avg_difficulty:.1f}")
        pieces.append(f"  • Тяжесть нарушения: {severity:.2f}")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        if options:
            pieces.append("🎯 НАЙДЕННЫЕ ПРЕДВАРИТЕЛЬНЫЕ ВЫБОРЫ:")
            for i, option in enumerate(options[:4]):  # Показываем первые 4
                name = option.get('name', 'Unknown')
                cost = option.get('cost', 0)
                category = option.get('category', 'unknown')
                difficulty = option.get('opt_out_difficulty', 0)
                pieces.append(f"  {i+1}. {name} (+{cost}) - {category} (сложность отказа: {difficulty})")
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
sneak_into_basket_browser_loop = LoopAgent(
    name="sneak_into_basket_browser_loop",
    description="Итеративное тестирование Sneak Into Basket: предварительно выбранные платные опции.",
    sub_agents=[
        sneak_into_basket_decider_agent,
        sneak_into_basket_navigator_agent,
        sneak_into_basket_form_filler_agent,
        sneak_into_basket_parser_agent,
        sneak_into_basket_critic_agent,
        sneak_into_basket_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=sneak_into_basket_after_loop_callback,
)
sneak_into_basket_root_agent = SequentialAgent(
    name="sneak_into_basket_pipeline",
    description="Полный пайплайн для детектирования Sneak Into Basket паттерна (предвыбранные платные опции).",
    sub_agents=[
        sneak_into_basket_ingest_agent,
        sneak_into_basket_browser_loop,
    ],
)