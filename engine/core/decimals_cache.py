import json
import logging
import os
import pathlib
from typing import Optional


class DecimalsCache:
    def __init__(self, logger: Optional[logging.Logger] = None, cache_file: Optional[str] = None):
        self.logger = logger or logging.getLogger(__name__)
        if cache_file is None:
            project_root = pathlib.Path(__file__).resolve().parents[2]
            default_path = project_root / "engine" / "data" / "decimals_cache.json"
            cache_file = os.getenv("DECIMALS_CACHE_FILE", str(default_path))
        self.cache_file = cache_file
        self._cache = {}
        self._load()

    def _load(self) -> None:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for key, value in data.items():
                        try:
                            self._cache[str(key).lower()] = int(value)
                        except Exception:
                            continue
            else:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load decimals cache: {e}")

    def get(self, address: Optional[str]) -> Optional[int]:
        if not address:
            return None
        return self._cache.get(str(address).lower())

    def set(self, address: Optional[str], decimals: int) -> None:
        if not address:
            return
        key = str(address).lower()
        try:
            decimals_int = int(decimals)
        except Exception:
            return
        if self._cache.get(key) == decimals_int:
            return
        self._cache[key] = decimals_int
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to persist decimals cache: {e}")
