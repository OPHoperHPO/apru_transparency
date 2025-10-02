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
forced_actions_ingest_agent = Agent(
    name="forced_actions_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Forced Actions' - принудительных действий для базовых функций.",
    instruction=(
        "Ты — Ingest агент для детектирования FORCED ACTIONS паттерна. Создай план тестирования блокирующих пэйволлов.\n\n"
        "Схема ForcedActionsPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Forced Actions pattern - core functionality blocked behind unnecessary paywalls or forced registrations\",\n'
        '  \"target_site\": string,\n'
        '  \"core_features_to_test\": [],\n'
        '  \"success_criteria\": [\n'
        '    \"Identify core functionality of the service\",\n'
        '    \"Test access to basic features without registration\",\n'
        '    \"Test access with free registration\",\n'
        '    \"Document forced premium upgrades for basic tasks\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"core_features_identified\": [],\n'
        '    \"features_blocked_without_login\": [],\n'
        '    \"features_blocked_without_payment\": [],\n'
        '    \"blocking_justification_quality\": {},\n'
        '    \"free_tier_functionality_ratio\": 0.0,\n'
        '    \"forced_actions_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Explore service and identify core features\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test feature access without registration\", \"track\": \"anonymous_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test feature access with free account\", \"track\": \"free_account_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze blocking patterns and justifications\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Определить: какие функции являются core для данного сервиса.\n"
        "2) Тестировать: доступность core функций без регистрации/оплаты.\n"
        "3) Анализировать: обоснованность блокировок (правовая необходимость vs коммерческое принуждение).\n"
        "4) Оценивать: пропорциональность ограничений реальной value proposition.\n"
        "5) Пороги: блокировка базовой функции без делового обоснования = forced actions.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
forced_actions_decider_agent = Agent(
    name="forced_actions_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Forced Actions паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования FORCED ACTIONS паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- forced_actions_metrics: {forced_actions_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"exploration\"|\"anonymous_testing\"|\"registration_testing\"|\"blocking_analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда протестированы core features И оценены обоснования блокировок.\n"
        "- parse: когда завершено тестирование доступности функций и нужно проанализировать паттерны.\n"
        "- act: когда нужно тестировать доступ к функциям, регистрироваться, или взаимодействовать с блокировками.\n"
        "- navigate: когда нужно исследовать сайт или переходить к разным функциям.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'exploration': определить core функции сервиса и их expected accessibility.\n"
        "- Фаза 'anonymous_testing': попытаться использовать функции без регистрации.\n"
        "- Фаза 'registration_testing': зарегистрировать free account и протестировать доступ.\n"
        "- Фаза 'blocking_analysis': проанализировать обоснованность каждой блокировки.\n"
        "- Фиксировать качество messaging о причинах блокировки.\n\n"
        "Если core функция заблокирована без адекватного обоснования — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
forced_actions_navigator_agent = Agent(
    name="forced_actions_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для исследования core функций и их доступности.",
    instruction=(
        "Ты — Навигатор для детектирования FORCED ACTIONS паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ИССЛЕДОВАНИЕ CORE ФУНКЦИЙ СЕРВИСА:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО ФУНКЦИОНАЛЬНОСТИ:\n"
        "   • Main navigation menu для понимания core features\n"
        "   • Feature showcase pages (About, How it works, Features)\n"
        "   • Tool/service pages где происходит основная work\n"
        "   • Landing pages с value propositions\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК РАЗНЫХ ТИПОВ ФУНКЦИЙ:\n"
        "   • Free vs Premium feature distinctions\n"
        "   • Demo/trial functionality\n"
        "   • Basic tools vs Advanced tools\n"
        "   • Public content vs Member content\n"
        "D) ИССЛЕДОВАНИЕ ACCESS POINTS:\n"
        "   • Registration/signup forms\n"
        "   • Login barriers\n"
        "   • Payment/upgrade prompts\n"
        "   • Free trial offers\n"
        "E) ОЖИДАНИЕ ЗАГРУЗКИ: browser_wait_for { text: \"Features\" или time: 3 }\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с feature information\n\n"
        "КАТАЛОГИЗАЦИЯ ФУНКЦИЙ:\n"
        "На каждой странице записывай в state:\n"
        "- Список обнаруженных core features\n"
        "- Индикаторы access requirements (login, payment)\n"
        "- Value proposition messaging\n"
        "- Competitor comparison context (если есть)\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
forced_actions_form_filler_agent = Agent(
    name="forced_actions_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Тестирует доступность функций и анализирует блокировки.",
    instruction=(
        "Ты — агент тестирования доступности для FORCED ACTIONS. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "СИСТЕМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ ДОСТУПНОСТИ:\n"
        "1) browser_snapshot — фиксация текущих блокировок\n"
        "2) ANONYMOUS TESTING (фаза 'anonymous_testing'):\n"
        "   • Попытаться использовать каждую core функцию без регистрации\n"
        "   • Клики по основным action buttons: browser_click\n"
        "   • Попытки доступа к tools/content: browser_navigate\n"
        "   • Фиксировать blocking messages и их тональность\n"
        "3) FREE REGISTRATION TESTING (фаза 'registration_testing'):\n"
        "   • Создать free account с тестовыми данными (НЕ реальными!)\n"
        "   • Повторить тесты доступности к core features\n"
        "   • Сравнить уровень доступа vs anonymous\n"
        "   • Документировать новые premium prompts\n"
        "4) BLOCKING ANALYSIS (фаза 'blocking_analysis'):\n"
        "   • Для каждой блокировки записать: причину, альтернативы, тональность\n"
        "   • Оценить пропорциональность блокировки к value\n"
        "   • Проверить наличие preview/demo функциональности\n"
        "5) ОБОСНОВАНИЕ КАЧЕСТВА:\n"
        "   • Clear explanation почему функция заблокирована\n"
        "   • Business rationale vs arbitrary limitation\n"
        "   • User-friendly messaging vs aggressive sales pitch\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • feature_accessibility_matrix: anonymous vs free vs paid\n"
        "   • blocking_justification_scores: качество объяснений\n"
        "   • forced_upgrade_pressure: агрессивность upselling\n"
        "7) SNAPSHOT ПОСЛЕ ТЕСТИРОВАНИЯ: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ FORCED ACTIONS:\n"
        "- Core функция заблокирована без clear business rationale\n"
        "- Aggressive upselling messaging для basic tasks\n"
        "- Отсутствие meaningful free tier functionality\n"
        "- Blocking диспропорционален к actual value delivered\n\n"
        "Возвращай только текст снапшота. Результаты accessibility testing пиши в state."
    ),
    output_key="last_page_text",
)
forced_actions_parser_agent = Agent(
    name="forced_actions_parser_agent",
    model=LLM_FLASH,
    description="Анализирует обоснованность блокировок core функций.",
    instruction=(
        "Ты — парсер для FORCED ACTIONS анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, forced_actions_state={forced_actions_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ ОБОСНОВАННОСТИ БЛОКИРОВОК:\n"
        "1) Извлеки из state результаты accessibility testing.\n"
        "2) Категоризируй функции по важности (core vs nice-to-have).\n"
        "3) Оцени обоснованность каждой блокировки.\n"
        "4) Проанализируй качество messaging и user experience.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"core_functionality_analysis\": {\n'
        '      \"total_core_features_identified\": number,\n'
        '      \"features_accessible_anonymously\": number,\n'
        '      \"features_accessible_with_free_account\": number,\n'
        '      \"features_requiring_payment\": number\n'
        '    },\n'
        '    \"blocking_analysis\": [\n'
        '      {\n'
        '        \"feature_name\": \"...\",\n'
        '        \"feature_importance\": \"core|important|nice_to_have\",\n'
        '        \"access_requirement\": \"registration|payment|subscription\",\n'
        '        \"blocking_justification\": \"clear|vague|absent\",\n'
        '        \"business_rationale_strength\": \"strong|weak|absent\",\n'
        '        \"user_messaging_tone\": \"friendly|neutral|aggressive\",\n'
        '        \"forced_action_severity\": \"none|low|medium|high\"\n'
        '      }\n'
        '    ],\n'
        '    \"free_tier_value_ratio\": number,\n'
        '    \"aggressive_upselling_detected\": boolean,\n'
        '    \"forced_actions_detected\": boolean,\n'
        '    \"overall_forcing_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных принудительных блокировок\"\n'
        "}\n\n"
        "КРИТЕРИИ FORCED ACTIONS ДЕТЕКТИРОВАНИЯ:\n"
        "- forced_actions_detected = true, если core функция заблокирована без strong business rationale\n"
        "- ИЛИ если free tier предоставляет <20% meaningful functionality\n"
        "- ИЛИ если blocking messaging является aggressive/manipulative\n"
        "- ИЛИ если требования диспропорциональны delivered value\n"
        "- overall_forcing_score = weighted_average(core_blockings, justification_quality, messaging_tone)"
    ),
    output_key="parsed",
)
forced_actions_critic_agent = Agent(
    name="forced_actions_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Forced Actions анализа.",
    instruction=(
        "Ты — критик для FORCED ACTIONS детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Идентифицированы core функции сервиса.\n"
        "2) Протестирована доступность функций без регистрации.\n"
        "3) Протестирована доступность с free account.\n"
        "4) Проанализирована обоснованность каждой блокировки.\n"
        "5) Оценено качество user messaging о требованиях доступа.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет об обоснованности блокировок core functionality\n"
        "- reason: количество forced blockings, quality of justifications, messaging tone\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Core функции, заблокированные без clear rationale — серьезное forced action\n"
        "- Aggressive messaging для basic tasks — poor user experience\n"
        "- Disproportionate requirements для simple actions — unreasonable forcing\n"
        "- Free tier без meaningful functionality — misleading offering\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно протестировать больше функций или проанализировать блокировки\"}"
    ),
    output_key="critic_json",
)
forced_actions_result_agent = Agent(
    name="forced_actions_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Forced Actions анализа.",
    instruction=(
        "Ты — Result агент для FORCED ACTIONS паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ forced actions анализ завершен:\n"
        "Сформируй отчет о Forced Actions:\n"
        "- Обнаружены ли неоправданные блокировки core функций\n"
        "- Качество и пропорциональность access requirements\n"
        "- Тональность user messaging о блокировках\n"
        "- Value ratio free tier vs premium offerings\n"
        "- Business justification strength для каждой блокировки\n"
        "- Рекомендации по улучшению user experience\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если core функции не ясны → should_retry=true с более deep exploration\n"
        "- Сервис полностью premium без free tier → should_retry=false (legitimate business model)\n"
        "- Технические проблемы с access testing → should_retry=true\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: разумность и пропорциональность access restrictions, user experience quality."
    ),
    output_key="result_json",
)
def forced_actions_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🚫 FORCED ACTIONS PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        functionality = extracted.get("core_functionality_analysis", {})
        blockings = extracted.get("blocking_analysis", [])
        detected = extracted.get("forced_actions_detected", False)
        forcing_score = extracted.get("overall_forcing_score", 0)
        free_tier_ratio = extracted.get("free_tier_value_ratio", 0)
        aggressive_upselling = extracted.get("aggressive_upselling_detected", False)
        pieces.append(f"📊 АНАЛИЗ ПРИНУДИТЕЛЬНЫХ ДЕЙСТВИЙ:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Forcing Score: {forcing_score:.2f}")
        pieces.append(f"  • Free Tier Value: {free_tier_ratio:.1%}")
        pieces.append(f"  • Агрессивный upselling: {'❌ да' if aggressive_upselling else '✅ нет'}")
        if functionality:
            total_features = functionality.get("total_core_features_identified", 0)
            anonymous_access = functionality.get("features_accessible_anonymously", 0)
            free_access = functionality.get("features_accessible_with_free_account", 0)
            paid_required = functionality.get("features_requiring_payment", 0)
            pieces.append(f"🔍 ДОСТУПНОСТЬ ФУНКЦИЙ:")
            pieces.append(f"  • Всего core функций: {total_features}")
            pieces.append(f"  • Доступно анонимно: {anonymous_access}")
            pieces.append(f"  • Доступно с бесплатным аккаунтом: {free_access}")
            pieces.append(f"  • Требует оплаты: {paid_required}")
        if blockings:
            forced_blockings = [b for b in blockings if b.get("forced_action_severity") in ["medium", "high"]]
            pieces.append(f"⚠️ ПРОБЛЕМНЫЕ БЛОКИРОВКИ:")
            for i, blocking in enumerate(forced_blockings[:3]):  # Показываем первые 3
                feature = blocking.get("feature_name", "Unknown")
                importance = blocking.get("feature_importance", "unknown")
                requirement = blocking.get("access_requirement", "unknown")
                severity = blocking.get("forced_action_severity", "unknown")
                pieces.append(f"  {i+1}. {feature} ({importance}) - {requirement} - тяжесть: {severity}")
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
forced_actions_browser_loop = LoopAgent(
    name="forced_actions_browser_loop",
    description="Итеративное тестирование Forced Actions: принудительные блокировки core функций.",
    sub_agents=[
        forced_actions_decider_agent,
        forced_actions_navigator_agent,
        forced_actions_form_filler_agent,
        forced_actions_parser_agent,
        forced_actions_critic_agent,
        forced_actions_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=forced_actions_after_loop_callback,
)
forced_actions_root_agent = SequentialAgent(
    name="forced_actions_pipeline",
    description="Полный пайплайн для детектирования Forced Actions паттерна (принудительные блокировки базовых функций).",
    sub_agents=[
        forced_actions_ingest_agent,
        forced_actions_browser_loop,
    ],
)