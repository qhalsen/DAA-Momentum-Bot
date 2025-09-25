import sqlite3
import pandas as pd
from config import settings
import os
import json
from datetime import datetime, timezone

# Der Name unserer lokalen Datenbankdatei
DB_FILE = "etf_data.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_FILE)

def get_db_connection():
    """Stellt eine Verbindung zur SQLite-Datenbank her."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Erstellt die notwendigen Tabellen, falls sie noch nicht existieren."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Eine Tabelle für jeden ETF, um die Kurse zu speichern
    all_tickers = list(set(
        settings.RISKY_UNIVERSE + 
        settings.CANARY_UNIVERSE + 
        settings.CASH_UNIVERSE
    ))
    
    for ticker in all_tickers:
    # Bereinigt den Ticker-Namen für den Tabellennamen
        table_name = f"price_{ticker.replace('.', '_')}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date TEXT PRIMARY KEY,
                close REAL NOT NULL
            )
        """)
    
    conn.commit()
    conn.close()
    print("Datenbank initialisiert und Tabellen erstellt.")

def save_prices_for_ticker(ticker: str, prices_df: pd.DataFrame):
    """
    Speichert einen DataFrame mit Preisen für einen bestimmten Ticker in der Datenbank.
    
    Args:
        ticker (str): Der Ticker des ETFs.
        prices_df (pd.DataFrame): Ein DataFrame mit den Spalten 'date' und 'close'.
    """
    table_name = f"price_{ticker.replace('.', '_')}"
    conn = get_db_connection()
    
    # 'to_sql' ist eine mächtige Pandas-Funktion, um Daten in eine DB zu schreiben
    prices_df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"{len(prices_df)} Kurse für {ticker} gespeichert.")

def get_prices_for_ticker(ticker: str, limit: int = 13) -> list:
    """
    Holt die letzten 'limit' Schlusskurse für einen Ticker aus der Datenbank.

    Args:
        ticker (str): Der Ticker des ETFs.
        limit (int): Die Anzahl der zu holenden Kurse. Standard ist 13.

    Returns:
        Eine Liste von Schlusskursen.
    """
    table_name = f"price_{ticker.replace('.', '_')}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT close FROM {table_name} ORDER BY date DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        # Die Kurse sind absteigend nach Datum, wir kehren sie für die Berechnung um
        prices = [row['close'] for row in reversed(rows)]
        return prices
    except sqlite3.OperationalError:
        # Falls die Tabelle nicht existiert oder leer ist
        return []
    finally:
        conn.close()

def initialize_reporting_tables():
    """Erstellt die Tabellen, die für das erweiterte Reporting benötigt werden."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Eine Tabelle, um den Portfoliowert über die Zeit zu verfolgen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            timestamp TEXT PRIMARY KEY,
            total_value REAL NOT NULL,
            cash REAL NOT NULL,
            positions_json TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("Reporting-Tabellen initialisiert.")

def save_portfolio_snapshot(total_value: float, cash: float, positions: dict):
    """Speichert eine Momentaufnahme des Portfoliowertes in der Datenbank."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now(timezone.utc).isoformat()
    positions_json = json.dumps(positions)
    
    cursor.execute("""
        INSERT INTO portfolio_history (timestamp, total_value, cash, positions_json)
        VALUES (?, ?, ?, ?)
    """, (timestamp, total_value, cash, positions_json))
    
    conn.commit()
    conn.close()
    print(f"Portfolio-Snapshot ({total_value:.2f} EUR) in der Datenbank gespeichert.")


# --- Testbereich ---
if __name__ == "__main__":
    print("Initialisiere die Datenbank...")
    initialize_database()
    initialize_reporting_tables() # Hinzugefügt
    
    # Erstelle fiktive Testdaten mit Pandas
    test_dates = pd.to_datetime(pd.date_range(end='2025-07-31', periods=20, freq='M')).strftime('%Y-%m-%d')
    test_prices = [100 + i for i in range(20)]
    test_df = pd.DataFrame({'date': test_dates, 'close': test_prices})
    
    print("\nSpeichere Testdaten für SXR8...")
    save_prices_for_ticker("SXR8", test_df)
    
    print("\nHole die letzten 13 Kurse für SXR8...")
    sxr8_prices = get_prices_for_ticker("SXR8")
    print(f"Gelesene Kurse: {sxr8_prices}")
    print(f"Anzahl der Kurse: {len(sxr8_prices)}")