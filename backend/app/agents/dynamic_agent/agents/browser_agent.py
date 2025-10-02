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
from app.agents.dynamic_agent.utils.llmproxy import GeminiLLM
LLM = GeminiLLM(model=os.getenv("BROWSER_LLM", "gemini-2.5-pro"))        # планирование/критика/итоги
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
ingest_agent = Agent(
    name="ingest_agent",
    model=LLM,
    description="Нормализует запрос пользователя в BrowsingPlan.",
    instruction=(
        "Ты — Entry/Ingest агент. На основе ПОСЛЕДНЕГО запроса пользователя верни ТОЛЬКО JSON по схеме BrowsingPlan.\n\n"
        "Схема BrowsingPlan:\n"
        "{\n"
        '  \"browse_goal\": string,\n'
        '  \"initial_url\": string|null,\n'
        '  \"query\": string|null,\n'
        '  \"success_criteria\": [string, ...],\n'
        '  \"steps\": [ { \"kind\": \"navigate\"|\"act\"|\"parse\", \"goal\": string, \"url\": string|null, \"query\": string|null, \"input\": object|null } ]\n'
        "}\n\n"
        "ПРАВИЛА СОСТАВЛЕНИЯ ПЛАНА (очень просто):\n"
        "1) Если в запросе есть явный URL — поставь его в initial_url. Иначе initial_url=null и сгенерируй короткий query для поиска (2–6 слов).\n"
        "2) success_criteria должны быть ИЗМЕРИМЫМИ и ПРОВЕРЯЕМЫМИ на странице, примеры:\n"
        "- «URL содержит '/pricing' И на странице есть текст 'Pricing'»\n"
        "- «Есть таблица с колонками 'Name' и 'Price' и ≥ 3 строк»\n"
        "- «Кнопка 'Add to cart' видима и кликабельна (role=button)»\n"
        "3) steps — минимальный маршрут: сначала navigate (на URL или по query), потом act (клики/вводы), затем parse (извлечение).\n"
        "4) Без комментариев. Верни только ЧИСТЫЙ JSON.\n"
    ),
    output_key="plan",
)
decider_agent = Agent(
    name="decider_agent",
    model=LLM_LITE,
    tools=[finish],  # раннее завершение по плану/критериям
    description="Определяет следующий шаг и выдаёт ПРЯМЫЕ инструкции другим агентам.",
    instruction=(
        "Ты — Диспетчер шагов. Решай строго и детерминированно.\n\n"
        "Контекст:\n"
        "- plan: {plan?}\n"
        "- last_page_text: {last_page_text?}\n"
        "- parsed: {parsed?}\n\n"
        "ФОРМАТ ВЫХОДА СТРОГО JSON:\n"
        '{ \"next_step\": \"navigate\"|\"act\"|\"parse\"|\"finish\", \"action_instructions\": \"...\" }\n\n'
        "КРИТЕРИИ ВЫБОРА ШАГА:\n"
        "- finish: когда ВСЕ success_criteria из plan выполнены.\n"
        "- parse: когда есть свежий и полный snapshot (в last_page_text) и пора извлекать данные.\n"
        "- act: когда на странице надо кликнуть/ввести/выбрать/переключить вкладку и т.п.\n"
        "- navigate: когда нужно пойти на URL, вернуться назад, обновить snapshot, открыть/закрыть/переключить вкладку.\n\n"
        "ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ:\n"
        "Если snapshot пустой/старый/сомнительный, много 'loading', 'error', видна капча/логин или ожидались другие элементы — установи next_step='navigate' и в "
        "action_instructions попроси СДЕЛАТЬ СВЕЖИЙ SNAPSHOT ТЕКУЩЕЙ СТРАНИЦЫ (без перехода) через 'browser_snapshot', а при необходимости — мягкий reload ожиданием и снова snapshot.\n\n"
        "Шаблоны action_instructions (текст, но максимально конкретный и пошаговый):\n"
        "— NAVIGATE:\n"
        "  1) Сделай 'browser_snapshot' (быстрый).\n"
        "  2) Вызови 'browser_navigate' с url=\"...\" ИЛИ 'browser_navigate_back' / 'browser_tabs' (action=create|select|close) по задаче.\n"
        "  3) Подожди 'browser_wait_for' (text=\"...\" ИЛИ time=2–5) по ситуации.\n"
        "  4) Сделай 'browser_snapshot' (полный) и верни текст.\n"
        "— ACT (пример для клика/ввода):\n"
        "  1) 'browser_snapshot' → найди целевой элемент по ролям/лейблам.\n"
        "  2) 'browser_click' с element=\"Кнопка ...\" и ref=\"<точный ref из snapshot>\" (или 'doubleClick': true при необходимости).\n"
        "  3) Если ввод: 'browser_type' с element/ref и text=\"...\", затем submit=true если надо Enter.\n"
        "  4) 'browser_wait_for' (text или time), затем 'browser_snapshot'.\n"
        "— PARSE:\n"
        "  1) Ничего не кликай. Используй текущий last_page_text. Извлекай только то, что реально есть.\n\n"
        "ВАЖНО:\n"
        "1) Для любых переходов и действий — инструктируй делать snapshot ДО и ПОСЛЕ операции.\n"
        "2) Всегда описывай ЧТО делаем, ЗАЧЕМ и КАКОЙ инструмент, с какими полями.\n"
        "3) Если успех по success_criteria уже достигнут — сразу вызови tool 'finish' с кратким summary и reason.\n"
        "Только JSON. Без пояснений."
    ),
    output_key="decider_json",
)
navigator_agent = Agent(
    name="navigator_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Навигация по вебу с MCP. Всегда синхронизирует состояние через частые snapshots.",
    instruction=(
        "Ты — Навигатор с MCP (Playwright). Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'navigate' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "Иначе выполняй ПРОСТО ТАК:\n"
        "A) СНАЧАЛА синхронизируйся: вызови 'browser_snapshot' (быстрый) — просто получить текущий снимок без переходов.\n"
        "B) ВЫПОЛНИ НАВИГАЦИЮ согласно action_instructions. Вот КАК вызывать инструменты (буквально):\n"
        "   • Перейти по URL: browser_navigate { url: \"https://...\" }\n"
        "   • Назад: browser_navigate_back {}\n"
        "   • Обновить состояние без перехода: просто сделай ещё один browser_snapshot спустя короткую паузу ('browser_wait_for' time=1–2).\n"
        "   • Управление вкладками: browser_tabs { action: \"create\"|\"select\"|\"close\", index?: number }\n"
        "   • Изменить размер окна: browser_resize { width: 1366, height: 900 }\n"
        "   • Закрыть страницу: browser_close {}\n"
        "   • Установить браузер при ошибке: browser_install {}\n"
        "C) ПОДОЖДИ СТАБИЛИЗАЦИИ: 'browser_wait_for' с подходящим параметром (text=\"...\" или time=2–5).\n"
        "D) СДЕЛАЙ ПОЛНЫЙ SNAPSHOT страницы: 'browser_snapshot'. Верни ТОЛЬКО сырой текст снапшота.\n"
        "E) ЕСЛИ контент динамический (ленивая загрузка, ajax): добавь маленькое ожидание и сделай ещё один 'browser_snapshot'.\n\n"
        "ПОЛЕЗНЫЕ ЧТЕНИЯ (не меняют страницу):\n"
        "   • Логи консоли: browser_console_messages {}\n"
        "   • Сеть: browser_network_requests {}\n\n"
        "ОПАСНЫЕ ИНСТРУМЕНТЫ (только при необходимости):\n"
        "   • Координаты мыши (требуют vision/XY): browser_mouse_move_xy / browser_mouse_click_xy / browser_mouse_drag_xy — используй ТОЛЬКО если нет надёжных refs.\n"
        "   • Сохранить PDF (если включено pdf): browser_pdf_save { filename?: \"page-<timestamp>.pdf\" }\n\n"
        "ВСЕГДА возвращай только сырой текст последнего 'browser_snapshot', без JSON или комментариев."
    ),
    output_key="last_page_text",
)
form_filler_agent = Agent(
    name="form_filler_agent",
    model=LLM_FLASH,
    tools=[toolset],
    description="Действия на странице через MCP. Всегда синхронизирует состояние через частые snapshots.",
    instruction=(
        "Ты — агент действий с MCP (Playwright). Контекст: {decider_json?}\n\n"
        "Если decider_json.next_step != 'act' — верни БЕЗ ИЗМЕНЕНИЙ {last_page_text?}.\n\n"
        "Иначе делай ВСЕГДА ТАК:\n"
        "1) 'browser_snapshot' (быстрый) — убедись, что элементы существуют.\n"
        "2) НАЙДИ НУЖНЫЙ ЭЛЕМЕНТ в snapshot: возьми его точный ref. Помни: element=человеческое описание, ref=точная ссылка из snapshot.\n"
        "3) ВЫПОЛНИ ДЕЙСТВИЕ. Вот cookbook инструментов ДЛЯ ДЕЙСТВИЙ:\n"
        "   • Клик: browser_click { element: \"Кнопка '...'\", ref: \"<ref>\", doubleClick?: true, button?: \"left|right|middle\" }\n"
        "   • Наведение: browser_hover { element: \"...\", ref: \"<ref>\" }  (read-only, но часто нужно перед кликом)\n"
        "   • Ввод: browser_type { element: \"Поле 'Email'\", ref: \"<ref>\", text: \"user@example.com\", submit?: true, slowly?: true }\n"
        "   • Выбор в селекте: browser_select_option { element: \"Dropdown 'Country'\", ref: \"<ref>\", values: [\"US\"] }\n"
        "   • Заполнение формы пачкой: browser_fill_form { fields: [ {element:\"Поле '...'\"," 
        "ref:\"<ref>\", value:\"...\"}, ... ] }\n"
        "   • Перетаскивание: browser_drag { startElement:\"Карточка #1\", startRef:\"<ref1>\", endElement:\"Список 'Done'\", endRef:\"<ref2>\" }\n"
        "   • Нажать клавишу: browser_press_key { key: \"Enter\"|\"Escape\"|\"ArrowLeft\"|\"a\" }\n"
        "   • Загрузить файл: browser_file_upload { paths: [\"/abs/path/to/file.ext\"] }\n"
        "   • Обработать диалог/alert/prompt: browser_handle_dialog { accept: true|false, promptText?: \"...\" }\n"
        "   • Вернуться/переход/вкладки — см. инструменты навигации у Navigator (при необходимости можешь вызвать и отсюда).\n"
        "4) ПОДОЖДИ СТАБИЛИЗАЦИИ: browser_wait_for { text?: \"...\", time?: 1–5 } по ситуации.\n"
        "5) 'browser_snapshot' (полный) — верни ТОЛЬКО текст снапшота.\n"
        "6) Многошаговые сценарии (несколько кликов/вводов): между КАЖДЫМ шагом делай короткий 'browser_snapshot', чтобы не потерять контекст.\n"
        "7) Сомнения/ошибки/редиректы/модалы — делай дополнительный 'browser_snapshot' и ТОЛЬКО потом продолжай.\n"
    ),
    output_key="last_page_text",
)
parser_agent = Agent(
    name="parser_agent",
    model=LLM_FLASH,
    description="Извлекает данные из свежего снимка страницы.",
    instruction=(
        "Ты — агент извлечения.\n"
        "Контекст: plan={plan?}, last_page_text={last_page_text?}, decider={decider_json?}\n\n"
        "Если decider_json.next_step != 'parse' — верни предыдущее значение parsed без изменений: {parsed?}\n\n"
        "Иначе:\n"
        "- Работай ТОЛЬКО по тексту last_page_text. Не придумывай значения, не делай предположений.\n"
        "- Если данных нет/неполны — явно так и скажи в notes, не выдумывай.\n"
        "- Верни СТРОГО JSON вида: {\"extracted\": {...}, \"notes\": \"...\"}.\n"
        "  Пример extracted: ключи = поля из success_criteria и плана (url, заголовки, цены, табличные строки и т.п.).\n"
        "- Никаких комментариев вне JSON."
    ),
    output_key="parsed",
)
critic_agent = Agent(
    name="critic_agent",
    model=LLM,
    tools=[finish],
    description="Проверяет success_criteria; при выполнении — завершает.",
    instruction=(
        "Ты — критик/валидатор результата.\n"
        "Контекст: plan={plan?}, parsed={parsed?}, last_page_text={last_page_text?}, decider={decider_json?}\n\n"
        "Как проверять:\n"
        "1) Пройди по каждому success_criteria из plan.\n"
        "2) Для текстовых критериев — ищи их прямые совпадения в last_page_text.\n"
        "3) Для структурных (таблица/кнопка видима/URL содержит ...) — смотри признаки в last_page_text (ролей, меток, фрагменты URL).\n"
        "4) Если всё выполнено — вызови tool 'finish' с:\n"
        "   - summary: 2–5 строк на человеческом языке (что нашли/сделали),\n"
        "   - reason: перечисли, какие критерии подтверждены,\n"
        "   - data: parsed.extracted.\n"
        "Иначе — верни СТРОГО JSON: {\"done\": false, \"reason\": \"что ещё требуется\"}."
    ),
    output_key="critic_json",
)
result_agent = Agent(
    name="result_agent",
    model=LLM,
    tools=[finish],
    description="Подводит итог; решает завершать или рекомендовать повтор.",
    instruction=(
        "Ты — Result агент. Цель: либо завершить (finish), либо дать чёткую рекомендацию: пробовать снова или нет.\n\n"
        "Контекст: plan={plan?}, parsed={parsed?}, critic={critic_json?}, decider={decider_json?}, last_page_text={last_page_text?}\n\n"
        "1) ЕСЛИ (decider_json.next_step == 'finish') ИЛИ все критерии выполнены (что видно из critic_json):\n"
        "- Сформируй краткое резюме (2–6 строк), упомяни конечный URL/раздел, если уместно.\n"
        "- Вызови tool 'finish' с summary=<текст>, reason=critic_json.reason (если есть), data=parsed.extracted (если есть).\n"
        "- Больше ничего не выводи.\n\n"
        "2) ИНАЧЕ: оцени, стоит ли пробовать снова, и как именно.\n"
        "- Временные причины (таймауты, 'loading', 429/500/502/503, капча, рассинхронизация snapshot'а) ⇒ should_retry=true,\n"
        "  proposed_fix: ещё один цикл с ДОП. 'browser_snapshot' до/после действий, возможно 'browser_wait_for' до network-idle, мягкий reload.\n"
        "- Постоянные причины (жёсткий логин/оплата, 403/404, контент отсутствует) ⇒ should_retry=false,\n"
        "  proposed_fix: попросить у пользователя доступ/креды/альтернативный сайт/ослабить критерии.\n"
        "- Верни СТРОГО JSON: {\"should_retry\": true|false, \"retry_reason\": \"...\", \"proposed_fix\": \"...\", \"confidence\": 0.0..1.0}\n"
        "- Не вызывай finish в этом случае."
    ),
    output_key="result_json",
)
def after_loop_callback(ctx: CallbackContext) -> Optional[types.Content]:
    state = ctx.state or {}
    if state.get("final_summary"):
        return types.Content(role="model", parts=[types.Part(text=state["final_summary"])])
    plan = state.get("plan") or {}
    parsed = state.get("parsed") or {}
    critic = state.get("critic_json") or {}
    result = state.get("result_json") or {}
    pieces = []
    goal = plan.get("browse_goal")
    if goal:
        pieces.append(f"Цель: {goal}")
    extracted = parsed.get("extracted") if isinstance(parsed, dict) else None
    if extracted:
        pretty = json.dumps(extracted, ensure_ascii=False, indent=2)
        pieces.append("Извлечённые данные:\n" + pretty)
    reason = state.get("final_reason") or critic.get("reason")
    if reason:
        pieces.append(f"Статус: {reason}")
    if isinstance(result, dict) and "should_retry" in result:
        sr = "да" if result.get("should_retry") else "нет"
        rr = result.get("retry_reason") or "—"
        fx = result.get("proposed_fix") or "—"
        conf = result.get("confidence")
        conf_txt = f"{conf:.2f}" if isinstance(conf, (int, float)) else "—"
        pieces.append(f"Пробовать ещё раз: {sr} (уверенность {conf_txt})\nПричина: {rr}\nЧто сделать: {fx}")
    else:
        pieces.append("Пробовать ещё раз: да — обновите страницу и получите свежий snapshot перед следующими действиями.")
    text = "\n\n".join(pieces)
    return types.Content(role="model", parts=[types.Part(text=text)])
browser_loop = LoopAgent(
    name="browser_loop",
    description="Итеративный веб-конвейер до достижения цели; частые snapshots для синхронизации состояния; завершение через finish.",
    sub_agents=[
        decider_agent,
        navigator_agent,
        form_filler_agent,
        parser_agent,
        critic_agent,
        result_agent,
    ],
    max_iterations=MAX_LOOP_ITERS,
    after_agent_callback=after_loop_callback,
)
