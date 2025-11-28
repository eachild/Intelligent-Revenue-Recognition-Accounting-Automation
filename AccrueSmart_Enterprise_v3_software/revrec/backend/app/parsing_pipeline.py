from typing import Optional, List

from . import nlp_rules, ai
from .schemas import IngestResult, ExtractedPO, RiskFinding, Recommendation

def run_contract_parsing(text: str) -> IngestResult:
    """
    Executes the contract parsing pipeline, attempting to use nlp_rules first
    and falling back to the AI module if nlp_rules encounter an exception.
    """
    standard: Optional[str] = None
    standard_reason: Optional[str] = None
    currency: Optional[str] = None
    transaction_price: Optional[float] = None
    performance_obligations: List[ExtractedPO] = []
    risks: List[RiskFinding] = []
    commissions: Optional[float] = None
    recommendations: List[Recommendation] = []
    revenue_summary: Optional[str] = None
    nonrevenue_summary: Optional[str] = None
    try:
        standard, standard_reason = nlp_rules.detect_standard(text)
        currency = nlp_rules.find_currency(text)
        transaction_price = nlp_rules.find_total_price(text)
        performance_obligations = nlp_rules.extract_pos(text)
        risks = nlp_rules.detect_risks(text)
        commissions = nlp_rules.extract_commission(text)
        recommendations = nlp_rules.recommendations(text)
        if standard == 'ASC606':
            revenue_summary = nlp_rules.summarize_revenue(text)
            nonrevenue_summary = None
        else:
            revenue_summary = None
            nonrevenue_summary = nlp_rules.summarize_nonrevenue(text)
    except Exception:
        # fallback to the lightweight ai module
        standard, standard_reason = ai.classify_standard(text)
        performance_obligations = ai.extract_pos(text)
        risks = ai.detect_risks(text)
        recommendations = ai.recommend_language(text)
        
        # ai module does not extract these fields, so they remain None
        currency = None
        transaction_price = None
        commissions = None
        revenue_summary = None
        nonrevenue_summary = None

    return IngestResult(
        standard=standard,
        standard_reason=standard_reason,
        currency=currency,
        transaction_price=transaction_price,
        performance_obligations=performance_obligations,
        risks=risks,
        commissions=commissions,
        recommendations=recommendations,
        revenue_summary=revenue_summary,
        nonrevenue_summary=nonrevenue_summary
    )
