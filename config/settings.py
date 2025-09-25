# === Asset-Universen & Kontrakt-Details (Finale, verifizierte IBKR-Version) ===
# Diese Konfiguration wurde durch das Skript check_tickers.py verifiziert und
# enthält die finalen, funktionierenden Einstellungen für den Bot.
# Jedes Asset ist mit seinem US-Pendant und seiner ISIN kommentiert.

ASSET_CONTRACTS: dict[str, dict] = {
    # ==============================================================================
    #  === Risky-Universe G12 =====================================================
    # ==============================================================================

    # Pendant: SPY (S&P 500)
    # ISIN: IE00B5BMR087
    "SXR8": {"symbol": "SXR8", "exchange": "SMART", "primaryExchange": "IBIS2", "currency": "EUR", "secType": "STK"},

    # Pendant: IWM (Russell 2000)
    # ISIN: IE00BJZ2DD79
    "XRSU": {"symbol": "XRSU", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},

    # Pendant: QQQ (Nasdaq 100)
    # ISIN: IE00B53SZB19
    "SXRV": {"symbol": "SXRV", "exchange": "SMART", "primaryExchange": "IBIS2", "currency": "EUR", "secType": "STK"},

    # Pendant: VGK (Europe Stocks)
    # ISIN: IE00B0M62S72
    "EXSA": {"symbol": "EXSA", "exchange": "SMART", "primaryExchange": "IBIS", "currency": "EUR", "secType": "STK"},

    # Pendant: EWJ (Japan Stocks)
    # ISIN: IE00B4L5Y983
    "SXR1": {"symbol": "SXR1", "exchange": "SMART", "primaryExchange": "IBIS2", "currency": "EUR", "secType": "STK"},

    # Pendant: VWO (Emerging Markets) -> Auch Canary-Asset
    # ISIN: IE00BKM4GZ66
    "EMIM": {"symbol": "EMIM", "exchange": "SMART", "primaryExchange": "AEB", "currency": "EUR", "secType": "STK"},

    # Pendant: VNQ (US REITs)
    # ISIN: IE00B1FZS350
    "IWDP": {"symbol": "IWDP", "exchange": "SMART", "primaryExchange": "AEB", "currency": "EUR", "secType": "STK"},

    # Pendant: GSG (Broad Commodities) -> STRATEGISCH KORREKTER ERSATZ
    # HINWEIS: Dieser ETC bildet Rohstoff-Futures direkt ab. Verifiziert mit check_tickers.py.
    # ISIN: IE00B5MTWH09
    "CMOD": {"symbol": "CMOD", "exchange": "SMART", "primaryExchange": "BVME.ETF", "currency": "EUR", "secType": "STK"},

    # Pendant: GLD (Gold)
    # ISIN: DE000A0S9GB0
    "4GLD": {"symbol": "4GLD", "exchange": "SMART", "primaryExchange": "IBIS", "currency": "EUR", "secType": "STK"},

    # Pendant: TLT (US Treasuries 20+y)
    # ISIN: IE00BSKRJ623
    "IDTL": {"symbol": "IDTL", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},

    # Pendant: HYG (US High-Yield Corp. Bonds)
    # ISIN: IE00B44CGS96
    "IHYU": {"symbol": "IHYU", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},

    # Pendant: LQD (US Inv.-Grade Corp. Bonds)
    # ISIN: IE00B4L60S22
    "LQDE": {"symbol": "LQDE", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},


    # ==============================================================================
    # === Canary-Universe P2 =======================================================
    # ==============================================================================

    # Pendant: BND (US Total Bond Market)
    # ISIN: IE00BDBRDM35
    "EUNA": {"symbol": "EUNA", "exchange": "SMART", "primaryExchange": "IBIS2", "currency": "EUR", "secType": "STK"},


    # ==============================================================================
    # === Cash-Universe C3 (aggressive) ============================================
    # ==============================================================================

    # Pendant: SHV (US Treasuries 0-1y)
    # ISIN: IE00BGSF1X88
    "IB01": {"symbol": "IB01", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},

    # Pendant: IEF (US Treasuries 7-10y)
    # HINWEIS: Dieses Asset dient auch als Ersatz für das gehebelte Produkt 'UST' aus Stabilitätsgründen.
    # ISIN: IE00B3VWN179
    "IBTA": {"symbol": "IBTA", "exchange": "SMART", "primaryExchange": "LSEETF", "currency": "USD", "secType": "STK"},
}


# === Finale Asset-Universen (mit strategisch besserem Rohstoff-ETF) ========
RISKY_UNIVERSE: list[str] = [
    "SXR8", "XRSU", "SXRV", "EXSA", "SXR1", "EMIM",
    "IWDP", "CMOD", "4GLD", "IDTL", "IHYU", "LQDE"  # CMOD ersetzt DXS1
]

CANARY_UNIVERSE: list[str] = ["EMIM", "EUNA"]

CASH_UNIVERSE: list[str] = ["IB01", "IBTA"]

# === Strategie-Parameter ======================================================
T: int = 2  # Top-n
B: int = 1  # Breadth → DAA1-G12 (aggressiv)

