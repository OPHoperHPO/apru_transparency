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
hidden_subscription_ingest_agent = Agent(
    name="hidden_subscription_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Hidden Subscription' - скрытых подписок и автопродлений.",
    instruction=(
        "Ты — Ingest агент для детектирования HIDDEN SUBSCRIPTION паттерна. Создай план тестирования скрытых автоподписок.\n\n"
        "Схема HiddenSubscriptionPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Hidden Subscription pattern - auto-renewal enabled by default without explicit consent\",\n'
        '  \"target_site\": string,\n'
        '  \"trial_service\": string|null,\n'
        '  \"success_criteria\": [\n'
        '    \"Identify free trial or subscription offers\",\n'
        '    \"Check auto-renewal default settings\",\n'
        '    \"Test subscription settings accessibility\",\n'
        '    \"Document billing information disclosure\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"trial_offer_found\": false,\n'
        '    \"auto_renewal_default_on\": false,\n'
        '    \"explicit_auto_renewal_consent\": false,\n'
        '    \"billing_date_visible\": false,\n'
        '    \"easy_cancellation_access\": false,\n'
        '    \"reminder_notifications_mentioned\": false,\n'
        '    \"hidden_subscription_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find trial/subscription offers\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Start trial signup process\", \"track\": \"signup_analysis\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Check auto-renewal settings\", \"track\": \"settings_review\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test subscription management access\", \"track\": \"management_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze subscription transparency\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: 'Free trial', 'Try free', subscription plans, premium services.\n"
        "2) Фиксировать: состояние auto-renewal settings по умолчанию.\n"
        "3) Тестировать: четкость информации о биллинге и способах отмены.\n"
        "4) Проверять: наличие явного согласия на автопродление.\n"
        "5) Пороги: автопродление включено по умолчанию без отдельного согласия = hidden subscription.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
hidden_subscription_decider_agent = Agent(
    name="hidden_subscription_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Hidden Subscription паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования HIDDEN SUBSCRIPTION паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- subscription_metrics: {subscription_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"discovery\"|\"signup_process\"|\"settings_check\"|\"management_test\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда проверены auto-renewal defaults И доступность настроек подписки И прозрачность биллинга.\n"
        "- parse: когда завершена одна из фаз и нужно проанализировать subscription practices.\n"
        "- act: когда нужно взаимодействовать с формами регистрации, настройками, переключателями.\n"
        "- navigate: когда нужно найти trial offers или перейти к настройкам аккаунта.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'discovery': найти free trial offers, subscription plans, premium features.\n"
        "- Фаза 'signup_process': пройти процесс регистрации до этапа payment info.\n"
        "- Фаза 'settings_check': проанализировать default states auto-renewal опций.\n"
        "- Фаза 'management_test': найти и протестировать subscription management interface.\n"
        "- Обращать внимание на четкость disclosure информации о billing dates.\n\n"
        "Если auto-renewal включено по умолчанию БЕЗ отдельного согласия — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
hidden_subscription_navigator_agent = Agent(
    name="hidden_subscription_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска подписок и тестирования их прозрачности.",
    instruction=(
        "Ты — Навигатор для детектирования HIDDEN SUBSCRIPTION паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК ПОДПИСОЧНЫХ СЕРВИСОВ:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО SUBSCRIPTION OFFERS:\n"
        "   • Landing pages с 'Free trial' buttons\n"
        "   • Pricing pages с subscription plans\n"
        "   • Premium feature pages\n"
        "   • Account signup/registration flows\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК НАСТРОЕК И АККАУНТОВ:\n"
        "   • Account settings/profile pages\n"
        "   • Billing/subscription management sections\n"
        "   • User dashboard с subscription info\n"
        "   • Navigation через меню профиля\n"
        "D) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Ищи разделы: 'Billing', 'Subscription', 'Account', 'Settings'\n"
        "   • Footer links к subscription policies\n"
        "   • Help/FAQ sections о subscription terms\n"
        "E) ОЖИДАНИЕ ЗАГРУЗКИ: browser_wait_for { text: \"Subscription\" или time: 3 }\n"
        "F) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с актуальной информацией\n\n"
        "ФИКСАЦИЯ SUBSCRIPTION ЭЛЕМЕНТОВ:\n"
        "На каждой странице записывай в state:\n"
        "- Найденные trial offers и их условия\n"
        "- Subscription plans и pricing\n"
        "- Auto-renewal mentions и их visibility\n"
        "- Billing date disclosure quality\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
hidden_subscription_form_filler_agent = Agent(
    name="hidden_subscription_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Анализирует процесс подписки и настройки автопродления.",
    instruction=(
        "Ты — агент анализа подписок для HIDDEN SUBSCRIPTION. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "АНАЛИЗ SUBSCRIPTION ПРОЦЕССОВ:\n"
        "1) browser_snapshot — фиксация текущего состояния форм\n"
        "2) АНАЛИЗ SIGNUP ПРОЦЕССА (фаза 'signup_process'):\n"
        "   • Начать процесс регистрации: browser_click на 'Start free trial'\n"
        "   • Заполнить базовую информацию (email, password) БЕЗ реальных данных\n"
        "   • НЕ ВВОДИТЬ реальную payment информацию!\n"
        "   • Отслеживать mentions об auto-renewal в процессе\n"
        "3) ПРОВЕРКА AUTO-RENEWAL SETTINGS (фаза 'settings_check'):\n"
        "   • Найти чекбоксы/переключатели related к auto-renewal\n"
        "   • Зафиксировать их default states (checked/unchecked)\n"
        "   • Проверить visibility и prominence согласия на автопродление\n"
        "   • Искать separate explicit consent для auto-renewal\n"
        "4) ТЕСТИРОВАНИЕ SUBSCRIPTION MANAGEMENT (фаза 'management_test'):\n"
        "   • Найти ссылки на subscription settings: browser_click\n"
        "   • Тестировать доступность cancellation options\n"
        "   • Проверить четкость billing date information\n"
        "   • Оценить легкость управления подпиской\n"
        "5) АНАЛИЗ DISCLOSURE КАЧЕСТВА:\n"
        "   • Размер шрифта billing terms\n"
        "   • Видимость auto-renewal warnings\n"
        "   • Четкость next billing date\n"
        "   • Presence of reminder notifications mentions\n"
        "6) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • auto_renewal_prominence: насколько заметно согласие\n"
        "   • billing_transparency: качество раскрытия billing info\n"
        "   • cancellation_ease: сложность отмены подписки\n"
        "7) SNAPSHOT ПОСЛЕ АНАЛИЗА: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ HIDDEN SUBSCRIPTION:\n"
        "- Auto-renewal включено по умолчанию без отдельного согласия\n"
        "- Billing date не указана четко или спрятана в мелком тексте\n"
        "- Отсутствуют упоминания о reminder notifications\n"
        "- Сложный доступ к subscription management\n\n"
        "Возвращай только текст снапшота. Анализ subscription practices пиши в state."
    ),
    output_key="last_page_text",
)
hidden_subscription_parser_agent = Agent(
    name="hidden_subscription_parser_agent",
    model=LLM_FLASH,
    description="Анализирует прозрачность подписочных практик и автопродления.",
    instruction=(
        "Ты — парсер для HIDDEN SUBSCRIPTION анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, subscription_state={subscription_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ ПРОЗРАЧНОСТИ ПОДПИСОК:\n"
        "1) Извлеки из state данные о subscription signup process.\n"
        "2) Оцени качество disclosure billing information.\n"
        "3) Проанализируй default states auto-renewal опций.\n"
        "4) Определи доступность и удобство subscription management.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"trial_subscription_analysis\": {\n'
        '      \"free_trial_offered\": boolean,\n'
        '      \"trial_duration_clearly_stated\": boolean,\n'
        '      \"trial_to_paid_transition_explained\": boolean\n'
        '    },\n'
        '    \"auto_renewal_analysis\": {\n'
        '      \"auto_renewal_default_enabled\": boolean,\n'
        '      \"explicit_auto_renewal_consent_required\": boolean,\n'
        '      \"auto_renewal_terms_prominent\": boolean,\n'
        '      \"easy_to_disable_auto_renewal\": boolean\n'
        '    },\n'
        '    \"billing_transparency\": {\n'
        '      \"next_billing_date_clearly_shown\": boolean,\n'
        '      \"billing_amount_clearly_stated\": boolean,\n'
        '      \"reminder_notifications_promised\": boolean,\n'
        '      \"billing_terms_font_size_adequate\": boolean\n'
        '    },\n'
        '    \"subscription_management\": {\n'
        '      \"easy_access_to_settings\": boolean,\n'
        '      \"clear_cancellation_process\": boolean,\n'
        '      \"no_dark_patterns_in_cancellation\": boolean\n'
        '    },\n'
        '    \"hidden_subscription_detected\": boolean,\n'
        '    \"transparency_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных проблем с прозрачностью подписки\"\n'
        "}\n\n"
        "КРИТЕРИИ HIDDEN SUBSCRIPTION ДЕТЕКТИРОВАНИЯ:\n"
        "- hidden_subscription_detected = true, если auto_renewal включен по умолчанию БЕЗ explicit consent\n"
        "- ИЛИ если billing date/amount не указаны четко\n"
        "- ИЛИ если отсутствуют обещания reminder notifications\n"
        "- ИЛИ если доступ к subscription management затруднен\n"
        "- transparency_score = weighted_average(consent_clarity, billing_disclosure, management_ease)"
    ),
    output_key="parsed",
)
hidden_subscription_critic_agent = Agent(
    name="hidden_subscription_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Hidden Subscription анализа.",
    instruction=(
        "Ты — критик для HIDDEN SUBSCRIPTION детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Найдены и проанализированы trial/subscription offers.\n"
        "2) Проверены default settings автопродления.\n"
        "3) Оценена качество billing information disclosure.\n"
        "4) Протестирована доступность subscription management.\n"
        "5) Определена общая прозрачность subscription practices.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о прозрачности subscription practices\n"
        "- reason: default auto-renewal states, billing disclosure quality, management accessibility\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Auto-renewal включен по умолчанию без explicit consent — серьезное нарушение\n"
        "- Скрытая или неясная billing date information — проблема transparency\n"
        "- Отсутствие reminder notifications — недостаточная поддержка пользователя\n"
        "- Сложный доступ к cancellation — potential retention dark pattern\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно найти subscription offers или протестировать больше аспектов\"}"
    ),
    output_key="critic_json",
)
hidden_subscription_result_agent = Agent(
    name="hidden_subscription_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Hidden Subscription анализа.",
    instruction=(
        "Ты — Result агент для HIDDEN SUBSCRIPTION паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ hidden subscription анализ завершен:\n"
        "Сформируй отчет о Hidden Subscription:\n"
        "- Обнаружены ли скрытые подписочные практики\n"
        "- Прозрачность auto-renewal settings и согласий\n"
        "- Качество billing information disclosure\n"
        "- Доступность subscription management функций\n"
        "- Соответствие best practices для subscription services\n"
        "- Рекомендации по улучшению transparency\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если subscription services не найдены → should_retry=true с поиском в других разделах\n"
        "- Сайт не предлагает subscriptions → should_retry=false\n"
        "- Нужен доступ к account area для полного анализа → should_retry=false (требует регистрации)\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: честность и прозрачность subscription practices, защита прав потребителей."
    ),
    output_key="result_json",
)
def hidden_subscription_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🔄 HIDDEN SUBSCRIPTION PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        trial_analysis = extracted.get("trial_subscription_analysis", {})
        auto_renewal = extracted.get("auto_renewal_analysis", {})
        billing = extracted.get("billing_transparency", {})
        management = extracted.get("subscription_management", {})
        detected = extracted.get("hidden_subscription_detected", False)
        transparency_score = extracted.get("transparency_score", 0)
        pieces.append(f"📊 АНАЛИЗ ПОДПИСОЧНЫХ ПРАКТИК:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Прозрачность (score): {transparency_score:.2f}")
        if trial_analysis:
            trial_offered = trial_analysis.get("free_trial_offered", False)
            duration_clear = trial_analysis.get("trial_duration_clearly_stated", False)
            transition_explained = trial_analysis.get("trial_to_paid_transition_explained", False)
            pieces.append(f"🆓 FREE TRIAL АНАЛИЗ:")
            pieces.append(f"  • Trial предлагается: {'✅ да' if trial_offered else '❌ нет'}")
            pieces.append(f"  • Длительность указана четко: {'✅ да' if duration_clear else '❌ нет'}")
            pieces.append(f"  • Переход на платный объяснен: {'✅ да' if transition_explained else '❌ нет'}")
        if auto_renewal:
            default_enabled = auto_renewal.get("auto_renewal_default_enabled", False)
            explicit_consent = auto_renewal.get("explicit_auto_renewal_consent_required", False)
            terms_prominent = auto_renewal.get("auto_renewal_terms_prominent", False)
            easy_disable = auto_renewal.get("easy_to_disable_auto_renewal", False)
            pieces.append(f"🔄 AUTO-RENEWAL:")
            pieces.append(f"  • Включено по умолчанию: {'❌ да' if default_enabled else '✅ нет'}")
            pieces.append(f"  • Требуется явное согласие: {'✅ да' if explicit_consent else '❌ нет'}")
            pieces.append(f"  • Условия заметны: {'✅ да' if terms_prominent else '❌ нет'}")
            pieces.append(f"  • Легко отключить: {'✅ да' if easy_disable else '❌ нет'}")
        if billing:
            date_shown = billing.get("next_billing_date_clearly_shown", False)
            amount_stated = billing.get("billing_amount_clearly_stated", False)
            reminders_promised = billing.get("reminder_notifications_promised", False)
            pieces.append(f"💳 BILLING ПРОЗРАЧНОСТЬ:")
            pieces.append(f"  • Дата списания указана: {'✅ да' if date_shown else '❌ нет'}")
            pieces.append(f"  • Сумма указана четко: {'✅ да' if amount_stated else '❌ нет'}")
            pieces.append(f"  • Обещаны напоминания: {'✅ да' if reminders_promised else '❌ нет'}")
        if management:
            easy_access = management.get("easy_access_to_settings", False)
            clear_cancellation = management.get("clear_cancellation_process", False)
            pieces.append(f"⚙️ УПРАВЛЕНИЕ ПОДПИСКОЙ:")
            pieces.append(f"  • Легкий доступ к настройкам: {'✅ да' if easy_access else '❌ нет'}")
            pieces.append(f"  • Четкий процесс отмены: {'✅ да' if clear_cancellation else '❌ нет'}")
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
hidden_subscription_browser_loop = LoopAgent(
    name="hidden_subscription_browser_loop",
    description="Итеративное тестирование Hidden Subscription: скрытые подписки и автопродление.",
    sub_agents=[
        hidden_subscription_decider_agent,
        hidden_subscription_navigator_agent,
        hidden_subscription_form_filler_agent,
        hidden_subscription_parser_agent,
        hidden_subscription_critic_agent,
        hidden_subscription_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=hidden_subscription_after_loop_callback,
)
hidden_subscription_root_agent = SequentialAgent(
    name="hidden_subscription_pipeline",
    description="Полный пайплайн для детектирования Hidden Subscription паттерна (скрытые подписки и автопродление).",
    sub_agents=[
        hidden_subscription_ingest_agent,
        hidden_subscription_browser_loop,
    ],
)