import random
from typing import Any, Dict


class DataFeed:
    def get_latest(self) -> Dict[str, float]:
        return {
            "price": round(random.uniform(100.0, 200.0), 2),
            "rsi": round(random.uniform(30.0, 70.0), 2)
        }

    def get_data(self) -> Any:
        return self.get_latest()
