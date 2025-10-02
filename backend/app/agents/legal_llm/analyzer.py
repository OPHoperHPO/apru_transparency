"""
Legal contract analyzer using Google Gemini AI with grouped parallel analysis
"""
import os
import asyncio
from datetime import datetime
from typing import Optional
from google import genai
from google.genai.types import GenerateContentConfig, SafetySetting, HarmCategory, HttpOptions, HarmBlockThreshold
from .models import (
    LegalAnalysisResult,
    ConsumerProtectionAnalysis,
    LegalFrameworkAnalysis,
    DataProtectionAnalysis,
    ContractStructureAnalysis,
    RegulatoryComplianceAnalysis,
    ComplianceStatus
)
def _create_consumer_protection_prompt(contract_text: str) -> str:
    """Create prompt for consumer protection analysis"""
    return f"""
Анализируйте следующий текст договора в соответствии с требованиями тайского законодательства по защите потребителей.
ТЕКСТ ДОГОВОРА:
{contract_text}
Проанализируйте данный договор согласно следующим критериям:
1. ОТСУТСТВИЕ ОДНОСТОРОННИХ ИЗМЕНЕНИЙ (unilateral_changes)
   Вопрос: Может ли провайдер менять условия без согласия потребителя?
   Ожидаемый результат: Нет односторонних изменений без согласия потребителя
   Правовая отсылка: Закон BE 2540, положение об односторонних изменениях
2. ПРОЗРАЧНОСТЬ И ДОСТУПНОСТЬ УСЛОВИЙ (transparency_conditions)
   Вопрос: Понятны ли условия договора? Все ли платежи и комиссии четко указаны?
   Ожидаемый результат: Ясное изложение условий, отсутствие скрытых платежей
   Правовая отсылка: Закон BE 2540, общий принцип прозрачности условий
3. СПРАВЕДЛИВОЕ РАСПРЕДЕЛЕНИЕ РИСКОВ (risk_distribution)
   Вопрос: Есть ли условия, предоставляющие одностороннее преимущество?
   Ожидаемый результат: Баланс прав и обязанностей сторон
   Правовая отсылка: Закон BE 2540, положения о балансе прав и обязанностей
4. ПРАВО НА РАСТОРЖЕНИЕ ДОГОВОРА (termination_rights)
   Вопрос: Есть ли возможность без штрафов расторгнуть договор, указаны ли сроки?
   Ожидаемый результат: Потребитель может расторгнуть договор с возвратом средств
   Правовая отсылка: Закон BE 2540, права потребителей на расторжение
Формат и стиль ответа (строго соблюдайте):
- Язык: русский.
- Для каждого критерия укажите:
  - status: "compliant", "non_compliant", "partially_compliant", или "unclear".
  - explanation: 1–2 коротких предложения (≤30 слов). Суть и факты. Без воды, без пересказа договора, без общих фраз.
  - recommendations: 1–3 конкретных шага по исправлению (лаконично, повелительное наклонение).
  - confidence_score: число от 0.0 до 1.0.
- Если данных в тексте нет — ставьте status="unclear" и explanation вида: "Нет явных положений в тексте".
- Не добавляйте вступления/заключения, только по критериям.
"""
def _create_legal_framework_prompt(contract_text: str) -> str:
    """Create prompt for legal framework analysis"""
    return f"""
Анализируйте следующий текст договора в соответствии с правовыми рамками тайского законодательства.
ТЕКСТ ДОГОВОРА:
{contract_text}
Проанализируйте данный договор согласно следующим критериям:
5. ОТВЕТСТВЕННОСТЬ СТОРОН (party_responsibility)
   Вопрос: Есть ли разумные ограничения ответственности? Не исключена ли полностью ответственность провайдера?
   Ожидаемый результат: Справедливое распределение ответственности, отсутствие полного освобождения провайдера
   Правовая отсылка: Тайский Гражданский кодекс, статья 171
6. ДОБРОСОВЕСТНОСТЬ ТОЛКОВАНИЯ ДОГОВОРА (good_faith_interpretation)
   Вопрос: Соответствует ли договор принципам добросовестности?
   Ожидаемый результат: Условия договора не нарушают принципы добросовестности
   Правовая отсылка: Тайский Гражданский кодекс, статья 368
7. СООТВЕТСТВИЕ ЗАКОНОДАТЕЛЬСТВУ (legal_compliance)
   Вопрос: Соответствует ли договор действующему тайскому законодательству?
   Ожидаемый результат: Полное соответствие национальному законодательству Таиланда
   Правовая отсылка: Конституция Таиланда и действующие законы
8. ИНФОРМАЦИЯ О РИСКАХ (risk_information)
   Вопрос: Раскрыты ли все существенные риски для потребителя?
   Ожидаемый результат: Полное раскрытие рисков, связанных с услугой
   Правовая отсылка: Закон BE 2540, обязанности по раскрытию информации
9. МЕХАНИЗМ ПОДАЧИ ЖАЛОБ И РАССМОТРЕНИЯ ИСКОВ (complaint_mechanism)
   Вопрос: Есть ли четкий механизм подачи и рассмотрения жалоб?
   Ожидаемый результат: Доступный и эффективный механизм разрешения споров
   Правовая отсылка: Закон BE 2540, процедуры рассмотрения жалоб
10. ИДЕНТИФИКАЦИЯ СТОРОН ДОГОВОРА (party_identification)
    Вопрос: Четко ли идентифицированы все стороны договора?
    Ожидаемый результат: Полная идентификация всех сторон с указанием реквизитов
    Правовая отсылка: Тайский Гражданский кодекс, требования к договорам
Формат и стиль ответа (строго соблюдайте):
- Язык: русский.
- Для каждого критерия укажите:
  - status: "compliant", "non_compliant", "partially_compliant", или "unclear".
  - explanation: 1–2 коротких предложения (≤30 слов), без воды и общих фраз.
  - recommendations: 1–3 конкретных шага (лаконично).
  - confidence_score: число 0.0–1.0.
- При отсутствии данных — status="unclear" и краткое объяснение: "Нет явных положений в тексте".
- Без вступлений и заключений — только по критериям.
"""
def _create_data_protection_prompt(contract_text: str) -> str:
    """Create prompt for data protection analysis"""
    return f"""
Анализируйте следующий текст договора в соответствии с требованиями по защите персональных данных.
ТЕКСТ ДОГОВОРА:
{contract_text}
Проанализируйте данный договор согласно следующим критериям:
11. ЗАЩИТА ПЕРСОНАЛЬНЫХ ДАННЫХ (personal_data_protection)
    Вопрос: Соблюдаются ли требования по защите персональных данных (ISO 27001)?
    Ожидаемый результат: Соответствие стандартам защиты персональных данных
    Правовая отсылка: Закон BE 2562 (2019), Закон о защите персональных данных
12. СОГЛАСИЕ СУБЪЕКТА ПЕРСОНАЛЬНЫХ ДАННЫХ (data_subject_consent)
    Вопрос: Получено ли явное согласие на обработку персональных данных?
    Ожидаемый результат: Явное и осознанное согласие субъекта данных
    Правовая отсылка: Закон BE 2562 (2019), статьи о согласии субъекта данных
Формат и стиль ответа (строго соблюдайте):
- Язык: русский.
- Для каждого критерия укажите:
  - status: "compliant", "non_compliant", "partially_compliant", или "unclear".
  - explanation: до 2 коротких предложений (≤30 слов), по делу.
  - recommendations: 1–3 конкретных шага (лаконично).
  - confidence_score: число 0.0–1.0.
- Если сведений нет — status="unclear" и explanation: "Нет явных положений в тексте".
- Никаких лишних вводных/заключений.
"""
def _create_contract_structure_prompt(contract_text: str) -> str:
    """Create prompt for contract structure analysis"""
    return f"""
Анализируйте следующий текст договора в соответствии с требованиями к структуре договора.
ТЕКСТ ДОГОВОРА:
{contract_text}
Проанализируйте данный договор согласно следующим критериям:
13. ЯЗЫК ДОГОВОРА (contract_language)
    Вопрос: Составлен ли договор на тайском языке или содержит объяснения на тайском?
    Ожидаемый результат: Договор на тайском языке или с переводом ключевых положений
    Правовая отсылка: Закон BE 2540, требования к языку договоров
14. УКАЗАНИЕ ПОЛНОЙ ЦЕНЫ (full_price_indication)
    Вопрос: Указана ли полная цена услуги включая все сборы и комиссии?
    Ожидаемый результат: Полная и прозрачная информация о стоимости
    Правовая отсылка: Закон BE 2540, требования к ценообразованию
15. ПОДРОБНОЕ ОПИСАНИЕ УСЛУГ (service_description)
    Вопрос: Подробно ли описаны предоставляемые услуги?
    Ожидаемый результат: Детальное описание всех услуг и их характеристик
    Правовая отсылка: Закон BE 2540, требования к описанию услуг
16. ИНФОРМАЦИЯ О ПРАВЕ РАСТОРЖЕНИЯ ДОГОВОРА (termination_right_info)
    Вопрос: Уведомлен ли потребитель о 7-дневном праве на расторжение?
    Ожидаемый результат: Четкая информация о праве расторжения в течение 7 дней
    Правовая отсылка: Закон BE 2540, статья о праве на охлаждение
Формат и стиль ответа (строго соблюдайте):
- Язык: русский.
- Для каждого критерия укажите:
  - status: "compliant", "non_compliant", "partially_compliant", или "unclear".
  - explanation: 1–2 коротких предложения (≤30 слов), только суть.
  - recommendations: 1–3 конкретных шага (кратко).
  - confidence_score: 0.0–1.0.
- При отсутствии данных — status="unclear" и краткое объяснение.
- Не добавляйте лишний текст до/после критериев.
"""
def _create_regulatory_compliance_prompt(contract_text: str) -> str:
    """Create prompt for regulatory compliance analysis"""
    return f"""
Анализируйте следующий текст договора в соответствии с требованиями регулятивного соответствия.
ТЕКСТ ДОГОВОРА:
{contract_text}
Проанализируйте данный договор согласно следующим критериям:
17. РЕГИСТРАЦИЯ ОПЕРАТОРА (operator_registration)
    Вопрос: Зарегистрирован ли оператор в соответствующих органах?
    Ожидаемый результат: Документальное подтверждение регистрации оператора
    Правовая отсылка: Закон BE 2568 (2025), требования к цифровым активам
18. ЮРИСДИКЦИЯ УСЛУГИ (service_jurisdiction)
    Вопрос: Ориентирована ли услуга на тайский рынок?
    Ожидаемый результат: Четкое определение юрисдикции и применимого права
    Правовая отсылка: Закон BE 2542 (1999), Закон об иностранном бизнесе
19. ЛИЦЕНЗИРОВАНИЕ И РЕГИСТРАЦИЯ (licensing_registration)
    Вопрос: Есть ли все необходимые лицензии для оказания услуг?
    Ожидаемый результат: Наличие всех требуемых лицензий и разрешений
    Правовая отсылка: Закон BE 2568 (2025), лицензионные требования
20. КВАЛИФИКАЦИЯ И ПРОВЕРКА КЛИЕНТОВ (KYC) (kyc_qualification)
    Вопрос: Внедрены ли процедуры идентификации и проверки клиентов?
    Ожидаемый результат: Соответствие требованиям KYC и AML
    Правовая отсылка: Закон BE 2560 (2017), Закон о платежных системах
21. МЕРЫ ПО БОРЬБЕ С МОШЕННИЧЕСТВОМ (anti_fraud_measures)
    Вопрос: Предусмотрены ли меры для предотвращения мошенничества?
    Ожидаемый результат: Комплексные меры по предотвращению и выявлению мошенничества
    Правовая отсылка: Закон BE 2560 (2017), антимошеннические требования
22. КАТЕГОРИЯ ПЛАТЕЖНОЙ СИСТЕМЫ (payment_system_category)
    Вопрос: Правильно ли классифицирована платежная система?
    Ожидаемый результат: Корректная классификация согласно типу платежной системы
    Правовая отсылка: Закон BE 2560 (2017), классификация платежных систем
23. ИНОСТРАННЫЙ СТАТУС КОМПАНИИ (foreign_company_status)
    Вопрос: Соблюдаются ли требования для иностранных компаний?
    Ожидаемый результат: Соответствие регулированию деятельности иностранных компаний
    Правовая отсылка: Закон BE 2542 (1999), ограничения для иностранного бизнеса
Формат и стиль ответа (строго соблюдайте):
- Язык: русский.
- Для каждого критерия укажите:
  - status: "compliant", "non_compliant", "partially_compliant", или "unclear".
  - explanation: 1–2 коротких предложения (≤30 слов), по делу, без воды.
  - recommendations: 1–3 конкретных шага (лаконично).
  - confidence_score: 0.0–1.0.
- Если сведений нет — status="unclear" и краткое объяснение.
- Выведите только ответы по критериям, без вступлений и выводов.
"""
def _configure_gemini() -> genai.Client:
    """Configure Gemini client"""
    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY"),
        vertexai=False,
        http_options=HttpOptions(api_version='v1beta',
                                       base_url=os.getenv("GOOGLE_API_BASE_URL", None))
    )
    return client
