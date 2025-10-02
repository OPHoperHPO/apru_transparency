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
currency_manipulation_ingest_agent = Agent(
    name="currency_manipulation_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Currency Manipulation' - введение в заблуждение единицами.",
    instruction=(
        "Ты — Ingest агент для детектирования CURRENCY MANIPULATION паттерна. Создай план поиска manipulative pricing units.\n\n"
        "Схема CurrencyManipulationPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Currency Manipulation pattern - misleading pricing units and currency conversions\",\n'
        '  \"target_site\": string,\n'
        '  \"pricing_contexts\": [\"loans_credit\", \"investments\", \"subscriptions\", \"international_services\"],\n'
        '  \"success_criteria\": [\n'
        '    \"Find pricing in different units (daily vs annual rates)\",\n'
        '    \"Test currency switching and conversion transparency\",\n'
        '    \"Check for effective rate vs promotional rate disclosure\",\n'
        '    \"Verify presence of local currency converters\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"misleading_rate_units\": [],\n'
        '    \"currency_conversion_transparency\": {},\n'
        '    \"promotional_vs_effective_rates\": {},\n'
        '    \"local_currency_converter_available\": false,\n'
        '    \"unit_manipulation_score\": 0.0,\n'
        '    \"currency_manipulation_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find pricing and rate information\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test currency switching options\", \"track\": \"currency_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Analyze rate unit presentations\", \"track\": \"rate_analysis\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test conversion transparency\", \"track\": \"conversion_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze currency and unit manipulation patterns\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: процентные ставки, subscription pricing, international payments.\n"
        "2) Тестировать: переключение валют, conversion rates, unit clarity.\n"
        "3) Анализировать: daily vs annual rates, promotional vs effective rates.\n"
        "4) Проверять: наличие THB converter, clear rate disclosures.\n"
        "5) Пороги: misleading unit presentation без clear converter = currency manipulation.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
currency_manipulation_decider_agent = Agent(
    name="currency_manipulation_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Currency Manipulation паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования CURRENCY MANIPULATION паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- currency_metrics: {currency_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"exploration\"|\"currency_testing\"|\"rate_analysis\"|\"conversion_testing\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда протестированы currency options И проанализированы rate units И проверена conversion transparency.\n"
        "- parse: когда завершена одна из фаз тестирования currency/rate presentation.\n"
        "- act: когда нужно тестировать currency switching, анализировать rates, проверять converters.\n"
        "- navigate: когда нужно найти pricing pages или переключиться между currency modes.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'exploration': найти страницы с pricing, rates, international payments.\n"
        "- Фаза 'currency_testing': переключать валюты и тестировать transparency.\n"
        "- Фаза 'rate_analysis': анализировать unit presentation (daily vs annual, etc.).\n"
        "- Фаза 'conversion_testing': проверить наличие и качество currency converters.\n"
        "- Искать: misleading unit labeling, hidden conversion fees, unclear effective rates.\n\n"
        "Если найдены misleading rate units БЕЗ clear converter ИЛИ hidden conversion costs — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
currency_manipulation_navigator_agent = Agent(
    name="currency_manipulation_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска pricing и currency information.",
    instruction=(
        "Ты — Навигатор для детектирования CURRENCY MANIPULATION паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК CURRENCY И RATE INFORMATION:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО PRICING AREAS:\n"
        "   • Loan/credit pages с interest rates\n"
        "   • Investment platforms с returns/fees\n"
        "   • Subscription services с international pricing\n"
        "   • E-commerce с multi-currency support\n"
        "   • Financial services с currency exchange\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК CURRENCY CONTROLS:\n"
        "   • Currency switcher dropdown menus\n"
        "   • Region/country selection options\n"
        "   • Language settings affecting currency display\n"
        "   • Payment method selection с currency implications\n"
        "D) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Interest rate calculators\n"
        "   • Currency conversion tools\n"
        "   • Pricing comparison tables\n"
        "   • International payment gateways\n"
        "E) RATE DISCLOSURE AREAS:\n"
        "   • Fine print sections\n"
        "   • Terms and conditions с rate details\n"
        "   • FAQ sections о fees и rates\n"
        "   • Regulatory disclosure pages\n"
        "F) ОЖИДАНИЕ ЗАГРУЗКИ: browser_wait_for { text: \"Rate\" или time: 3 }\n"
        "G) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с visible pricing/rates\n\n"
        "ФИКСАЦИЯ CURRENCY PATTERNS:\n"
        "На каждой странице записывай в state:\n"
        "- Обнаруженные rate presentations и их units\n"
        "- Currency options и switching mechanisms\n"
        "- Conversion transparency levels\n"
        "- Disclosed vs undisclosed fees/rates\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
currency_manipulation_form_filler_agent = Agent(
    name="currency_manipulation_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Тестирует currency switching и анализирует rate presentations.",
    instruction=(
        "Ты — агент тестирования currency для CURRENCY MANIPULATION. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "SYSTEMATIC CURRENCY/RATE TESTING:\n"
        "1) browser_snapshot — фиксация current pricing state\n"
        "2) CURRENCY SWITCHING TESTING (фаза 'currency_testing'):\n"
        "   • Найти currency switcher: browser_select_option или browser_click\n"
        "   • Переключить на разные валюты (USD, EUR, THB, etc.)\n"
        "   • Сравнить pricing consistency между валютами\n"
        "   • Проверить conversion rate transparency\n"
        "3) RATE UNIT ANALYSIS (фаза 'rate_analysis'):\n"
        "   • Записать все найденные rate presentations\n"
        "   • Идентифицировать misleading units: daily rate vs annual rate\n"
        "   • Проверить promotional rate vs effective rate disclosure\n"
        "   • Найти APR/effective rate calculations если доступны\n"
        "4) CONVERSION TRANSPARENCY TESTING (фаза 'conversion_testing'):\n"
        "   • Искать built-in currency converters: browser_click на converter tools\n"
        "   • Тестировать real-time rate updates\n"
        "   • Проверить disclosure conversion fees\n"
        "   • Сравнить displayed rate vs market rate (если возможно)\n"
        "5) MISLEADING PRESENTATION DETECTION:\n"
        "   • Intermediate currency токены вместо direct THB\n"
        "   • Daily/weekly rates instead of annual для loans\n"
        "   • Promotional rates без effective rate context\n"
        "   • Hidden conversion fees в checkout процессе\n"
        "6) CALCULATOR TESTING:\n"
        "   • Если есть rate calculators: input test values\n"
        "   • Проверить accuracy расчетов\n"
        "   • Сравнить calculator results vs advertised rates\n"
        "7) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • rate_unit_analysis: misleading vs clear presentations\n"
        "   • conversion_transparency_scores: fee disclosure quality\n"
        "   • effective_vs_promotional_rates: comparison matrix\n"
        "8) SNAPSHOT ПОСЛЕ АНАЛИЗА: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ CURRENCY MANIPULATION:\n"
        "- Misleading rate units (daily instead of annual) без converter\n"
        "- Hidden conversion fees или poor rate disclosure\n"
        "- Intermediate currency без clear THB equivalent\n"
        "- Promotional rates без effective rate warnings\n\n"
        "Возвращай только текст снапшота. Currency analysis results пиши в state."
    ),
    output_key="last_page_text",
)
currency_manipulation_parser_agent = Agent(
    name="currency_manipulation_parser_agent",
    model=LLM_FLASH,
    description="Анализирует manipulative currency и unit presentations.",
    instruction=(
        "Ты — парсер для CURRENCY MANIPULATION анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, currency_state={currency_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ CURRENCY/UNIT MANIPULATION:\n"
        "1) Извлеки из state все currency и rate testing results.\n"
        "2) Классифицируй misleading presentations по severity.\n"
        "3) Оцени transparency conversion mechanisms.\n"
        "4) Проанализируй impact на user understanding эффективных costs.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"rate_unit_manipulation\": {\n'
        '      \"misleading_rate_presentations\": [\n'
        '        {\n'
        '          \"displayed_unit\": \"daily_rate|weekly_rate|token_rate\",\n'
        '          \"actual_effective_unit\": \"annual_rate|thb_equivalent\",\n'
        '          \"conversion_factor\": number,\n'
        '          \"transparency_provided\": boolean,\n'
        '          \"manipulation_severity\": \"low|medium|high\"\n'
        '        }\n'
        '      ],\n'
        '      \"effective_rate_disclosure_quality\": \"clear|vague|absent\"\n'
        '    },\n'
        '    \"currency_conversion_analysis\": {\n'
        '      \"conversion_transparency_score\": number,\n'
        '      \"hidden_conversion_fees_detected\": boolean,\n'
        '      \"real_time_rates_provided\": boolean,\n'
        '      \"local_currency_converter_available\": boolean,\n'
        '      \"conversion_fee_disclosure_quality\": \"clear|hidden|absent\"\n'
        '    },\n'
        '    \"promotional_rate_analysis\": {\n'
        '      \"promotional_rates_found\": number,\n'
        '      \"effective_rates_disclosed\": number,\n'
        '      \"rate_duration_clarity\": \"clear|vague|absent\",\n'
        '      \"post_promotional_rate_disclosed\": boolean\n'
        '    },\n'
        '    \"currency_manipulation_detected\": boolean,\n'
        '    \"overall_manipulation_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных currency manipulation techniques\"\n'
        "}\n\n"
        "КРИТЕРИИ CURRENCY MANIPULATION ДЕТЕКТИРОВАНИЯ:\n"
        "- currency_manipulation_detected = true, если найдены misleading rate units БЕЗ clear converter\n"
        "- ИЛИ если hidden conversion fees без proper disclosure\n"
        "- ИЛИ если promotional rates без effective rate context\n"
        "- ИЛИ если intermediate currency без local equivalent показан\n"
        "- overall_manipulation_score = weighted_average(rate_unit_misleading, conversion_transparency, promotional_clarity)"
    ),
    output_key="parsed",
)
currency_manipulation_critic_agent = Agent(
    name="currency_manipulation_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Currency Manipulation анализа.",
    instruction=(
        "Ты — критик для CURRENCY MANIPULATION детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Проанализированы rate unit presentations на misleading nature.\n"
        "2) Протестирована currency conversion transparency.\n"
        "3) Проверена promotional vs effective rate disclosure.\n"
        "4) Оценена доступность local currency converters.\n"
        "5) Определена общая степень currency manipulation.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о найденных currency manipulation practices\n"
        "- reason: types of misleading presentations, transparency issues, disclosure quality\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Daily rates instead of annual для loans — misleading magnitude\n"
        "- Hidden conversion fees — unfair cost increase\n"
        "- Intermediate currency без THB equivalent — confusion tactic\n"
        "- Promotional rates без effective rate disclosure — bait tactic\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти больше pricing information или протестировать currency options\"}"
    ),
    output_key="critic_json",
)
currency_manipulation_result_agent = Agent(
    name="currency_manipulation_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Currency Manipulation анализа.",
    instruction=(
        "Ты — Result агент для CURRENCY MANIPULATION паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ currency manipulation анализ завершен:\n"
        "Сформируй отчет о Currency Manipulation:\n"
        "- Обнаружены ли misleading currency/unit presentations\n"
        "- Transparency currency conversion processes\n"
        "- Quality promotional vs effective rate disclosures\n"
        "- Availability и accuracy local currency tools\n"
        "- Impact на user understanding real costs\n"
        "- Рекомендации по improvement transparency\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если pricing/rate information не найдена → should_retry=true\n"
        "- Сайт не работает с multiple currencies → should_retry=false\n"
        "- Нужен доступ к financial calculators → should_retry=true with expanded search\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность и clarity в currency/rate presentations, consumer protection."
    ),
    output_key="result_json",
)
def currency_manipulation_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("💱 CURRENCY MANIPULATION PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        rate_manipulation = extracted.get("rate_unit_manipulation", {})
        conversion_analysis = extracted.get("currency_conversion_analysis", {})
        promotional_analysis = extracted.get("promotional_rate_analysis", {})
        detected = extracted.get("currency_manipulation_detected", False)
        manipulation_score = extracted.get("overall_manipulation_score", 0)
        pieces.append(f"📊 АНАЛИЗ CURRENCY MANIPULATION:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Manipulation Score: {manipulation_score:.2f}")
        if rate_manipulation:
            misleading_presentations = rate_manipulation.get("misleading_rate_presentations", [])
            disclosure_quality = rate_manipulation.get("effective_rate_disclosure_quality", "unknown")
            pieces.append(f"📈 RATE UNIT MANIPULATION:")
            pieces.append(f"  • Misleading presentations: {len(misleading_presentations)}")
            pieces.append(f"  • Effective rate disclosure: {disclosure_quality}")
            high_severity = [p for p in misleading_presentations if p.get("manipulation_severity") == "high"]
            for i, pres in enumerate(high_severity[:2]):  # Первые 2 высокой тяжести
                displayed = pres.get("displayed_unit", "unknown")
                actual = pres.get("actual_effective_unit", "unknown") 
                transparency = pres.get("transparency_provided", False)
                pieces.append(f"    {i+1}. {displayed} вместо {actual} (прозрачность: {'✅' if transparency else '❌'})")
        if conversion_analysis:
            transparency_score = conversion_analysis.get("conversion_transparency_score", 0)
            hidden_fees = conversion_analysis.get("hidden_conversion_fees_detected", False)
            local_converter = conversion_analysis.get("local_currency_converter_available", False)
            fee_disclosure = conversion_analysis.get("conversion_fee_disclosure_quality", "unknown")
            pieces.append(f"💱 CURRENCY CONVERSION:")
            pieces.append(f"  • Transparency Score: {transparency_score:.2f}")
            pieces.append(f"  • Скрытые conversion fees: {'❌ обнаружены' if hidden_fees else '✅ не обнаружены'}")
            pieces.append(f"  • Local currency converter: {'✅ доступен' if local_converter else '❌ отсутствует'}")
            pieces.append(f"  • Fee disclosure quality: {fee_disclosure}")
        if promotional_analysis:
            promotional_found = promotional_analysis.get("promotional_rates_found", 0)
            effective_disclosed = promotional_analysis.get("effective_rates_disclosed", 0)
            duration_clarity = promotional_analysis.get("rate_duration_clarity", "unknown")
            post_promo_disclosed = promotional_analysis.get("post_promotional_rate_disclosed", False)
            pieces.append(f"🎯 PROMOTIONAL RATES:")
            pieces.append(f"  • Promotional rates найдено: {promotional_found}")
            pieces.append(f"  • Effective rates раскрыто: {effective_disclosed}")
            pieces.append(f"  • Duration clarity: {duration_clarity}")
            pieces.append(f"  • Post-promotional rate disclosed: {'✅ да' if post_promo_disclosed else '❌ нет'}")
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
currency_manipulation_browser_loop = LoopAgent(
    name="currency_manipulation_browser_loop",
    description="Итеративное тестирование Currency Manipulation: misleading currency и unit presentations.",
    sub_agents=[
        currency_manipulation_decider_agent,
        currency_manipulation_navigator_agent,
        currency_manipulation_form_filler_agent,
        currency_manipulation_parser_agent,
        currency_manipulation_critic_agent,
        currency_manipulation_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=currency_manipulation_after_loop_callback,
)
currency_manipulation_root_agent = SequentialAgent(
    name="currency_manipulation_pipeline",
    description="Полный пайплайн для детектирования Currency Manipulation паттерна (manipulative currency/unit presentations).",
    sub_agents=[
        currency_manipulation_ingest_agent,
        currency_manipulation_browser_loop,
    ],
)