# strategy/logic.py

import pandas as pd
from config import settings
from data import database # Import für Signal-Historie

def berechne_momentum(monats_schlusskurse: list) -> dict:
    # ... (Diese Funktion bleibt unverändert)
    if len(monats_schlusskurse) < 13:
        raise ValueError(f"Nicht genügend Daten. Erhalten: {len(monats_schlusskurse)}, benötigt: 13.")
    
    aktueller_kurs = monats_schlusskurse[-1]
    ret1 = (aktueller_kurs / monats_schlusskurse[-2]) - 1
    ret3 = (aktueller_kurs / monats_schlusskurse[-4]) - 1
    ret6 = (aktueller_kurs / monats_schlusskurse[-7]) - 1
    ret12 = (aktueller_kurs / monats_schlusskurse[-13]) - 1

    score = ((ret1*12) + (ret3*4) + (ret6*2) + (ret12*1)) / 4
    
    return {'momentum_score': score, 'input_prices': monats_schlusskurse}

def canary_check(daten_aller_assets: dict) -> dict:
    # ... (Diese Funktion bleibt unverändert)
    canary_details = {}
    final_signal = "RISK_ON"
    for ticker in settings.CANARY_UNIVERSE:
        berechnungs_ergebnis = berechne_momentum(daten_aller_assets[ticker])
        status = "Gesund" if berechnungs_ergebnis['momentum_score'] > 0 else "Krank"
        if status == "Krank":
            final_signal = "RISK_OFF"
        canary_details[ticker] = {'status': status, 'berechnung': berechnungs_ergebnis}
    return {'final_signal': final_signal, 'canary_details': canary_details}

def bestimme_ziel_portfolio(daten_aller_assets: dict) -> dict:
    """Die Haupt-Entscheidungsfunktion, jetzt inkl. Berechnung des Kontexts."""
    markt_signal_details = canary_check(daten_aller_assets)
    markt_signal = markt_signal_details['final_signal']
    
    # --- Kontext-Berechnungen ---
    # 1. Marktbreite
    risky_momentum_scores = {
        ticker: berechne_momentum(daten_aller_assets[ticker])['momentum_score']
        for ticker in settings.RISKY_UNIVERSE
    }
    positive_momentum_count = sum(1 for score in risky_momentum_scores.values() if score > 0)
    marktbreite_prozent = (positive_momentum_count / len(settings.RISKY_UNIVERSE)) * 100

    # 2. Dauer des Signals
    signal_historie = database.get_signal_history()
    signal_dauer = 0
    for signal in reversed(signal_historie):
        if signal == markt_signal:
            signal_dauer += 1
        else:
            break
    signal_dauer += 1 # Das aktuelle Event mitzählen

    # --- Portfolio-Logik (RISK-ON) ---
    if markt_signal == "RISK_ON":
        sortierte_assets = sorted(risky_momentum_scores.items(), key=lambda item: item[1], reverse=True)
        top_assets = sortierte_assets[:settings.T]
        ziel_portfolio = {asset[0]: 1 / settings.T for asset in top_assets}

        # 3. Korrelations-Matrix für die Top-Assets
        top_asset_tickers = [asset[0] for asset in top_assets]
        prices_df = pd.DataFrame({
            ticker: daten_aller_assets[ticker] for ticker in top_asset_tickers
        })
        returns_df = prices_df.pct_change().dropna()
        korrelations_matrix = returns_df.corr()

        return {
            'canary_report': markt_signal_details,
            'momentum_ranking': sortierte_assets,
            'portfolio': ziel_portfolio,
            'entscheidungskontext': {
                'marktbreite_prozent': marktbreite_prozent,
                'signal_duration': signal_dauer,
                'korrelations_matrix': korrelations_matrix
            }
        }

    # --- Portfolio-Logik (RISK-OFF) ---
    else:
        cash_momentum_scores = {
            ticker: berechne_momentum(daten_aller_assets[ticker])['momentum_score']
            for ticker in settings.CASH_UNIVERSE
        }
        sortierte_assets = sorted(cash_momentum_scores.items(), key=lambda item: item[1], reverse=True)
        bestes_asset = sortierte_assets[0][0]
        ziel_portfolio = {bestes_asset: 1.0}

        return {
            'canary_report': markt_signal_details,
            'momentum_ranking': sortierte_assets,
            'portfolio': ziel_portfolio,
            'entscheidungskontext': {
                'marktbreite_prozent': marktbreite_prozent,
                'signal_duration': signal_dauer,
                'korrelations_matrix': None # Keine Korrelation bei nur einem Asset
            }
        }