async def _analyze_group(
    client: genai.Client,
    prompt: str,
    model_name: str,
    response_schema: type
) -> dict:
    """Analyze a single group of criteria"""
    config = GenerateContentConfig(
        temperature=1.0,  # Low temperature for consistent, factual responses
        max_output_tokens=65536,
        top_p=0.95,
        response_mime_type="application/json",
        response_schema=response_schema,
        safety_settings=[
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
    )
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    if not response.candidates or not response.candidates[0].content.parts:
        raise Exception("No response generated by Gemini")
    if hasattr(response, 'parsed') and response.parsed:
        result = response.parsed
    else:
        response_text = response.candidates[0].content.parts[0].text
        import json
        analysis_data = json.loads(response_text)
        result = response_schema(**analysis_data)
    return result
def _calculate_overall_compliance(results: dict) -> tuple[float, list[str], list[str]]:
    """Calculate overall compliance score and extract issues/recommendations"""
    all_criteria = []
    critical_issues = []
    recommendations = []
    for group_result in results.values():
        for field_name, field_value in group_result.__dict__.items():
            if hasattr(field_value, 'status'):
                all_criteria.append(field_value)
                if field_value.status == ComplianceStatus.NON_COMPLIANT:
                    critical_issues.append(f"{field_name}: {field_value.explanation}")
                if field_value.recommendations:
                    recommendations.append(field_value.recommendations)
    if not all_criteria:
        return 0.0, critical_issues, recommendations
    compliance_scores = []
    for criterion in all_criteria:
        if criterion.status == ComplianceStatus.COMPLIANT:
            compliance_scores.append(1.0)
        elif criterion.status == ComplianceStatus.PARTIALLY_COMPLIANT:
            compliance_scores.append(0.5)
        elif criterion.status == ComplianceStatus.NON_COMPLIANT:
            compliance_scores.append(0.0)
        else:  # UNCLEAR
            compliance_scores.append(0.25)
    overall_score = sum(compliance_scores) / len(compliance_scores)
    return overall_score, critical_issues, recommendations
def _create_summary(results: dict, overall_score: float) -> str:
    """Create executive summary based on results"""
    compliance_level = "высокий" if overall_score > 0.8 else "средний" if overall_score > 0.5 else "низкий"
    non_compliant_count = 0
    for group_result in results.values():
        for field_name, field_value in group_result.__dict__.items():
            if hasattr(field_value, 'status') and field_value.status == ComplianceStatus.NON_COMPLIANT:
                non_compliant_count += 1
    summary = f"""
Анализ договора показал {compliance_level} уровень соответствия требованиям тайского законодательства 
(общая оценка: {overall_score:.2f}). Выявлено {non_compliant_count} критических нарушений 
из 23 проанализированных критериев. Основные области для улучшения включают защиту потребителей, 
соблюдение регулятивных требований и структуру договора.
"""
    return summary.strip()
def analyze_contract(
    contract_text: str,
    api_key: Optional[str] = None,
    contract_id: Optional[str] = None,
    model_name: str = "gemini-2.5-pro"
) -> LegalAnalysisResult:
    """
    Analyze a legal contract using Google Gemini AI with grouped parallel analysis
    Args:
        contract_text: The contract text to analyze
        api_key: Google Gemini API key (if not provided, will use GEMINI_API_KEY env var)
        contract_id: Optional contract identifier
        model_name: Gemini model to use
    Returns:
        LegalAnalysisResult: Structured analysis result
    Raises:
        ValueError: If API key is not provided or invalid
        Exception: If analysis fails
    """
    client = _configure_gemini()
    async def run_parallel_analysis():
        """Run all analysis groups in parallel"""
        tasks = [
            _analyze_group(
                client,
                _create_consumer_protection_prompt(contract_text),
                model_name,
                ConsumerProtectionAnalysis
            ),
            _analyze_group(
                client,
                _create_legal_framework_prompt(contract_text),
                model_name,
                LegalFrameworkAnalysis
            ),
            _analyze_group(
                client,
                _create_data_protection_prompt(contract_text),
                model_name,
                DataProtectionAnalysis
            ),
            _analyze_group(
                client,
                _create_contract_structure_prompt(contract_text),
                model_name,
                ContractStructureAnalysis
            ),
            _analyze_group(
                client,
                _create_regulatory_compliance_prompt(contract_text),
                model_name,
                RegulatoryComplianceAnalysis
            )
        ]
        results = await asyncio.gather(*tasks)
        return {
            'consumer_protection': results[0],
            'legal_framework': results[1],
            'data_protection': results[2],
            'contract_structure': results[3],
            'regulatory_compliance': results[4]
        }
    try:
        results = asyncio.run(run_parallel_analysis())
        overall_score, critical_issues, recommendations = _calculate_overall_compliance(results)
        summary = _create_summary(results, overall_score)
        result = LegalAnalysisResult(
            contract_id=contract_id,
            analysis_date=datetime.now().isoformat(),
            overall_compliance_score=overall_score,
            unilateral_changes=results['consumer_protection'].unilateral_changes,
            transparency_conditions=results['consumer_protection'].transparency_conditions,
            risk_distribution=results['consumer_protection'].risk_distribution,
            termination_rights=results['consumer_protection'].termination_rights,
            party_responsibility=results['legal_framework'].party_responsibility,
            good_faith_interpretation=results['legal_framework'].good_faith_interpretation,
            legal_compliance=results['legal_framework'].legal_compliance,
            risk_information=results['legal_framework'].risk_information,
            complaint_mechanism=results['legal_framework'].complaint_mechanism,
            party_identification=results['legal_framework'].party_identification,
            personal_data_protection=results['data_protection'].personal_data_protection,
            data_subject_consent=results['data_protection'].data_subject_consent,
            contract_language=results['contract_structure'].contract_language,
            full_price_indication=results['contract_structure'].full_price_indication,
            service_description=results['contract_structure'].service_description,
            termination_right_info=results['contract_structure'].termination_right_info,
            operator_registration=results['regulatory_compliance'].operator_registration,
            service_jurisdiction=results['regulatory_compliance'].service_jurisdiction,
            licensing_registration=results['regulatory_compliance'].licensing_registration,
            kyc_qualification=results['regulatory_compliance'].kyc_qualification,
            anti_fraud_measures=results['regulatory_compliance'].anti_fraud_measures,
            payment_system_category=results['regulatory_compliance'].payment_system_category,
            foreign_company_status=results['regulatory_compliance'].foreign_company_status,
            summary=summary,
            critical_issues=critical_issues,
            recommendations=recommendations
        )
        return result
    except Exception as e:
        raise Exception(f"Failed to analyze contract: {str(e)}")
