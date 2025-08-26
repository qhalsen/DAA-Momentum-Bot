# === Asset-Universen ===
# Diese Listen definieren die ETFs, die die Strategie beobachtet.

# U_R: Die 12 Assets des riskanten G12-Universums
# Definiert in Sektion 4, Seite 8
RISKY_UNIVERSE = [
    "SPY",  # S&P 500
    "IWM",  # Russell 2000 (US Small Caps)
    "QQQ",  # Nasdaq 100
    "VGK",  # European Stocks
    "EWJ",  # Japan Stocks
    "VWO",  # Emerging Markets Stocks
    "VNQ",  # Real Estate
    "GSG",  # Commodities
    "GLD",  # Gold
    "TLT",  # Long-Term US-Treasuries
    "HYG",  # High-Yield Corporate Bonds
    "LQD"   # Investment-Grade Corporate Bonds
]

# U_B: (Breadth/ protective) Die 2 Assets des "Canary" oder Schutz-Universums
# Definiert in Sektion 3, Seite 7 des Papers 
CANARY_UNIVERSE = [
    "VWO",  # Emerging Markets Stocks
    "BND"   # Total US Bond Market
]

# U_C: (Cash)Die 3 Assets des "aggressiven" Cash-Universums für die DAA1-Variante
# Definiert in Sektion 9, Seite 20 des Papers
CASH_UNIVERSE = [
    "SHV",  # Short-Term US-Treasuries (1-12 Monate)
    "IEF",  # Intermediate-Term US-Treasuries (7-10 Jahre)
    "UST"   # 2x Leveraged US-Treasuries (7-10 Jahre)
]


# === Strategie-Parameter ===
# Dies sind die "Schalter und Regler" der DAA1-G12 Strategie.

# T: Die Anzahl der Top-Assets, die im Risk-On-Modus ausgewählt werden.
# Optimiert für DAA1-G12 in Sektion 9, Seite 20 
T = 2

# B: Der Schwellenwert für den Schutzmechanismus (Anzahl "kranker" Kanarienvögel).
# Definiert für DAA "Aggressive" in Sektion 9, Seite 19
B = 1