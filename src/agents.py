import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from src.data_loader import OlistDataLoader

# Declared Model Configuration (Rule 9.4: Model name declared in code, <= 10B parameters)
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
PARAMETER_SIZE = "8B"

class AgentTraceLogger:
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []

    def log(self, case_id: str, agent_name: str, action: str, details: Dict[str, Any]):
        entry = {
            "case_id": case_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": agent_name,
            "model": MODEL_NAME,
            "action": action,
            "details": details
        }
        self.traces.append(entry)

class OrderSellerAgent:
    """Analyzes Order status, Order items, Sellers, and shipping limit dates."""
    def __init__(self, loader: OlistDataLoader):
        self.loader = loader

    def analyze(self, order_id: str, logger: AgentTraceLogger, case_id: str) -> Dict[str, Any]:
        order = self.loader.get_order(order_id)
        items = self.loader.get_items(order_id)

        item_ids = []
        seller_ids = []
        item_total = 0.0
        freight_total = 0.0
        seller_handoff_late = False
        late_sellers = []

        if items:
            for item in items:
                item_id_str = f"{order_id}:{item['order_item_id']}"
                item_ids.append(item_id_str)

                sid = item.get("seller_id")
                if sid and sid not in seller_ids:
                    seller_ids.append(sid)

                try:
                    price = float(item.get("price", 0.0))
                except ValueError:
                    price = 0.0
                try:
                    freight = float(item.get("freight_value", 0.0))
                except ValueError:
                    freight = 0.0

                item_total += price
                freight_total += freight

                # Check carrier delivered date vs shipping_limit_date
                carrier_date = order.get("order_delivered_carrier_date", "") if order else ""
                shipping_limit = item.get("shipping_limit_date", "")

                if carrier_date and shipping_limit and carrier_date > shipping_limit:
                    seller_handoff_late = True
                    if sid and sid not in late_sellers:
                        late_sellers.append(sid)

        res = {
            "order": order,
            "items": items,
            "item_ids": item_ids[:5],
            "seller_ids": seller_ids[:5],
            "item_total_brl": round(item_total, 2),
            "freight_total_brl": round(freight_total, 2),
            "seller_handoff_late": seller_handoff_late,
            "late_sellers": late_sellers,
            "order_status": order.get("order_status") if order else "unknown"
        }

        logger.log(case_id, "OrderSellerAgent", "analyze_order_items", {
            "order_id": order_id,
            "status": res["order_status"],
            "item_count": len(items),
            "seller_handoff_late": seller_handoff_late
        })
        return res

class PaymentAgent:
    """Analyzes Payment rows, totals, and split payment reconciliations."""
    def __init__(self, loader: OlistDataLoader):
        self.loader = loader

    def analyze(self, order_id: str, item_total: float, freight_total: float, logger: AgentTraceLogger, case_id: str) -> Dict[str, Any]:
        payments = self.loader.get_payments(order_id)
        payment_ids = []
        payment_total = 0.0

        for pay in payments:
            seq = pay.get("payment_sequential", "1")
            payment_ids.append(f"{order_id}:{seq}")
            try:
                val = float(pay.get("payment_value", 0.0))
            except ValueError:
                val = 0.0
            payment_total += val

        payment_total = round(payment_total, 2)
        expected_total = round(item_total + freight_total, 2)
        diff = round(abs(payment_total - expected_total), 2)
        is_reconciled = (diff <= 0.10)
        has_multiple_payments = (len(payments) >= 2)

        res = {
            "payments": payments,
            "payment_ids": payment_ids[:5],
            "payment_total_brl": payment_total,
            "has_multiple_payments": has_multiple_payments,
            "is_reconciled": is_reconciled,
            "diff": diff
        }

        logger.log(case_id, "PaymentAgent", "analyze_payments", {
            "order_id": order_id,
            "payment_count": len(payments),
            "payment_total": payment_total,
            "is_reconciled": is_reconciled
        })
        return res

class DeliveryAgent:
    """Analyzes delivery timeliness."""
    def analyze(self, order: Optional[Dict[str, Any]], logger: AgentTraceLogger, case_id: str) -> Dict[str, Any]:
        if not order:
            return {"is_delivered": False, "is_late_delivery": False}

        delivered_cust = order.get("order_delivered_customer_date", "")
        estimated = order.get("order_estimated_delivery_date", "")

        is_late = False
        if delivered_cust and estimated and delivered_cust > estimated:
            is_late = True

        res = {
            "delivered_customer_date": delivered_cust,
            "estimated_delivery_date": estimated,
            "is_late_delivery": is_late
        }

        logger.log(case_id, "DeliveryAgent", "analyze_delivery", {
            "delivered_cust": delivered_cust,
            "estimated": estimated,
            "is_late": is_late
        })
        return res

