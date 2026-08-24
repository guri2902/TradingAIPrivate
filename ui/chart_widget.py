from datetime import datetime

import numpy as np
import pandas as pd
import pyqtgraph as pg

from PySide6.QtCore import QPointF, QRectF, Signal, Qt
from PySide6.QtGui import QPainter, QPicture
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)


# ================================================================
# TIME AXIS
# ================================================================

class TimeAxis(pg.AxisItem):

    def __init__(self, orientation="bottom"):
        super().__init__(orientation=orientation)

        self.timestamps = []
        self.timeframe = "5m"

    # ------------------------------------------------------------
    # TIMEFRAME
    # ------------------------------------------------------------

    def set_timeframe(self, timeframe):

        self.timeframe = str(timeframe)

        self.picture = None
        self.update()

    # ------------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------------

    def set_timestamps(self, timestamps):

        self.timestamps = list(timestamps or [])

        self.picture = None
        self.update()

    # ------------------------------------------------------------
    # NORMALIZE TIMESTAMP
    # ------------------------------------------------------------

    def _convert_timestamp(self, timestamp):

        try:

            if timestamp is None:
                return None

            # ----------------------------------------------------
            # Numeric Unix timestamps
            # ----------------------------------------------------

            if isinstance(
                timestamp,
                (int, float, np.integer, np.floating)
            ):

                value = float(timestamp)

                if not np.isfinite(value):
                    return None

                # milliseconds
                if abs(value) > 1e11:

                    dt = pd.to_datetime(
                        value,
                        unit="ms",
                        utc=True,
                    )

                # seconds
                elif abs(value) > 1e9:

                    dt = pd.to_datetime(
                        value,
                        unit="s",
                        utc=True,
                    )

                else:

                    dt = pd.to_datetime(
                        value,
                        unit="s",
                        utc=True,
                    )

            else:

                dt = pd.to_datetime(
                    timestamp,
                    errors="coerce",
                )

            if pd.isna(dt):
                return None

            # ----------------------------------------------------
            # Convert everything to India time
            # ----------------------------------------------------

            if getattr(dt, "tzinfo", None) is not None:

                dt = dt.tz_convert(
                    "Asia/Kolkata"
                )

            else:

                # Yahoo normally gives timezone-aware values.
                # If a source gives naive timestamps, treat them
                # as India market time.
                dt = dt.tz_localize(
                    "Asia/Kolkata"
                )

            return dt

        except Exception:

            return None

    # ------------------------------------------------------------
    # TICK STRINGS
    # ------------------------------------------------------------

    def tickStrings(
        self,
        values,
        scale,
        spacing,
    ):

        if not self.timestamps:

            return [
                str(int(round(value)))
                for value in values
            ]

        converted = []

        for timestamp in self.timestamps:

            converted.append(
                self._convert_timestamp(
                    timestamp
                )
            )

        valid_dates = [
            value.date()
            for value in converted
            if value is not None
        ]

        # --------------------------------------------------------
        # Determine whether the visible dataset contains
        # multiple trading dates.
        # --------------------------------------------------------

        multiple_days = (
            len(set(valid_dates)) > 1
            if valid_dates
            else False
        )

        result = []

        count = len(converted)

        for value in values:

            try:

                index = int(
                    round(float(value))
                )

            except Exception:

                result.append("")
                continue

            if index < 0 or index >= count:

                result.append("")
                continue

            dt = converted[index]

            if dt is None:

                result.append("")
                continue

            # ====================================================
            # DAILY
            # ====================================================

            if self.timeframe in (
                "1D",
                "1d",
            ):

                result.append(
                    dt.strftime("%d %b")
                )

                continue

            # ====================================================
            # INTRADAY
            # ====================================================

            if multiple_days:

                # Example:
                # 11 Aug 09:15
                result.append(
                    dt.strftime(
                        "%d %b %H:%M"
                    )
                )

            else:

                # Example:
                # 09:15
                result.append(
                    dt.strftime(
                        "%H:%M"
                    )
                )

        return result


# ================================================================
# CANDLESTICK ITEM
# ================================================================

