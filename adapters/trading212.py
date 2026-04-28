import base64
import logging
from typing import Dict, List

import requests

from adapters.broker import Broker
from core.models import Order, Position


class Trading212Broker(Broker):
    def __init__(self, api_key: str, secret: str, live: bool = False):
        if live:
            self._base_url = "https://live.trading212.com/api/v0"
        else:
            self._base_url = "https://demo.trading212.com/api/v0"

        credentials = f"{api_key}:{secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self._headers = {"Authorization": f"Basic {encoded}"}

    def _get(self, path: str) -> Dict:
        url = f"{self._base_url}{path}"
        response = requests.get(url, headers=self._headers)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, body: Dict) -> requests.Response:
        url = f"{self._base_url}{path}"
        response = requests.post(url, headers=self._headers, json=body)
        if response.status_code == 429:
            logging.warning(f"Rate limit hit for {path}")
            return response
        logging.info(f"Response body: {response.text}")
        response.raise_for_status()
        return response

    def get_balance(self) -> float:
        try:
            response = self._get("/equity/account/summary")
            return float(response["cash"]["availableToTrade"])
        except Exception as e:
            logging.error(f"Error getting balance: {e}")
            raise

    def get_positions(self) -> List[Position]:
        try:
            response = self._get("/equity/positions")
            positions = []
            for item in response:
                symbol = item["instrument"]["ticker"]
                quantity = float(item["quantity"])
                entry_price = float(item["averagePricePaid"])
                positions.append(Position(symbol=symbol, quantity=quantity, entry_price=entry_price))
            return positions
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            raise

    def place_order(self, order: Order) -> None:
        try:
            # Convert symbol to Trading212 ticker format
            if order.symbol.endswith("_US_EQ"):
                ticker = order.symbol
            else:
                ticker = f"{order.symbol}_US_EQ"

            # Set quantity positive for buys, negative for sells
            if order.side.lower() == "buy":
                quantity = abs(order.quantity)
            else:
                quantity = -abs(order.quantity)

            quantity = round(quantity, 2)

            if quantity == 0.0:
                logging.warning(f"Quantity rounded to 0 for {order.symbol}, skipping order")
                return

            body = {
                "ticker": ticker,
                "quantity": quantity,
                "extendedHours": False
            }

            response = self._post("/equity/orders/market", body)
            logging.info(f"Order response: {response.text}")
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            raise
