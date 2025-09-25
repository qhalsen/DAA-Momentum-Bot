import pandas as pd
import numpy as np
from config import settings
import numbers # Import the 'numbers' module for type checking


def safe_float(value) -> float:
    """Safely convert any value to native Python float."""
    return float(np.asarray(value).item())


def calculate_returns(history_df: pd.DataFrame, value_column: str) -> pd.Series:
    """
    Berechnet die periodischen (monatlichen) Renditen aus einer Historien-DataFrame.
    """
    if value_column not in history_df.columns:
        raise ValueError(f"DataFrame muss eine '{value_column}' Spalte enthalten.")
    if len(history_df) < 2:
        return pd.Series(dtype=np.float64)


    df = history_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()


    monthly_values = df[value_column].resample('M').last()


    return monthly_values.pct_change().dropna()


def calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Berechnet das Beta des Portfolios im Vergleich zur Benchmark."""
    combined = pd.DataFrame({'portfolio': portfolio_returns, 'benchmark': benchmark_returns}).dropna()


    if len(combined) < 2:
        return 0.0


    # Use safe_float to convert pandas scalars to native Python floats
    covariance = safe_float(combined['portfolio'].cov(combined['benchmark']))
    variance = safe_float(combined['benchmark'].var())


    if variance > 0:
        return covariance / variance


    return 0.0


def calculate_max_drawdown(portfolio_history_df: pd.DataFrame) -> float:
    """Berechnet den maximalen Drawdown aus der Portfolio-Historie."""
    if 'total_value' not in portfolio_history_df.columns or portfolio_history_df.empty:
        return 0.0


    df = portfolio_history_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()


    rolling_max = df['total_value'].cummax()
    drawdown = (df['total_value'] / rolling_max) - 1
    
    # Use safe_float to convert pandas scalar to native Python float
    min_drawdown = safe_float(drawdown.min())
    return abs(min_drawdown)


def calculate_all_metrics(portfolio_returns: pd.Series, portfolio_history_df: pd.DataFrame, benchmark_returns: pd.Series) -> dict:
    """
    Berechnet alle gewünschten Risiko- und Performance-Kennzahlen.
    """
    if len(portfolio_returns) < 2:
        return {"error": "Nicht genügend Daten für die Berechnung der Metriken."}


    annualization_factor = 12


    # Use safe_float to convert pandas Series values to native Python floats
    mean_return_annual = safe_float(portfolio_returns.mean()) * annualization_factor
    volatility_annual = safe_float(portfolio_returns.std()) * np.sqrt(annualization_factor)
    max_drawdown = calculate_max_drawdown(portfolio_history_df)


    beta = calculate_beta(portfolio_returns, benchmark_returns)
    sharpe_ratio = (mean_return_annual - settings.RISK_FREE_RATE) / volatility_annual if volatility_annual > 0 else 0


    negative_returns = portfolio_returns[portfolio_returns < 0]
    
    # Use safe_float for conversion, with fallback for empty series
    downside_deviation_annual = safe_float(negative_returns.std()) * np.sqrt(annualization_factor) if not negative_returns.empty else 0.0
    sortino_ratio = (mean_return_annual - settings.RISK_FREE_RATE) / downside_deviation_annual if downside_deviation_annual > 0 else 0


    calmar_ratio = mean_return_annual / max_drawdown if max_drawdown > 0 else 0


    treynor_ratio = (mean_return_annual - settings.RISK_FREE_RATE) / beta if beta > 0 else 0


    return {
        "annualized_return_percent": mean_return_annual * 100,
        "annualized_volatility_percent": volatility_annual * 100,
        "max_drawdown_percent": max_drawdown * 100,
        "portfolio_beta": beta,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "calmar_ratio": calmar_ratio,
        "treynor_ratio": treynor_ratio,
    }
