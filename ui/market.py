from datetime import datetime
import math

import pandas as pd
import yfinance as yf

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QSizePolicy
)

from ui import theme


# ============================================================
# DATA UNIVERSE
# ============================================================
INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "MIDCAP NIFTY": "NIFTY_MIDCAP_100.NS",
}

VIX_SYMBOLS = ("^INDIAVIX", "INDIAVIX.NS")

GLOBAL_MARKETS = {
    "DOW JONES": "^DJI",
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "GOLD": "GC=F",
    "BRENT OIL": "BZ=F",
}

SECTORS = {
    "Nifty Auto": "^CNXAUTO",
    "Nifty Energy": "^CNXENERGY",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Realty": "^CNXREALTY",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
}

STOCKS = {
    "RELIANCE": "RELIANCE.NS", "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS",
    "INFY": "INFY.NS", "TCS": "TCS.NS", "ITC": "ITC.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "LT": "LT.NS", "AXISBANK": "AXISBANK.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "M&M": "M&M.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "HINDUNILVR": "HINDUNILVR.NS", "MARUTI": "MARUTI.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS", "ADANIENT": "ADANIENT.NS", "NTPC": "NTPC.NS",
    "POWERGRID": "POWERGRID.NS", "TATASTEEL": "TATASTEEL.NS", "HCLTECH": "HCLTECH.NS",
    "WIPRO": "WIPRO.NS", "TECHM": "TECHM.NS", "ASIANPAINT": "ASIANPAINT.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS", "NESTLEIND": "NESTLEIND.NS", "JSWSTEEL": "JSWSTEEL.NS",
    "TATAMOTORS": "TMPV.NS", "COALINDIA": "COALINDIA.NS", "ONGC": "ONGC.NS",
    "GRASIM": "GRASIM.NS", "ADANIPORTS": "ADANIPORTS.NS", "EICHERMOT": "EICHERMOT.NS",
    "CIPLA": "CIPLA.NS", "DRREDDY": "DRREDDY.NS", "APOLLOHOSP": "APOLLOHOSP.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS", "BRITANNIA": "BRITANNIA.NS", "HEROMOTOCO": "HEROMOTOCO.NS",
    "INDUSINDBK": "INDUSINDBK.NS", "BEL": "BEL.NS", "TRENT": "TRENT.NS",
    "SHRIRAMFIN": "SHRIRAMFIN.NS", "HINDALCO": "HINDALCO.NS", "BPCL": "BPCL.NS",
    "DIVISLAB": "DIVISLAB.NS", "TATACONSUM": "TATACONSUM.NS",
}


def number(value, default=None):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except Exception:
        return default


def price(value):
    value = number(value)
    return "--" if value is None else f"{value:,.2f}"


def percentage(value):
    value = number(value)
    return "--" if value is None else f"{value:+.2f}%"


def volume(value):
    value = number(value)
    if value is None:
        return "--"
    if value >= 1e7:
        return f"{value / 1e7:.2f} Cr"
    if value >= 1e5:
        return f"{value / 1e5:.2f} L"
    if value >= 1e3:
        return f"{value / 1e3:.1f} K"
    return f"{value:,.0f}"


def movement_color(value):
    value = number(value, 0)
    if value > 0:
        return theme.GREEN
    if value < 0:
        return theme.RED
    return theme.TEXT_MUTED


def clean_frame(frame):
    if frame is None or frame.empty:
        return pd.DataFrame()
    frame = frame.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [c[-1] if isinstance(c, tuple) else c for c in frame.columns]
    mapping = {str(c).lower(): c for c in frame.columns}
    out = pd.DataFrame(index=frame.index)
    for col in ("open", "high", "low", "close", "volume"):
        if col in mapping:
            out[col.title()] = frame[mapping[col]]
    required = ["Open", "High", "Low", "Close"]
    if not all(c in out for c in required):
        return pd.DataFrame()
    if "Volume" not in out:
        out["Volume"] = 0
    return out.dropna(subset=required)


def extract_ticker(data, ticker):
    if data is None or data.empty:
        return pd.DataFrame()
    try:
        if isinstance(data.columns, pd.MultiIndex):
            level0 = data.columns.get_level_values(0)
            level1 = data.columns.get_level_values(1)
            if ticker in level0:
                return clean_frame(data[ticker])
            if ticker in level1:
                return clean_frame(data.xs(ticker, axis=1, level=1))
        return clean_frame(data)
    except Exception:
        return pd.DataFrame()


