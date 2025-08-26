# Importiert settings aus der Konfigurationsdatei
from config import settings

def berechne_momentum(monats_schlusskurse: list) -> float:
    """
    Berechnet den 13612W Momentum-Score exakt nach der Papiermethodik.

    Args:
        monats_schlusskurse: Eine Liste von 13 Monats-Schlusskursen (aktueller Monat + 12 Vormonate).

    Returns:
        Den 13612W Momentum-Score als Fließkommazahl.
    """
    # Sicherstellen, dass wir genug Daten haben.
    if len(monats_schlusskurse) < 13:
        # Wenn nicht genügend historische Daten vorhanden sind, ist das ein
        # kritisches Datenproblem. Wir lösen einen Fehler aus, der auf ein
        # Problem im Datenbeschaffungsprozess (z.B. ingest.py) hinweist.
        raise ValueError(
            f"Nicht genügend Daten für Momentum-Berechnung. "
            f"Erhalten: {len(monats_schlusskurse)} Kurse, benötigt: 13. "
            f"Bitte den Daten-Ingestion-Prozess prüfen."
        )

    # Preise zu den relevanten Zeitpunkten extrahieren.
    # Der letzte Eintrag ist der aktuellste Kurs.
    aktueller_kurs        = monats_schlusskurse[-1]
    kurs_vor_1_monat      = monats_schlusskurse[-2]
    kurs_vor_3_monaten    = monats_schlusskurse[-4]
    kurs_vor_6_monaten    = monats_schlusskurse[-7]
    kurs_vor_12_monaten   = monats_schlusskurse[-13]

    # 1. Renditen für die vier Zeiträume berechnen
    ret1 = (aktueller_kurs / kurs_vor_1_monat) - 1
    ret3 = (aktueller_kurs / kurs_vor_3_monaten) - 1
    ret6 = (aktueller_kurs / kurs_vor_6_monaten) - 1
    ret12 = (aktueller_kurs / kurs_vor_12_monaten) - 1

    # 2. Renditen annualisieren (das ist die Gewichtung "W")
    # Quelle: Fußnote 3, Seite 1 des Papers
    annual_ret1 = ret1 * 12
    annual_ret3 = ret3 * 4
    annual_ret6 = ret6 * 2
    annual_ret12 = ret12 * 1

    # 3. Den Durchschnitt der vier annualisierten Renditen berechnen
    # Quelle: Fußnote 3, Seite 1 des Papers
    score = (annual_ret1 + annual_ret3 + annual_ret6 + annual_ret12) / 4
    
    return score

def canary_check(daten_aller_assets: dict) -> str:
    """
    Überprüft die "Kanarienvogel"-Assets. Gibt 'RISK_OFF' zurück, wenn ein Vogel
    ein negatives Momentum hat, ansonsten 'RISK_ON'.

    Args:
        daten_aller_assets: Ein Dictionary, das für jeden Ticker eine Liste
                            historischer Kurse enthält. z.B. {'VWO': [...], 'BND': [...]}

    Returns:
        Einen String: 'RISK_ON' oder 'RISK_OFF'.
    """
    for ticker in settings.CANARY_UNIVERSE:
        # Hole die Kurse für den aktuellen Kanarienvogel
        vogel_kurse = daten_aller_assets[ticker]
        
        # Berechne seine "Gesundheit" (Momentum)
        momentum_score = berechne_momentum(vogel_kurse)
        
        # Die B=1 Regel: Wenn ein Vogel krank ist, sofort Alarm schlagen.
        # Ein "bad" asset hat ein "non-positive" momentum (<= 0).
        if momentum_score <= 0:
            return "RISK_OFF" # Ein kranker Kanarienvogel, also kein Risiko
            
    # Diese Zeile wird nur erreicht, wenn alle Kanarienvögel gesund sind.
    return "RISK_ON"

