# Dieses Skript wird dafür verantwortlich sein, die Daten von einer externen
# Quelle (z.B. Broker-API) zu holen und in unserer lokalen Datenbank zu speichern.

# HINWEIS: Dies ist im Moment nur eine Platzhalterstruktur. Die eigentliche
# Implementierung hängt stark von der gewählten Datenquelle ab (z.B. Interactive Brokers).

import pandas as pd
from data import database
from config import settings

def fetch_data_from_source(ticker: str) -> pd.DataFrame:
    """
    Platzhalter-Funktion zum Abrufen von Daten.
    In der realen Implementierung würde hier der API-Aufruf zum Broker stattfinden.
    """
    print(f"Platzhalter: Rufe Daten für {ticker} von externer Quelle ab...")
    # Erstellen wir fiktive Daten für Demonstrationszwecke
    # KORREKTUR: 'M' wurde durch 'ME' (Month-End) ersetzt, um die Warnung zu beheben.
    dates = pd.to_datetime(pd.date_range(end='2025-07-31', periods=24, freq='ME')).strftime('%Y-%m-%d')
    prices = [100 + i*0.5 for i in range(24)]
    
    # Die API würde typischerweise ein Datenformat wie dieses zurückgeben
    df = pd.DataFrame({'date': dates, 'close': prices})
    return df

def update_all_data():
    """
    Holt die Daten für alle benötigten Ticker und speichert sie in der Datenbank.
    Dieses Skript würde einmal täglich laufen.
    """
    print("Starte den täglichen Daten-Ingestion-Prozess...")
    
    # Erstelle eine einzigartige Liste aller Ticker, die wir benötigen
    all_tickers = list(set(
        settings.RISKY_UNIVERSE + 
        settings.CANARY_UNIVERSE + 
        settings.CASH_UNIVERSE
    ))
    
    for ticker in all_tickers:
        # 1. Daten von der Quelle holen
        price_df = fetch_data_from_source(ticker)
        
        # 2. Daten in unserer lokalen Datenbank speichern
        if not price_df.empty:
            database.save_prices_for_ticker(ticker, price_df)
        else:
            print(f"Keine Daten für {ticker} erhalten.")
            
    print("\nDaten-Ingestion-Prozess abgeschlossen.")

if __name__ == "__main__":
    # Initialisiert die Datenbank, falls noch nicht geschehen
    database.initialize_database()
    
    # Führt das Update für alle Ticker durch
    update_all_data()
