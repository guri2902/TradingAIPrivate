from data_engine.tradingai_agent import TradingAIAgent

result = {
    "selected_index": "NIFTY 50",
    "trades": [
        {
            "strike": 24250.0,
            "type": "CE",
            "ai_score": 73.0,
            "probability": 65.0,
            "reasons": ["Market trend supports CE"],
            "warnings": [],
            "risk": {
                "entry": 103.0,
                "sl": 87.55,
                "target1": 123.60,
                "rr": 2.67,
            },
            "unified_components": {
                "ml_score": 0,
                "ml_signal": "UNAVAILABLE",
                "futures_score": 5,
            },
        },
        {
            "strike": 24300.0,
            "type": "CE",
            "ai_score": 73.0,
            "probability": 65.0,
        },
    ],
}

agent = TradingAIAgent(result)
evidence = agent.inspect_trade()

assert evidence["top_trade"]["strike"] == 24250.0
assert evidence["risk"]["entry"] == 103.0
assert evidence["unified_context"]["futures_score"] == 5
assert len(evidence["candidate_comparison"]) == 1

print("TradingAI Agent Test PASSED")
print("Available tools:", TradingAIAgent.TOOL_NAMES)