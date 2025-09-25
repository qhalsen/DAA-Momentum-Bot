# DAA Momentum Bot/main.py

import sys
import os
import time
import threading
import json
from datetime import datetime, timezone
import pandas as pd # Import für die Matrix-Anzeige

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from config import settings
from strategy import logic
from execution import broker, portfolio
from data import database, ingest

def run_monthly_rebalancing():
    # ... (Code von Anfang bis Ende Schritt 1 bleibt unverändert) ...
    print("==============================================")
    print("=== Starte monatliches DAA-Rebalancing...  ===")
    print("==============================================")
    app = broker.IBKRClient()
    app.connect("127.0.0.1", 7497, clientId=123)
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    time.sleep(3)
    print("\nSchritt 1: Lade historische Preisdaten...")
    daten_aller_assets = {}
    all_tickers = list(set(settings.RISKY_UNIVERSE + settings.CASH_UNIVERSE + settings.CANARY_UNIVERSE))
    for ticker in all_tickers:
        print(f"Prüfe Daten für {ticker}...")
        kurse = database.get_prices_for_ticker(ticker, limit=26)
        if len(kurse) < 13:
            print(f"--> Daten unvollständig. Starte API-Abruf...")
            ingest.update_data_for_ticker(app, ticker)
            kurse = database.get_prices_for_ticker(ticker, limit=26)
            if len(kurse) < 13:
                 print(f"--> FATALER FEHLER: Konnte auch nach API-Abruf nicht genügend Daten für {ticker} laden. Breche ab.")
                 app.disconnect()
                 return
        daten_aller_assets[ticker] = kurse[-13:]
    print("Historische Daten erfolgreich geladen.")

    # --- Schritt 2: Entscheidung & Reporting (inkl. Kontext) ---
    print("\nSchritt 2: Führe Strategie-Analyse durch...")
    strategie_ergebnis = logic.bestimme_ziel_portfolio(daten_aller_assets)
    ziel_portfolio = strategie_ergebnis['portfolio']
    canary_report = strategie_ergebnis['canary_report']
    momentum_ranking = strategie_ergebnis['momentum_ranking']
    kontext = strategie_ergebnis['entscheidungskontext']

    # --- Canary & Momentum Reporting (unverändert) ---
    print("\n--- Canary-Analyse Ergebnis ---")
    print(f"Finales Signal: {canary_report['final_signal']}")
    for ticker, details in canary_report['canary_details'].items():
        score = details['berechnung']['momentum_score']
        print(f"  - {ticker}: Status={details['status']}, Momentum-Score={score:.4f}")
    print("\n--- Momentum-Rangliste ---")
    aktives_universum = "RISKY UNIVERSE" if canary_report['final_signal'] == "RISK_ON" else "CASH UNIVERSE"
    print(f"Aktives Universum: {aktives_universum}")
    print(f"{'Ticker':<10} | {'Momentum Score'}")
    print("-" * 30)
    for ticker, score in momentum_ranking:
        print(f"{ticker:<10} | {score:.4f}")

    # +++ NEUES REPORTING-MODUL FÜR DAS "WARUM" +++
    print("\n--- Erweiterter Markt- & Entscheidungskontext (Das 'Warum') ---")
    print(f"Marktbreite (Risk-On Assets mit pos. Momentum): {kontext['marktbreite_prozent']:.1f}%")
    print(f"Dauer des aktuellen Signals: {kontext['signal_duration']} Monat(e)")
    if kontext['korrelations_matrix'] is not None:
        print("Korrelations-Matrix der Top-Assets:")
        # Pandas-Styling für bessere Lesbarkeit in der Konsole
        styled_matrix = kontext['korrelations_matrix'].style.format("{:.2f}").background_gradient(cmap='coolwarm', vmin=-1, vmax=1)
        print(styled_matrix)
    print("-------------------------------------------------------------")

    print(f"\nStrategie-Entscheidung (Zielportfolio): {ziel_portfolio}")

    # --- Schritte 3, 4, 5, 6 (bleiben unverändert) ---
    print("\nSchritt 3: Frage aktuelles Depot und Gesamtwert ab...")
    cash, aktuelle_positionen = broker.get_account_details(app)
    market_value = sum(broker.get_current_price_ibkr(app, s) * q for s, q in aktuelle_positionen.items())
    total_portfolio_value = cash + market_value
    print(f"GESAMTWERT DES PORTFOLIOS: {total_portfolio_value:.2f} EUR")
    print("\nSchritt 4: Berechne notwendige Trades...")
    trades = portfolio.calculate_trades(app, aktuelle_positionen, ziel_portfolio, total_portfolio_value)
    print(f"Zu tätigende Trades: {trades}")
    print("\nSchritt 5: Speichere vollumfängliches Ergebnis...")
    strategie_ergebnis['timestamp_utc'] = datetime.now(timezone.utc).isoformat()
    strategie_ergebnis['total_portfolio_value'] = total_portfolio_value
    strategie_ergebnis['calculated_trades'] = trades
    database.save_rebalancing_event(strategie_ergebnis)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_dir = os.path.join(SCRIPT_DIR, 'history')
    os.makedirs(history_dir, exist_ok=True)
    filename = os.path.join(history_dir, f"rebalancing_{date_str}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(strategie_ergebnis, f, default=str, ensure_ascii=False, indent=4) # default=str für Matrix
    print(f"Zusätzliches JSON-Log in {filename} gespeichert.")
    print("\nSchritt 6: Führe Trades aus...")
    if trades:
        print("Handelsausführung ist für diesen Test deaktiviert.")
    else:
        print("\nKeine Trades notwendig.")
    app.disconnect()
    print("\n==============================================")
    print("=== Rebalancing-Prozess abgeschlossen.     ===")
    print("==============================================")

if __name__ == "__main__":
    database.initialize_database()
    run_monthly_rebalancing()