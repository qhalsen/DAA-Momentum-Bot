import pandas as pd
import threading
import time
import sys
import os

# --- KORREKTUR: Python den Weg zu den Modulen zeigen ---
# Dieser Block fügt das Hauptverzeichnis des Projekts zum Python-Pfad hinzu.
# Das ist notwendig, damit die Imports wie `from data import database` funktionieren,
# wenn man dieses Skript direkt aus dem Hauptordner ausführt.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
# ----------------------------------------------------

from data import database
from config import settings
from execution import broker

def update_all_data():
    """
    Holt die echten historischen Daten für alle benötigten Ticker von Interactive Brokers
    und speichert sie in der lokalen Datenbank. Dieses Skript sollte täglich laufen.
    """
    print("======================================================")
    print("=== Starte Daten-Ingestion von Interactive Brokers ===")
    print("======================================================")

    # --- Verbindung zu IBKR herstellen ---
    app = broker.IBKRClient()
    # Port 7497 ist der Standard für Paper-Trading
    app.connect("127.0.0.1", 7497, clientId=456) # Eigene ClientId für diesen Prozess
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    time.sleep(3) # Gib der Verbindung Zeit

    # Erstelle eine einzigartige Liste aller Ticker
    all_tickers = list(set(
        settings.RISKY_UNIVERSE + 
        settings.CANARY_UNIVERSE + 
        settings.CASH_UNIVERSE
    ))
    
    for ticker in all_tickers:
        print(f"\n--- Lade Daten für Ticker: {ticker} ---")
        
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
            
    # --- Verbindung trennen ---
    app.disconnect()
    print("\n======================================================")
    print("=== Daten-Ingestion-Prozess abgeschlossen          ===")
    print("======================================================")


if __name__ == "__main__":
    # Dieser Block wird ausgeführt, wenn wir das Skript direkt starten.
    
    # 1. Initialisiert die Datenbankstruktur, falls noch nicht geschehen
    database.initialize_database()
    
    # 2. Führt das Update für alle Ticker mit echten Daten durch
    update_all_data()
