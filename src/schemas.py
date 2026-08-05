from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseAgent:
    def __init__(self, name: str):
        self.name = name


class AgentResult(BaseModel):
    agent_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class CustomerRequest(BaseModel):
    language: str
    message: str
    claimed_order_id: str


class CaseInput(BaseModel):
    case_id: str
    opened_at: str
    customer_request: CustomerRequest
    policy_version: str = "EC_POLICY_V1"


class CaseContext(BaseModel):
    case_input: CaseInput
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    order_seller: Optional[OrderSellerAnalysis] = None
    payment: Optional[PaymentAnalysis] = None
    delivery: Optional[DeliveryAnalysis] = None
    policy: Optional[PolicyResolution] = None
    verification_errors: List[str] = Field(default_factory=list)


class OrderSellerAnalysis(BaseModel):
    order_id: str
    order_status: str = "unknown"
    seller_ids: List[str] = Field(default_factory=list)
    item_ids: List[str] = Field(default_factory=list)
    shipping_limit_dates: List[str] = Field(default_factory=list)
    item_total_brl: float = 0.0
    freight_total_brl: float = 0.0
    is_seller_late: bool = False
    evidence_ids: List[str] = Field(default_factory=list)


class PaymentAnalysis(BaseModel):
    order_id: str
    payment_ids: List[str] = Field(default_factory=list)
    payment_total_brl: float = 0.0
    payment_count: int = 0
    is_split_payment: bool = False
    reconciled_with_items: bool = False
    payment_diff_brl: float = 0.0
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
    primary_issue: str
    case_status: str
    confidence: float
    ranked_causes: List[Dict[str, Any]] = Field(default_factory=list)
    responsible_parties: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_refund_brl: float = 0.0
    resolution_actions: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