def bestimme_ziel_portfolio(daten_aller_assets: dict) -> dict:
    """
    Die Haupt-Entscheidungsfunktion. Sie führt den Canary-Check durch und
    bestimmt basierend auf dem Ergebnis das finale Zielportfolio.

    Args:
        daten_aller_assets: Ein Dictionary, das für JEDEN Ticker in ALLEN
                            Universen die historischen Kurse enthält.

    Returns:
        Ein Dictionary, das das Zielportfolio repräsentiert,
        z.B. {'SPY': 0.5, 'QQQ': 0.5} oder {'IEF': 1.0}.
    """
    # Schritt 1: Den übergeordneten Markttrend bestimmen
    markt_signal = canary_check(daten_aller_assets)

    # Schritt 2: Basierend auf dem Signal das Portfolio bauen
    if markt_signal == "RISK_ON":
        # --- RISK-ON LOGIK ---
        # 1. Berechne die Momentum-Scores für alle riskanten Assets
        risky_momentum_scores = {}
        for ticker in settings.RISKY_UNIVERSE:
            kurse = daten_aller_assets[ticker]
            score = berechne_momentum(kurse)
            risky_momentum_scores[ticker] = score
        
        # 2. Sortiere die Assets absteigend nach ihrem Score
        sortierte_assets = sorted(
            risky_momentum_scores.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
        
        # 3. Wähle die Top T Assets aus (T=2 in unseren Einstellungen)
        top_assets = sortierte_assets[:settings.T]
        
        # 4. Erstelle das finale Portfolio-Dictionary
        ziel_portfolio = {asset[0]: 1 / settings.T for asset in top_assets}
        return ziel_portfolio

    else: # markt_signal == "RISK_OFF"
        # --- RISK-OFF LOGIK ---
        # 1. Berechne die Momentum-Scores für alle Cash-Assets
        cash_momentum_scores = {}
        for ticker in settings.CASH_UNIVERSE:
            kurse = daten_aller_assets[ticker]
            score = berechne_momentum(kurse)
            cash_momentum_scores[ticker] = score
            
        # 2. Finde das eine Asset mit dem höchsten Score
        # KORRIGIERTE ZEILE: Wir verwenden .items() und eine lambda-Funktion für Klarheit.
        bestes_asset = max(cash_momentum_scores.items(), key=lambda item: item[1])[0]
        
        # 3. Erstelle das finale Portfolio-Dictionary
        ziel_portfolio = {bestes_asset: 1.0}
        return ziel_portfolio

# --- Finaler Testbereich ---
if __name__ == "__main__":
    
    print("--- Teste die Hauptfunktion: bestimme_ziel_portfolio ---")

    # Wir erstellen ein umfassendes Test-Daten-Set
    test_kurse_sehr_positiv = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124]
    test_kurse_positiv      = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112]
    test_kurse_neutral      = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    test_kurse_negativ      = [112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100]

    # Szenario 1: RISK-ON
    # Die Kanarienvögel (VWO, BND) sind gesund.
    # Wir geben den riskanten Assets unterschiedliche positive Scores, um die Sortierung zu testen.
    test_daten_risk_on = {
        "SPY": test_kurse_sehr_positiv, # Bester
        "IWM": test_kurse_positiv,      # Zweitbester
        "QQQ": test_kurse_neutral,      # Schlechter
        "VGK": test_kurse_neutral,
        "EWJ": test_kurse_neutral,
        "VWO": test_kurse_positiv,      # Canary -> gesund
        "VNQ": test_kurse_neutral,
        "GSG": test_kurse_neutral,
        "GLD": test_kurse_neutral,
        "TLT": test_kurse_neutral,
        "HYG": test_kurse_neutral,
        "LQD": test_kurse_neutral,
        "BND": test_kurse_positiv,      # Canary -> gesund
        "SHV": test_kurse_neutral,
        "IEF": test_kurse_neutral,
        "UST": test_kurse_neutral
    }
    
    portfolio_on = bestimme_ziel_portfolio(test_daten_risk_on)
    print(f"\nSzenario RISK-ON:")
    print(f"Zielportfolio: {portfolio_on} (Erwartet: Die Top 2 riskanten Assets, SPY und IWM)")

    # Szenario 2: RISK-OFF
    # Einer der Kanarienvögel (BND) ist krank.
    # Wir geben den Cash-Assets unterschiedliche Scores, um die Auswahl zu testen.
    test_daten_risk_off = {
        "SPY": test_kurse_sehr_positiv,
        "IWM": test_kurse_positiv,
        "QQQ": test_kurse_neutral,
        "VGK": test_kurse_neutral,
        "EWJ": test_kurse_neutral,
        "VWO": test_kurse_positiv,      # Canary -> gesund
        "VNQ": test_kurse_neutral,
        "GSG": test_kurse_neutral,
        "GLD": test_kurse_neutral,
        "TLT": test_kurse_neutral,
        "HYG": test_kurse_neutral,
        "LQD": test_kurse_neutral,
        "BND": test_kurse_negativ,      # Canary -> KRANK!
        "SHV": test_kurse_neutral,
        "IEF": test_kurse_sehr_positiv, # Bestes Cash-Asset
        "UST": test_kurse_positiv
    }

    portfolio_off = bestimme_ziel_portfolio(test_daten_risk_off)
    print(f"\nSzenario RISK-OFF:")
    print(f"Zielportfolio: {portfolio_off} (Erwartet: Das beste Cash-Asset, IEF)")
