# ============================================================
# TradingAI - API
# ============================================================

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from data_engine.realtime_data_orchestrator import (
    RealtimeDataOrchestrator,
)

from data_engine.risk_engine import (
    RiskEngine,
    RiskConfig,
)


app = FastAPI(
    title="TradingAI API",
    version="1.0.0",
)


# ============================================================
# CONFIG
# ============================================================

RISK_CONFIG = RiskConfig(
    capital=100000,
    risk_per_trade_pct=1.0,
    max_daily_loss_pct=3.0,
    max_positions=1,
    min_risk_reward=1.5,
    max_position_value_pct=100.0,
)

# ============================================================
# SINGLETON SERVICES
# ============================================================

_orchestrator = (
    RealtimeDataOrchestrator()
)

_risk_engine = RiskEngine(
    config=RISK_CONFIG
)

# ============================================================
# SHORT API CACHE
# ============================================================

MARKET_CACHE_TTL = 10.0

_market_cache = {}

def _get_cached_tradingai_state(
    symbol: str,
):

    symbol = (
        str(symbol)
        .strip()
        .upper()
    )

    now = time.monotonic()

    cached = (
        _market_cache.get(
            symbol
        )
    )

    if cached is not None:

        cached_at, state = cached

        if (
            now - cached_at
            < MARKET_CACHE_TTL
        ):

            return state

    state = (
        _orchestrator.build_state(
            symbol
        )
    )

    _market_cache[
        symbol
    ] = (
        now,
        state,
    )

    return state

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "TradingAI API",
        "timestamp":
            datetime.now().isoformat(),
    }


# ============================================================
# MARKET STATE
# ============================================================

@app.get("/v1/market/{symbol}")
def market_state(
    symbol: str,
):

    symbol = (
        symbol
        .upper()
        .strip()
    )

    try:

        state = (
            _get_cached_tradingai_state(
                symbol
            )
        )

        return {
            "ok": True,
            "data": state,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(exc),
            },
        )


# ============================================================
# RISK CHECK
# ============================================================

@app.get("/v1/risk/check")
def risk_check(
    side: str = Query(
        ...,
        description="LONG or SHORT",
    ),

    entry: float = Query(...),

    stop_loss: float = Query(...),

    target: float = Query(...),

    quantity: Optional[int] = Query(
        None
    ),

    current_daily_pnl: float = Query(
        0.0
    ),

    open_positions: int = Query(
        0
    ),
):

    try:

        result = (
            _risk_engine.evaluate(
                side=side,
                entry=entry,
                stop_loss=stop_loss,
                target=target,
                quantity=quantity,
                current_daily_pnl=current_daily_pnl,
                open_positions=open_positions,
            )
        )

        return {
            "ok": True,
            "data": result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error": str(exc),
            },
        )


# ============================================================
# COMBINED TRADINGAI STATE
# ============================================================

@app.get("/v1/tradingai/{symbol}")
def tradingai_state(
    symbol: str,
):

    symbol = (
        symbol
        .upper()
        .strip()
    )

    try:

        state = (
            _orchestrator.build_state(
                symbol
            )
        )

        return {
            "ok": True,
            "data": state,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(exc),
            },
        )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "TradingAI API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/v1/market/{symbol}",
            "/v1/risk/check",
            "/v1/tradingai/{symbol}",
        ],
    }