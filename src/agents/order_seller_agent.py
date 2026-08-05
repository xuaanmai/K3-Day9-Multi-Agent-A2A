"""
Order & Seller Domain Agent.
Responsible for investigating order status, item items, seller IDs, item totals, freight totals, and shipping limit dates.
"""

from typing import List
import pandas as pd
from src.schemas import BaseAgent, CaseContext, AgentResult, OrderSellerAnalysis
from src.policies import fmt_order_evidence, fmt_item_evidence, fmt_seller_evidence


class OrderSellerAgent(BaseAgent):
    """Investigates order status, seller info, items, prices and seller handoff limits."""

    def __init__(self):
        super().__init__(name="OrderSellerAgent")

    def process(self, context: CaseContext) -> AgentResult:
        order_id = context.case_input.customer_request.claimed_order_id
        raw_data = context.raw_data

        order_row = raw_data.get("order_row") or {}
        items = raw_data.get("items") or []

        order_status = order_row.get("order_status", "unknown")
        
        seller_ids: List[str] = []
        item_ids: List[str] = []
        shipping_limit_dates: List[str] = []
        evidence_ids: List[str] = []

        if order_row:
            evidence_ids.append(fmt_order_evidence(order_id))

        item_total_brl = 0.0
        freight_total_brl = 0.0
        carrier_delivered_date = order_row.get("order_delivered_carrier_date")
        if not isinstance(carrier_delivered_date, str):
            carrier_delivered_date = None

        is_seller_late = False

        for item in items:
            s_id = item.get("seller_id")
            item_seq = item.get("order_item_id")
            if isinstance(s_id, str) and s_id not in seller_ids:
                seller_ids.append(s_id)
                evidence_ids.append(fmt_seller_evidence(s_id))
            
            if item_seq is not None and not (isinstance(item_seq, float) and pd.isna(item_seq)):
                i_id = fmt_item_evidence(order_id, item_seq)
                item_ids.append(i_id)
                evidence_ids.append(i_id)

            price = float(item.get("price", 0.0)) if not pd.isna(item.get("price", 0.0)) else 0.0
            freight = float(item.get("freight_value", 0.0)) if not pd.isna(item.get("freight_value", 0.0)) else 0.0
            item_total_brl += price
            freight_total_brl += freight

            limit_date = item.get("shipping_limit_date")
            if isinstance(limit_date, str):
                shipping_limit_dates.append(limit_date)
                if carrier_delivered_date and carrier_delivered_date > limit_date:
                    is_seller_late = True

        analysis = OrderSellerAnalysis(
            order_id=order_id,
            order_status=order_status,
            seller_ids=seller_ids,
            item_ids=item_ids,
            item_total_brl=round(item_total_brl, 2),
            freight_total_brl=round(freight_total_brl, 2),
            shipping_limit_dates=shipping_limit_dates,
            is_seller_late=is_seller_late,
            evidence_ids=evidence_ids
        )

        context.order_seller = analysis

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "order_status": order_status,
                "seller_count": len(seller_ids),
                "item_count": len(item_ids),
                "item_total_brl": analysis.item_total_brl,
                "freight_total_brl": analysis.freight_total_brl,
                "is_seller_late": is_seller_late
            }
        )
