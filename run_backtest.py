from backtest.backtest_engine import BacktestEngine


CE_FILE = (
    r"C:\TradingAI\OPTIDX_NIFTY_CE_10-Jul-2026_TO_10-Aug-2026.csv"
)

PE_FILE = (
    r"C:\TradingAI\OPTIDX_NIFTY_PE_10-Jul-2026_TO_10-Aug-2026.csv"
)


engine = BacktestEngine(
    CE_FILE,
    PE_FILE
)

results = engine.run()

print("\n==============================")
print("BACKTEST RESULTS")
print("==============================\n")

print(results.to_string(index=False))

results.to_csv(
    "backtest_results.csv",
    index=False
)

print("\nSaved:")
print("backtest_results.csv")