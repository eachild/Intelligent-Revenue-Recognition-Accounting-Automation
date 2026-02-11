# No new dependencies; uses numpy/pandas already in your requirements
# backend/app/services/forecast.py
from __future__ import annotations
from typing import Dict, List, Literal, Tuple
import pandas as pd
import numpy as np

# Type alias for forecasting methods
Method = Literal["exp_smooth", "seasonal_ma"]

# Helper to convert history dict to pandas Series
def _to_series(history: Dict[str, float]) -> pd.Series:
    s = pd.Series(history, dtype=float)
    s.index = pd.to_datetime(s.index)  # keys like "2024-01"
    s = s.sort_index()
    return s

# Exponential smoothing forecast
def exp_smoothing_forecast(history: Dict[str, float], horizon: int, alpha: float = 0.35) -> Dict:
    """
    Simple single-parameter exponential smoothing.
    """
    s = _to_series(history)
    if len(s) == 0:
        return {"forecast": {}, "fitted": {}}

    fitted = []
    level = s.iloc[0]
    for x in s:
        level = alpha * x + (1 - alpha) * level
        fitted.append(level)
    fitted_series = pd.Series(fitted, index=s.index)

    # Forecast = last level repeated
    last = level
    freq = pd.infer_freq(s.index) or "MS"
    future_idx = pd.date_range(s.index[-1] + pd.tseries.frequencies.to_offset(freq), periods=horizon, freq=freq)
    forecast_vals = [last for _ in range(horizon)]
    fc = pd.Series(forecast_vals, index=future_idx)

    return {
        "method": "exp_smooth",
        "params": {"alpha": alpha},
        "fitted": {d.strftime("%Y-%m"): float(v) for d, v in fitted_series.items()},
        "forecast": {d.strftime("%Y-%m"): float(v) for d, v in fc.items()},
    }

# Seasonal moving average forecast
def seasonal_moving_average(history: Dict[str, float], horizon: int, season: int = 12) -> Dict:
    """
    Seasonal moving average: average by month-of-year (or period-of-season).
    """
    s = _to_series(history)
    if len(s) < season:
        # fall back to simple mean if not enough history
        mean = float(s.mean()) if len(s) else 0.0
        freq = pd.infer_freq(s.index) or "MS"
        future_idx = pd.date_range(s.index[-1] + pd.tseries.frequencies.to_offset(freq), periods=horizon, freq=freq)
        fc = pd.Series([mean]*horizon, index=future_idx)
        return {
            "method": "seasonal_ma",
            "params": {"season": season},
            "fitted": {},
            "forecast": {d.strftime("%Y-%m"): float(v) for d, v in fc.items()},
        }

    # Compute seasonality by month (0..season-1)
    df = s.to_frame("y")
    df["k"] = np.arange(len(df)) % season
    seasonal_avg = df.groupby("k")["y"].mean()

    # Forecast by cycling seasonal averages
    freq = pd.infer_freq(s.index) or "MS"
    future_idx = pd.date_range(s.index[-1] + pd.tseries.frequencies.to_offset(freq), periods=horizon, freq=freq)
    fvals = []
    start_k = (len(s)) % season
    for i in range(horizon):
        k = (start_k + i) % season
        fvals.append(float(seasonal_avg[k]))
    fc = pd.Series(fvals, index=future_idx)

    return {
        "method": "seasonal_ma",
        "params": {"season": season},
        "fitted": {},  # optional (not needed)
        "forecast": {d.strftime("%Y-%m"): float(v) for d, v in fc.items()},
    }

# Main dispatch function for forecasting
def forecast_revenue(
    history: Dict[str, float],
    horizon: int = 12,
    method: Method = "exp_smooth",
    **kwargs
) -> Dict:
    """
    Dispatch forecaster; history keys = ISO months 'YYYY-MM' (recognized revenue).
    """
    if method == "exp_smooth":
        return exp_smoothing_forecast(history, horizon, alpha=float(kwargs.get("alpha", 0.35)))
    return seasonal_moving_average(history, horizon, season=int(kwargs.get("season", 12)))