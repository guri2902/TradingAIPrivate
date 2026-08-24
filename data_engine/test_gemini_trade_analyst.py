from data_engine.gemini_trade_analyst import GeminiTradeAnalyst

sample_result = {
    "selected_index": "NIFTY 50",
    "expiry": "2026-08-25",
    "trades": [
        {
            "strike": 24250.0,
            "type": "CE",
            "recommendation": "⭐⭐⭐ TRADEABLE SETUP",
            "ai_score": 73.0,
            "probability": 65.0,
            "premium": 96.25,
            "reasons": [
                "Market bias supports option direction",
                "MACD bullish",
                "Strike close to ATM",
                "Futures price supports CE",
            ],
            "warnings": [],
            "risk": {
                "entry": 103.0,
                "sl": 87.55,
                "target1": 123.60,
                "target2": 144.20,
                "target3": 163.62,
                "rr": 2.67,
                "position_size": 34,
                "max_loss": 500.0,
            },
            "unified_components": {
                "ml_score": 0,
                "ml_direction_probability": 0.0,
                "ml_signal": "UNAVAILABLE",
                "ml_regime": "",
                "futures_score": 5,
            },
        }
    ],
}

analyst = GeminiTradeAnalyst()

print("Gemini key configured:", analyst.available)
print("Gemini model:", analyst.model)

result = analyst.explain_trade_result(
    sample_result
)

if analyst.available:
    if not result["available"]:
        raise RuntimeError(
            result.get("error", "Gemini request failed.")
        )
    print("\nGemini response:\n")
    print(result["text"])
else:
    assert result["available"] is False
    assert "GEMINI_API_KEY" in result["error"]
    print("\nGraceful missing-key behavior validated.")

print("\nGEMINI TRADE ANALYST TEST PASSED")