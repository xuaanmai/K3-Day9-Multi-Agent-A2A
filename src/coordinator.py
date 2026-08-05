from typing import Any, Dict, List, Optional

from src.data_repository import DataRepository
from src.llm_client import LLMClient
from src.schemas import CaseContext, CaseInput
from src.trace_writer import TraceWriter
from src.agents.delivery_agent import DeliveryAgent
from src.agents.order_seller_agent import OrderSellerAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.verifier_agent import VerifierAgent


class Coordinator:
    def __init__(
        self,
        data_repository: DataRepository,
        trace_writer: TraceWriter,
        llm_client: LLMClient,
    ):
        self.data_repository = data_repository
        self.trace_writer = trace_writer
        self.llm_client = llm_client
        self.agents = [
            OrderSellerAgent(),
            PaymentAgent(),
            DeliveryAgent(),
            PolicyAgent(),
            VerifierAgent(),
        ]

    def _build_case_input(self, case_input: Any) -> CaseInput:
        if isinstance(case_input, CaseInput):
            return case_input
        if isinstance(case_input, dict):
            return CaseInput(**case_input)
        raise TypeError("case_input must be a dict or CaseInput instance")

    def run(self, case_input: Any) -> Dict[str, Any]:
        case = self._build_case_input(case_input)
        order_id = case.customer_request.claimed_order_id

        raw_data: Dict[str, Any] = {
            "order_row": self.data_repository.get_order(order_id),
            "items": self.data_repository.get_order_items(order_id),
            "payments": self.data_repository.get_order_payments(order_id),
        }

        context = CaseContext(case_input=case, raw_data=raw_data)
        trace: Dict[str, Any] = {
            "case_id": case.case_id,
            "order_id": order_id,
            "raw_data_counts": {
                "order_row": 1 if raw_data["order_row"] else 0,
                "items": len(raw_data["items"]),
                "payments": len(raw_data["payments"]),
            },
            "agent_results": [],
        }

        last_result: Optional[Dict[str, Any]] = None
        for agent in self.agents:
            result = agent.process(context)
            trace["agent_results"].append(
                {
                    "agent": agent.name,
                    "success": result.success,
                    "data": result.data,
                    "error_message": result.error_message,
                }
            )
            last_result = result.data

        self.trace_writer.write(trace)

        output = {"case_id": case.case_id}
        if last_result is not None:
            output.update(last_result)
        if context.verification_errors:
            output["verification_errors"] = context.verification_errors
        return output
