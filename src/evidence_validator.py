"""Syntax validation for evidence identifiers allowed by the assignment."""

import re


EVIDENCE_PATTERNS = (
    re.compile(r"^order:[^:]+$"),
    re.compile(r"^item:[^:]+:[1-9][0-9]*$"),
    re.compile(r"^payment:[^:]+:[1-9][0-9]*$"),
    re.compile(r"^seller:[^:]+$"),
    re.compile(
        r"^policy:(?:SELLER_HANDOFF_AFTER_LIMIT|"
        r"CARRIER_DELIVERED_AFTER_ESTIMATE|"
        r"ORDER_CANCELED_AFTER_PAYMENT|"
        r"ORDER_UNAVAILABLE_AFTER_PAYMENT|"
        r"MULTIPLE_PAYMENTS_RECONCILED|"
        r"DELIVERY_WITHIN_ESTIMATE)$"
    ),
)


def is_valid_evidence_id(evidence_id: object) -> bool:
    """Return True only for evidence IDs directly derivable from allowed sources."""

    return isinstance(evidence_id, str) and any(
        pattern.fullmatch(evidence_id) for pattern in EVIDENCE_PATTERNS
    )
