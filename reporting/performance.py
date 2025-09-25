import sys
import os
import pandas as pd

# Python den Weg zu den Modulen zeigen
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from data import database

def calculate_performance_since_last_snapshot():
    """
    Berechnet die Portfolio-Performance und die Performance einer 70/30
    World/EM-Benchmark seit dem vorletzten Eintrag in der Historie.
    """
    conn = database.get_db_connection()
    
    # 1. Hole die letzten zwei Portfolio-Snapshots
    try:
        history_df = pd.read_sql_query(
            "SELECT timestamp, total_value FROM portfolio_history ORDER BY timestamp DESC LIMIT 2", conn
        )
        if len(history_df) < 2:
            return {"error": "Nicht genügend Daten für Performance-Vergleich (mind. 2 Snapshots benötigt)."}
            
        end_value = history_df.iloc[0]['total_value']
        start_value = history_df.iloc[1]['total_value']
        start_date = pd.to_datetime(history_df.iloc[1]['timestamp']).strftime('%Y-%m-%d')
        end_date = pd.to_datetime(history_df.iloc[0]['timestamp']).strftime('%Y-%m-%d')

        portfolio_performance = (end_value / start_value - 1) * 100
    except Exception as e:
        # Verbindung hier im Fehlerfall schließen
        conn.close()
        return {"error": f"Fehler beim Lesen der Portfolio-Historie: {e}"}

    # 2. Hole die Benchmark-Daten für den gleichen Zeitraum
    try:
        # Definiere die Benchmark-Komponenten und ihre Gewichtung
        benchmark_components = {
            "SXR8": 0.70,  # 70% S&P 500 als Proxy für MSCI World
            "EMIM": 0.30   # 30% Emerging Markets
        }
        
        total_benchmark_performance = 0

        for ticker, weight in benchmark_components.items():
            table_name = f"price_{ticker}"  # Dynamischer Tabellenname
            
            benchmark_df = pd.read_sql_query(
                f"SELECT date, close FROM {table_name} WHERE date >= ? AND date <= ? ORDER BY date ASC",
                conn, params=(start_date, end_date)
            )
            
            if len(benchmark_df) < 2:
                 return {"error": f"Nicht genügend Benchmark-Daten für {ticker} im Zeitraum {start_date} - {end_date}."}

            benchmark_start_price = benchmark_df.iloc[0]['close']
            benchmark_end_price = benchmark_df.iloc[-1]['close']
            
            # Performance für diese Komponente berechnen
            component_performance = (benchmark_end_price / benchmark_start_price - 1)
            
            # Gewichtete Performance zum Total addieren
            total_benchmark_performance += component_performance * weight

        # Umrechnung in Prozent
        total_benchmark_performance *= 100

    except Exception as e:
        return {"error": f"Fehler beim Lesen der Benchmark-Daten: {e}"}
    finally:
        conn.close()

    return {
        "zeitraum": f"{start_date} bis {end_date}",
        "portfolio_performance_percent": portfolio_performance,
        "benchmark_performance_percent": total_benchmark_performance,
        "start_wert_portfolio": start_value,
        "end_wert_portfolio": end_value,
    }

if __name__ == '__main__':
    # Diesen Block ausführen, um das Modul direkt zu testen
    # WICHTIG: Sie müssen zuerst `main.py` mindestens zweimal laufen lassen,
    # damit zwei Einträge in der `portfolio_history` existieren.
    
    # Führen Sie zuerst `python data/database.py` aus, um die Tabellen zu erstellen.
    # Führen Sie dann `python main.py` zweimal aus.
    # Führen Sie dann `python reporting/performance.py` aus.
    
    performance_data = calculate_performance_since_last_snapshot()
    print("--- Performance Report ---")
    if "error" in performance_data:
        print(f"Fehler: {performance_data['error']}")
    else:
        print(f"Zeitraum: {performance_data['zeitraum']}")
        print(f"Portfolio-Wertentwicklung: {performance_data['portfolio_performance_percent']:.2f}%")
        print(f"Benchmark-Entwicklung (70/30 World/EM): {performance_data['benchmark_performance_percent']:.2f}%")
    print("--------------------------")

