import os
import csv
from typing import Dict, List, Any, Optional

class OlistDataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.order_items: Dict[str, List[Dict[str, Any]]] = {}
        self.order_payments: Dict[str, List[Dict[str, Any]]] = {}
        self.order_reviews: Dict[str, List[Dict[str, Any]]] = {}
        self.sellers: Dict[str, Dict[str, Any]] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}
        self._is_loaded = False

    def load_data(self):
        if self._is_loaded:
            return

        # 1. Load orders
        orders_path = os.path.join(self.data_dir, "olist_orders_dataset.csv")
        if os.path.exists(orders_path):
            with open(orders_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.orders[row["order_id"]] = row

        # 2. Load order_items
        items_path = os.path.join(self.data_dir, "olist_order_items_dataset.csv")
        if os.path.exists(items_path):
            with open(items_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    oid = row["order_id"]
                    if oid not in self.order_items:
                        self.order_items[oid] = []
                    self.order_items[oid].append(row)

        # 3. Load order_payments
        payments_path = os.path.join(self.data_dir, "olist_order_payments_dataset.csv")
        if os.path.exists(payments_path):
            with open(payments_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    oid = row["order_id"]
                    if oid not in self.order_payments:
                        self.order_payments[oid] = []
                    self.order_payments[oid].append(row)

        # 4. Load sellers
        sellers_path = os.path.join(self.data_dir, "olist_sellers_dataset.csv")
        if os.path.exists(sellers_path):
            with open(sellers_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.sellers[row["seller_id"]] = row

        # 5. Load customers
        cust_path = os.path.join(self.data_dir, "olist_customers_dataset.csv")
        if os.path.exists(cust_path):
            with open(cust_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.customers[row["customer_id"]] = row

        self._is_loaded = True

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders.get(order_id)

    def get_items(self, order_id: str) -> List[Dict[str, Any]]:
        return self.order_items.get(order_id, [])

    def get_payments(self, order_id: str) -> List[Dict[str, Any]]:
        return self.order_payments.get(order_id, [])
