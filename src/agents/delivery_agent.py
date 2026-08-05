"""
Delivery & Logistics Domain Agent.
Responsible for evaluating delivery timelines, estimated delivery dates, and logistics timestamps.
"""

from src.schemas import BaseAgent, CaseContext, AgentResult, DeliveryAnalysis


class DeliveryAgent(BaseAgent):
    """Evaluates actual delivery timestamps against estimated delivery dates."""

    def __init__(self):
        super().__init__(name="DeliveryAgent")

    def process(self, context: CaseContext) -> AgentResult:
        order_id = context.case_input.customer_request.claimed_order_id
        raw_data = context.raw_data
        order_row = raw_data.get("order_row") or {}

        delivered_cust = order_row.get("order_delivered_customer_date")
        if not isinstance(delivered_cust, str):
            delivered_cust = None

        estimated_del = order_row.get("order_estimated_delivery_date")
        if not isinstance(estimated_del, str):
            estimated_del = None

        delivered_carrier = order_row.get("order_delivered_carrier_date")
        if not isinstance(delivered_carrier, str):
            delivered_carrier = None

        is_delivered_late = False
        if delivered_cust and estimated_del and delivered_cust > estimated_del:
            is_delivered_late = True

        # Carrier late handoff is determined per item limit date in order_seller agent,
        # but carrier handoff date relative to items is stored here as context.
        is_carrier_late_handoff = False
        if context.order_seller and context.order_seller.is_seller_late:
            is_carrier_late_handoff = True

        analysis = DeliveryAnalysis(
            order_id=order_id,
            order_delivered_customer_date=delivered_cust,
            order_estimated_delivery_date=estimated_del,
            order_delivered_carrier_date=delivered_carrier,
            is_delivered_late=is_delivered_late,
            is_carrier_late_handoff=is_carrier_late_handoff,
            evidence_ids=[]
        )

        context.delivery = analysis

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "delivered_customer_date": delivered_cust,
                "estimated_delivery_date": estimated_del,
                "is_delivered_late": is_delivered_late,
                "is_carrier_late_handoff": is_carrier_late_handoff
            }
        )
