from app.portfolio.csv_io import export_trades_csv, parse_holdings_csv


def test_parse_broker_csv_with_alias_headers():
    csv_text = "Instrument,Qty,Avg Price\nRELIANCE.NS,10,2400\n"

    result = parse_holdings_csv(csv_text, valid_symbols={"RELIANCE.NS"})

    assert result["holdings"][0]["symbol"] == "RELIANCE.NS"
    assert result["holdings"][0]["shares"] == 10
    assert result["holdings"][0]["averageCost"] == 2400
    assert result["holdings"][0]["status"] == "valid"
    assert result["warnings"] == []


def test_parse_csv_warns_for_unknown_symbol_and_rejects_negative_values():
    csv_text = "symbol,shares,value\nUNKNOWN.NS,2,5000\nTCS.NS,-1,1000\n"

    result = parse_holdings_csv(csv_text, valid_symbols={"TCS.NS"})

    assert result["holdings"][0]["symbol"] == "UNKNOWN.NS"
    assert result["holdings"][0]["status"] == "warning"
    assert result["holdings"][1]["status"] == "error"
    assert result["warnings"]


def test_export_trades_csv_contains_order_sheet_columns():
    trades = [
        {
            "symbol": "TCS.NS",
            "tradeAction": "buy",
            "currentValue": 0,
            "targetValue": 50000,
            "tradeValue": 50000,
            "latestPrice": 4000,
            "estimatedShares": 12.5,
            "reason": "New target position",
        }
    ]

    csv_text = export_trades_csv(trades)

    assert "symbol,action,current_value,target_value,trade_value,latest_price,estimated_shares,whole_shares,reason" in csv_text
    assert "TCS.NS,buy,0,50000,50000,4000,12.5,12,New target position" in csv_text