def download_symbol(symbol, period="5d", interval="5m"):
    try:
        data = yf.download(symbol, period=period, interval=interval,
                           progress=False, auto_adjust=False, threads=False)
        frame = clean_frame(data)
        if not frame.empty:
            return frame
    except Exception as exc:
        print(f"yfinance download failed for {symbol}: {exc}")
    try:
        data = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        frame = clean_frame(data)
        if not frame.empty:
            return frame
    except Exception as exc:
        print(f"yfinance history failed for {symbol}: {exc}")
    return pd.DataFrame()


def summarize(frame):
    frame = clean_frame(frame)
    if frame.empty:
        return {}
    last = frame.iloc[-1]
    previous = frame.iloc[-2] if len(frame) > 1 else last
    close = number(last["Close"])
    previous_close = number(previous["Close"])
    if close is None:
        return {}
    change = close - previous_close if previous_close is not None else 0
    change_pct = change / previous_close * 100 if previous_close else 0
    return {
        "price": close, "previous_close": previous_close, "change": change,
        "change_pct": change_pct, "open": number(last["Open"]),
        "high": number(last["High"]), "low": number(last["Low"]),
        "volume": number(last.get("Volume", 0), 0), "frame": frame,
    }


def calculate_max_pain(rows):
    """Calculate approximate NIFTY max-pain strike from option-chain OI."""
    strikes = []
    for row in rows:
        strike = number(row.get("strikePrice"))
        if strike is not None:
            strikes.append(strike)
    if not strikes:
        return None
    best_strike, best_loss = None, None
    for candidate in strikes:
        loss = 0.0
        for row in rows:
            strike = number(row.get("strikePrice"))
            ce = row.get("CE") or {}
            pe = row.get("PE") or {}
            ce_oi = number(ce.get("openInterest"), 0)
            pe_oi = number(pe.get("openInterest"), 0)
            if strike is None:
                continue
            loss += max(0, candidate - strike) * ce_oi
            loss += max(0, strike - candidate) * pe_oi
        if best_loss is None or loss < best_loss:
            best_strike, best_loss = candidate, loss
    return best_strike


class MarketWorker(QThread):
    data_ready = Signal(dict)
    error = Signal(str)

    def run(self):
        try:
            self.data_ready.emit(self.fetch_market())
        except Exception as exc:
            self.error.emit(str(exc))

    def fetch_market(self):
        result = {
            "indices": {}, "stocks": {}, "sectors": {}, "vix": {},
            "options": {}, "global": {}, "news": [], "updated": datetime.now(),
        }

        # Indices
        for name, symbol in INDEXES.items():
            try:
                summary = summarize(download_symbol(symbol, "5d", "5m"))
                if summary:
                    result["indices"][name] = summary
            except Exception as exc:
                print(f"Index error {name}: {exc}")

        # India VIX
        for symbol in VIX_SYMBOLS:
            summary = summarize(download_symbol(symbol, "5d", "5m"))
            if summary:
                result["vix"] = summary
                break

        # Stocks / sectors - daily data keeps the market page reasonably fast.
        try:
            symbols = list(STOCKS.values())
            data = yf.download(symbols, period="5d", interval="1d", progress=False,
                                auto_adjust=False, group_by="ticker", threads=True)
            for name, symbol in STOCKS.items():
                summary = summarize(extract_ticker(data, symbol))
                if summary:
                    result["stocks"][name] = summary
        except Exception as exc:
            print(f"Stock data error: {exc}")

        try:
            symbols = list(SECTORS.values())
            data = yf.download(symbols, period="5d", interval="1d", progress=False,
                                auto_adjust=False, group_by="ticker", threads=True)
            for name, symbol in SECTORS.items():
                summary = summarize(extract_ticker(data, symbol))
                if summary:
                    result["sectors"][name] = summary
        except Exception as exc:
            print(f"Sector data error: {exc}")

        # Option chain: preserve real rows so the page can show most-active strikes.
        try:
            from engine.option_chain import OptionChain
            raw = OptionChain().get_nifty()
            records = raw.get("records", {}) if raw else {}
            rows = records.get("data", [])
            calls, puts = [], []
            for row in rows:
                ce, pe = row.get("CE") or {}, row.get("PE") or {}
                strike = number(row.get("strikePrice"))
                calls.append((number(ce.get("openInterest"), 0), strike))
                puts.append((number(pe.get("openInterest"), 0), strike))

            total_call_oi = sum(v for v, _ in calls)
            total_put_oi = sum(v for v, _ in puts)
            result["options"] = {
                "spot": number(records.get("underlyingValue")),
                "expiry": (records.get("expiryDates") or [None])[0],
                "pcr": total_put_oi / total_call_oi if total_call_oi else None,
                "max_call_oi": max(calls, default=(0, None)),
                "max_put_oi": max(puts, default=(0, None)),
                "max_pain": calculate_max_pain(rows),
                "rows": rows,
            }
        except Exception as exc:
            print(f"Option snapshot error: {exc}")

        # Global markets.
        for name, symbol in GLOBAL_MARKETS.items():
            try:
                summary = summarize(download_symbol(symbol, "5d", "1d"))
                if summary:
                    result["global"][name] = summary
            except Exception as exc:
                print(f"Global market error {name}: {exc}")

        # Yahoo news is optional. Never let it break the market page.
        try:
            news = yf.Ticker("^NSEI").news or []
            for item in news[:6]:
                content = item.get("content", item)
                title = content.get("title") or item.get("title")
                if title:
                    provider = content.get("provider", {}).get("displayName", "Market feed")
                    result["news"].append({"title": title, "provider": provider})
        except Exception as exc:
            print(f"News feed unavailable: {exc}")

        return result


