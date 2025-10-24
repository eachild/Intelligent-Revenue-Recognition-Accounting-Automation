from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

RecognitionMethod = Literal['point_in_time', 'straight_line', 'milestone', 'percent_complete', 'usage_royalty']

class Milestone(BaseModel):
    id: str
    description: str = ""
    percent_of_price: float = Field(ge=0.0, le=1.0)
    met_date: Optional[str] = None

class UsageRecord(BaseModel):
    period: str
    amount: float

class Payment(BaseModel):
    period: str
    amount: float

class FinancingComponent(BaseModel):
    timing_months: int = 0
    annual_rate: Optional[float] = None

class PrincipalAgentIndicators(BaseModel):
    control_before_transfer: bool = False
    inventory_risk: bool = False
    pricing_discretion: bool = False
    credit_risk: bool = False
    primary_obligor: bool = False

class PrincipalAgent(BaseModel):
    role: Literal['principal', 'agent'] = 'principal'
    indicators: PrincipalAgentIndicators = PrincipalAgentIndicators()
    evidence: Optional[Dict] = None
    net_revenue_amount: Optional[float] = None

class POParams(BaseModel):
    milestones: List[Milestone] = []
    percent_schedule: List[Dict] = []
    usage_schedule: List[UsageRecord] = []
    payments: List[Payment] = []
    release_date: Optional[str] = None
    notes: Optional[str] = None

class PerformanceObligationIn(BaseModel):
    po_id: str
    description: str
    ssp: float
    method: RecognitionMethod
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    params: POParams = POParams()
    principal_agent: PrincipalAgent = PrincipalAgent()
    financing: Optional[FinancingComponent] = None
    bill_and_hold: bool = False
    consignment: bool = False
    acceptance_required: bool = False

class VariableConsideration(BaseModel):
    returns_rate: float = 0.0
    loyalty_pct: float = 0.0
    loyalty_months: int = 12
    loyalty_breakage_rate: float = 0.0

class CommissionPlanIn(BaseModel):
    total_commission: float
    benefit_months: int = 12
    practical_expedient_1yr: bool = False
    

class ContractIn(BaseModel):
    contract_id: str
    customer: str
    transaction_price: float
    standard: str = "ASC606"
    raw_text: Optional[str] = ""
    pos: List[PerformanceObligationIn]
    commission: Optional[CommissionPlanIn] = None
    variable: Optional[VariableConsideration] = None
    entity: Optional[str] = None
    currency: Optional[str] = "USD"
    product_line: Optional[str] = None
    geography: Optional[str] = None

class AllocResult(BaseModel):
    po_id: str
    ssp: float
    allocated_price: float

class AllocationResponse(BaseModel):
    allocated: List[AllocResult]
    schedules: Dict[str, Dict[str, float]]
    commission_schedule: Dict[str, float] | None = None
    adjustments: Dict | None = None

class ExtractedPO(BaseModel):
    description: str
    ssp: Optional[float] = None
    method: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class RiskFinding(BaseModel):
    type: str
    snippet: str
    severity: Literal['low', 'medium', 'high'] = 'medium'
    comment: Optional[str] = None

class Recommendation(BaseModel):
    issue: str
    suggested_language: str
    rationale: str

class IngestResult(BaseModel):
    standard: Literal['ASC606', 'ASC842', 'ASC808', 'ASC610-20', 'ASC945/944', 'NonRevenue', 'Unknown'] = 'Unknown'
    standard_reason: str
    currency: Optional[str] = None
    transaction_price: Optional[float] = None
    performance_obligations: List[ExtractedPO] = []
    commissions: Optional[float] = None
    risks: List[RiskFinding] = []
    recommendations: List[Recommendation] = []
    revenue_summary: Optional[str] = None
    nonrevenue_summary: Optional[str] = None

class FXRate(BaseModel):
    period: str
    currency: str
    rate_to_parent: float
    rate_type: Optional[Literal['average', 'month_end']] = None

class EntityTrial(BaseModel):
    entity: str
    currency: str
    schedules: Dict[str, float]
    commissions: Dict[str, float] = {}

class ConsolidationIn(BaseModel):
    parent_currency: str = "USD"
    entities: List[EntityTrial]
    fx_rates: List[FXRate]
    eliminations: List[Dict] = []
    rate_type: Literal['average', 'month_end'] = 'month_end'
    intercompany: List[Dict] = []
