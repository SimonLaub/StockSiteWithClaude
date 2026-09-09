from pathlib import Path
from datetime import datetime

import joblib
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from stocks import STOCKS

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

LAGS = [1, 2, 3, 5, 10, 20]
ROLL_WINDOWS = [5, 10, 20]
FEATURE_COLUMNS = [f"lag_{lag}" for lag in LAGS] + [f"roll_{w}" for w in ROLL_WINDOWS]
MIN_HISTORY = max(LAGS + ROLL_WINDOWS)


def fetch_history(ticker, period="5y"):
    history = yf.Ticker(ticker).history(period=period, interval="1d")
    history = history.reset_index()[["Date", "Close"]]
    history["Date"] = pd.to_datetime(history["Date"]).dt.date
    return history.dropna(subset=["Close"]).reset_index(drop=True)


def fetch_live_price(ticker):
    return float(yf.Ticker(ticker).fast_info["last_price"])


def _feature_row(closes):
    row = {f"lag_{lag}": closes[-lag] for lag in LAGS}
    row.update({f"roll_{w}": closes[-w:].mean() for w in ROLL_WINDOWS})
    return row


def _direction(value, baseline):
    if value is None or baseline is None:
        return None
    if value > baseline:
        return "op"
    if value < baseline:
        return "ned"
    return "uændret"


def _data_path(ticker):
    return DATA_DIR / f"{ticker}.csv"


def _model_path(ticker):
    return MODELS_DIR / f"{ticker}.joblib"


def load_cached_history(ticker):
    df = pd.read_csv(_data_path(ticker))
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


def build_features(df):
    df = df.sort_values("Date").reset_index(drop=True)
    for lag in LAGS:
        df[f"lag_{lag}"] = df["Close"].shift(lag)
    for window in ROLL_WINDOWS:
        df[f"roll_{window}"] = df["Close"].shift(1).rolling(window).mean()
    return df.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def train_ticker(ticker):
    history = fetch_history(ticker)
    DATA_DIR.mkdir(exist_ok=True)
    history.to_csv(_data_path(ticker), index=False)

    features = build_features(history)
    split = int(len(features) * 0.8)
    train, test = features.iloc[:split], features.iloc[split:]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(train[FEATURE_COLUMNS], train["Close"])

    if len(test):
        predictions = model.predict(test[FEATURE_COLUMNS])
        mae = mean_absolute_error(test["Close"], predictions)
        print(f"{ticker}: MAE={mae:.2f} (on {len(test)} test days)")

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, _model_path(ticker))


def valid_date_range():
    min_dates, max_dates = [], []
    for ticker in STOCKS:
        history = load_cached_history(ticker)
        if len(history) <= MIN_HISTORY:
            continue
        min_dates.append(history["Date"].iloc[MIN_HISTORY])
        max_dates.append(history["Date"].iloc[-1])
    return max(min_dates), min(max_dates)


def predict_for_date(ticker, target_date):
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    history = load_cached_history(ticker)
    before = history[history["Date"] < target_date].sort_values("Date")

    previous_close = None
    predicted = None
    if len(before) >= MIN_HISTORY:
        closes = before["Close"].values
        previous_close = float(closes[-1])
        model = joblib.load(_model_path(ticker))
        features = pd.DataFrame([_feature_row(closes)])[FEATURE_COLUMNS]
        predicted = float(model.predict(features)[0])

    actual_row = history[history["Date"] == target_date]
    actual = float(actual_row["Close"].iloc[0]) if len(actual_row) else None

    return {
        "ticker": ticker,
        "name": STOCKS[ticker],
        "predicted": predicted,
        "actual": actual,
        "predicted_direction": _direction(predicted, previous_close),
        "actual_direction": _direction(actual, previous_close),
    }


def get_today_view(ticker):
    """Fetch fresh (non-cached) recent history to predict today's close and compare
    it against the live price, so results stay accurate between training runs."""
    recent = fetch_history(ticker, period="3mo")
    closes = recent["Close"].values

    previous_close = None
    predicted = None
    if len(closes) >= MIN_HISTORY:
        previous_close = float(closes[-1])
        model = joblib.load(_model_path(ticker))
        features = pd.DataFrame([_feature_row(closes)])[FEATURE_COLUMNS]
        predicted = float(model.predict(features)[0])

    live_price = fetch_live_price(ticker)

    return {
        "ticker": ticker,
        "name": STOCKS[ticker],
        "live_price": live_price,
        "predicted": predicted,
        "predicted_direction": _direction(predicted, previous_close),
    }
