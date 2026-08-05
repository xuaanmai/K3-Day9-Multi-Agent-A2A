from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


class DataRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.orders_df = self._load_csv("olist_orders_dataset.csv")
        self.items_df = self._load_csv("olist_order_items_dataset.csv")
        self.payments_df = self._load_csv("olist_order_payments_dataset.csv")
        self.sellers_df = self._load_csv("olist_sellers_dataset.csv")
        self.customers_df = self._load_csv("olist_customers_dataset.csv")
        self.products_df = self._load_csv("olist_products_dataset.csv")
        self.geolocation_df = self._load_csv("olist_geolocation_dataset.csv")
        self.reviews_df = self._load_csv("olist_order_reviews_dataset.csv")
        self.category_df = self._load_csv("product_category_name_translation.csv")

    def _load_csv(self, file_name: str) -> pd.DataFrame:
        path = self.data_dir / file_name
        df = pd.read_csv(path, dtype=str)
        return df

    def _normalize_row(self, row: pd.Series) -> Dict[str, Any]:
        return {k: (None if pd.isna(v) else v) for k, v in row.items()}

    def get_order(self, order_id: str) -> Dict[str, Any]:
        order_rows = self.orders_df.loc[self.orders_df["order_id"] == order_id]
        if order_rows.empty:
            return {}
        return self._normalize_row(order_rows.iloc[0])

    def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        item_rows = self.items_df.loc[self.items_df["order_id"] == order_id]
        if item_rows.empty:
            return []
        return [self._normalize_row(row) for _, row in item_rows.iterrows()]

    def get_order_payments(self, order_id: str) -> List[Dict[str, Any]]:
        payment_rows = self.payments_df.loc[self.payments_df["order_id"] == order_id]
        if payment_rows.empty:
            return []
        return [self._normalize_row(row) for _, row in payment_rows.iterrows()]

    def seller_exists(self, seller_id: str) -> bool:
        return not self.sellers_df.loc[self.sellers_df["seller_id"] == seller_id].empty

    def item_exists(self, order_id: str, item_id: int) -> bool:
        return not self.items_df.loc[
            (self.items_df["order_id"] == order_id)
            & (self.items_df["order_item_id"] == str(item_id))
        ].empty

    def payment_exists(self, order_id: str, sequence: int) -> bool:
        return not self.payments_df.loc[
            (self.payments_df["order_id"] == order_id)
            & (self.payments_df["payment_sequential"] == str(sequence))
        ].empty

    def schema_report(self) -> Dict[str, Any]:
        return {
            "orders": self._describe(self.orders_df),
            "items": self._describe(self.items_df),
            "payments": self._describe(self.payments_df),
            "sellers": self._describe(self.sellers_df),
            "customers": self._describe(self.customers_df),
            "products": self._describe(self.products_df),
            "geolocation": self._describe(self.geolocation_df),
            "reviews": self._describe(self.reviews_df),
            "categories": self._describe(self.category_df),
        }

    def _describe(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isna().sum().to_dict(),
        }
