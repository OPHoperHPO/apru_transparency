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
navigation_obstacles_ingest_agent = Agent(
    name="navigation_obstacles_ingest_agent",
    model=LLM,
    description="Нормализует запрос для детектирования паттерна 'Navigation Obstacles' - препятствий для сравнения.",
    instruction=(
        "Ты — Ingest агент для детектирования NAVIGATION OBSTACLES паттерна. Создай план тестирования препятствий сравнения.\n\n"
        "Схема NavigationObstaclesPlan:\n"
        "{\n"
        '  \"browse_goal\": \"Detect Navigation Obstacles pattern - blocked comparison and information access barriers\",\n'
        '  \"target_site\": string,\n'
        '  \"comparison_scenarios\": [\"pricing_comparison\", \"feature_comparison\", \"terms_access\", \"competitor_mentions\"],\n'
        '  \"success_criteria\": [\n'
        '    \"Test opening key information in new tabs\",\n'
        '    \"Check hover-dependent critical information\",\n'
        '    \"Test mobile vs desktop information parity\",\n'
        '    \"Verify deep-link accessibility to specific terms\"\n'
        '  ],\n'
        '  \"metrics_to_collect\": {\n'
        '    \"new_tab_blocking_detected\": [],\n'
        '    \"hover_only_critical_info\": [],\n'
        '    \"mobile_desktop_info_disparity\": [],\n'
        '    \"deep_link_accessibility\": {},\n'
        '    \"comparison_obstacles_score\": 0.0,\n'
        '    \"navigation_obstacles_detected\": false\n'
        '  },\n'
        '  \"steps\": [\n'
        '    { \"kind\": \"navigate\", \"goal\": \"Find key information pages\", \"url\": \"target_site\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test new tab opening capabilities\", \"track\": \"new_tab_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test hover-dependent information\", \"track\": \"hover_testing\" },\n'
        '    { \"kind\": \"act\", \"goal\": \"Test mobile user-agent accessibility\", \"track\": \"mobile_testing\" },\n'
        '    { \"kind\": \"parse\", \"goal\": \"Analyze information accessibility barriers\" }\n'
        '  ]\n'
        "}\n\n"
        "ПРАВИЛА:\n"
        "1) Искать: pricing tables, terms/conditions, detailed specifications, comparison charts.\n"
        "2) Тестировать: возможность открытия в новых вкладках, hover-only content accessibility.\n"
        "3) Сравнивать: desktop vs mobile информационный паритет.\n"
        "4) Проверять: глубокие ссылки на конкретные разделы условий.\n"
        "5) Пороги: критичная информация доступна только при hover или заблокирована для new tabs.\n"
        "6) Только чистый JSON.\n"
    ),
    output_key="plan",
)
navigation_obstacles_decider_agent = Agent(
    name="navigation_obstacles_decider_agent",
    model=LLM_LITE,
    tools=[finish],
    description="Определяет следующий шаг для детектирования Navigation Obstacles паттерна.",
    instruction=(
        "Ты — Диспетчер для детектирования NAVIGATION OBSTACLES паттерна.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n"
        "- obstacles_metrics: {obstacles_metrics?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\", \"current_phase\": \"exploration\"|\"new_tab_testing\"|\"hover_testing\"|\"mobile_testing\"|\"analysis\" }\n\n'
        "ЛОГИКА ПРИНЯТИЯ РЕШЕНИЙ:\n"
        "- finish: когда протестированы new tab accessibility И hover dependencies И mobile parity.\n"
        "- parse: когда завершена одна из фаз тестирования и нужно проанализировать accessibility.\n"
        "- act: когда нужно тестировать navigation capabilities, hover behavior, mobile access.\n"
        "- navigate: когда нужно найти key information pages или переключиться между view modes.\n\n"
        "СПЕЦИФИЧНЫЕ ИНСТРУКЦИИ:\n"
        "- Фаза 'exploration': найти страницы с pricing, terms, specifications, comparisons.\n"
        "- Фаза 'new_tab_testing': попытаться открыть key links в новых вкладках.\n"
        "- Фаза 'hover_testing': проверить hover-only content и его доступность без hover.\n"
        "- Фаза 'mobile_testing': переключиться на mobile user-agent и сравнить доступность.\n"
        "- Искать: блокировки right-click, disabled links, JavaScript-dependent content.\n\n"
        "Если критичная информация доступна только через hover ИЛИ заблокированы new tabs — вызови finish.\n"
        "Только JSON."
    ),
    output_key="decider_json",
)
navigation_obstacles_navigator_agent = Agent(
    name="navigation_obstacles_navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация для поиска и тестирования информационных барьеров.",
    instruction=(
        "Ты — Навигатор для детектирования NAVIGATION OBSTACLES паттерна. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "ПОИСК INFORMATION ACCESS POINTS:\n"
        "A) SNAPSHOT: browser_snapshot для фиксации текущего состояния\n"
        "B) НАВИГАЦИЯ ПО KEY INFORMATION AREAS:\n"
        "   • Pricing pages с detailed breakdown\n"
        "   • Terms & Conditions, Privacy Policy, Service Agreement\n"
        "   • Product specification и feature comparison pages\n"
        "   • FAQ sections с detailed information\n"
        "   • Help/Support pages с policy details\n"
        "   • Переходы: browser_navigate { url: \"...\" }\n"
        "C) ПОИСК DIFFERENT VIEW MODES:\n"
        "   • Desktop vs mobile responsive design\n"
        "   • Different browser user-agents\n"
        "   • Accessibility modes (если доступны)\n"
        "   • Print-friendly versions страниц\n"
        "D) СПЕЦИАЛИЗИРОВАННЫЙ ПОИСК:\n"
        "   • Footer links к detailed policies\n"
        "   • Fine print sections\n"
        "   • Expandable/collapsible content areas\n"
        "   • Tooltip-dependent information\n"
        "E) USER-AGENT ПЕРЕКЛЮЧЕНИЯ:\n"
        "   • Desktop user-agent: стандартный режим\n"
        "   • Mobile user-agent: изменение через browser settings\n"
        "   • Tablet user-agent: промежуточный режим\n"
        "F) ОЖИДАНИЕ ЗАГРУЗКИ: browser_wait_for { time: 3 }\n"
        "G) ФИНАЛЬНЫЙ SNAPSHOT: browser_snapshot с current view mode\n\n"
        "ФИКСАЦИЯ NAVIGATION PATTERNS:\n"
        "На каждой странице записывай в state:\n"
        "- Обнаруженные information access methods\n"
        "- Link behaviors (clickable, disabled, hover-only)\n"
        "- User-agent specific content differences\n"
        "- Deep-link accessibility test results\n\n"
        "Возвращай только сырой текст browser_snapshot."
    ),
    output_key="last_page_text",
)
navigation_obstacles_form_filler_agent = Agent(
    name="navigation_obstacles_form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Тестирует различные navigation scenarios и accessibility barriers.",
    instruction=(
        "Ты — агент тестирования navigation для NAVIGATION OBSTACLES. Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "СИСТЕМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ NAVIGATION:\n"
        "1) browser_snapshot — фиксация current navigation state\n"
        "2) NEW TAB ACCESSIBILITY TESTING (фаза 'new_tab_testing'):\n"
        "   • Попытки открыть key links: right-click → 'Open in new tab'\n"
        "   • Тестирование Ctrl+Click behavior на important links\n"
        "   • browser_tabs { action: \"create\" } для manual new tab creation\n"
        "   • Проверить, работают ли deep links в новых вкладках\n"
        "3) HOVER DEPENDENCY TESTING (фаза 'hover_testing'):\n"
        "   • browser_hover над элементами с potential hidden content\n"
        "   • Поиск tooltips с critical information (pricing details, terms)\n"
        "   • Тестирование touch devices behavior (без hover capability)\n"
        "   • Проверить accessibility на мобильных устройствах\n"
        "4) MOBILE USER-AGENT TESTING (фаза 'mobile_testing'):\n"
        "   • Изменить user-agent на mobile (если поддерживается MCP)\n"
        "   • Сравнить информационный контент desktop vs mobile\n"
        "   • Проверить navigation menu accessibility\n"
        "   • Искать missing information на mobile версии\n"
        "5) DEEP LINK ACCESSIBILITY:\n"
        "   • Попытки прямого доступа к specific sections\n"
        "   • Тестирование anchor links (#section-name)\n"
        "   • Проверить, работают ли bookmarkable URLs\n"
        "6) INFORMATION BLOCKING DETECTION:\n"
        "   • JavaScript-dependent content без fallback\n"
        "   • Right-click disabled на important content\n"
        "   • Text selection блокировка на key information\n"
        "   • Copy-paste restrictions на terms/pricing\n"
        "7) ЗАПИСЬ РЕЗУЛЬТАТОВ:\n"
        "   • accessibility_matrix: desktop vs mobile vs tablet\n"
        "   • hover_dependency_critical: list of hover-only critical info\n"
        "   • navigation_blocking_detected: types of restrictions\n"
        "8) SNAPSHOT ПОСЛЕ ТЕСТОВ: browser_snapshot\n\n"
        "ДЕТЕКТИРОВАНИЕ NAVIGATION OBSTACLES:\n"
        "- Critical information доступна только при hover\n"
        "- New tab opening заблокировано для key links\n"
        "- Mobile version скрывает important details\n"
        "- Deep links не работают или redirected\n\n"
        "Возвращай только текст снапшота. Navigation test results пиши в state."
    ),
    output_key="last_page_text",
)
navigation_obstacles_parser_agent = Agent(
    name="navigation_obstacles_parser_agent",
    model=LLM_FLASH,
    description="Анализирует препятствия для доступа к информации и сравнения.",
    instruction=(
        "Ты — парсер для NAVIGATION OBSTACLES анализа.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}, obstacles_state={obstacles_metrics?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущий parsed: {parsed?}\n\n"
        "АНАЛИЗ NAVIGATION ACCESSIBILITY:\n"
        "1) Извлеки из state результаты всех navigation tests.\n"
        "2) Классифицируй обнаруженные препятствия по типам и критичности.\n"
        "3) Оцени impact на user's ability to compare и access key information.\n"
        "4) Проанализируй information parity между different access methods.\n\n"
        "ФОРМАТ ОТВЕТА JSON:\n"
        "{\n"
        '  \"extracted\": {\n'
        '    \"new_tab_accessibility\": {\n'
        '      \"critical_links_tested\": number,\n'
        '      \"new_tab_blocked_links\": number,\n'
        '      \"right_click_disabled\": boolean,\n'
        '      \"ctrl_click_blocked\": boolean\n'
        '    },\n'
        '    \"hover_dependency_analysis\": {\n'
        '      \"hover_only_critical_info_found\": [\n'
        '        {\"content_type\": \"pricing|terms|specifications\", \"accessibility_impact\": \"high|medium|low\"}\n'
        '      ],\n'
        '      \"touch_device_inaccessible_content\": number\n'
        '    },\n'
        '    \"mobile_desktop_parity\": {\n'
        '      \"information_missing_on_mobile\": [...],\n'
        '      \"navigation_features_missing_mobile\": [...],\n'
        '      \"parity_score\": number\n'
        '    },\n'
        '    \"deep_link_accessibility\": {\n'
        '      \"direct_section_access_works\": boolean,\n'
        '      \"anchor_links_functional\": boolean,\n'
        '      \"bookmarkable_urls_work\": boolean\n'
        '    },\n'
        '    \"comparison_obstacles_detected\": boolean,\n'
        '    \"overall_accessibility_score\": number\n'
        '  },\n'
        '  \"notes\": \"Детальное описание найденных navigation obstacles\"\n'
        "}\n\n"
        "КРИТЕРИИ NAVIGATION OBSTACLES ДЕТЕКТИРОВАНИЯ:\n"
        "- comparison_obstacles_detected = true, если critical info доступна только при hover\n"
        "- ИЛИ если new tab opening заблокировано для key comparison links\n"
        "- ИЛИ если significant mobile-desktop information disparity (parity_score < 0.7)\n"
        "- ИЛИ если deep links к specific terms/sections не функционируют\n"
        "- overall_accessibility_score = weighted_average(new_tab_access, hover_independence, mobile_parity, deep_link_functionality)"
    ),
    output_key="parsed",
)
navigation_obstacles_critic_agent = Agent(
    name="navigation_obstacles_critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет завершенность Navigation Obstacles анализа.",
    instruction=(
        "Ты — критик для NAVIGATION OBSTACLES детектирования.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}\n\n"
        "КРИТЕРИИ ЗАВЕРШЕНИЯ:\n"
        "1) Протестирована new tab accessibility для key links.\n"
        "2) Проверены hover dependencies для critical information.\n"
        "3) Сравнена information parity между desktop и mobile.\n"
        "4) Протестирована deep link accessibility.\n"
        "5) Оценен общий уровень navigation obstacles.\n\n"
        "ЕСЛИ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ:\n"
        "Вызови finish с:\n"
        "- summary: отчет о найденных navigation obstacles и их влиянии на comparison\n"
        "- reason: types of obstacles, accessibility impact, information parity issues\n"
        "- data: parsed.extracted со всеми деталями анализа\n\n"
        "ОСОБОЕ ВНИМАНИЕ:\n"
        "- Hover-only critical information — серьезный accessibility barrier\n"
        "- Blocked new tab opening — препятствует comparison\n"
        "- Mobile information gaps — неравный доступ к information\n"
        "- Non-functional deep links — затрудняет sharing и direct access\n\n"
        "ИНАЧЕ верни JSON: {\"done\": false, \"reason\": \"нужно протестировать больше navigation scenarios\"}"
    ),
    output_key="critic_json",
)
navigation_obstacles_result_agent = Agent(
    name="navigation_obstacles_result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итоги Navigation Obstacles анализа.",
    instruction=(
        "Ты — Result агент для NAVIGATION OBSTACLES паттерна.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}\n\n"
        "1) ЕСЛИ decider_json.next_step == 'finish' ИЛИ navigation obstacles анализ завершен:\n"
        "Сформируй отчет о Navigation Obstacles:\n"
        "- Обнаружены ли препятствия для comparison и information access\n"
        "- Impact hover dependencies на accessibility\n"
        "- Information parity между различными access methods\n"
        "- Deep link functionality для direct content access\n"
        "- Влияние obstacles на informed decision making\n"
        "- Рекомендации по улучшению information accessibility\n"
        "Вызови finish.\n\n"
        "2) ИНАЧЕ оцени возможность продолжения:\n"
        "- Если key information pages не найдены → should_retry=true\n"
        "- Сайт имеет простую структуру без complex navigation → should_retry=false\n"
        "- Технические ограничения для user-agent testing → should_retry=true with alternative methods\n"
        "- Верни JSON с рекомендацией\n\n"
        "ФОКУС: равноправный доступ к information, user autonomy в comparison процессе."
    ),
    output_key="result_json",
)
def navigation_obstacles_after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    pieces.append("🚧 NAVIGATION OBSTACLES PATTERN ANALYSIS")
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        new_tab = extracted.get("new_tab_accessibility", {})
        hover = extracted.get("hover_dependency_analysis", {})
        mobile_parity = extracted.get("mobile_desktop_parity", {})
        deep_links = extracted.get("deep_link_accessibility", {})
        detected = extracted.get("comparison_obstacles_detected", False)
        accessibility_score = extracted.get("overall_accessibility_score", 0)
        pieces.append(f"📊 АНАЛИЗ NAVIGATION OBSTACLES:")
        pieces.append(f"  • Паттерн обнаружен: {'❌ ДА' if detected else '✅ НЕТ'}")
        pieces.append(f"  • Accessibility Score: {accessibility_score:.2f}")
        if new_tab:
            tested_links = new_tab.get("critical_links_tested", 0)
            blocked_links = new_tab.get("new_tab_blocked_links", 0)
            right_click_disabled = new_tab.get("right_click_disabled", False)
            pieces.append(f"📑 NEW TAB ДОСТУПНОСТЬ:")
            pieces.append(f"  • Протестировано критических ссылок: {tested_links}")
            pieces.append(f"  • Заблокировано new tab: {blocked_links}")
            pieces.append(f"  • Right-click отключен: {'❌ да' if right_click_disabled else '✅ нет'}")
        if hover:
            hover_critical = hover.get("hover_only_critical_info_found", [])
            touch_inaccessible = hover.get("touch_device_inaccessible_content", 0)
            pieces.append(f"👆 HOVER ЗАВИСИМОСТИ:")
            pieces.append(f"  • Критичная информация только при hover: {len(hover_critical)}")
            pieces.append(f"  • Недоступно на touch устройствах: {touch_inaccessible}")
            if hover_critical:
                for info in hover_critical[:2]:  # Показываем первые 2
                    content_type = info.get("content_type", "unknown")
                    impact = info.get("accessibility_impact", "unknown")
                    pieces.append(f"    • {content_type} (impact: {impact})")
        if mobile_parity:
            missing_mobile = mobile_parity.get("information_missing_on_mobile", [])
            parity_score = mobile_parity.get("parity_score", 0)
            pieces.append(f"📱 MOBILE-DESKTOP ПАРИТЕТ:")
            pieces.append(f"  • Parity Score: {parity_score:.2f}")
            pieces.append(f"  • Информация отсутствует на mobile: {len(missing_mobile)}")
        if deep_links:
            section_access = deep_links.get("direct_section_access_works", False)
            anchor_links = deep_links.get("anchor_links_functional", False) 
            bookmarkable = deep_links.get("bookmarkable_urls_work", False)
            pieces.append(f"🔗 DEEP LINK ДОСТУПНОСТЬ:")
            pieces.append(f"  • Прямой доступ к разделам: {'✅ работает' if section_access else '❌ не работает'}")
            pieces.append(f"  • Anchor links: {'✅ работают' if anchor_links else '❌ не работают'}")
            pieces.append(f"  • Bookmarkable URLs: {'✅ работают' if bookmarkable else '❌ не работают'}")
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
navigation_obstacles_browser_loop = LoopAgent(
    name="navigation_obstacles_browser_loop",
    description="Итеративное тестирование Navigation Obstacles: препятствия для сравнения и доступа к информации.",
    sub_agents=[
        navigation_obstacles_decider_agent,
        navigation_obstacles_navigator_agent,
        navigation_obstacles_form_filler_agent,
        navigation_obstacles_parser_agent,
        navigation_obstacles_critic_agent,
        navigation_obstacles_result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=navigation_obstacles_after_loop_callback,
)
navigation_obstacles_root_agent = SequentialAgent(
    name="navigation_obstacles_pipeline",
    description="Полный пайплайн для детектирования Navigation Obstacles паттерна (препятствия для сравнения).",
    sub_agents=[
        navigation_obstacles_ingest_agent,
        navigation_obstacles_browser_loop,
    ],
)