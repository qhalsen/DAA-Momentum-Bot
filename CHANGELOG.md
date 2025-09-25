# Changelog

All notable changes to this project will be documented in this file.

---

## [1.0.0] - 2025-09-26

This is the initial stable release of the DAA Momentum Bot with a full reporting suite.

### Added
- **Core Strategy Engine:** Implemented the DAA momentum strategy including Canary Analysis and Risk-On/Risk-Off logic.
- **IBKR Integration:** Established connection to Interactive Brokers for fetching historical data, account details, and current prices.
- **Database Storage:** Created a robust SQLite database schema to save all rebalancing events, including decisions, rankings, and context.
- **Professional Metrics:** Integrated calculation and reporting for key financial ratios:
    - Sharpe Ratio
    - Sortino Ratio
    - Calmar Ratio
    - Treynor Ratio
    - Portfolio Volatility
    - Maximum Drawdown
- **"The Why" Context:** Added advanced context reporting:
    - Market Breadth (percentage of risky assets with positive momentum).
    - Correlation Matrix for top assets.
    - Signal Duration to track the persistence of the market signal.
- **Configuration File:** Centralized all settings, including asset universes, risk-free rate, and benchmark components.

---

## [Unreleased]

This section tracks upcoming features and improvements for the next version.

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