import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from src.data_repository import DataRepository


def test_data_repository_order_lookup():
    repo = DataRepository(data_dir="data")
    order_id = "0008288aa423d2a3f00fcb17cd7d8719"

    order = repo.get_order(order_id)
    assert order["order_id"] == order_id
    assert order["order_status"] == "delivered"
    assert order["order_delivered_customer_date"] == "2018-02-26 13:55:22"

    items = repo.get_order_items(order_id)
    assert len(items) == 2
    assert items[0]["order_item_id"] == "1"
    assert items[1]["order_item_id"] == "2"
    assert items[0]["seller_id"] == "1f50f920176fa81dab994f9023523100"

    payments = repo.get_order_payments(order_id)
    assert len(payments) == 1
    assert payments[0]["payment_sequential"] == "1"
    assert payments[0]["payment_value"] == "126.54"

    assert repo.seller_exists("1f50f920176fa81dab994f9023523100") is True
    assert repo.seller_exists("missing_seller") is False
    assert repo.item_exists(order_id, 1) is True
    assert repo.item_exists(order_id, 99) is False
    assert repo.payment_exists(order_id, 1) is True
    assert repo.payment_exists(order_id, 2) is False
