import sys
import os
import time
import threading
import json
from datetime import datetime

# --- Python den Weg zu den Modulen zeigen ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from config import settings
from strategy import logic
from execution import broker
from execution import portfolio

def run_monthly_rebalancing():
    """
    Dies ist die Hauptfunktion, die den gesamten monatlichen Prozess steuert.
    """
    print("==============================================")
    print("=== Starte monatliches DAA-Rebalancing...  ===")
    print("==============================================")

    # --- Verbindung zu IBKR herstellen ---
    app = broker.IBKRClient()
    app.connect("127.0.0.1", 7497, clientId=123)
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    time.sleep(3)

    # --- Schritt 1: Historische Daten sammeln ---
    print("\nSchritt 1: Lade historische Preisdaten...")
    daten_aller_assets = {}
    all_tickers = list(set(settings.RISKY_UNIVERSE + settings.CASH_UNIVERSE + settings.CANARY_UNIVERSE))
    
    for ticker in all_tickers:
        print(f"Lade Daten für {ticker}...")
        kurse_roh = broker.get_data_for_ticker_ibkr(app, ticker)
        if len(kurse_roh) < 13:
            print(f"--> FEHLER: Nicht genügend historische Daten für {ticker}. Breche ab.")
            app.disconnect()
            return
        daten_aller_assets[ticker] = [item[1] for item in kurse_roh]
    print("Historische Daten erfolgreich geladen.")

    # --- Schritt 2: Entscheidung treffen & Reporting ---
    print("\nSchritt 2: Führe Strategie-Analyse durch...")
    strategie_ergebnis = logic.bestimme_ziel_portfolio(daten_aller_assets)
    ziel_portfolio = strategie_ergebnis['portfolio']
    canary_report = strategie_ergebnis['canary_report']
    momentum_ranking = strategie_ergebnis['momentum_ranking']

    # --- Canary-Analyse Reporting ---
    print("\n--- Canary-Analyse Ergebnis ---")
    print(f"Finales Signal: {canary_report['final_signal']}")
    for ticker, details in canary_report['canary_details'].items():
        score = details['berechnung']['momentum_score']
        print(f"  - {ticker}: Status={details['status']}, Momentum-Score={score:.4f}")
    print("-----------------------------")

    # --- Momentum-Rangliste Reporting ---
    print("\n--- Momentum-Rangliste ---")
    aktives_universum = "RISKY UNIVERSE" if canary_report['final_signal'] == "RISK_ON" else "CASH UNIVERSE"
    print(f"Aktives Universum: {aktives_universum}")
    print(f"{'Ticker':<10} | {'Momentum Score'}")
    print("-" * 30)
    for ticker, score in momentum_ranking:
        print(f"{ticker:<10} | {score:.4f}")
    print("--------------------------")

    print(f"\nStrategie-Entscheidung (Zielportfolio): {ziel_portfolio}")

    # --- Schritt 3: Aktuelles Depot berechnen ---
    print("\nSchritt 3: Frage aktuelles Depot und Gesamtwert ab...")
    cash, aktuelle_positionen = broker.get_account_details(app)
    
    market_value = 0
    for symbol, quantity in aktuelle_positionen.items():
        price = broker.get_current_price_ibkr(app, symbol)
        market_value += price * quantity
        
    total_portfolio_value = cash + market_value
    print(f"Aktueller Cash-Bestand: {cash:.2f} EUR")
    print(f"Aktuelle Positionen: {aktuelle_positionen}")
    print(f"GESAMTWERT DES PORTFOLIOS: {total_portfolio_value:.2f} EUR")

    # --- Schritt 4: Trades berechnen ---
    print("\nSchritt 4: Berechne notwendige Trades...")
    trades = portfolio.calculate_trades(app, aktuelle_positionen, ziel_portfolio, total_portfolio_value)
    print(f"Zu tätigende Trades: {trades}")

    # --- Schritt 5: Ergebnis für die Historie speichern ---
    print("\nSchritt 5: Speichere Ergebnis in der Historie...")
    
    # Füge finale Daten zum Ergebnis-Report hinzu
    strategie_ergebnis['timestamp_utc'] = datetime.utcnow().isoformat()
    strategie_ergebnis['total_portfolio_value'] = total_portfolio_value
    strategie_ergebnis['calculated_trades'] = trades

    # Erstelle Dateiname und Ordner
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_dir = os.path.join(SCRIPT_DIR, 'history')
    os.makedirs(history_dir, exist_ok=True)
    filename = os.path.join(history_dir, f"rebalancing_{date_str}.json")

    # Speichere die Datei
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(strategie_ergebnis, f, ensure_ascii=False, indent=4)
        print(f"Ergebnis erfolgreich in {filename} gespeichert.")
    except Exception as e:
        print(f"FEHLER beim Speichern der Historie: {e}")

    # --- Schritt 6: Trades ausführen ---
    if trades:
        print("\nSchritt 6: Führe Trades aus...")
        # broker.execute_trades(app, trades)
        print("Handelsausführung ist für diesen Test deaktiviert.")
    else:
        print("\nKeine Trades notwendig.")

    # --- Verbindung trennen ---
    app.disconnect()
    print("\n==============================================")
    print("=== Rebalancing-Prozess abgeschlossen.     ===")
    print("==============================================")

if __name__ == "__main__":
    run_monthly_rebalancing()