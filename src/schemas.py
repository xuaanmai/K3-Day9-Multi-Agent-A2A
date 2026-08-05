"""Shared contracts and output validation schemas for the multi-agent pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


PrimaryIssue = Literal[
    "canceled_order_paid",
    "unavailable_order_paid",
    "late_delivery_seller",
    "late_delivery_logistics",
    "valid_split_payment",
    "unsupported_late_claim",
]
CaseStatus = Literal["action_required", "no_action"]
ResolutionAction = Literal[
    "issue_full_refund",
    "refund_freight",
    "explain_valid_split_payment",
    "reject_late_refund",
]
CauseCode = Literal[
    "SELLER_HANDOFF_AFTER_LIMIT",
    "CARRIER_DELIVERED_AFTER_ESTIMATE",
    "ORDER_CANCELED_AFTER_PAYMENT",
    "ORDER_UNAVAILABLE_AFTER_PAYMENT",
    "MULTIPLE_PAYMENTS_RECONCILED",
    "DELIVERY_WITHIN_ESTIMATE",
]
PartyType = Literal["platform", "seller", "logistics_provider"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerRequest(StrictModel):
    language: str
    message: str
    claimed_order_id: str = Field(min_length=1)


class CaseInput(StrictModel):
    case_id: str = Field(pattern=r"^EC_[A-Za-z0-9_]+$")
    opened_at: str
    customer_request: CustomerRequest
    policy_version: str = "EC_POLICY_V1"


class AgentResult(BaseModel):
    agent_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class Payment(BaseModel):
    payment_sequential: int
    payment_type: str
    payment_value_brl: float = Field(ge=0)


class PaymentAnalysis(BaseModel):
    """Payment contract compatible with the deterministic Payment Agent."""

    order_id: str
    payments: List[Payment] = Field(default_factory=list)
    payment_ids: List[str] = Field(default_factory=list)
    payment_row_count: int = Field(default=0, ge=0)
    payment_total_brl: float = Field(default=0.0, ge=0)
    expected_total_brl: float = Field(default=0.0, ge=0)
    difference_brl: float = Field(default=0.0, ge=0)
    payment_matches: bool = True
    is_split_payment: bool = False
    evidence_ids: List[str] = Field(default_factory=list)

    # Compatibility aliases used by the original Policy/Verifier agents.
    @property
    def payment_count(self) -> int:
        return self.payment_row_count

    @property
    def reconciled_with_items(self) -> bool:
        return self.payment_matches

    @property
    def payment_diff_brl(self) -> float:
        return self.difference_brl

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class OrderSellerAnalysis(BaseModel):
    order_id: str
    order_status: str = "unknown"
    seller_ids: List[str] = Field(default_factory=list)
    item_ids: List[str] = Field(default_factory=list)
    item_total_brl: float = Field(default=0.0, ge=0)
    freight_total_brl: float = Field(default=0.0, ge=0)
    shipping_limit_dates: List[str] = Field(default_factory=list)
    is_seller_late: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class DeliveryAnalysis(BaseModel):
    order_id: str
    order_delivered_customer_date: Optional[str] = None
    order_estimated_delivery_date: Optional[str] = None
    order_delivered_carrier_date: Optional[str] = None
    is_delivered_late: bool = False
    is_carrier_late_handoff: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class PolicyResolution(BaseModel):
    primary_issue: PrimaryIssue
    case_status: CaseStatus
    confidence: float = Field(ge=0, le=1)
    ranked_causes: List[Dict[str, Any]] = Field(default_factory=list)
    responsible_parties: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_refund_brl: float = Field(default=0.0, ge=0)
    resolution_actions: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class CaseContext(BaseModel):
    """Mutable handoff state shared by the coordinator and domain agents."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_input: CaseInput
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    # Any keeps this shared contract compatible with team-owned dataclass fixtures.
    order_seller: Any = None
    payment: Optional[PaymentAnalysis] = None
    delivery: Optional[DeliveryAnalysis] = None
    policy: Optional[PolicyResolution] = None
    verification_errors: List[str] = Field(default_factory=list)


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, context: CaseContext) -> AgentResult:
        raise NotImplementedError


class Assessment(StrictModel):
    primary_issue: PrimaryIssue
    case_status: CaseStatus
    confidence: float = Field(ge=0, le=1)


class AffectedEntities(StrictModel):
    order_ids: List[str] = Field(default_factory=list, max_length=5)
    item_ids: List[str] = Field(default_factory=list, max_length=5)
    seller_ids: List[str] = Field(default_factory=list, max_length=5)
    payment_ids: List[str] = Field(default_factory=list, max_length=5)


class RankedCause(StrictModel):
    cause_code: CauseCode
    rank: int = Field(ge=1, le=3)


class ResponsibleParty(StrictModel):
    party_type: PartyType
    party_id: str = Field(min_length=1)


class RootCauseAnalysis(StrictModel):
    ranked_causes: List[RankedCause] = Field(default_factory=list, max_length=3)
    responsible_parties: List[ResponsibleParty] = Field(default_factory=list, max_length=3)


class FinancialResolution(StrictModel):
    currency: Literal["BRL"]
    item_total_brl: float = Field(ge=0)
    freight_total_brl: float = Field(ge=0)
    payment_total_brl: float = Field(ge=0)
    recommended_refund_brl: float = Field(ge=0)


class CaseOutput(StrictModel):
    """Exact submission schema, including all limits stated in the assignment."""

    case_id: str = Field(pattern=r"^EC_[A-Za-z0-9_]+$")
    assessment: Assessment
    affected_entities: AffectedEntities
    root_cause_analysis: RootCauseAnalysis
    evidence_ids: List[str] = Field(max_length=10)
    financial_resolution: FinancialResolution
    resolution_actions: List[ResolutionAction] = Field(max_length=5)

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence_ids(cls, values: List[str]) -> List[str]:
        from src.evidence_validator import is_valid_evidence_id

        invalid = [value for value in values if not is_valid_evidence_id(value)]
        if invalid:
            raise ValueError(f"invalid evidence ID format: {invalid}")
        if len(values) != len(set(values)):
            raise ValueError("evidence IDs must be unique")
        return values


class VerificationError(StrictModel):
    code: str
    field: str
    message: str


class VerificationResult(StrictModel):
    """Contract returned by Verifier Agent to Coordinator Agent."""

    valid: bool
    errors: List[VerificationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @field_validator("errors")
    @classmethod
    def errors_must_match_validity(cls, errors: List[VerificationError], info: Any):
        if info.data.get("valid") is True and errors:
            raise ValueError("a valid result cannot contain errors")
        return errors
