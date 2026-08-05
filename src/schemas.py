"""Minimal shared contracts required by the deterministic Payment Agent.

The repository does not yet contain the team-owned Pydantic schemas.  These
dataclasses preserve the existing agent interface without introducing schemas
for the other domain agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class CustomerRequest:
    language: str
    message: str
    claimed_order_id: str


@dataclass
class CaseInput:
    case_id: str
    opened_at: str
    customer_request: CustomerRequest
    policy_version: str = "EC_POLICY_V1"


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class BaseAgent:
    """Common interface already used by the repository's agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, context: "CaseContext") -> AgentResult:
        raise NotImplementedError


@dataclass
class Payment:
    payment_sequential: int
    payment_type: str
    payment_value_brl: float


@dataclass
class PaymentAnalysis:
    order_id: str
    payments: list[Payment] = field(default_factory=list)
    payment_ids: list[str] = field(default_factory=list)
    payment_row_count: int = 0
    payment_total_brl: float = 0.0
    expected_total_brl: float = 0.0
    difference_brl: float = 0.0
    payment_matches: bool = True
    is_split_payment: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaseContext:
    case_input: CaseInput
    raw_data: dict[str, Any] = field(default_factory=dict)
    order_seller: Any = None
    payment: Optional[PaymentAnalysis] = None
