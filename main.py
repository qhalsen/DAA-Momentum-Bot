from config import settings
from data import database
from strategy import logic
import os

def run_monthly_rebalancing():
    """
    Dies ist die Hauptfunktion, die den gesamten monatlichen Prozess steuert.
    Sie wird einmal am letzten Handelstag des Monats ausgeführt.
    """
    print("==============================================")
    print("=== Starte monatliches DAA-Rebalancing...  ===")
    print("==============================================")

    # --- Schritt 1: Daten sammeln ---
    # Unser "Gehirn" (logic.py) benötigt die Kursdaten für ALLE Assets,
    # um seine Entscheidung treffen zu können.
    
    print("\nSchritt 1: Lade Preisdaten aus der lokalen Datenbank...")
    
    # Sammle alle Ticker aus unseren Einstellungsdateien
    all_tickers = list(set(
        settings.RISKY_UNIVERSE + 
        settings.CANARY_UNIVERSE + 
        settings.CASH_UNIVERSE
    ))
    
    # Erstelle ein Dictionary, um die Kursdaten für jeden Ticker zu speichern
    daten_aller_assets = {}
    for ticker in all_tickers:
        # Rufe die Funktion aus database.py auf, um die letzten 13 Kurse zu holen
        kurse = database.get_prices_for_ticker(ticker, limit=13)
        
        # Überprüfe, ob wir genügend Daten erhalten haben
        if len(kurse) < 13:
            print(f"FEHLER: Nicht genügend Daten für {ticker} in der Datenbank gefunden. Breche ab.")
            # In einem echten Bot würden wir hier eine Benachrichtigung senden.
            return 
            
        daten_aller_assets[ticker] = kurse
        
    print("Daten für alle Assets erfolgreich geladen.")

    # --- Schritt 2: Entscheidung treffen ---
    # Jetzt, wo wir alle Daten haben, übergeben wir sie an unser "Gehirn".
    
    print("\nSchritt 2: Übergebe Daten an die Strategie-Engine zur Entscheidung...")
    
    try:
        # Rufe die Hauptfunktion aus logic.py auf
        ziel_portfolio = logic.bestimme_ziel_portfolio(daten_aller_assets)
        
        print("Entscheidung der Strategie-Engine erhalten.")
        
    except ValueError as e:
        # Fängt den Fehler ab, den wir in berechne_momentum definiert haben
        print(f"FEHLER bei der Strategie-Berechnung: {e}")
        return

    # --- Schritt 3: Ergebnis anzeigen ---
    # In einem echten Bot würden wir dieses `ziel_portfolio` an den
    # "Roboterarm" (execution/broker.py) übergeben, um die Trades auszuführen.
    # Fürs Erste geben wir das Ergebnis einfach auf dem Bildschirm aus.
    
    print("\n==============================================")
    print("=== FINALES ZIELPORTFOLIO                  ===")
    print("==============================================")
    print(f"Das zu haltende Portfolio für den nächsten Monat ist:")
    
    if not ziel_portfolio:
        print("Keine Assets zum Halten.")
    else:
        for ticker, gewichtung in ziel_portfolio.items():
            print(f"  - {ticker}: {gewichtung:.2%}")
    print("==============================================")


if __name__ == "__main__":
    # Dieser Block wird ausgeführt, wenn wir das Skript direkt starten.
    
    # Bevor wir den Prozess starten, stellen wir sicher, dass unsere Datenbank
    # und die (simulierten) Daten existieren.
    # In einem echten Szenario würde `ingest.py` täglich laufen.
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'etf_data.db')
    if not os.path.exists(db_path):
        print("Datenbank nicht gefunden. Führe den initialen Daten-Ingestion-Prozess aus...")
        from data import ingest
        ingest.update_all_data()
        print("-" * 20)

    # Starte den eigentlichen Rebalancing-Prozess
    run_monthly_rebalancing()
