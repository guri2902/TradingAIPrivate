# ============================================================
# TradingAI - AI JOURNAL REVIEW TEST
# ============================================================

from data_engine.ai_journal_review import (
    AIJournalReview,
)


print("=" * 70)
print("TradingAI - AI JOURNAL REVIEW TEST")
print("=" * 70)


# ============================================================
# TEST 1 - LOAD JOURNAL
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 - LOAD TRADE JOURNAL")
print("=" * 70)

reviewer = AIJournalReview()

trades = reviewer.load_trades()

print(
    f"Journal trades: {len(trades)}"
)

if not trades:

    raise RuntimeError(
        "Trade journal is empty. Add completed trades first."
    )


# ============================================================
# TEST 2 - BUILD SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 - BUILD JOURNAL SUMMARY")
print("=" * 70)

summary = reviewer.build_summary(
    trades
)

for key, value in summary.items():

    if isinstance(
        value,
        float,
    ):

        print(
            f"{key}: {value:.4f}"
        )

    else:

        print(
            f"{key}: {value}"
        )


# ============================================================
# TEST 3 - AI REVIEW
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 - AI JOURNAL REVIEW")
print("=" * 70)

analysis = reviewer.review(
    trades
)

if not analysis:

    raise RuntimeError(
        "AI Journal Review returned empty output."
    )


# ============================================================
# TEST 4 - VALIDATION
# ============================================================

required_sections = [
    "OVERALL ASSESSMENT:",
    "PERFORMANCE SUMMARY:",
    "STRENGTHS:",
    "WEAKNESSES:",
    "RECURRING PATTERNS:",
    "RISK MANAGEMENT:",
    "MODEL PERFORMANCE:",
    "IMPROVEMENT ACTIONS:",
    "PRIORITY FOCUS:",
]

missing = [
    section
    for section in required_sections
    if section not in analysis
]

if missing:

    raise RuntimeError(
        f"Missing journal review sections: {missing}"
    )


print()
print(analysis)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("AI JOURNAL REVIEW TEST PASSED")
print("=" * 70)