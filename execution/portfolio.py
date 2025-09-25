# execution/portfolio.py

from execution import broker

def calculate_trades(app, current_positions: dict, target_portfolio: dict, total_portfolio_value: float) -> list:
    """
    Vergleicht das aktuelle Depot mit dem Zielportfolio und berechnet die notwendigen Trades.

    Args:
        app: Die aktive IBKR-Client-Verbindung.
        current_positions: Dict des aktuellen Portfolios, z.B. {'SXR8': 10}.
        target_portfolio: Dict des Zielportfolios, z.B. {'SXR8': 0.5, 'SXRV': 0.5}.
        total_portfolio_value: Der Gesamtwert des Portfolios (Cash + Wert der Positionen).

    Returns:
        Eine Liste von Trade-Dictionaries, z.B. [{'symbol': 'SXR8', 'quantity': 3, 'action': 'BUY'}].
    """
    trades = []
    
    # --- Schritt 1: Verkäufe berechnen ---
    # Gehe durch die aktuellen Positionen und verkaufe alles, was nicht im Zielportfolio ist.
    for symbol, quantity in current_positions.items():
        if symbol not in target_portfolio:
            print(f"Verkaufs-Signal: {symbol} ist nicht im Zielportfolio. Verkaufe {quantity} Stk.")
            trades.append({'symbol': symbol, 'quantity': quantity, 'action': 'SELL'})

    # --- Schritt 2: Käufe und Anpassungen berechnen ---
    for symbol, target_weight in target_portfolio.items():
        # Berechne den Zielwert für dieses Asset
        target_value = total_portfolio_value * target_weight
        
        # Hole den aktuellen Marktpreis, um die Stückzahl zu berechnen
        current_price = broker.get_current_price_ibkr(app, symbol)
        
        if current_price == 0:
            print(f"FEHLER: Konnte aktuellen Preis für {symbol} nicht abrufen. Überspringe Trade.")
            continue

        # Berechne die Ziel-Stückzahl (abgerundet auf ganze Anteile)
        target_quantity = int(target_value / current_price)
        
        # Hole die aktuelle Stückzahl aus unseren Positionen
        current_quantity = current_positions.get(symbol, 0)
        
        # Berechne die Differenz
        trade_quantity = target_quantity - current_quantity
        
        if trade_quantity > 5: # Schwellenwert, um kleine Trades zu vermeiden
            print(f"Kauf-Signal für {symbol}: Zielmenge={target_quantity}, Aktuell={current_quantity}. Kaufe {trade_quantity} Stk.")
            trades.append({'symbol': symbol, 'quantity': trade_quantity, 'action': 'BUY'})
        elif trade_quantity < -5: # Schwellenwert, um kleine Trades zu vermeiden
            print(f"Verkaufs-Signal für {symbol}: Zielmenge={target_quantity}, Aktuell={current_quantity}. Verkaufe {abs(trade_quantity)} Stk.")
            trades.append({'symbol': symbol, 'quantity': abs(trade_quantity), 'action': 'SELL'})
            
    return trades
