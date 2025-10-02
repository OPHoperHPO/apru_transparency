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
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "14"))
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
bait_and_switch_ingest_agent = Agent(
    name="bait_and_switch_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Bait & Switch' - подмены заманивающих предложений.",
    instruction=(
        "Ты — Ingest агент для детектирования BAIT & SWITCH паттерна. Создай план тестирования подмены предложений.\n\n"
        "Схема BaitAndSwitchPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Bait & Switch pattern - advertised offers that become unavailable or get replaced\",\n'
        '  \"target_site\": string,\n'
        '  \"advertised_offer\": string|null,\n'
        '  \"success_criteria\": [\n'
        '    \"Identify attractive advertised offer\",\n'
        '    \"Attempt to select/purchase advertised offer\",\n'
        '    \"Document any substitutions or unavailability\",\n'
        '    \"Compare final available options with initial advertisement\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"advertised_offer_details\": {},\n'
        '    \"final_available_offer\": {},\n'
        '    \"offer_substitution_detected\": false,\n'
        '    \"unavailability_reason\": null,\n'
        '    \"price_difference\": 0.0,\n'
        '    \"feature_differences\": [],\n'
        '    \"bait_and_switch_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find advertised offers or deals\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Document advertised offer details\", \"track\": \"advertisement_capture\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Attempt to select/purchase offer\", \"track\": \"selection_attempt\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Compare advertised vs available offers\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: выгодные предложения, акции, 'Best deal', специальные цены.\n"
        "2) Фиксировать: все детали рекламируемого предложения (цена, условия, особенности).\n"
        "3) Тестировать: доступность рекламируемого предложения при попытке выбора.\n"
        "4) Сравнивать: что было заявлено vs что реально доступно.\n"
        "5) Пороги: недоступность заявленного предложения без четкого объяснения = bait & switch.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
bait_and_switch_decider_agent = Agent(
    name="bait_and_switch_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Bait & Switch паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования BAIT & SWITCH паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- bait_switch_metrics: {bait_switch_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"discovery\"|\"documentation\"|\"selection_test\"|\"comparison\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда зафиксированы детали рекламного предложения И протестирована его доступность.\n"
        "- parse: когда завершена попытка выбора предложения и нужно сравнить с рекламой.\n"
        "- act: когда нужно задокументировать предложение или попытаться его выбрать.\n"
        "- navigate: когда нужно найти рекламируемые предложения или перейти к оформлению.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'discovery': найти страницы с заманчивыми предложениями, акциями.\n"
        "- Фаза 'documentation': детально зафиксировать все детали рекламы.\n"
        "- Фаза 'selection_test': попытаться выбрать/купить рекламируемое предложение.\n"
        "- Фаза 'comparison': сравнить доступные варианты с первоначальной рекламой.\n"
        "- Обращать внимание на redirects, замены, 'sold out', альтернативные предложения.\n\n"
        "Если рекламируемое предложение недоступно И предлагается более дорогая замена — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
bait_and_switch_navigator_agent = Agent(
    name="bait_and_switch_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска рекламируемых предложений и тестирования их доступности.",
    instruction=(
        "Ты — Навигатор для детектирования BAIT & SWITCH паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК РЕКЛАМИРУЕМЫХ ПРЕДЛОЖЕНИЙ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО ЗАМАНЧИВЫМ ПРЕДЛОЖЕНИЯМ:\n"
        "   • Landing pages с 'Special offers', 'Limited deals'\n"
        "   • Banner ads с привлекательными ценами\n"
        "   • Category pages с 'Featured deals'\n"
        "   • Email campaign links (если доступны)\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК РАЗНЫХ ТИПОВ ПРЕДЛОЖЕНИЙ:\n"
        "   • Pricing plans с 'Most popular' или 'Best value'\n"
        "   • Product bundles с экономией\n"
        "   • Subscription offers с introductory rates\n"
        "   • Clearance или sale items\n"
        "D) ПЕРЕХОДЫ К ОФОРМЛЕНИЮ:\n"
        "   • От рекламного блока к форме заказа\n"
        "   • От цены к детальной странице товара\n"
        "   • От 'Buy now' к checkout процессу\n"
        "E) ОЖИДАНИЕ ЗАГРУЗКИ: browser_wait_for { text: \"Price\" или time: 3 }\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с актуальными предложениями\n\n"
        "ФИКСАЦИЯ РЕКЛАМНЫХ ЭЛЕМЕНТОВ:\n"
        "На каждой странице записывай в state:\n"
        "- Текст рекламных предложений\n"
        "- Заявленные цены и условия\n"
        "- Screenshots ключевых рекламных блоков\n"
        "- URLs переходов от рекламы к оформлению\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
bait_and_switch_form_filler_agent = Agent(
    name="bait_and_switch_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Документирует рекламные предложения и тестирует их реальную доступность.",
    instruction=(
        "Ты — агент тестирования для BAIT & SWITCH. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ДОКУМЕНТИРОВАНИЕ И ТЕСТИРОВАНИЕ ПРЕДЛОЖЕНИЙ:\n"
        "1) browser_snapshot — фиксация рекламных материалов\n"
        "2) ДЕТАЛЬНОЕ ДОКУМЕНТИРОВАНИЕ (фаза 'documentation'):\n"
        "   • Извлечь точный текст рекламных заголовков\n"
        "   • Зафиксировать заявленные цены, скидки, условия\n"
        "   • Записать особенности предложения (features, benefits)\n"
        "   • Screenshot ключевых рекламных блоков\n"
        "3) ТЕСТИРОВАНИЕ ДОСТУПНОСТИ (фаза 'selection_test'):\n"
        "   • Клик по рекламируемому предложению: browser_click\n"
        "   • Попытка добавить в корзину: browser_click на 'Add to cart'\n"
        "   • Заполнение форм для оформления заказа\n"
        "   • Отслеживание redirects и изменений предложения\n"
        "4) ФИКСАЦИЯ ИЗМЕНЕНИЙ:\n"
        "   • Если появился 'Not available' или 'Sold out'\n"
        "   • Если предложена замена с другой ценой\n"
        "   • Если условия изменились в процессе оформления\n"
        "   • Если произошел redirect на другую страницу/товар\n"
        "5) СРАВНИТЕЛЬНЫЙ АНАЛИЗ:\n"
        "   • Сопоставить изначальную рекламу с финальным предложением\n"
        "   • Зафиксировать различия в цене, функциях, условиях\n"
        "   • Записать предложенные альтернативы\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • advertised_vs_available: детальное сравнение\n"
        "   • substitution_type: 'unavailable', 'higher_price', 'reduced_features'\n"
        "   • explanation_provided: качество объяснения изменений\n"
        "7) SNAPSHOT ПОСЛЕ ТЕСТИРОВАНИЯ: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ BAIT & SWITCH:\n"
        "- Рекламируемое предложение недоступно без четкого объяснения\n"
        "- Предложена более дорогая альтернатива\n"
        "- Условия существенно отличаются от заявленных\n\n"
        "Возвращай только текст снапшота. Результаты сравнения пиши в state."
    ),
    output_key="last_page_text",
)
bait_and_switch_parser_agent = Agent(
    name="bait_and_switch_parser_agent",
    model=LLM_FLASH,
    description="Анализирует соответствие рекламируемых и доступных предложений.",
    instruction=(
        "Ты — парсер для BAIT & SWITCH анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, bait_switch_state={bait_switch_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ СООТВЕТСТВИЯ ПРЕДЛОЖЕНИЙ:\n"
        "1) Извлеки из state детали рекламируемого и финального предложений.\n"
        "2) Сравни ключевые параметры: цену, функции, условия, доступность.\n"
        "3) Оцени качество объяснений любых изменений или недоступности.\n"
        "4) Определи тип и серьезность обнаруженных расхождений.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"advertised_offer\": {\n'
        '      \"title\": \"...\",\n'
        '      \"price\": \"...\",\n'
        '      \"features\": [...],\n'
        '      \"conditions\": \"...\"\n'
        '    },\n'
        '    \"final_available_offer\": {\n'
        '      \"title\": \"...\",\n'
        '      \"price\": \"...\",\n'
        '      \"features\": [...],\n'
        '      \"conditions\": \"...\",\n'
        '      \"availability_status\": \"available|unavailable|substituted\"\n'
        '    },\n'
        '    \"discrepancies_found\": [\n'
        '      {\n'
        '        \"type\": \"price_increase|feature_reduction|unavailability\",\n'
        '        \"description\": \"...\",\n'
        '        \"impact_severity\": \"low|medium|high\"\n'
        '      }\n'
        '    ],\n'
        '    \"explanation_quality\": \"clear|vague|absent\",\n'
        '    \"alternative_offers_provided\": boolean,\n'
        '    \"bait_and_switch_detected\": boolean,\n'
        '    \"severity_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных расхождений между рекламой и реальностью\"\n'
        "}\n\n"
        "КРИТЕРИИ BAIT & SWITCH ДЕТЕКТИРОВАНИЯ:\n"
        "- bait_and_switch_detected = true, если рекламируемое предложение недоступно без четкого объяснения\n"
        "- ИЛИ если предложена существенно худшая альтернатива (цена выше >10%, меньше функций)\n"
        "- ИЛИ если условия предложения существенно изменились в процессе оформления\n"
        "- severity_score = impact_magnitude * explanation_quality_penalty"
    ),
    output_key="parsed",
)
bait_and_switch_critic_agent = Agent(
    name="bait_and_switch_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Bait & Switch анализа.",
    instruction=(
        "Ты — критик для BAIT & SWITCH детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдены и задокументированы рекламируемые предложения.\n"
        "2) Протестирована реальная доступность рекламируемых предложений.\n"
        "3) Проведено детальное сравнение заявленного и доступного.\n"
        "4) Оценено качество объяснений любых расхождений.\n"
        "5) Определена серьезность обнаруженных проблем.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о соответствии рекламируемых и доступных предложений\n"
        "- reason: типы найденных расхождений, качество объяснений, серьезность\n"
        "- data: parsed.extracted со всеми деталями сравнения\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Недоступность заявленного предложения без объяснения — явный bait & switch\n"
        "- Существенное увеличение цены (>15%) — серьезная проблема\n"
        "- Сокращение заявленных функций — misleading advertising\n"
        "- Отсутствие альтернатив или их неадекватность — poor customer experience\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти рекламируемые предложения или протестировать их доступность\"}"
    ),
    output_key="critic_json",
)
bait_and_switch_result_agent = Agent(
    name="bait_and_switch_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Bait & Switch анализа.",
    instruction=(
        "Ты — Result агент для BAIT & SWITCH паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ bait & switch анализ завершен:\n"
        "Сформируй отчет о Bait & Switch:\n"
        "- Обнаружены ли случаи подмены рекламируемых предложений\n"
        "- Типы и серьезность найденных расхождений\n"
        "- Качество предоставленных объяснений\n"
        "- Адекватность предложенных альтернатив\n"
        "- Влияние на принятие решений потребителем\n"
        "- Рекомендации по обеспечению соответствия рекламы и реальности\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если рекламируемые предложения не найдены → should_retry=true с поиском в других разделах\n"
        "- Сайт не использует заманчивые предложения → should_retry=false\n"
        "- Технические проблемы с доступом к предложениям → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность рекламных обещаний и их выполнение в реальности."
    ),
    output_key="result_json",
)
def bait_and_switch_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🎣 BAIT & SWITCH PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        advertised = extracted.get("advertised_offer", {})
        final = extracted.get("final_available_offer", {})
        discrepancies = extracted.get("discrepancies_found", [])
        detected = extracted.get("bait_and_switch_detected", False)
        severity = extracted.get("severity_score", 0)
        explanation_quality = extracted.get("explanation_quality", "unknown")
        pieces.append(f"📊 СРАВНЕНИЕ ПРЕДЛОЖЕНИЙ:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Серьезность нарушения: {severity:.2f}")
        pieces.append(f"  • Качество объяснений: {explanation_quality}")
        if advertised:
            pieces.append(f"📢 РЕКЛАМИРУЕМОЕ ПРЕДЛОЖЕНИЕ:")
            pieces.append(f"  • Название: {advertised.get('title', 'N/A')}")
            pieces.append(f"  • Цена: {advertised.get('price', 'N/A')}")
        if final:
            pieces.append(f"🎯 ФИНАЛЬНОЕ ПРЕДЛОЖЕНИЕ:")
            pieces.append(f"  • Название: {final.get('title', 'N/A')}")
            pieces.append(f"  • Цена: {final.get('price', 'N/A')}")
            pieces.append(f"  • Статус: {final.get('availability_status', 'unknown')}")
        if discrepancies:
            pieces.append(f"⚠️ ОБНАРУЖЕННЫЕ РАСХОЖДЕНИЯ:")
            for i, disc in enumerate(discrepancies[:3]):  # Показываем первые 3
                disc_type = disc.get("type", "unknown")
                desc = disc.get("description", "N/A")
                severity_level = disc.get("impact_severity", "unknown")
                pieces.append(f"  {i+1}. {disc_type} ({severity_level}): {desc}")
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
bait_and_switch_browser_loop = LoopAgent(
    name="bait_and_switch_browser_loop",
    description="Итеративное тестирование Bait & Switch: подмена рекламируемых предложений.",
    sub_agents=[
        bait_and_switch_decider_agent,
        bait_and_switch_navigator_agent,
        bait_and_switch_form_filler_agent,
        bait_and_switch_parser_agent,
        bait_and_switch_critic_agent,
        bait_and_switch_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=bait_and_switch_after_loop_callback,
)
bait_and_switch_root_agent = SequentialAgent(
    name="bait_and_switch_pipeline",
    description="Полный пайплайн для детектирования Bait & Switch паттерна (подмена заманивающих предложений).",
    sub_agents=[
        bait_and_switch_ingest_agent,
        bait_and_switch_browser_loop,
    ],
)