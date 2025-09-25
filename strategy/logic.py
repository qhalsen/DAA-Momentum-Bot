# strategy/logic.py

from config import settings

def berechne_momentum(monats_schlusskurse: list) -> dict:
    """
    Berechnet den 13612W Momentum-Score und gibt alle Berechnungsdetails zurück.

    Args:
        monats_schlusskurse: Eine Liste von 13 Monats-Schlusskursen.

    Returns:
        Ein Dictionary mit dem Score und den zur Berechnung verwendeten Daten.
    """
    if len(monats_schlusskurse) < 13:
        raise ValueError(
            f"Nicht genügend Daten für Momentum-Berechnung. "
            f"Erhalten: {len(monats_schlusskurse)} Kurse, benötigt: 13."
        )

    # Preise zu den relevanten Zeitpunkten extrahieren.
    aktueller_kurs        = monats_schlusskurse[-1]
    kurs_vor_1_monat      = monats_schlusskurse[-2]
    kurs_vor_3_monaten    = monats_schlusskurse[-4]
    kurs_vor_6_monaten    = monats_schlusskurse[-7]
    kurs_vor_12_monaten   = monats_schlusskurse[-13]

    # Renditen berechnen
    ret1 = (aktueller_kurs / kurs_vor_1_monat) - 1
    ret3 = (aktueller_kurs / kurs_vor_3_monaten) - 1
    ret6 = (aktueller_kurs / kurs_vor_6_monaten) - 1
    ret12 = (aktueller_kurs / kurs_vor_12_monaten) - 1

    # Renditen annualisieren
    annual_ret1 = ret1 * 12
    annual_ret3 = ret3 * 4
    annual_ret6 = ret6 * 2
    annual_ret12 = ret12 * 1

    # Score berechnen
    score = (annual_ret1 + annual_ret3 + annual_ret6 + annual_ret12) / 4
    
    return {
        'momentum_score': score,
        'input_prices': monats_schlusskurse,
        'calculation_details': {
            'aktueller_kurs': aktueller_kurs,
            'kurs_vor_1m': kurs_vor_1_monat,
            'kurs_vor_3m': kurs_vor_3_monaten,
            'kurs_vor_6m': kurs_vor_6_monaten,
            'kurs_vor_12m': kurs_vor_12_monaten
        }
    }

def canary_check(daten_aller_assets: dict) -> dict:
    """
    Überprüft die Kanarienvogel-Assets und gibt ein detailliertes Ergebnis zurück.
    """
    canary_details = {}
    final_signal = "RISK_ON"

    for ticker in settings.CANARY_UNIVERSE:
        vogel_kurse = daten_aller_assets[ticker]
        
        berechnungs_ergebnis = berechne_momentum(vogel_kurse)
        momentum_score = berechnungs_ergebnis['momentum_score']
        
        status = "Gesund"
        if momentum_score <= 0:
            status = "Krank"
            final_signal = "RISK_OFF"

        canary_details[ticker] = {
            'status': status,
            'berechnung': berechnungs_ergebnis
        }
            
    return {
        'final_signal': final_signal,
        'canary_details': canary_details
    }

def bestimme_ziel_portfolio(daten_aller_assets: dict) -> dict:
    """
    Die Haupt-Entscheidungsfunktion. Sie gibt ein umfassendes Ergebnis-Dictionary
    inklusive einer kompletten Momentum-Rangliste zurück.
    """
    markt_signal_details = canary_check(daten_aller_assets)
    markt_signal = markt_signal_details['final_signal']

    # Logik für RISK-ON
    if markt_signal == "RISK_ON":
        risky_momentum_scores = {
            ticker: berechne_momentum(daten_aller_assets[ticker])['momentum_score']
            for ticker in settings.RISKY_UNIVERSE
        }
        sortierte_assets = sorted(risky_momentum_scores.items(), key=lambda item: item[1], reverse=True)
        top_assets = sortierte_assets[:settings.T]
        ziel_portfolio = {asset[0]: 1 / settings.T for asset in top_assets}

        # Baue das finale Ergebnis sauber zusammen
        return {
            'canary_report': markt_signal_details,
            'momentum_ranking': sortierte_assets,
            'portfolio': ziel_portfolio
        }

    # Logik für RISK-OFF
    else:
        cash_momentum_scores = {
            ticker: berechne_momentum(daten_aller_assets[ticker])['momentum_score']
            for ticker in settings.CASH_UNIVERSE
        }
        sortierte_assets = sorted(cash_momentum_scores.items(), key=lambda item: item[1], reverse=True)
        bestes_asset = sortierte_assets[0][0]
        ziel_portfolio = {bestes_asset: 1.0}

        # Baue das finale Ergebnis sauber zusammen
        return {
            'canary_report': markt_signal_details,
            'momentum_ranking': sortierte_assets,
            'portfolio': ziel_portfolio
        }