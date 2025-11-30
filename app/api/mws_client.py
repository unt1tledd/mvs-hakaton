from typing import List, Type
from fastapi import HTTPException
import requests
from app.models import Post


class MWSClient:
    BASE_URL = "https://tables.mws.ru/fusion/v1/datasheets"

    def __init__(self, datasheet_id: str, view_id: str, token: str, model: Type[Post], limit: int = 10000):
        self.datasheet_id = datasheet_id
        self.view_id = view_id
        self.token = token
        self.limit = limit
        self._post_db: List[Post] = []
        self.model = model
        self._last_update: float = 0
        self._update_interval: float = 1

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @property
    def records_url(self):
        return f"{self.BASE_URL}/{self.datasheet_id}/records"

    def _fetch_posts(self):
        params = {"viewId": self.view_id}

        resp = requests.get(self.records_url, headers=self.headers, params=params)
        resp.raise_for_status()

        data = resp.json()
        self._post_db = [self.model(**item) for item in data["records"]]

    def create_record(self, fields: dict):
        payload = {
            "records": [{"fields": fields}],
            "fieldKey": "name"
        }

        url = f"{self.records_url}?viewId={self.view_id}"
        resp = requests.post(url, json=payload, headers=self.headers)
        js = resp.json()

        if resp.status_code != 200 or not js.get("success"):
            raise HTTPException(resp.status_code, f"MWS Error: {js}")

        return js["data"]["records"][0]

    def update_record(self, record_id: str, fields: dict):
        url = f"{self.records_url}/{record_id}"
        payload = {"fields": fields}

        resp = requests.patch(url, json=payload, headers=self.headers)
        js = resp.json()

        if resp.status_code != 200 or not js.get("success"):
            raise HTTPException(resp.status_code, f"MWS Error: {js}")

        return js["data"]["records"][0]

    def get_client(self):
        return self.model

    def get_posts(self):
        self.refresh()
        return self._post_db[:self.limit]

    def refresh(self, force: bool = False):
        import time
        now = time.time()
        if force or not self._post_db or now - self._last_update > self._update_interval:
            self._fetch_posts()
            self._last_update = now

    def find_post(self, post_id: str):
        self.refresh()
        for post in self._post_db:
            if post.post_id == post_id:
                return post
        return None

    def filter_posts(self, cond: str, **filters):
        self.refresh()

        ops = {
            "eq": lambda a, b: a == b,
            "lt": lambda a, b: a < b,
            "lte": lambda a, b: a <= b,
            "gt": lambda a, b: a > b,
            "gte": lambda a, b: a >= b,
        }

        if cond not in ops:
            raise ValueError(f"Unknown condition: {cond}")

        op_func = ops[cond]

        result = self._post_db
        for field, value in filters.items():
            self.check_field(field)
            result = [p for p in result if op_func(getattr(p, field), value)]

        return result

    def sort_posts(self, field: str, limit: int = 10, descending: bool = True):
        self.refresh()
        sorted_posts = sorted(self._post_db, key=lambda p: getattr(p, field), reverse=descending)
        return sorted_posts[:limit]

    def check_field(self, field: str):
        if field not in self.model.model_fields:
            raise HTTPException(400, f"Field '{field}' not exists")
