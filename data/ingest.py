# DAA Momentum Bot/data/ingest.py

import pandas as pd
import threading
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from data import database
from config import settings
from execution import broker

def update_data_for_ticker(app, ticker: str):
    """
    Holt die historischen Daten für einen einzelnen Ticker von IBKR und speichert sie.
    Diese Funktion kann von anderen Modulen aufgerufen werden.
    """
    print(f"--- Starte Daten-Download für Ticker: {ticker} ---")
    
    # 1. Rufe die Funktion aus broker.py auf, um die echten Daten zu holen
    raw_data = broker.get_data_for_ticker_ibkr(app, ticker)
    
    # 2. Verarbeite und speichere die Daten
    if raw_data:
        # Wandle die Rohdaten in einen sauberen DataFrame um
        price_df = pd.DataFrame(raw_data, columns=['date', 'close'])
        price_df['date'] = pd.to_datetime(price_df['date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
        
        # Speichere den DataFrame in unserer lokalen Datenbank
        database.save_prices_for_ticker(ticker, price_df)
    else:
        print(f"WARNUNG: Keine historischen Daten für {ticker} von IBKR erhalten. Überspringe.")

def update_all_data():
    """
    Holt die historischen Daten für ALLE Ticker und speichert sie.
    Dieses Skript kann weiterhin manuell für ein komplettes Update ausgeführt werden.
    """
    print("======================================================")
    print("=== Starte manuelle Daten-Ingestion von IBKR         ===")
    print("======================================================")

    app = broker.IBKRClient()
    app.connect("127.0.0.1", 7497, clientId=456)
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    time.sleep(3)

    all_tickers = list(set(
        settings.RISKY_UNIVERSE + 
        settings.CANARY_UNIVERSE + 
        settings.CASH_UNIVERSE
    ))
    
    for ticker in all_tickers:
        update_data_for_ticker(app, ticker)
            
    app.disconnect()
    print("\n======================================================")
    print("=== Manuelle Daten-Ingestion abgeschlossen         ===")
    print("======================================================")

if __name__ == "__main__":
    database.initialize_database()
    update_all_data()