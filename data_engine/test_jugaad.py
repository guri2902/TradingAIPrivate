from datetime import date

from data_engine.jugaad_source import JugaadSource
from data_engine.config import JUGAAD_RAW_DIR


source = JugaadSource(
    JUGAAD_RAW_DIR
)


df = source.get_index(
    symbol="NIFTY 50",
    from_date=date(2025, 1, 1),
    to_date=date(2026, 8, 17)
)


print("\n" + "=" * 70)
print("JUGAAD DATA TEST")
print("=" * 70)

print("\nRows:", len(df))

print("\nColumns:")
print(list(df.columns))

print("\nFirst 5:")
print(df.head())

print("\nLast 5:")
print(df.tail())