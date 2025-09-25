import sys
import os
import threading
import time
import itertools

# --- Python den Weg zu den Modulen zeigen ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from execution import broker
from config import settings
from ibapi.contract import Contract

# === Konfiguration für den Diagnose-Lauf ===
# Eine Liste von häufigen Börsen und Währungen, die wir testen wollen.
COMMON_EXCHANGES = ["SMART", "IBIS2", "LSEETF", "BVME", "IBIS", "AEB"]
COMMON_CURRENCIES = ["EUR", "USD", "GBP"]
COMMON_SECTYPES = ["STK", "CMDTY"]

class DiagnosticClient(broker.IBKRClient):
    """Eine erweiterte Client-Klasse nur für die Diagnose."""
    def __init__(self):
        super().__init__()
        self.contract_details_received = threading.Event()
        self.found_contracts = []

    def contractDetails(self, reqId, contractDetails):
        """Wird aufgerufen, wenn ein passender Kontrakt gefunden wird."""
        super().contractDetails(reqId, contractDetails)
        self.found_contracts.append(contractDetails.contract)

    def contractDetailsEnd(self, reqId):
        """Wird aufgerufen, wenn die Suche beendet ist."""
        super().contractDetailsEnd(reqId)
        self.contract_details_received.set()

    def test_single_config(self, contract_to_test: Contract):
        """Testet eine einzelne, spezifische Kontrakt-Konfiguration."""
        self.found_contracts = []
        self.contract_details_received.clear()
        
        print(f"  -> Teste: Symbol={contract_to_test.symbol}, Exchange={contract_to_test.exchange}, Currency={contract_to_test.currency}, SecType={contract_to_test.secType}...")
        
        self.reqContractDetails(int(time.time()), contract_to_test)
        self.contract_details_received.wait(timeout=3)
        
        return self.found_contracts[0] if self.found_contracts else None

    def find_working_contract(self, symbol_to_test):
        """
        Testet systematisch verschiedene Konfigurationen für ein Symbol.
        """
        # --- Schritt 1: Teste die Konfiguration aus settings.py ZUERST ---
        print("  -> Teste Konfiguration aus settings.py...")
        try:
            initial_contract = self.get_etf_contract(symbol_to_test)
            result = self.test_single_config(initial_contract)
            if result:
                print("    --> ERFOLG! Konfiguration aus settings.py ist korrekt.")
                return result
            else:
                print("    --> FEHLSCHLAG. Starte Brute-Force-Suche...")
        except Exception as e:
            print(f"    --> FEHLER beim Erstellen des Kontrakts: {e}. Starte Brute-Force-Suche...")

        # --- Schritt 2: Wenn Schritt 1 fehlschlägt, starte die Brute-Force-Suche ---
        test_combinations = list(itertools.product(COMMON_EXCHANGES, COMMON_CURRENCIES, COMMON_SECTYPES))

        for exchange, currency, secType in test_combinations:
            contract = Contract()
            contract.symbol = symbol_to_test
            contract.exchange = exchange
            contract.currency = currency
            contract.secType = secType
            
            result = self.test_single_config(contract)
            if result:
                print(f"    --> ERFOLG! Gültige Konfiguration gefunden.")
                return result
        
        return None # Nichts gefunden

def run_diagnostics():
    """
    Führt die erweiterte Diagnose für alle Ticker durch.
    """
    print("=====================================================")
    print("=== Starte ERWEITERTE Ticker-Diagnose...          ===")
    print("=====================================================")

    app = DiagnosticClient()
    app.connect("127.0.0.1", 7497, clientId=1000)
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    time.sleep(3)

    all_tickers = sorted(list(settings.ASSET_CONTRACTS.keys()))
    working_configs = {}
    failed_tickers = []

    for ticker in all_tickers:
        print(f"\n--- Prüfe Ticker: {ticker} ---")
        found_contract = app.find_working_contract(ticker)
        
        if found_contract:
            working_configs[ticker] = {
                "symbol": found_contract.symbol,
                "exchange": found_contract.exchange,
                "primaryExchange": found_contract.primaryExchange,
                "currency": found_contract.currency,
                "secType": found_contract.secType
            }
        else:
            failed_tickers.append(ticker)
    
    app.disconnect()

    # --- Zusammenfassung ---
    print("\n\n=====================================================")
    print("=== FINALES DIAGNOSE-ERGEBNIS                  ===")
    print("=====================================================")
    
    print("### Funktionierende Konfigurationen ###")
    for ticker, config in working_configs.items():
        print(f'"{ticker}": {config},')
        
    if failed_tickers:
        print("\n### FEHLGESCHLAGENE Ticker ###")
        print("Für die folgenden Ticker konnte keine gültige Konfiguration gefunden werden:")
        for ticker in failed_tickers:
            print(f"  - {ticker}")
    
    print("=====================================================")

if __name__ == "__main__":
    run_diagnostics()