class CandlestickItem(pg.GraphicsObject):

    def __init__(self):

        super().__init__()

        self.data = []
        self.picture = None

        self.width = 0.30

    # ------------------------------------------------------------

    def set_data(
        self,
        data,
        width=None,
    ):

        self.data = list(
            data or []
        )

        if width is not None:

            self.width = max(
                0.05,
                min(
                    0.48,
                    float(width),
                ),
            )

        self.picture = None

        self.prepareGeometryChange()

        self.update()

    # ------------------------------------------------------------

    def generate_picture(self):

        picture = QPicture()

        painter = QPainter(
            picture
        )

        if not self.data:

            painter.end()

            return picture

        width = self.width

        for candle in self.data:

            try:

                x = float(
                    candle["x"]
                )

                open_price = float(
                    candle["open"]
                )

                high_price = float(
                    candle["high"]
                )

                low_price = float(
                    candle["low"]
                )

                close_price = float(
                    candle["close"]
                )

                values = [
                    x,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                ]

                if not all(
                    np.isfinite(value)
                    for value in values
                ):
                    continue

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                continue

            # ====================================================
            # COLOR
            # ====================================================

            if close_price >= open_price:

                painter.setPen(
                    pg.mkPen(
                        "#25d17d",
                        width=1,
                    )
                )

                painter.setBrush(
                    pg.mkBrush(
                        "#25d17d"
                    )
                )

            else:

                painter.setPen(
                    pg.mkPen(
                        "#ff4d5a",
                        width=1,
                    )
                )

                painter.setBrush(
                    pg.mkBrush(
                        "#ff4d5a"
                    )
                )

            # ====================================================
            # WICK
            # ====================================================

            painter.drawLine(
                QPointF(
                    x,
                    low_price,
                ),
                QPointF(
                    x,
                    high_price,
                ),
            )

            # ====================================================
            # BODY
            # ====================================================

            body_low = min(
                open_price,
                close_price,
            )

            body_high = max(
                open_price,
                close_price,
            )

            # Prevent invisible candle
            if abs(
                body_high - body_low
            ) < 0.01:

                body_high += 0.005
                body_low -= 0.005

            painter.drawRect(
                QRectF(
                    x - width,
                    body_low,
                    width * 2,
                    body_high - body_low,
                )
            )

        painter.end()

        return picture

    # ------------------------------------------------------------

    def paint(
        self,
        painter,
        option,
        widget=None,
    ):

        if self.picture is None:

            self.picture = (
                self.generate_picture()
            )

        painter.drawPicture(
            0,
            0,
            self.picture,
        )

    # ------------------------------------------------------------

    def boundingRect(self):

        if not self.data:

            return QRectF()

        valid = []

        for candle in self.data:

            try:

                valid.append(
                    (
                        float(
                            candle["x"]
                        ),
                        float(
                            candle["low"]
                        ),
                        float(
                            candle["high"]
                        ),
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                continue

        if not valid:

            return QRectF()

        xs = [
            value[0]
            for value in valid
        ]

        lows = [
            value[1]
            for value in valid
        ]

        highs = [
            value[2]
            for value in valid
        ]

        return QRectF(
            min(xs) - 1,
            min(lows),
            max(xs) - min(xs) + 2,
            max(highs) - min(lows),
        )


# ================================================================
# CHART WIDGET
# ================================================================

class ChartWidget(QWidget):

    # Dashboard / MarketWorker listens to this.
    timeframe_changed = Signal(str)

    def __init__(self):

        super().__init__()

        self.setMinimumHeight(
            250
        )

        # ========================================================
        # STATE
        # ========================================================

        self.candles = []

        self.timestamps = []

        self.user_moved = False

        self.initialized = False

        self.programmatic_range = False

        self.max_visible_candles = 100

        self.current_timeframe = "5m"

        # ========================================================
        # LAYOUT
        # ========================================================

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(0)

        # ========================================================
        # TIME AXIS
        # ========================================================

        self.axis = TimeAxis(
            "bottom"
        )

        self.axis.set_timeframe(
            self.current_timeframe
        )

        # ========================================================
        # TIMEFRAME BAR
        # ========================================================

        timeframe_layout = QHBoxLayout()

        timeframe_layout.setContentsMargins(
            8,
            4,
            8,
            4,
        )

        timeframe_layout.setSpacing(4)

        timeframe_label = QLabel(
            "TIMEFRAME"
        )

        timeframe_label.setStyleSheet("""
            QLabel {
                color: #7f8b99;
                font-size: 10px;
                font-weight: 600;
            }
        """)

        timeframe_layout.addWidget(
            timeframe_label
        )

        timeframe_layout.addSpacing(
            6
        )

        self.timeframe_buttons = {}

        for timeframe in [
            "1m",
            "5m",
            "15m",
            "30m",
            "1H",
            "1D",
        ]:

            button = QPushButton(
                timeframe
            )

            button.setFixedHeight(
                24
            )

            button.setMinimumWidth(
                38
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.clicked.connect(
                lambda checked=False,
                tf=timeframe:
                self._timeframe_clicked(
                    tf
                )
            )

            self.timeframe_buttons[
                timeframe
            ] = button

            timeframe_layout.addWidget(
                button
            )

        timeframe_layout.addStretch()

        layout.addLayout(
            timeframe_layout
        )

        self._update_timeframe_buttons()

        # ========================================================
        # GRAPH
        # ========================================================

        self.graph = pg.PlotWidget(
            axisItems={
                "bottom": self.axis
            }
        )

        self.graph.setBackground(
            "#20262f"
        )

        self.graph.showGrid(
            x=True,
            y=True,
            alpha=0.15,
        )

        self.graph.setMenuEnabled(
            False
        )

        self.graph.setMouseEnabled(
            x=True,
            y=True,
        )

        self.graph.getPlotItem().hideButtons()

        # ========================================================
        # AXIS COLORS
        # ========================================================

        left_axis = (
            self.graph
            .getPlotItem()
            .getAxis("left")
        )

        bottom_axis = (
            self.graph
            .getPlotItem()
            .getAxis("bottom")
        )

        left_axis.setTextPen(
            pg.mkPen(
                "#c9d1d9"
            )
        )

        bottom_axis.setTextPen(
            pg.mkPen(
                "#c9d1d9"
            )
        )

        # ========================================================
        # CANDLE ITEM
        # ========================================================

        self.candle_item = (
            CandlestickItem()
        )

        self.graph.addItem(
            self.candle_item
        )

        # ========================================================
        # EMA 20
        # ========================================================

        self.ema20_line = (
            self.graph.plot(
                [],
                [],
                pen=pg.mkPen(
                    "#27c7ff",
                    width=1.5,
                ),
            )
        )

        # ========================================================
        # EMA 50
        # ========================================================

        self.ema50_line = (
            self.graph.plot(
                [],
                [],
                pen=pg.mkPen(
                    "#ffd84d",
                    width=1.5,
                ),
            )
        )

        # ========================================================
        # EMA 200
        # ========================================================

        self.ema200_line = (
            self.graph.plot(
                [],
                [],
                pen=pg.mkPen(
                    "#ff5555",
                    width=1.5,
                ),
            )
        )

        layout.addWidget(
            self.graph
        )

        # ========================================================
        # RANGE CHANGE
        # ========================================================

        # Do NOT use sigRangeChangedManually.
        #
        # Different pyqtgraph versions expose different
        # signatures for that signal.
        #
        # sigXRangeChanged is stable.

        self.graph \
            .getViewBox() \
            .sigXRangeChanged \
            .connect(
                self._x_range_changed
            )

    # ============================================================
    # TIMEFRAME CLICK
    # ============================================================

    def _timeframe_clicked(
        self,
        timeframe,
    ):

        if (
            timeframe
            == self.current_timeframe
        ):
            return

        print(
            "Chart timeframe changed:",
            self.current_timeframe,
            "->",
            timeframe,
        )

        self.current_timeframe = (
            timeframe
        )

        # Tell axis how to format timestamps.
        self.axis.set_timeframe(
            timeframe
        )

        # New timeframe should begin
        # at latest candles.
        self.user_moved = False

        # Update selected button.
        self._update_timeframe_buttons()

        # Clear old timeframe while
        # waiting for new data.
        self.clear()

        # Dashboard / MarketWorker handles
        # fetching the new timeframe.
        self.timeframe_changed.emit(
            timeframe
        )

    # ============================================================
    # TIMEFRAME BUTTON STYLE
    # ============================================================

    def _update_timeframe_buttons(
        self,
    ):

        for (
            timeframe,
            button,
        ) in self.timeframe_buttons.items():

            if (
                timeframe
                == self.current_timeframe
            ):

                button.setStyleSheet("""
                    QPushButton {
                        background: #2a9dff;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 2px 8px;
                        font-size: 11px;
                        font-weight: 600;
                    }

                    QPushButton:hover {
                        background: #3aa8ff;
                    }
                """)

            else:

                button.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #8f9baa;
                        border: 1px solid #303843;
                        border-radius: 5px;
                        padding: 2px 8px;
                        font-size: 11px;
                        font-weight: 500;
                    }

                    QPushButton:hover {
                        background: #252c35;
                        color: white;
                        border: 1px solid #46515f;
                    }
                """)

    # ============================================================
    # PUBLIC API
    # ============================================================

    def plot_data(
        self,
        data,
    ):

        """
        Compatibility method.

        Dashboard can use:

            chart.plot_data(data)
        """

        self.set_data(
            data
        )

    # ------------------------------------------------------------

    def update_chart(
        self,
        data,
    ):

        self.set_data(
            data
        )

    # ------------------------------------------------------------

    def set_timeframe(
        self,
        timeframe,
    ):

        """
        Allows Dashboard to update the chart timeframe
        programmatically.
        """

        timeframe = str(
            timeframe
        )

        if timeframe not in (
            "1m",
            "5m",
            "15m",
            "30m",
            "1H",
            "1D",
        ):

            return

        self.current_timeframe = (
            timeframe
        )

        self.axis.set_timeframe(
            timeframe
        )

        self._update_timeframe_buttons()

    # ============================================================
    # SET DATA
    # ============================================================

    def set_data(
        self,
        data,
    ):

        if data is None:
            return

        try:

            timestamps = None

            payload = data

            # ====================================================
            # MARKET WORKER FORMAT
            # ====================================================

            if (
                isinstance(
                    data,
                    dict,
                )
                and "candles" in data
            ):

                payload = data.get(
                    "candles",
                    [],
                )

                timestamps = data.get(
                    "timestamps",
                    [],
                )

            # ====================================================
            # NORMALIZE
            # ====================================================

            rows = self._normalize_rows(
                payload
            )

            if not rows:
                return

            self.timestamps = (
                self._normalize_timestamps(
                    timestamps,
                    len(rows),
                )
            )

            self._update_chart(
                rows
            )

        except Exception as e:

            print(
                "ChartWidget set_data error:",
                e,
            )

    # ============================================================
    # NORMALIZE ROWS
    # ============================================================

    def _normalize_rows(
        self,
        data,
    ):

        if data is None:
            return []

        # ========================================================
        # DATAFRAME
        # ========================================================

        if hasattr(
            data,
            "columns",
        ):

            columns = {
                str(column).lower(): column
                for column in data.columns
            }

            required = [
                "open",
                "high",
                "low",
                "close",
            ]

            if not all(
                value in columns
                for value in required
            ):

                print(
                    "ChartWidget: missing OHLC columns:",
                    data.columns.tolist(),
                )

                return []

            rows = []

            for i, (
                _,
                row,
            ) in enumerate(
                data.iterrows()
            ):

                try:

                    rows.append(
                        {
                            "x": float(i),

                            "open": float(
                                row[
                                    columns[
                                        "open"
                                    ]
                                ]
                            ),

                            "high": float(
                                row[
                                    columns[
                                        "high"
                                    ]
                                ]
                            ),

                            "low": float(
                                row[
                                    columns[
                                        "low"
                                    ]
                                ]
                            ),

                            "close": float(
                                row[
                                    columns[
                                        "close"
                                    ]
                                ]
                            ),
                        }
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

            return rows

        # ========================================================
        # LIST / TUPLE
        # ========================================================

        if not isinstance(
            data,
            (list, tuple),
        ):

            return []

        if not data:
            return []

        first = data[0]

        rows = []

        # ========================================================
        # DICT CANDLES
        # ========================================================

        if isinstance(
            first,
            dict,
        ):

            for i, candle in enumerate(
                data
            ):

                try:

                    open_value = candle.get(
                        "open",
                        candle.get(
                            "Open"
                        ),
                    )

                    high_value = candle.get(
                        "high",
                        candle.get(
                            "High"
                        ),
                    )

                    low_value = candle.get(
                        "low",
                        candle.get(
                            "Low"
                        ),
                    )

                    close_value = candle.get(
                        "close",
                        candle.get(
                            "Close"
                        ),
                    )

                    if (
                        open_value is None
                        or high_value is None
                        or low_value is None
                        or close_value is None
                    ):

                        continue

                    rows.append(
                        {
                            "x": float(
                                candle.get(
                                    "x",
                                    i,
                                )
                            ),

                            "open": float(
                                open_value
                            ),

                            "high": float(
                                high_value
                            ),

                            "low": float(
                                low_value
                            ),

                            "close": float(
                                close_value
                            ),
                        }
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

            return rows

        # ========================================================
        # OHLC TUPLES
        # ========================================================

        if isinstance(
            first,
            (list, tuple),
        ):

            for i, candle in enumerate(
                data
            ):

                if len(candle) < 4:
                    continue

                try:

                    rows.append(
                        {
                            "x": float(i),

                            "open": float(
                                candle[0]
                            ),

                            "high": float(
                                candle[1]
                            ),

                            "low": float(
                                candle[2]
                            ),

                            "close": float(
                                candle[3]
                            ),
                        }
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

            return rows

        # ========================================================
        # CLOSE ONLY FALLBACK
        # ========================================================

        if isinstance(
            first,
            (
                int,
                float,
                np.number,
            ),
        ):

            previous = None

            for i, value in enumerate(
                data
            ):

                try:

                    close = float(
                        value
                    )

                    if not np.isfinite(
                        close
                    ):

                        continue

                    if previous is None:

                        open_price = close

                    else:

                        open_price = previous

                    rows.append(
                        {
                            "x": float(i),

                            "open": open_price,

                            "high": max(
                                open_price,
                                close,
                            ),

                            "low": min(
                                open_price,
                                close,
                            ),

                            "close": close,
                        }
                    )

                    previous = close

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

        return rows

    # ============================================================
    # NORMALIZE TIMESTAMPS
    # ============================================================

    def _normalize_timestamps(
        self,
        timestamps,
        count,
    ):

        if timestamps is None:

            return [
                None
                for _ in range(count)
            ]

        values = list(
            timestamps
        )

        if len(values) < count:

            values.extend(
                [
                    None
                    for _ in range(
                        count
                        - len(values)
                    )
                ]
            )

        return values[:count]

    # ============================================================
    # UPDATE CHART
    # ============================================================

    def _update_chart(
        self,
        rows,
    ):

        clean = []

        for candle in rows:

            try:

                x = float(
                    candle["x"]
                )

                o = float(
                    candle["open"]
                )

                h = float(
                    candle["high"]
                )

                l = float(
                    candle["low"]
                )

                c = float(
                    candle["close"]
                )

                values = [
                    x,
                    o,
                    h,
                    l,
                    c,
                ]

                if not all(
                    np.isfinite(value)
                    for value in values
                ):

                    continue

                clean.append(
                    {
                        "x": x,

                        "open": o,

                        "high": max(
                            h,
                            o,
                            c,
                        ),

                        "low": min(
                            l,
                            o,
                            c,
                        ),

                        "close": c,
                    }
                )

            except Exception:

                continue

        if not clean:
            return

        self.candles = clean

        # ========================================================
        # TIMESTAMP AXIS
        # ========================================================

        self.axis.set_timestamps(
            self.timestamps
        )

        # ========================================================
        # CANDLE WIDTH
        # ========================================================

        self._refresh_candle_width()

        self.candle_item.set_data(
            clean,
            self.candle_item.width,
        )

        # ========================================================
        # EMA
        # ========================================================

        closes = np.asarray(
            [
                candle["close"]
                for candle in clean
            ],
            dtype=float,
        )

        x = np.asarray(
            [
                candle["x"]
                for candle in clean
            ],
            dtype=float,
        )

        self.ema20_line.setData(
            x,
            self._ema(
                closes,
                20,
            ),
        )

        self.ema50_line.setData(
            x,
            self._ema(
                closes,
                50,
            ),
        )

        self.ema200_line.setData(
            x,
            self._ema(
                closes,
                200,
            ),
        )

        # ========================================================
        # INITIAL LOAD
        # ========================================================

        if not self.initialized:

            self.initialized = True

            self._show_latest()

        # ========================================================
        # LIVE UPDATE
        # ========================================================

        elif not self.user_moved:

            self._show_latest()

        else:

            self._refresh_candle_width()

            self._fit_visible_y()

    # ============================================================
    # EMA
    # ============================================================

    def _ema(
        self,
        values,
        period,
    ):

        if len(values) == 0:

            return np.array([])

        alpha = (
            2.0
            / (
                period
                + 1.0
            )
        )

        result = np.empty(
            len(values),
            dtype=float,
        )

        result[0] = values[0]

        for i in range(
            1,
            len(values),
        ):

            result[i] = (
                alpha * values[i]
                + (
                    1.0 - alpha
                )
                * result[i - 1]
            )

        return result

    # ============================================================
    # DYNAMIC CANDLE WIDTH
    # ============================================================

    def _refresh_candle_width(
        self,
    ):

        if not self.candles:
            return

        try:

            x_min, x_max = (
                self.graph
                .getViewBox()
                .viewRange()[0]
            )

            span = max(
                1.0,
                float(
                    x_max - x_min
                ),
            )

            pixel_width = max(
                300.0,
                float(
                    self.graph
                    .viewport()
                    .width()
                ),
            )

            units_per_pixel = (
                span
                / pixel_width
            )

            desired_pixel_width = 7.0

            width = (
                desired_pixel_width
                * units_per_pixel
                / 2.0
            )

            width = max(
                0.08,
                min(
                    0.42,
                    width,
                ),
            )

            if abs(
                width
                - self.candle_item.width
            ) > 0.01:

                self.candle_item.set_data(
                    self.candles,
                    width,
                )

        except Exception:

            pass

    # ============================================================
    # X RANGE CHANGED
    # ============================================================

    def _x_range_changed(
        self,
        view_box,
        range_value,
    ):

        if not self.candles:
            return

        self._refresh_candle_width()

        if (
            self.programmatic_range
            or not self.initialized
        ):

            return

        # User manually zoomed/panned.
        self.user_moved = True

        self._fit_visible_y()

    # ============================================================
    # FIT Y AXIS TO VISIBLE CANDLES
    # ============================================================

    def _fit_visible_y(
        self,
    ):

        if not self.candles:
            return

        try:

            x_min, x_max = (
                self.graph
                .getViewBox()
                .viewRange()[0]
            )

            visible = [
                candle
                for candle in self.candles
                if (
                    x_min
                    <= candle["x"]
                    <= x_max
                )
            ]

            if not visible:
                return

            low = min(
                candle["low"]
                for candle in visible
            )

            high = max(
                candle["high"]
                for candle in visible
            )

            spread = high - low

            if spread <= 0:

                spread = max(
                    abs(high) * 0.001,
                    1.0,
                )

            padding = (
                spread * 0.12
            )

            self.programmatic_range = True

            self.graph.setYRange(
                low - padding,
                high + padding,
                padding=0,
            )

        except Exception:

            pass

        finally:

            self.programmatic_range = False

    # ============================================================
    # SHOW LATEST
    # ============================================================

    def _show_latest(
        self,
    ):

        if not self.candles:
            return

        total = len(
            self.candles
        )

        visible = min(
            self.max_visible_candles,
            total,
        )

        start = max(
            0,
            total - visible,
        )

        end = total

        self.programmatic_range = True

        try:

            # ----------------------------------------------------
            # X RANGE
            # ----------------------------------------------------

            self.graph.setXRange(
                start - 2,
                end + 2,
                padding=0,
            )

            # ----------------------------------------------------
            # Y RANGE
            # ----------------------------------------------------

            visible_candles = (
                self.candles[
                    start:end
                ]
            )

            low = min(
                candle["low"]
                for candle
                in visible_candles
            )

            high = max(
                candle["high"]
                for candle
                in visible_candles
            )

            spread = (
                high - low
            )

            if spread <= 0:

                spread = max(
                    abs(high) * 0.001,
                    1.0,
                )

            padding = (
                spread * 0.12
            )

            self.graph.setYRange(
                low - padding,
                high + padding,
                padding=0,
            )

        finally:

            self.programmatic_range = False

        self._refresh_candle_width()

    # ============================================================
    # RESET TO LIVE
    # ============================================================

    def reset_to_live(
        self,
    ):

        self.user_moved = False

        self._show_latest()

    # ============================================================
    # CLEAR
    # ============================================================

    def clear(
        self,
    ):

        self.candles = []

        self.timestamps = []

        self.candle_item.set_data(
            []
        )

        self.ema20_line.setData(
            [],
            [],
        )

        self.ema50_line.setData(
            [],
            [],
        )

        self.ema200_line.setData(
            [],
            [],
        )

        self.axis.set_timestamps(
            []
        )

        self.initialized = False

        self.programmatic_range = True

        try:

            self.graph.enableAutoRange()

        finally:

            self.programmatic_range = False