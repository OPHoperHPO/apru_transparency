"""
Pydantic models for structured legal analysis output with grouped criteria
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
class ComplianceStatus(str, Enum):
    """Compliance status enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNCLEAR = "unclear"
class LegalCriterion(BaseModel):
    """Base model for legal criterion analysis"""
    status: ComplianceStatus = Field(description="Compliance status")
    explanation: str = Field(description="Detailed explanation of the analysis")
    recommendations: Optional[str] = Field(None, description="Recommendations for compliance")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of the analysis (0-1)")
class UnilateralChanges(LegalCriterion):
    """Analysis of unilateral changes clause"""
    pass
class TransparencyConditions(LegalCriterion):
    """Analysis of transparency and accessibility conditions"""
    pass
class RiskDistribution(LegalCriterion):
    """Analysis of fair risk distribution"""
    pass
class TerminationRights(LegalCriterion):
    """Analysis of contract termination rights"""
    pass
class PartyResponsibility(LegalCriterion):
    """Analysis of party responsibilities"""
    pass
class GoodFaithInterpretation(LegalCriterion):
    """Analysis of good faith interpretation"""
    pass
class LegalCompliance(LegalCriterion):
    """Analysis of legal compliance"""
    pass
class RiskInformation(LegalCriterion):
    """Analysis of risk information disclosure"""
    pass
class ComplaintMechanism(LegalCriterion):
    """Analysis of complaint and lawsuit mechanisms"""
    pass
class PartyIdentification(LegalCriterion):
    """Analysis of party identification"""
    pass
class PersonalDataProtection(LegalCriterion):
    """Analysis of personal data protection"""
    pass
class DataSubjectConsent(LegalCriterion):
    """Analysis of data subject consent"""
    pass
class ContractLanguage(LegalCriterion):
    """Analysis of contract language"""
    pass
class FullPriceIndication(LegalCriterion):
    """Analysis of full price indication"""
    pass
class ServiceDescription(LegalCriterion):
    """Analysis of detailed service description"""
    pass
class TerminationRightInfo(LegalCriterion):
    """Analysis of termination right information"""
    pass
class OperatorRegistration(LegalCriterion):
    """Analysis of operator registration"""
    pass
class ServiceJurisdiction(LegalCriterion):
    """Analysis of service jurisdiction"""
    pass
class LicensingRegistration(LegalCriterion):
    """Analysis of licensing and registration"""
    pass
class KYCQualification(LegalCriterion):
    """Analysis of KYC qualification and client verification"""
    pass
class AntiFraudMeasures(LegalCriterion):
    """Analysis of anti-fraud measures"""
    pass
class PaymentSystemCategory(LegalCriterion):
    """Analysis of payment system category"""
    pass
class ForeignCompanyStatus(LegalCriterion):
    """Analysis of foreign company status"""
    pass
class ConsumerProtectionAnalysis(BaseModel):
    """Consumer protection criteria analysis"""
    unilateral_changes: UnilateralChanges
    transparency_conditions: TransparencyConditions
    risk_distribution: RiskDistribution
    termination_rights: TerminationRights
class LegalFrameworkAnalysis(BaseModel):
    """Legal framework criteria analysis"""
    party_responsibility: PartyResponsibility
    good_faith_interpretation: GoodFaithInterpretation
    legal_compliance: LegalCompliance
    risk_information: RiskInformation
    complaint_mechanism: ComplaintMechanism
    party_identification: PartyIdentification
class DataProtectionAnalysis(BaseModel):
    """Data protection criteria analysis"""
    personal_data_protection: PersonalDataProtection
    data_subject_consent: DataSubjectConsent
class ContractStructureAnalysis(BaseModel):
    """Contract structure criteria analysis"""
    contract_language: ContractLanguage
    full_price_indication: FullPriceIndication
    service_description: ServiceDescription
    termination_right_info: TerminationRightInfo
class RegulatoryComplianceAnalysis(BaseModel):
    """Regulatory compliance criteria analysis"""
    operator_registration: OperatorRegistration
    service_jurisdiction: ServiceJurisdiction
    licensing_registration: LicensingRegistration
    kyc_qualification: KYCQualification
    anti_fraud_measures: AntiFraudMeasures
    payment_system_category: PaymentSystemCategory
    foreign_company_status: ForeignCompanyStatus
class LegalAnalysisResult(BaseModel):
    """Complete legal analysis result"""
    contract_id: Optional[str] = Field(None, description="Contract identifier")
    analysis_date: str = Field(description="Date of analysis (ISO format)")
    overall_compliance_score: float = Field(ge=0.0, le=1.0, description="Overall compliance score (0-1)")
    unilateral_changes: UnilateralChanges
    transparency_conditions: TransparencyConditions
    risk_distribution: RiskDistribution
    termination_rights: TerminationRights
    party_responsibility: PartyResponsibility
    good_faith_interpretation: GoodFaithInterpretation
    legal_compliance: LegalCompliance
    risk_information: RiskInformation
    complaint_mechanism: ComplaintMechanism
    party_identification: PartyIdentification
    personal_data_protection: PersonalDataProtection
    data_subject_consent: DataSubjectConsent
    contract_language: ContractLanguage
    full_price_indication: FullPriceIndication
    service_description: ServiceDescription
    termination_right_info: TerminationRightInfo
    operator_registration: OperatorRegistration
    service_jurisdiction: ServiceJurisdiction
    licensing_registration: LicensingRegistration
    kyc_qualification: KYCQualification
    anti_fraud_measures: AntiFraudMeasures
    payment_system_category: PaymentSystemCategory
    foreign_company_status: ForeignCompanyStatus
    summary: str = Field(description="Executive summary of the analysis")
    critical_issues: list[str] = Field(description="List of critical compliance issues")
    recommendations: list[str] = Field(description="List of recommendations for improvement")