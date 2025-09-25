# execution/broker.py

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.ticktype import TickTypeEnum
import threading
import time
from config import settings

class IBKRClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.historical_data = []
        self.portfolio_data = []
        self.account_summary = {}
        self.current_price = 0
        
        self.data_received_event = threading.Event()
        self.portfolio_received_event = threading.Event()
        self.account_summary_received_event = threading.Event()
        self.price_received_event = threading.Event()

    def historicalData(self, reqId, bar):
        self.historical_data.append([bar.date, bar.close])

    def historicalDataEnd(self, reqId, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        self.data_received_event.set()

    def accountSummary(self, reqId, account, tag, value, currency):
        if tag == "TotalCashValue":
            self.account_summary[tag] = float(value)

    def accountSummaryEnd(self, reqId: int):
        super().accountSummaryEnd(reqId)
        self.account_summary_received_event.set()

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        if position != 0:
            self.portfolio_data.append({'symbol': contract.symbol, 'position': int(position)})

    def positionEnd(self):
        super().positionEnd()
        self.portfolio_received_event.set()

    def tickPrice(self, reqId, tickType, price, attrib):
        # 4 = LAST_PRICE, 9 = CLOSE_PRICE
        if tickType in [4, 9] and price > 0:
            self.current_price = price
            self.price_received_event.set()

    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        super().error(reqId, errorCode, errorString)
        if errorCode not in [2104, 2106, 2158, 2109, 2100]:
             print(f"Error: {errorCode}, {errorString}")

    def get_etf_contract(self, symbol: str) -> Contract:
        contract_details = settings.ASSET_CONTRACTS.get(symbol)
        if not contract_details:
            raise ValueError(f"Keine Kontrakt-Details für Symbol {symbol} in settings.py gefunden.")

        contract = Contract()
        contract.symbol = contract_details["symbol"]
        
        # Liest den secType jetzt dynamisch aus den Settings
        contract.secType = contract_details.get("secType", "STK") # Standardwert ist "STK"
            
        contract.exchange = contract_details["exchange"]
        contract.currency = contract_details["currency"]
        
        if "primaryExchange" in contract_details:
            contract.primaryExchange = contract_details["primaryExchange"]

        return contract

    def fetch_historical_data(self, symbol: str):
        contract = self.get_etf_contract(symbol)
        self.historical_data = []
        self.data_received_event.clear()
        
        self.reqHistoricalData(
            reqId=int(time.time()),
            contract=contract,
            endDateTime="",
            durationStr="2 Y",
            barSizeSetting="1 month",
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        self.data_received_event.wait(timeout=15)
        return self.historical_data

    def fetch_account_summary(self):
        self.account_summary = {}
        self.account_summary_received_event.clear()
        self.reqAccountSummary(9001, "All", "TotalCashValue")
        self.account_summary_received_event.wait(timeout=10)
        return self.account_summary

    def fetch_positions(self):
        self.portfolio_data = []
        self.portfolio_received_event.clear()
        self.reqPositions()
        self.portfolio_received_event.wait(timeout=10)
        return self.portfolio_data
        
    def fetch_current_price(self, symbol: str):
        contract = self.get_etf_contract(symbol)
        self.current_price = 0
        self.price_received_event.clear()
        reqId = int(time.time())
        self.reqMktData(reqId, contract, "", False, False, [])
        self.price_received_event.wait(timeout=5)
        self.cancelMktData(reqId)
        return self.current_price

    def place_market_order(self, symbol: str, quantity: int, action: str):
        contract = self.get_etf_contract(symbol)
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = abs(quantity)
        order_id = int(time.time())
        print(f"Platziere {action}-Order für {abs(quantity)} Stk. von {symbol} (Order ID: {order_id})...")
        self.placeOrder(order_id, contract, order)
        time.sleep(1)

# --- Öffentliche Funktionen ---
def get_data_for_ticker_ibkr(app, ticker):
    return app.fetch_historical_data(ticker)

def get_account_details(app):
    cash = app.fetch_account_summary().get("TotalCashValue", 0)
    positions = app.fetch_positions()
    return cash, {p['symbol']: p['position'] for p in positions}

def get_current_price_ibkr(app, ticker):
    return app.fetch_current_price(ticker)

def execute_trades(app, trades):
    for trade in trades:
        app.place_market_order(trade['symbol'], trade['quantity'], trade['action'])