# ============================================================
# UI COMPONENTS
# ============================================================
class Card(QFrame):
    def __init__(self, title, icon="", accent=None, action=None):
        super().__init__()
        self.setObjectName("MarketCard")
        self.setStyleSheet(f"""
            QFrame#MarketCard {{
                background: rgba(18, 23, 31, 0.88);
                border: 1px solid {theme.BORDER_SOFT};
                border-radius: 12px;
            }}
            QFrame#MarketCard:hover {{ border: 1px solid rgba(120,140,170,0.28); }}
            QFrame#MarketCard QLabel {{ background: transparent; border: none; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 10)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(6)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color:{accent or theme.PRIMARY};font-size:11px;font-weight:800;")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color:{theme.TEXT};font-size:12px;font-weight:700;")
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        if action:
            btn = QPushButton(action)
            btn.setFixedHeight(23)
            btn.setStyleSheet(f"font-size:13px;padding:2px 8px;border-radius:7px;")
            header.addWidget(btn)
            self.action_button = btn
        layout.addLayout(header)
        self.body = QVBoxLayout()
        self.body.setSpacing(5)
        layout.addLayout(self.body)


class IndexCard(QFrame):
    clicked = Signal(str)

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.active = False
        self.setObjectName("IndexCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(1)
        self.name_label = QLabel(name)
        self.price_label = QLabel("--")
        self.change_label = QLabel("--")
        self.range_label = QLabel("H --   L --")
        layout.addWidget(self.name_label)
        layout.addWidget(self.price_label)
        layout.addWidget(self.change_label)
        layout.addWidget(self.range_label)
        self.apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.name)
        super().mousePressEvent(event)

    def set_active(self, active):
        self.active = active
        self.apply_style()

    def apply_style(self):
        border = "#3B82F6" if self.active else theme.BORDER_SOFT
        bg = "rgba(35, 70, 110, 0.20)" if self.active else "rgba(18,23,31,0.80)"
        self.setStyleSheet(f"""
            QFrame#IndexCard {{ background:{bg}; border:1px solid {border}; border-radius:11px; }}
            QFrame#IndexCard:hover {{ border:1px solid #3B82F6; }}
            QLabel {{ background:transparent; border:none; }}
        """)
        self.name_label.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:13px;font-weight:600;")
        self.price_label.setStyleSheet(f"color:{theme.TEXT};font-size:18px;font-weight:750;")
        self.range_label.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:12px;")

    def update_data(self, data):
        pct = data.get("change_pct")
        self.price_label.setText(price(data.get("price")))
        self.change_label.setText(f"{price(data.get('change'))}  ({percentage(pct)})")
        self.change_label.setStyleSheet(f"color:{movement_color(pct)};font-size:13px;font-weight:700;")
        self.range_label.setText(f"H {price(data.get('high'))}   L {price(data.get('low'))}")


class Metric(QFrame):
    def __init__(self, label, value="--"):
        super().__init__()
        self.setStyleSheet(f"QFrame{{background:rgba(255,255,255,0.025);border:1px solid {theme.BORDER_SOFT};border-radius:8px;}} QLabel{{background:transparent;border:none;}}")
        l = QVBoxLayout(self)
        l.setContentsMargins(9, 6, 9, 6)
        l.setSpacing(1)
        self.label = QLabel(label.upper())
        self.value = QLabel(value)
        self.label.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:11px;font-weight:650;")
        self.value.setStyleSheet(f"color:{theme.TEXT};font-size:14px;font-weight:750;")
        l.addWidget(self.label)
        l.addWidget(self.value)

    def set_value(self, text, color=None):
        self.value.setText(text)
        self.value.setStyleSheet(f"color:{color or theme.TEXT};font-size:14px;font-weight:750;")


class TableCard(Card):
    def __init__(self, title, icon, accent, rows=5):
        super().__init__(title, icon, accent)
        self.rows = rows
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(3)
        self.body.addLayout(self.grid)

    def set_data(self, data, columns):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for c, name in enumerate(columns):
            label = QLabel(name)
            label.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:10px;font-weight:750;")
            self.grid.addWidget(label, 0, c)
        for r, row in enumerate(data[:self.rows], 1):
            for c, text in enumerate(row):
                label = QLabel(str(text))
                label.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:13px;")
                if c == 0:
                    label.setStyleSheet(f"color:{theme.TEXT};font-size:13px;font-weight:700;")
                self.grid.addWidget(label, r, c)


# ============================================================
# MARKET PAGE
# ============================================================
class Market(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.market_data = {}
        self.selected_index = "NIFTY 50"
        self.setObjectName("MarketPage")
        self.setStyleSheet(f"""
            QWidget#MarketPage {{ background:{theme.BACKGROUND}; color:{theme.TEXT}; font-family:"{theme.FONT}"; }}
            QWidget#MarketPage QLabel {{ color:{theme.TEXT}; background:transparent; }}
            QWidget#MarketPage QPushButton {{
                background:rgba(255,255,255,0.035); color:{theme.TEXT_SECONDARY};
                border:1px solid {theme.BORDER_SOFT}; border-radius:7px; padding:3px 9px;
                font-size:13px; font-weight:650;
            }}
            QWidget#MarketPage QPushButton:hover {{ background:rgba(59,130,246,0.12); border:1px solid #3B82F6; color:{theme.TEXT}; }}
            QWidget#MarketPage QPushButton:checked {{ background:#2563EB; border:1px solid #3B82F6; color:white; }}
        """)
        self.build_ui()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(60_000)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()
        QTimer.singleShot(200, self.refresh)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(max(8, theme.CONTENT_MARGIN), 7, max(8, theme.CONTENT_MARGIN), 7)
        root.setSpacing(6)

        # Compact macOS-style header.
        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("Market")
        title.setStyleSheet(f"font-size:20px;font-weight:760;color:{theme.TEXT};")
        live = QLabel("● Live")
        live.setStyleSheet(f"color:{theme.GREEN};font-size:13px;font-weight:700;background:rgba(45,200,120,0.08);border:1px solid rgba(45,200,120,0.18);border-radius:8px;padding:3px 7px;")
        header.addWidget(title)
        header.addWidget(live)
        header.addStretch()
        self.status = QLabel("● Live market data")
        self.status.setStyleSheet(f"color:{theme.GREEN};font-size:12px;font-weight:650;")
        header.addWidget(self.status)
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setToolTip("Refresh market data")
        self.refresh_button.setFixedSize(28, 25)
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)
        root.addLayout(header)

        # Index strip.
        index_grid = QGridLayout()
        index_grid.setSpacing(6)
        self.index_cards = {}
        for col, name in enumerate(INDEXES):
            card = IndexCard(name)
            card.clicked.connect(self.select_index)
            self.index_cards[name] = card
            index_grid.addWidget(card, 0, col)
        self.vix_card = IndexCard("INDIA VIX")
        self.vix_card.setCursor(Qt.ArrowCursor)
        index_grid.addWidget(self.vix_card, 0, 4)
        self.index_cards[self.selected_index].set_active(True)
        root.addLayout(index_grid)

        # Pulse / levels / status.
        top = QGridLayout(); top.setSpacing(6)
        pulse = Card("Market Pulse", "⌁", theme.CYAN)
        metrics = QHBoxLayout(); metrics.setSpacing(5)
        self.metric_breadth = Metric("Breadth")
        self.metric_sentiment = Metric("Sentiment")
        self.metric_vix = Metric("India VIX")
        self.metric_range = Metric("Nifty Range")
        self.metric_pcr = Metric("PCR")
        for m in (self.metric_breadth, self.metric_sentiment, self.metric_vix, self.metric_range, self.metric_pcr):
            metrics.addWidget(m, 1)
        pulse.body.addLayout(metrics)
        top.addWidget(pulse, 0, 0, 1, 2)

        levels = Card("Key Levels ", "⌁", theme.CYAN)
        level_row = QHBoxLayout(); level_row.setSpacing(10)
        self.levels = {}
        for name in ("Resistance 2", "Resistance 1", "Pivot", "Support 1", "Support 2"):
            box = QVBoxLayout(); box.setSpacing(1)
            l = QLabel(name); v = QLabel("--")
            l.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:10px;")
            v.setStyleSheet(f"color:{theme.TEXT};font-size:13px;font-weight:750;")
            box.addWidget(l); box.addWidget(v); level_row.addLayout(box, 1)
            self.levels[name] = v
        levels.body.addLayout(level_row)
        top.addWidget(levels, 0, 2, 1, 3)

        status = Card("Market Status", "▥", theme.GREEN)
        self.status_grid = QGridLayout()
        self.status_grid.setVerticalSpacing(6)
        self.status_grid.setHorizontalSpacing(25)
        self.status_grid.setContentsMargins(10, 0, 10, 0)
        self.status_values = {}
        for r, name in enumerate(("Market", "Session", "Advance / Decline", "New 52W Highs", "New 52W Lows")):
            a = QLabel(name) 
            b = QLabel("--")
            a.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:13px;")
            b.setStyleSheet(f"color:{theme.TEXT};font-size:10px;font-weight:700;")
            self.status_grid.addWidget(a, r, 0) 
            self.status_grid.addWidget(b, r, 1, alignment=Qt.AlignRight)
            self.status_values[name] = b
        status.body.addLayout(self.status_grid)
        top.addWidget(status, 0, 5,1,1)
        root.addLayout(top)

        top.setColumnStretch(0, 1)
        top.setColumnStretch(1, 1)
        top.setColumnStretch(2, 1)
        top.setColumnStretch(3, 1)
        top.setColumnStretch(4, 1)
        top.setColumnStretch(5, 1)

        # Movers row: separate cards are much easier to scan than tabs.
        movers = QGridLayout(); movers.setSpacing(6)
        self.gainers_card = TableCard("Top Gainers", "↗", theme.GREEN)
        self.losers_card = TableCard("Top Losers", "↘", theme.RED)
        self.active_card = TableCard("Active by Volume", "▥", theme.PURPLE)
        movers.addWidget(self.gainers_card, 0, 0)
        movers.addWidget(self.losers_card, 0, 1)
        movers.addWidget(self.active_card, 0, 2)
        root.addLayout(movers)

        # Analytics row.
        analytics = QGridLayout(); analytics.setSpacing(6)
        self.breadth_card = Card("Market Breadth", "◒", theme.PURPLE)
        self.breadth_layout = QVBoxLayout(); self.breadth_layout.setSpacing(4)
        self.breadth_card.body.addLayout(self.breadth_layout)
        analytics.addWidget(self.breadth_card, 0, 0)

        self.volatility_card = Card("Volatility Watch", "◈", theme.CYAN)
        self.volatility_layout = QVBoxLayout(); self.volatility_layout.setSpacing(5)
        self.volatility_card.body.addLayout(self.volatility_layout)
        analytics.addWidget(self.volatility_card, 0, 1)

        self.options_card = Card("Option Chain Snapshot (NIFTY)", "⌁", theme.ORANGE, "View Option Chain")
        self.options_grid = QGridLayout(); self.options_grid.setHorizontalSpacing(8); self.options_grid.setVerticalSpacing(4)
        self.option_values = {}
        for c, field in enumerate(("Spot", "Expiry", "PCR", "Max Call OI", "Max Put OI", "Max Pain")):
            box = QVBoxLayout(); box.setSpacing(1)
            a = QLabel(field); b = QLabel("--")
            a.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:12px;")
            b.setStyleSheet(f"color:{theme.TEXT};font-size:10px;font-weight:750;")
            box.addWidget(a); box.addWidget(b); self.options_grid.addLayout(box, 0 if c < 3 else 1, c % 3)
            self.option_values[field] = b
        self.options_card.body.addLayout(self.options_grid)
        analytics.addWidget(self.options_card, 0, 2)

        self.active_options_card = TableCard("Most Active Options (NIFTY)", "⌁", theme.RED)
        analytics.addWidget(self.active_options_card, 0, 3)
        root.addLayout(analytics)

        # Bottom informational strip: useful without adding another chart.
        bottom = QGridLayout(); bottom.setSpacing(6)
        self.news_card = Card("Market News", "•", theme.GREEN)
        self.news_layout = QVBoxLayout(); self.news_layout.setSpacing(3)
        self.news_card.body.addLayout(self.news_layout)
        bottom.addWidget(self.news_card, 0, 0)

        calendar = Card("Economic Calendar", "▣", theme.CYAN)
        calendar.body.addWidget(QLabel("No economic-calendar feed is connected yet."))
        note = QLabel("Connect an economic data source to populate events, actuals and forecasts.")
        note.setWordWrap(True); note.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:12px;")
        calendar.body.addWidget(note)
        bottom.addWidget(calendar, 0, 1)

        self.global_card = Card("Global Market Overview", "▦", theme.PURPLE)
        self.global_layout = QHBoxLayout(); self.global_layout.setSpacing(5)
        self.global_card.body.addLayout(self.global_layout)
        bottom.addWidget(self.global_card, 0, 2)
        bottom.setColumnStretch(0, 1.15); bottom.setColumnStretch(1, 0.9); bottom.setColumnStretch(2, 1.45)
        root.addLayout(bottom)

        footer = QHBoxLayout(); footer.setContentsMargins(3, 0, 3, 0)
        self.footer = QLabel("Market • NIFTY 50 selected • Live market feed")
        self.footer.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:12px;")
        footer.addWidget(self.footer); footer.addStretch()
        root.addLayout(footer)

    def refresh(self):
        if self.worker and self.worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.status.setText("● Updating market data…")
        self.status.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:12px;font-weight:650;")
        self.worker = MarketWorker()
        self.worker.data_ready.connect(self.update_market)
        self.worker.error.connect(self.market_error)
        self.worker.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.worker.start()

    def market_error(self, message):
        print("Market page error:", message)
        self.status.setText("● Market data unavailable")
        self.status.setStyleSheet(f"color:{theme.RED};font-size:12px;font-weight:650;")

    def update_market(self, data):
        self.market_data = data
        self.update_indexes()
        self.update_top()
        self.update_movers()
        self.update_analytics()
        self.update_options()
        self.update_news()
        self.update_global()
        ts = data.get("updated")
        timestamp = ts.strftime("%H:%M:%S") if ts else "--"
        self.status.setText(f"● Live market data • {timestamp} IST")
        self.status.setStyleSheet(f"color:{theme.GREEN};font-size:12px;font-weight:650;")
        self.footer.setText(f"Market • {self.selected_index} selected • Live market feed")

    def update_indexes(self):
        indexes = self.market_data.get("indices", {})
        for name, card in self.index_cards.items():
            if name in INDEXES and indexes.get(name):
                card.update_data(indexes[name])
        vix = self.market_data.get("vix")
        if vix:
            self.vix_card.update_data(vix)

    def select_index(self, name):
        if name not in INDEXES:
            return
        self.selected_index = name
        for n, card in self.index_cards.items():
            if n in INDEXES:
                card.set_active(n == name)
        if self.market_data:
            self.update_top()

    def update_top(self):
        indexes = self.market_data.get("indices", {})
        stocks = self.market_data.get("stocks", {})
        nifty = indexes.get(self.selected_index, {})
        vix = self.market_data.get("vix", {})
        options = self.market_data.get("options", {})

        advances = sum(number(v.get("change_pct"), 0) > 0 for v in stocks.values())
        declines = sum(number(v.get("change_pct"), 0) < 0 for v in stocks.values())
        unchanged = max(0, len(stocks) - advances - declines)
        ratio = advances / declines if declines else float(advances)
        pcr = number(options.get("pcr"))
        nifty_pct = number(nifty.get("change_pct"), 0)
        sentiment = "Bullish" if nifty_pct > 0.15 else "Bearish" if nifty_pct < -0.15 else "Neutral"
        sentiment_color = theme.GREEN if sentiment == "Bullish" else theme.RED if sentiment == "Bearish" else theme.TEXT

        self.metric_breadth.set_value(f"{advances} ↑  {declines} ↓", theme.GREEN if advances >= declines else theme.RED)
        self.metric_sentiment.set_value(sentiment, sentiment_color)
        self.metric_vix.set_value(price(vix.get("price")), movement_color(vix.get("change_pct")))
        self.metric_range.set_value(f"{price(nifty.get('low'))} – {price(nifty.get('high'))}")
        pcr_text = "--" if pcr is None else f"{pcr:.2f}  {'Bullish' if pcr > 1.15 else 'Bearish' if pcr < 0.85 else 'Neutral'}"
        self.metric_pcr.set_value(pcr_text, theme.GREEN if pcr and pcr > 1.15 else theme.RED if pcr and pcr < 0.85 else theme.TEXT)

        high = number(nifty.get("high")); low = number(nifty.get("low")); previous = number(nifty.get("previous_close"))
        if None not in (high, low, previous):
            pivot = (high + low + previous) / 3
            vals = {
                "Resistance 2": pivot + high - low,
                "Resistance 1": 2 * pivot - low,
                "Pivot": pivot,
                "Support 1": 2 * pivot - high,
                "Support 2": pivot - high + low,
            }
            for key, val in vals.items():
                self.levels[key].setText(price(val))

        self.status_values["Market"].setText("OPEN")
        self.status_values["Market"].setStyleSheet(f"color:{theme.GREEN};font-size:10px;font-weight:700;")
        self.status_values["Session"].setText("Normal")
        self.status_values["Advance / Decline"].setText(f"{advances} / {declines}")
        self.status_values["New 52W Highs"].setText("--")
        self.status_values["New 52W Lows"].setText("--")

    def _table_rows(self, mode):
        stocks = list(self.market_data.get("stocks", {}).items())
        if mode == "gainers":
            stocks.sort(key=lambda x: number(x[1].get("change_pct"), -999), reverse=True)
        elif mode == "losers":
            stocks.sort(key=lambda x: number(x[1].get("change_pct"), 999))
        else:
            stocks.sort(key=lambda x: number(x[1].get("volume"), 0), reverse=True)
        return [(s, price(d.get("price")), percentage(d.get("change_pct")), volume(d.get("volume"))) for s, d in stocks[:5]]

    def update_movers(self):
        self.gainers_card.set_data(self._table_rows("gainers"), ("SYMBOL", "LTP", "CHG%", "VOLUME"))
        self.losers_card.set_data(self._table_rows("losers"), ("SYMBOL", "LTP", "CHG%", "VOLUME"))
        self.active_card.set_data(self._table_rows("active"), ("SYMBOL", "LTP", "CHG%", "VOLUME"))

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def update_analytics(self):
        stocks = self.market_data.get("stocks", {})
        advances = sum(number(v.get("change_pct"), 0) > 0 for v in stocks.values())
        declines = sum(number(v.get("change_pct"), 0) < 0 for v in stocks.values())
        unchanged = max(0, len(stocks) - advances - declines)
        total = max(1, len(stocks))
        self.clear_layout(self.breadth_layout)
        for label, value, color in (("Advances", advances, theme.GREEN), ("Declines", declines, theme.RED), ("Unchanged", unchanged, theme.TEXT_MUTED)):
            row = QHBoxLayout(); a = QLabel(label); b = QLabel(f"{value}  ({value / total * 100:.1f}%)")
            a.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:12px;"); b.setStyleSheet(f"color:{color};font-size:10px;font-weight:700;")
            row.addWidget(a); row.addStretch(); row.addWidget(b); self.breadth_layout.addLayout(row)
        bar = QLabel(f"{advances}  /  {declines}")
        bar.setAlignment(Qt.AlignCenter); bar.setStyleSheet(f"color:{theme.TEXT};font-size:16px;font-weight:800;padding:7px;background:rgba(255,255,255,0.025);border-radius:8px;")
        self.breadth_layout.addWidget(bar)

        self.clear_layout(self.volatility_layout)
        vix = self.market_data.get("vix", {})
        nifty = self.market_data.get("indices", {}).get("NIFTY 50", {})
        bank = self.market_data.get("indices", {}).get("BANK NIFTY", {})
        rows = [("INDIA VIX", price(vix.get("price")), percentage(vix.get("change_pct"))),
                ("NIFTY IV", "--", "Connect option IV feed"),
                ("BANK NIFTY", percentage(bank.get("change_pct")), "5m move"),
                ("NIFTY 50", percentage(nifty.get("change_pct")), "session move")]
        for name, value, note in rows:
            row = QHBoxLayout(); a = QLabel(name); b = QLabel(value); c = QLabel(note)
            a.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:12px;"); b.setStyleSheet(f"color:{movement_color(nifty.get('change_pct') if name=='NIFTY 50' else vix.get('change_pct') if name=='INDIA VIX' else bank.get('change_pct'))};font-size:13px;font-weight:700;"); c.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:10px;")
            row.addWidget(a); row.addStretch(); row.addWidget(b); row.addWidget(c); self.volatility_layout.addLayout(row)

        # Most-active options from the real option chain.
        rows = []
        for item in self.market_data.get("options", {}).get("rows", []):
            ce = item.get("CE") or {}; pe = item.get("PE") or {}; strike = item.get("strikePrice")
            for kind, side in (("CE", ce), ("PE", pe)):
                oi = number(side.get("openInterest"), 0); vol = number(side.get("totalTradedVolume"), 0)
                ltp = number(side.get("lastPrice")); pct = number(side.get("pChange"))
                rows.append((oi + vol, kind, strike, ltp, pct, oi))
        rows.sort(reverse=True, key=lambda x: x[0])
        table = [(r[1], price(r[2]), price(r[3]), percentage(r[4]), volume(r[5])) for r in rows[:5]]
        self.active_options_card.set_data(table, ("TYPE", "STRIKE", "LTP", "CHG%", "OI"))

    def update_options(self):
        options = self.market_data.get("options", {})
        if not options:
            for label in self.option_values.values():
                label.setText("--")
            return
        pcr = number(options.get("pcr"))
        call = options.get("max_call_oi", (0, None)); put = options.get("max_put_oi", (0, None))
        self.option_values["Spot"].setText(price(options.get("spot")))
        self.option_values["Expiry"].setText(str(options.get("expiry") or "--"))
        self.option_values["PCR"].setText(f"{pcr:.2f}" if pcr is not None else "--")
        self.option_values["Max Call OI"].setText(f"{call[1] or '--'} ({volume(call[0])})")
        self.option_values["Max Put OI"].setText(f"{put[1] or '--'} ({volume(put[0])})")
        self.option_values["Max Pain"].setText(price(options.get("max_pain")))
        if pcr is not None:
            color = theme.GREEN if pcr > 1.15 else theme.RED if pcr < 0.85 else theme.TEXT
            self.option_values["PCR"].setStyleSheet(f"color:{color};font-size:11px;font-weight:750;")

    def update_news(self):
        self.clear_layout(self.news_layout)
        news = self.market_data.get("news", [])
        if not news:
            label = QLabel("Live market news feed unavailable.")
            label.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:10px;")
            self.news_layout.addWidget(label)
            return
        for item in news[:5]:
            row = QHBoxLayout(); dot = QLabel("•"); title = QLabel(item.get("title", ""))
            dot.setStyleSheet(f"color:{theme.GREEN};font-size:10px;"); title.setStyleSheet(f"color:{theme.TEXT_SECONDARY};font-size:12px;")
            title.setWordWrap(False); row.addWidget(dot); row.addWidget(title, 1); self.news_layout.addLayout(row)

    def update_global(self):
        self.clear_layout(self.global_layout)
        for name, data in self.market_data.get("global", {}).items():
            card = QFrame(); card.setStyleSheet(f"QFrame{{background:rgba(255,255,255,0.025);border:1px solid {theme.BORDER_SOFT};border-radius:8px;}}")
            l = QVBoxLayout(card); l.setContentsMargins(7, 6, 7, 6); l.setSpacing(1)
            a = QLabel(name); b = QLabel(price(data.get("price"))); c = QLabel(percentage(data.get("change_pct")))
            a.setStyleSheet(f"color:{theme.TEXT_MUTED};font-size:10px;"); b.setStyleSheet(f"color:{theme.TEXT};font-size:10px;font-weight:750;"); c.setStyleSheet(f"color:{movement_color(data.get('change_pct'))};font-size:12px;font-weight:700;")
            l.addWidget(a); l.addWidget(b); l.addWidget(c); self.global_layout.addWidget(card, 1)

    def closeEvent(self, event):
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(1500)
        event.accept()


MarketPage = Market