"""Single official coordinator for deterministic tools plus Ollama reviews."""

from typing import Any, Dict, Optional

from src.agents.delivery_agent import DeliveryAgent
from src.agents.order_seller_agent import OrderSellerAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.verifier_agent import VerifierAgent
from src.data_repository import DataRepository
from src.llm_client import LLMClient, PARAMETER_SIZE, PROVIDER
from src.schemas import CaseContext, CaseInput
from src.trace_writer import TraceWriter


AGENT_ACTIONS = {
    "OrderSellerAgent": "analyze_order_items",
    "PaymentAgent": "analyze_payments",
    "DeliveryAgent": "analyze_delivery",
    "PolicyAgent": "evaluate_policy",
    "VerifierAgent": "verify_output",
}


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
            VerifierAgent(data_repository=self.data_repository),
        ]

    @staticmethod
    def _build_case_input(case_input: Any) -> CaseInput:
        if isinstance(case_input, CaseInput):
            return case_input
        if isinstance(case_input, dict):
            return CaseInput(**case_input)
        raise TypeError("case_input must be a dict or CaseInput instance")

    def _trace(
        self,
        case_id: str,
        agent: str,
        action: str,
        details: Dict[str, Any],
        llm_result: Dict[str, Any],
    ) -> None:
        self.trace_writer.write_event(
            case_id=case_id,
            agent=agent,
            model=self.llm_client.model,
            parameter_size=PARAMETER_SIZE,
            provider=PROVIDER,
            action=action,
            details=details,
            llm_result=llm_result,
        )

    def run(self, case_input: Any) -> Dict[str, Any]:
        case = self._build_case_input(case_input)
        order_id = case.customer_request.claimed_order_id
        raw_data: Dict[str, Any] = {
            "order_row": self.data_repository.get_order(order_id),
            "items": self.data_repository.get_order_items(order_id),
            "payments": self.data_repository.get_order_payments(order_id),
        }
        context = CaseContext(case_input=case, raw_data=raw_data)

        coordinator_facts = {
            "case_id": case.case_id,
            "order_id": order_id,
            "policy_version": case.policy_version,
            "task": "Route verified order, payment, delivery, policy and verification work.",
        }
        coordinator_review = self.llm_client.review("CoordinatorAgent", coordinator_facts)
        self._trace(
            case.case_id,
            "CoordinatorAgent",
            "receive_case",
            coordinator_facts,
            coordinator_review,
        )

        last_result: Optional[Dict[str, Any]] = None
        for agent in self.agents:
            result = agent.process(context)
            review_facts = {
                "case_id": case.case_id,
                "order_id": order_id,
                "success": result.success,
                "result": result.data,
                "error_message": result.error_message,
            }
            llm_review = self.llm_client.review(agent.name, review_facts)
            trace_details = result.data
            if agent.name == "VerifierAgent":
                trace_details = {
                    "case_id": case.case_id,
                    "status": "passed" if result.success else "failed",
                    "error_count": len(context.verification_errors),
                }
            self._trace(
                case.case_id,
                agent.name,
                AGENT_ACTIONS[agent.name],
                trace_details,
                llm_review,
            )
            if not result.success:
                raise RuntimeError(
                    f"{agent.name} rejected {case.case_id}: {result.error_message}"
                )
            last_result = result.data

        if last_result is None:
            raise RuntimeError(f"No output produced for {case.case_id}")
        return last_result
