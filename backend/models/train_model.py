"""Train RandomForest + LSTM ensemble on synthetic vitals and save weights."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# Allow `python backend/models/train_model.py` from project root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import (  # noqa: E402
    DATA_PATH,
    FEATURE_COLUMNS,
    LSTM_MODEL_PATH,
    LSTM_SCALER_PATH,
    LSTM_SEQ_LEN,
    RF_MODEL_PATH,
    VITAL_RANGES,
    WEIGHTS_DIR,
)
from backend.models.risk_engine import heuristic_hri  # noqa: E402


def _label_from_row(row: pd.Series) -> int:
    """Binary elevated-risk label derived from heuristic HRI."""
    hri = heuristic_hri(row.to_dict())
    return 1 if hri >= 50 else 0


def _regression_target(row: pd.Series) -> float:
    return heuristic_hri(row.to_dict()) / 100.0


def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing synthetic dataset: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing columns: {missing}")
    return df


def train_random_forest(df: pd.DataFrame) -> RandomForestClassifier:
    x = df[FEATURE_COLUMNS].astype(float).values
    y = df.apply(_label_from_row, axis=1).values
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    clf.fit(x_train, y_train)
    acc = float(clf.score(x_test, y_test))
    print(f"RandomForest test accuracy: {acc:.3f}")
    return clf


def _build_sequences(values: np.ndarray, targets: np.ndarray, seq_len: int):
    xs, ys = [], []
    for i in range(seq_len, len(values)):
        xs.append(values[i - seq_len : i])
        ys.append(targets[i])
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


def train_lstm(df: pd.DataFrame):
    from tensorflow import keras
    from tensorflow.keras import layers

    raw = df[FEATURE_COLUMNS].astype(float).values
    targets = df.apply(_regression_target, axis=1).values.astype(np.float32)

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(raw).astype(np.float32)
    x_seq, y_seq = _build_sequences(scaled, targets, LSTM_SEQ_LEN)

    split = int(len(x_seq) * 0.8)
    x_train, x_test = x_seq[:split], x_seq[split:]
    y_train, y_test = y_seq[:split], y_seq[split:]

    model = keras.Sequential(
        [
            layers.Input(shape=(LSTM_SEQ_LEN, len(FEATURE_COLUMNS))),
            layers.LSTM(32, return_sequences=False),
            layers.Dense(16, activation="relu"),
            layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(
        x_train,
        y_train,
        validation_data=(x_test, y_test),
        epochs=12,
        batch_size=32,
        verbose=1,
    )
    loss, mae = model.evaluate(x_test, y_test, verbose=0)
    print(f"LSTM test loss={loss:.4f} mae={mae:.4f}")
    return model, scaler


def main() -> None:
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Loading data from {DATA_PATH}")
    df = load_dataset()
    print(f"Rows: {len(df)} | Features: {FEATURE_COLUMNS}")

    rf = train_random_forest(df)
    joblib.dump(rf, RF_MODEL_PATH)
    print(f"Saved RF → {RF_MODEL_PATH}")

    try:
        lstm, scaler = train_lstm(df)
        lstm.save(LSTM_MODEL_PATH)
        joblib.dump(scaler, LSTM_SCALER_PATH)
        print(f"Saved LSTM → {LSTM_MODEL_PATH}")
        print(f"Saved scaler → {LSTM_SCALER_PATH}")
    except ImportError as exc:
        print(f"Skipping LSTM (TensorFlow not installed): {exc}")
        print("RandomForest weights are ready; risk engine will use RF / heuristic.")
    print("Training complete.")


if __name__ == "__main__":
    main()
