# DAA Momentum Bot/data/database.py

import sqlite3
import pandas as pd
from config import settings
import os
import json

DB_FILE = "etf_data.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_FILE)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Erstellt/verifiziert das gesamte Datenbankschema, inkl. der neuen Kontext-Tabellen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Preistabellen (unverändert) ---
    all_tickers = list(set(
        settings.RISKY_UNIVERSE + settings.CANARY_UNIVERSE + settings.CASH_UNIVERSE
    ))
    for ticker in all_tickers:
        table_name = f"price_{ticker.replace('.', '_')}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date TEXT PRIMARY KEY, close REAL NOT NULL
            )
        """)

    # --- Event-Tabellen ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rebalancing_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL UNIQUE,
            final_signal TEXT NOT NULL,
            total_portfolio_value REAL NOT NULL,
            signal_duration INTEGER,
            market_breadth_percent REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_canary_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            ticker TEXT NOT NULL, status TEXT NOT NULL, momentum_score REAL NOT NULL,
            FOREIGN KEY (event_id) REFERENCES rebalancing_events (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_momentum_ranking (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            ticker TEXT NOT NULL, momentum_score REAL NOT NULL, rank INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES rebalancing_events (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_target_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            ticker TEXT NOT NULL, weight REAL NOT NULL,
            FOREIGN KEY (event_id) REFERENCES rebalancing_events (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_calculated_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            symbol TEXT NOT NULL, quantity INTEGER NOT NULL, action TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES rebalancing_events (id)
        )
    """)
    # NEUE Tabelle für die Korrelationsmatrix
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_correlation_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL,
            matrix_json TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES rebalancing_events (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Datenbank initialisiert und alle Tabellen (inkl. Kontext) erstellt/verifiziert.")

def save_rebalancing_event(strategie_ergebnis: dict):
    """Speichert ein komplettes Rebalancing-Event inkl. der neuen Kontext-Daten."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        context = strategie_ergebnis.get('entscheidungskontext', {})
        cursor.execute("""
            INSERT INTO rebalancing_events (timestamp, final_signal, total_portfolio_value, signal_duration, market_breadth_percent)
            VALUES (?, ?, ?, ?, ?)
        """, (
            strategie_ergebnis['timestamp_utc'],
            strategie_ergebnis['canary_report']['final_signal'],
            strategie_ergebnis['total_portfolio_value'],
            context.get('signal_duration'),
            context.get('marktbreite_prozent')
        ))
        event_id = cursor.lastrowid

        # Speichern von Canary, Ranking, Portfolio, Trades (unverändert)
        for ticker, details in strategie_ergebnis['canary_report']['canary_details'].items():
            cursor.execute("INSERT INTO event_canary_details (event_id, ticker, status, momentum_score) VALUES (?, ?, ?, ?)", (event_id, ticker, details['status'], details['berechnung']['momentum_score']))
        for i, (ticker, score) in enumerate(strategie_ergebnis['momentum_ranking']):
            cursor.execute("INSERT INTO event_momentum_ranking (event_id, ticker, momentum_score, rank) VALUES (?, ?, ?, ?)", (event_id, ticker, score, i + 1))
        for ticker, weight in strategie_ergebnis['portfolio'].items():
            cursor.execute("INSERT INTO event_target_portfolio (event_id, ticker, weight) VALUES (?, ?, ?)", (event_id, ticker, weight))
        for trade in strategie_ergebnis['calculated_trades']:
            cursor.execute("INSERT INTO event_calculated_trades (event_id, symbol, quantity, action) VALUES (?, ?, ?, ?)", (event_id, trade['symbol'], trade['quantity'], trade['action']))

        # Speichern der Korrelationsmatrix
        if 'korrelations_matrix' in context and context['korrelations_matrix'] is not None:
            matrix_json = context['korrelations_matrix'].to_json(orient='split')
            cursor.execute("INSERT INTO event_correlation_matrix (event_id, matrix_json) VALUES (?, ?)", (event_id, matrix_json))

        conn.commit()
        print(f"Rebalancing-Event (ID: {event_id}) vollständig in der Datenbank gespeichert.")
    except Exception as e:
        conn.rollback()
        print(f"FEHLER: Das Rebalancing-Event konnte nicht gespeichert werden. Rollback wird ausgeführt. Fehler: {e}")
    finally:
        conn.close()

def get_signal_history() -> list:
    """Holt die letzten 12 Signale aus der DB, um die Signaldauer zu berechnen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT final_signal FROM rebalancing_events ORDER BY timestamp DESC LIMIT 12")
        rows = cursor.fetchall()
        return [row['final_signal'] for row in reversed(rows)] # Ältestes zuerst
    except:
        return [] # Bei Fehler oder leerer Tabelle
    finally:
        conn.close()

# --- Bestehende Preis-Funktionen (unverändert) ---
def save_prices_for_ticker(ticker: str, prices_df: pd.DataFrame):
    table_name = f"price_{ticker.replace('.', '_')}"
    conn = get_db_connection()
    prices_df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print(f"{len(prices_df)} Kurse für {ticker} gespeichert.")

def get_prices_for_ticker(ticker: str, limit: int = 13) -> list:
    table_name = f"price_{ticker.replace('.', '_')}"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT close FROM {table_name} ORDER BY date DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [row['close'] for row in reversed(rows)]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()