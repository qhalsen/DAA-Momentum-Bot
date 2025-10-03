# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Planned Features
- **Order Execution Details:**
    - Implement a feedback loop to capture and store the actual execution prices from the broker.
    - Record and report exact commissions for each trade.
    - Save the precise execution timestamp for all orders.
- **Post-Rebalancing Snapshot:**
    - Add a final query after trades are executed to get the true end-of-day holdings and cash balance.
    - Calculate and report the real asset allocation percentages after rebalancing.
- **System & Data Integrity:**
    - Implement a data quality flag (e.g., a traffic light system) to report issues during data fetching.
    - Store a clear "proof of origin" for the specific price data used in each decision.

---

## [1.0.1] - 2025-09-26

### Added
- **Interactive Web Dashboard:** Replaced the static HTML report with a dynamic, interactive dashboard using Dash and Plotly.
- **Modular Reporting Architecture:** Refactored the reporting logic into a clean, modular structure (`dashboard.py`, `reporting/data_provider.py`, `reporting/components.py`).

### Removed
- Deprecated the static reporting scripts (`reporting/performance.py`, `reporting/metrics.py`, `reporting/html_generator.py`).

---

## [1.0.0] - 2025-09-26

### Added
- **Core Strategy Engine:** Implemented the DAA momentum strategy including Canary Analysis and Risk-On/Risk-Off logic.
- **IBKR Integration:** Established connection to Interactive Brokers for fetching historical data, account details, and current prices.
- **Database Storage:** Created a robust SQLite database schema to save all rebalancing events, including decisions, rankings, and context.
- **Professional Metrics:** Integrated calculation and reporting for key financial ratios (Sharpe, Sortino, Calmar, Treynor, etc.).
- **"The Why" Context:** Added advanced context reporting (Market Breadth, Correlation Matrix, Signal Duration).
- **Configuration File:** Centralized all settings, including asset universes, risk-free rate, and benchmark components.