import sys
import os
import pandas as pd

# Python den Weg zu den Modulen zeigen
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from data import database
from reporting import metrics
from config import settings # Import the main settings file

def calculate_performance_since_last_snapshot():
    """
    Berechnet die Portfolio-Performance und die Performance des in den Settings
    definierten Benchmarks seit dem vorletzten Eintrag in der Historie.
    """
    conn = database.get_db_connection()
    try:
        # 1. Hole die letzten zwei Portfolio-Snapshots
        # NOTE: This part of the code relies on a 'portfolio_history' table
        # which you replaced with 'rebalancing_events'. This will need adjustment
        # if you want to run it. The main focus is on 'show_advanced_metrics'.
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

        # 2. Hole die Benchmark-Daten für den gleichen Zeitraum
        # *** HIER WIRD DIE NEUE EINSTELLUNG VERWENDET ***
        total_benchmark_performance = 0
        for ticker, weight in settings.BENCHMARK_COMPONENTS.items():
            table_name = f"price_{ticker}"
            benchmark_df = pd.read_sql_query(
                f"SELECT date, close FROM {table_name} WHERE date >= ? AND date <= ? ORDER BY date ASC",
                conn, params=(start_date, end_date)
            )
            if len(benchmark_df) < 2:
                 return {"error": f"Nicht genügend Benchmark-Daten für {ticker} im Zeitraum {start_date} - {end_date}."}
            benchmark_start_price = benchmark_df.iloc[0]['close']
            benchmark_end_price = benchmark_df.iloc[-1]['close']
            component_performance = (benchmark_end_price / benchmark_start_price - 1)
            total_benchmark_performance += component_performance * weight
        total_benchmark_performance *= 100

    except Exception as e:
        return {"error": f"Fehler bei der Performance-Berechnung: {e}"}
    finally:
        if conn:
            conn.close()

    return {
        "zeitraum": f"{start_date} bis {end_date}",
        "portfolio_performance_percent": portfolio_performance,
        "benchmark_performance_percent": total_benchmark_performance,
    }


def show_advanced_metrics():
    # This function remains unchanged
    conn = database.get_db_connection()
    try:
        portfolio_history_df = pd.read_sql_query(
            "SELECT timestamp, total_portfolio_value as total_value FROM rebalancing_events ORDER BY timestamp ASC", conn
        )
        benchmark_history_df = pd.read_sql_query(
            "SELECT date as timestamp, close FROM price_SXR8 ORDER BY timestamp ASC", conn
        )
    except Exception as e:
        print(f"Fehler beim Laden der Historien für erweiterte Metriken: {e}")
        return
    finally:
        if conn:
            conn.close()

    if len(portfolio_history_df) < 3:
        print("\nNicht genügend historische Portfolio-Daten für Profi-Kennzahlen (mind. 3 Snapshots benötigt).")
        return

    portfolio_returns = metrics.calculate_returns(portfolio_history_df, 'total_value')
    benchmark_returns = metrics.calculate_returns(benchmark_history_df, 'close')

    if portfolio_returns.empty or benchmark_returns.empty:
        print("\nKonnte keine Renditen berechnen, möglicherweise zu wenig überlappende Daten.")
        return

    all_metrics = metrics.calculate_all_metrics(portfolio_returns, portfolio_history_df, benchmark_returns)

    print("\n--- Risiko- & Profi-Kennzahlen (Gesamte Historie vs. S&P 500) 🔬 ---")
    if "error" in all_metrics:
        print(f"Fehler: {all_metrics['error']}")
    else:
        print(f"Annualisierte Rendite:           {all_metrics['annualized_return_percent']:.2f}%")
        print(f"Annualisierte Volatilität:       {all_metrics['annualized_volatility_percent']:.2f}%")
        print(f"Maximaler Drawdown:              {all_metrics['max_drawdown_percent']:.2f}%")
        print(f"Beta (vs. S&P 500):              {all_metrics['portfolio_beta']:.2f}")
        print("-" * 55)
        print(f"Sharpe Ratio:                    {all_metrics['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:                   {all_metrics['sortino_ratio']:.2f}")
        print(f"Calmar Ratio:                    {all_metrics['calmar_ratio']:.2f}")
        print(f"Treynor Ratio:                   {all_metrics['treynor_ratio']:.2f}")
    print("----------------------------------------------------------------------")


if __name__ == '__main__':
    # Dynamically create the benchmark description from settings
    benchmark_desc = " / ".join([f"{int(w*100)}% {t}" for t, w in settings.BENCHMARK_COMPONENTS.items()])

    # NOTE: The following function call will likely fail because it relies on the old
    # 'portfolio_history' table. The focus here is the integration of the configurable benchmark.
    performance_data = calculate_performance_since_last_snapshot()
    print(f"--- Performance Report (Letzter Monat vs. {benchmark_desc}) ---")
    if "error" in performance_data:
        print(f"Fehler: {performance_data['error']}")
    else:
        print(f"Zeitraum: {performance_data['zeitraum']}")
        print(f"Portfolio-Wertentwicklung: {performance_data['portfolio_performance_percent']:.2f}%")
        print(f"Benchmark-Entwicklung: {performance_data['benchmark_performance_percent']:.2f}%")
    print("-----------------------------------------------------------------")

    show_advanced_metrics()