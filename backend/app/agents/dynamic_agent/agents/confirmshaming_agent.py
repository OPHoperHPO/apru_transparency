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
MAX_LOOP_ITERS = int(os.getenv("BROWSER_PIPELINE_ITERS", "12"))
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
confirmshaming_ingest_agent = Agent(
    name="confirmshaming_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Confirmshaming' - манипулятивных подтверждений.",
    instruction=(
        "Ты — Ingest агент для детектирования CONFIRMSHAMING паттерна. Создай план поиска манипулятивных CTA.\n\n"
        "Схема ConfirmshamingPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Confirmshaming pattern - manipulative confirmations and asymmetric button labeling\",\n'
        '  \"target_site\": string,\n'
        '  \"interaction_scenarios\": [\"modal_dialogs\", \"subscription_flows\", \"marketing_offers\", \"unsubscribe_flows\"],\n'
        '  \"success_criteria\": [\n'
        '    \"Find consent/confirmation dialogs\",\n'
        '    \"Analyze button text symmetry and tone\",\n'
        '    \"Test actual vs expected button actions\",\n'
        '    \"Document manipulative language patterns\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"confirmation_dialogs_found\": [],\n'
        '    \"asymmetric_button_pairs\": [],\n'
        '    \"shaming_language_detected\": [],\n'
        '    \"misleading_cta_buttons\": [],\n'
        '    \"confirmshaming_severity_score\": 0.0,\n'
        '    \"confirmshaming_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find pages with dialogs and CTAs\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Trigger various confirmation dialogs\", \"track\": \"dialog_analysis\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test button actions and language\", \"track\": \"cta_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze manipulative language patterns\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: модальные окна, confirmation dialogs, subscribe/unsubscribe flows.\n"
        "2) Анализировать: тексты кнопок согласия vs отказа (symmetry, tone, shaming).\n"
        "3) Тестировать: соответствие button labels реальным действиям.\n"
        "4) Выявлять: guilt-tripping, shaming language, misleading CTAs.\n"
        "5) Пороги: asymmetric button labeling + guilt language = confirmshaming.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
confirmshaming_decider_agent = Agent(
    name="confirmshaming_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Confirmshaming паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования CONFIRMSHAMING паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- confirmshaming_metrics: {confirmshaming_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"exploration\"|\"dialog_testing\"|\"cta_analysis\"|\"language_evaluation\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда найдены confirmation dialogs И проанализированы button texts И выявлены manipulative patterns.\n"
        "- parse: когда собраны примеры dialogs/CTAs и нужно проанализировать language patterns.\n"
        "- act: когда нужно триггерить dialogs, тестировать buttons, анализировать их behavior.\n"
        "- navigate: когда нужно найти страницы с confirmation flows или marketing offers.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'exploration': найти страницы с modals, popups, subscription flows.\n"
        "- Фаза 'dialog_testing': триггерить различные confirmation dialogs.\n"
        "- Фаза 'cta_analysis': анализировать button texts, actions, symmetry.\n"
        "- Фаза 'language_evaluation': оценить manipulative/shaming aspects.\n"
        "- Искать паттерны: 'No thanks, I prefer to pay more', 'Skip this great offer'.\n\n"
        "Если найдены guilt-tripping button texts ИЛИ misleading CTAs — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
confirmshaming_navigator_agent = Agent(
    name="confirmshaming_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска confirmation dialogs и CTA элементов.",
    instruction=(
        "Ты — Навигатор для детектирования CONFIRMSHAMING паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК CONFIRMATION И CTA ЭЛЕМЕНТОВ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО POTENTIAL CONFIRMSHAMING AREAS:\n"
        "   • Marketing landing pages с offers\n"
        "   • Subscription/signup flows\n"
        "   • Checkout processes с upsells\n"
        "   • Account settings/cancellation flows\n"
        "   • Newsletter signup/unsubscribe pages\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК ТРИГГЕРОВ ДЛЯ DIALOGS:\n"
        "   • Cookie consent banners\n"
        "   • Exit-intent popups (движение мыши к краю)\n"
        "   • Modal triggers при closing tabs\n"
        "   • Decline/cancel buttons в формах\n"
        "D) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Ищи кнопки: 'No thanks', 'Maybe later', 'Cancel', 'Decline'\n"
        "   • Hover над элементами для активации tooltips/modals\n"
        "   • Попытки закрыть вкладку для exit-intent triggers\n"
        "E) ОЖИДАНИЕ ПОЯВЛЕНИЯ DIALOGS: browser_wait_for { time: 5 }\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с visible dialogs\n\n"
        "ФИКСАЦИЯ CTA И DIALOG ЭЛЕМЕНТОВ:\n"
        "На каждой странице записывай в state:\n"
        "- Найденные confirmation dialogs\n"
        "- Button pairs (accept vs decline)\n"
        "- CTA texts и их тональность\n"
        "- Modal trigger mechanisms\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
confirmshaming_form_filler_agent = Agent(
    name="confirmshaming_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Триггерит и анализирует confirmation dialogs на предмет manipulative language.",
    instruction=(
        "Ты — агент анализа dialogs для CONFIRMSHAMING. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ТРИГГЕРИНГ И АНАЛИЗ CONFIRMATION DIALOGS:\n"
        "1) browser_snapshot — фиксация видимых dialogs\n"
        "2) АКТИВАЦИЯ РАЗЛИЧНЫХ DIALOGS:\n"
        "   • Попытки отказа от offers: browser_click на 'No thanks'\n"
        "   • Попытки unsubscribe: browser_click на unsubscribe links\n"
        "   • Попытки закрытия signup forms: browser_click на close buttons\n"
        "   • Exit-intent triggers: движение мыши или попытки закрыть\n"
        "3) АНАЛИЗ BUTTON TEXTS (фаза 'cta_analysis'):\n"
        "   • Для каждого dialog найти positive и negative buttons\n"
        "   • Записать точные тексты кнопок\n"
        "   • Оценить symmetry: neutral language vs guilt-tripping\n"
        "   • Примеры confirmshaming: 'No, I don't want to save money', 'I prefer paying full price'\n"
        "4) ТЕСТИРОВАНИЕ BUTTON ACTIONS:\n"
        "   • НЕ кликать по кнопкам пока не задокументированы!\n"
        "   • Проверить, соответствуют ли button labels реальным действиям\n"
        "   • Искать misleading CTAs: 'Continue' вместо 'Purchase now'\n"
        "5) LANGUAGE PATTERN АНАЛИЗ (фаза 'language_evaluation'):\n"
        "   • Guilt-tripping phrases: 'Don't you care about...?'\n"
        "   • Shame-based language: 'Smart people choose...'\n"
        "   • False urgency in button texts: 'Last chance'\n"
        "   • Asymmetric prominence: accept button большой, decline мелкий\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • button_pair_analysis: для каждой пары кнопок\n"
        "   • manipulative_language_examples: конкретные фразы\n"
        "   • visual_manipulation: размер, цвет, позиция кнопок\n"
        "7) SNAPSHOT ПОСЛЕ АНАЛИЗА: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ CONFIRMSHAMING:\n"
        "- Button texts используют guilt/shame language\n"
        "- Asymmetric labeling: positive neutral, negative guilt-tripping\n"
        "- Misleading CTAs, не соответствующие real actions\n"
        "- Visual manipulation: accept prominent, decline hidden\n\n"
        "Возвращай только текст снапшота. Language analysis пиши в state."
    ),
    output_key="last_page_text",
)
confirmshaming_parser_agent = Agent(
    name="confirmshaming_parser_agent",
    model=LLM_FLASH,
    description="Анализирует manipulative patterns в confirmation dialogs и CTAs.",
    instruction=(
        "Ты — парсер для CONFIRMSHAMING анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, confirmshaming_state={confirmshaming_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ MANIPULATIVE LANGUAGE PATTERNS:\n"
        "1) Извлеки из state все найденные confirmation dialogs и button pairs.\n"
        "2) Классифицируй language patterns по типам manipulation.\n"
        "3) Оцени visual и textual asymmetry между positive/negative options.\n"
        "4) Определи misleading nature CTAs и их actual actions.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"confirmation_dialogs_analyzed\": [\n'
        '      {\n'
        '        \"dialog_context\": \"subscription_offer|unsubscribe|cookie_consent\",\n'
        '        \"positive_button_text\": \"...\",\n'
        '        \"negative_button_text\": \"...\",\n'
        '        \"text_symmetry_score\": number,\n'
        '        \"shaming_language_detected\": boolean,\n'
        '        \"guilt_tripping_phrases\": [...],\n'
        '        \"visual_manipulation\": {\"size_asymmetry\": boolean, \"color_manipulation\": boolean, \"position_bias\": boolean},\n'
        '        \"confirmshaming_severity\": \"none|low|medium|high\"\n'
        '      }\n'
        '    ],\n'
        '    \"misleading_cta_buttons\": [\n'
        '      {\n'
        '        \"button_text\": \"...\",\n'
        '        \"expected_action\": \"...\",\n'
        '        \"actual_action\": \"...\",\n'
        '        \"misleading_severity\": \"low|medium|high\"\n'
        '      }\n'
        '    ],\n'
        '    \"manipulation_techniques_found\": [\n'
        '      \"guilt_tripping\", \"shame_language\", \"false_urgency\", \"visual_bias\", \"misleading_labels\"\n'
        '    ],\n'
        '    \"confirmshaming_detected\": boolean,\n'
        '    \"overall_manipulation_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных manipulative patterns\"\n'
        "}\n\n"
        "КРИТЕРИИ CONFIRMSHAMING ДЕТЕКТИРОВАНИЯ:\n"
        "- confirmshaming_detected = true, если найдены guilt-tripping или shame-based button texts\n"
        "- ИЛИ если significant visual manipulation (размер, цвет, позиция)\n"
        "- ИЛИ если misleading CTAs не соответствуют actual actions\n"
        "- ИЛИ если asymmetric language (positive neutral, negative guilt-inducing)\n"
        "- overall_manipulation_score = weighted_average(language_severity, visual_manipulation, misleading_ctas)"
    ),
    output_key="parsed",
)
confirmshaming_critic_agent = Agent(
    name="confirmshaming_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Confirmshaming анализа.",
    instruction=(
        "Ты — критик для CONFIRMSHAMING детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдены и проанализированы confirmation dialogs.\n"
        "2) Оценены button text symmetry и manipulative language.\n"
        "3) Проверены CTA buttons на misleading nature.\n"
        "4) Проанализированы visual manipulation techniques.\n"
        "5) Классифицированы manipulation patterns по severity.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о найденных confirmshaming и manipulative patterns\n"
        "- reason: types of manipulation, severity levels, frequency of occurrence\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Guilt-tripping button texts — явный confirmshaming\n"
        "- Shame-based language patterns — emotional manipulation\n"
        "- Misleading CTAs — потенциальный fraud\n"
        "- Significant visual bias — unfair choice architecture\n\n"
        "IНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти больше dialogs или проанализировать CTA patterns\"}"
    ),
    output_key="critic_json",
)
confirmshaming_result_agent = Agent(
    name="confirmshaming_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Confirmshaming анализа.",
    instruction=(
        "Ты — Result агент для CONFIRMSHAMING паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ confirmshaming анализ завершен:\n"
        "Сформируй отчет о Confirmshaming:\n"
        "- Обнаружены ли manipulative confirmation dialogs\n"
        "- Типы и тяжесть manipulation techniques\n"
        "- Symmetry и fairness choice presentation\n"
        "- Misleading nature CTA buttons и их actions\n"
        "- Влияние на user decision-making autonomy\n"
        "- Рекомендации по ethical choice architecture\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если confirmation dialogs не найдены → should_retry=true с поиском triggers\n"
        "- Сайт не использует interactive dialogs → should_retry=false\n"
        "- Нужно больше interaction scenarios → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: ethical presentation choices, user autonomy respect, fair decision architecture."
    ),
    output_key="result_json",
)
def confirmshaming_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("😔 CONFIRMSHAMING PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        dialogs = extracted.get("confirmation_dialogs_analyzed", [])
        misleading_ctas = extracted.get("misleading_cta_buttons", [])
        manipulation_techniques = extracted.get("manipulation_techniques_found", [])
        detected = extracted.get("confirmshaming_detected", False)
        manipulation_score = extracted.get("overall_manipulation_score", 0)
        pieces.append(f"📊 АНАЛИЗ MANIPULATIVE PATTERNS:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Manipulation Score: {manipulation_score:.2f}")
        pieces.append(f"  • Проанализировано dialogs: {len(dialogs)}")
        pieces.append(f"  • Misleading CTAs найдено: {len(misleading_ctas)}")
        if manipulation_techniques:
            pieces.append(f"🎭 ОБНАРУЖЕННЫЕ ТЕХНИКИ:")
            technique_names = {
                "guilt_tripping": "Guilt-tripping",
                "shame_language": "Shame language", 
                "false_urgency": "False urgency",
                "visual_bias": "Visual bias",
                "misleading_labels": "Misleading labels"
            }
            for technique in manipulation_techniques:
                display_name = technique_names.get(technique, technique)
                pieces.append(f"  • ❌ {display_name}")
        if dialogs:
            shaming_dialogs = [d for d in dialogs if d.get("shaming_language_detected", False)]
            pieces.append(f"💬 CONFIRMATION DIALOGS:")
            pieces.append(f"  • Всего проанализировано: {len(dialogs)}")
            pieces.append(f"  • С shaming language: {len(shaming_dialogs)}")
            for i, dialog in enumerate(shaming_dialogs[:2]):  # Первые 2
                context = dialog.get("dialog_context", "unknown")
                negative_text = dialog.get("negative_button_text", "N/A")
                severity = dialog.get("confirmshaming_severity", "unknown")
                pieces.append(f"    {i+1}. {context} - \"{negative_text}\" (тяжесть: {severity})")
        if misleading_ctas:
            high_severity = [c for c in misleading_ctas if c.get("misleading_severity") == "high"]
            pieces.append(f"🔀 MISLEADING CTAs:")
            for i, cta in enumerate(high_severity[:2]):  # Первые 2 высокой тяжести
                button_text = cta.get("button_text", "N/A")
                expected = cta.get("expected_action", "N/A")
                actual = cta.get("actual_action", "N/A")
                pieces.append(f"    {i+1}. \"{button_text}\" - ожидание: {expected}, реальность: {actual}")
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
confirmshaming_browser_loop = LoopAgent(
    name="confirmshaming_browser_loop",
    description="Итеративное тестирование Confirmshaming: манипулятивные confirmation dialogs и CTAs.",
    sub_agents=[
        confirmshaming_decider_agent,
        confirmshaming_navigator_agent,
        confirmshaming_form_filler_agent,
        confirmshaming_parser_agent,
        confirmshaming_critic_agent,
        confirmshaming_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=confirmshaming_after_loop_callback,
)
confirmshaming_root_agent = SequentialAgent(
    name="confirmshaming_pipeline",
    description="Полный пайплайн для детектирования Confirmshaming паттерна (манипулятивные подтверждения).",
    sub_agents=[
        confirmshaming_ingest_agent,
        confirmshaming_browser_loop,
    ],
)