import threading

import requests

from core.config import save_config


class KeyManager:
    def __init__(self, keys_data=None):
        self.keys = keys_data or []
        self.current_index = 0
        self._lock = threading.Lock()

    def add_key(self, key, remark="", monthly_limit=500):
        self.keys.append({
            "key": key,
            "remark": remark,
            "monthly_usage": 0,
            "monthly_limit": monthly_limit,
            "enabled": True,
            "in_use": False,
        })

    def remove_key(self, index):
        if 0 <= index < len(self.keys):
            self.keys.pop(index)

    def toggle_key(self, index):
        if 0 <= index < len(self.keys):
            self.keys[index]["enabled"] = not self.keys[index]["enabled"]

    def get_available_keys(self):
        return [
            k for k in self.keys
            if k["enabled"] and k["monthly_usage"] < k["monthly_limit"]
        ]

    def acquire_key(self):
        with self._lock:
            for offset in range(len(self.keys)):
                idx = (self.current_index + offset) % len(self.keys)
                k = self.keys[idx]
                if (k["enabled"] and k["monthly_usage"] < k["monthly_limit"]
                        and not k.get("in_use", False)):
                    k["in_use"] = True
                    self.current_index = (idx + 1) % len(self.keys)
                    return k
            return None

    def release_key(self, key_val):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["in_use"] = False
                    break

    def disable_key(self, key_val):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["enabled"] = False
                    k["in_use"] = False
                    break

    def update_usage(self, key_val, usage):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["monthly_usage"] = usage
                    k["in_use"] = False
                    break

    def check_compression_count(self, key_data):
        try:
            resp = requests.post(
                "https://api.tinify.com/shrink",
                auth=("api", key_data["key"]),
                data=b"",
                headers={"Content-Type": "application/octet-stream"},
                timeout=10,
            )
            count = resp.headers.get("Compression-Count")
            if count is not None:
                return int(count)
        except:
            pass
        return None

    def refresh_all_usage(self):
        for k in self.keys:
            count = self.check_compression_count(k)
            if count is not None:
                k["monthly_usage"] = count

    def save(self, config):
        config["api_keys"] = self.keys
        save_config(config)

    @classmethod
    def from_config(cls, config):
        return cls(config.get("api_keys", []))