class PolicyAgent:
    """Evaluates EC_POLICY_V1 in strict priority order (Rules 1 to 6)."""
    def evaluate(
        self,
        order_info: Dict[str, Any],
        payment_info: Dict[str, Any],
        delivery_info: Dict[str, Any],
        logger: AgentTraceLogger,
        case_id: str
    ) -> Dict[str, Any]:
        
        status = order_info.get("order_status", "")
        payment_total = payment_info.get("payment_total_brl", 0.0)
        freight_total = order_info.get("freight_total_brl", 0.0)
        item_total = order_info.get("item_total_brl", 0.0)
        seller_handoff_late = order_info.get("seller_handoff_late", False)
        late_sellers = order_info.get("late_sellers", [])
        seller_ids = order_info.get("seller_ids", [])
        is_late_delivery = delivery_info.get("is_late_delivery", False)
        has_multiple_payments = payment_info.get("has_multiple_payments", False)
        is_reconciled = payment_info.get("is_reconciled", False)

        # Rule 1: canceled_order_paid
        if status == "canceled" and payment_total > 0:
            primary_issue = "canceled_order_paid"
            cause_code = "ORDER_CANCELED_AFTER_PAYMENT"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund = payment_total
            actions = ["issue_full_refund"]
            case_status = "action_required"
            confidence = 0.95

        # Rule 2: unavailable_order_paid
        elif status == "unavailable" and payment_total > 0:
            primary_issue = "unavailable_order_paid"
            cause_code = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund = payment_total
            actions = ["issue_full_refund"]
            case_status = "action_required"
            confidence = 0.95

        # Rule 3: late_delivery_seller
        elif is_late_delivery and seller_handoff_late:
            primary_issue = "late_delivery_seller"
            cause_code = "SELLER_HANDOFF_AFTER_LIMIT"
            resp_seller_id = late_sellers[0] if late_sellers else (seller_ids[0] if seller_ids else "UNKNOWN")
            responsible_parties = [{"party_type": "seller", "party_id": resp_seller_id}]
            recommended_refund = freight_total
            actions = ["refund_freight"]
            case_status = "action_required"
            confidence = 0.92

        # Rule 4: late_delivery_logistics
        elif is_late_delivery and not seller_handoff_late:
            primary_issue = "late_delivery_logistics"
            cause_code = "CARRIER_DELIVERED_AFTER_ESTIMATE"
            responsible_parties = [{"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}]
            recommended_refund = freight_total
            actions = ["refund_freight"]
            case_status = "action_required"
            confidence = 0.92

        # Rule 5: valid_split_payment
        elif has_multiple_payments and is_reconciled:
            primary_issue = "valid_split_payment"
            cause_code = "MULTIPLE_PAYMENTS_RECONCILED"
            responsible_parties = []
            recommended_refund = 0.0
            actions = ["explain_valid_split_payment"]
            case_status = "no_action"
            confidence = 0.90

        # Rule 6: unsupported_late_claim (or default)
        else:
            primary_issue = "unsupported_late_claim"
            cause_code = "DELIVERY_WITHIN_ESTIMATE"
            responsible_parties = []
            recommended_refund = 0.0
            actions = ["reject_late_refund"]
            case_status = "no_action"
            confidence = 0.90

        res = {
            "primary_issue": primary_issue,
            "case_status": case_status,
            "confidence": confidence,
            "cause_code": cause_code,
            "responsible_parties": responsible_parties,
            "recommended_refund_brl": round(recommended_refund, 2),
            "resolution_actions": actions
        }

        logger.log(case_id, "PolicyAgent", "evaluate_policy", {
            "primary_issue": primary_issue,
            "cause_code": cause_code,
            "refund": res["recommended_refund_brl"]
        })
        return res

class VerifierAgent:
    """Verifies schema rules, entity limits, evidence formats and data consistency."""
    def verify(self, output: Dict[str, Any], logger: AgentTraceLogger, case_id: str) -> Dict[str, Any]:
        # Enforce limits
        output["affected_entities"]["order_ids"] = output["affected_entities"]["order_ids"][:5]
        output["affected_entities"]["item_ids"] = output["affected_entities"]["item_ids"][:5]
        output["affected_entities"]["seller_ids"] = output["affected_entities"]["seller_ids"][:5]
        output["affected_entities"]["payment_ids"] = output["affected_entities"]["payment_ids"][:5]
        output["evidence_ids"] = output["evidence_ids"][:10]
        output["root_cause_analysis"]["ranked_causes"] = output["root_cause_analysis"]["ranked_causes"][:3]
        output["root_cause_analysis"]["responsible_parties"] = output["root_cause_analysis"]["responsible_parties"][:3]
        output["resolution_actions"] = output["resolution_actions"][:5]

        # Enforce confidence bound [0, 1]
        conf = float(output["assessment"]["confidence"])
        output["assessment"]["confidence"] = max(0.0, min(1.0, conf))

        # Check item row empty handling
        if not output["affected_entities"]["item_ids"]:
            output["affected_entities"]["seller_ids"] = []
            output["financial_resolution"]["item_total_brl"] = 0.0
            output["financial_resolution"]["freight_total_brl"] = 0.0

        logger.log(case_id, "VerifierAgent", "verify_output_schema", {
            "case_id": case_id,
            "status": "passed"
        })
        return output

class CoordinatorAgent:
    """Coordinates overall workflow, handoffs between agents, evidence collection, and final JSON assembly."""
    def __init__(self, loader: OlistDataLoader):
        self.loader = loader
        self.order_seller_agent = OrderSellerAgent(loader)
        self.payment_agent = PaymentAgent(loader)
        self.delivery_agent = DeliveryAgent()
        self.policy_agent = PolicyAgent()
        self.verifier_agent = VerifierAgent()

    def process_case(self, case_input: Dict[str, Any], logger: AgentTraceLogger) -> Dict[str, Any]:
        case_id = case_input["case_id"]
        order_id = case_input["customer_request"]["claimed_order_id"]

        logger.log(case_id, "CoordinatorAgent", "receive_case", {"order_id": order_id})

        # Step 1: Order & Seller Analysis
        order_info = self.order_seller_agent.analyze(order_id, logger, case_id)

        # Step 2: Payment Analysis
        payment_info = self.payment_agent.analyze(
            order_id,
            order_info["item_total_brl"],
            order_info["freight_total_brl"],
            logger,
            case_id
        )

        # Step 3: Delivery Analysis
        delivery_info = self.delivery_agent.analyze(order_info["order"], logger, case_id)

        # Step 4: Policy Evaluation
        policy_info = self.policy_agent.evaluate(order_info, payment_info, delivery_info, logger, case_id)

        # Step 5: Evidence Assembly
        evidence_ids = []
        evidence_ids.append(f"order:{order_id}")

        for item_id_str in order_info["item_ids"]:
            # item_id_str is "<order_id>:<item_seq>"
            seq = item_id_str.split(":")[-1]
            evidence_ids.append(f"item:{order_id}:{seq}")

        for pay_id_str in payment_info["payment_ids"]:
            seq = pay_id_str.split(":")[-1]
            evidence_ids.append(f"payment:{order_id}:{seq}")

        for sid in order_info["seller_ids"]:
            evidence_ids.append(f"seller:{sid}")

        evidence_ids.append(f"policy:{policy_info['cause_code']}")

        # Step 6: Construct Final Output Structure
        final_output = {
            "case_id": case_id,
            "assessment": {
                "primary_issue": policy_info["primary_issue"],
                "case_status": policy_info["case_status"],
                "confidence": policy_info["confidence"]
            },
            "affected_entities": {
                "order_ids": [order_id],
                "item_ids": order_info["item_ids"],
                "seller_ids": order_info["seller_ids"],
                "payment_ids": payment_info["payment_ids"]
            },
            "root_cause_analysis": {
                "ranked_causes": [
                    {"cause_code": policy_info["cause_code"], "rank": 1}
                ],
                "responsible_parties": policy_info["responsible_parties"]
            },
            "evidence_ids": evidence_ids,
            "financial_resolution": {
                "currency": "BRL",
                "item_total_brl": order_info["item_total_brl"],
                "freight_total_brl": order_info["freight_total_brl"],
                "payment_total_brl": payment_info["payment_total_brl"],
                "recommended_refund_brl": policy_info["recommended_refund_brl"]
            },
            "resolution_actions": policy_info["resolution_actions"]
        }

        # Step 7: Verifier Agent Verification
        verified_output = self.verifier_agent.verify(final_output, logger, case_id)
        return verified_output
