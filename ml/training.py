"""Shared training pipeline for the diabetes and cardiac baseline models.

Labels come from public clinical datasets. Probabilities are calibrated on the
training split only. Holdout metrics are the numbers to quote in the viva.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from backend.app.core.config import DISCLAIMER, FIGURES_DIR, METRICS_PATH

RANDOM_STATE: int = 42
TEST_SIZE: float = 0.2
CV_FOLDS: int = 5
# Platt scaling. Isotonic needs more events than these teaching sets reliably have.
CALIBRATION_METHOD: str = "sigmoid"


@dataclass
class DatasetSpec:
    """One disease model: where the CSV lives and which columns are the label."""

    key: str
    title: str
    csv_path: Path
    model_path: Path
    target: str
    citation: str
    limitation: str
    zero_as_missing: list[str] = field(default_factory=list)
    drop_columns: list[str] = field(default_factory=list)


def mark_impossible_zeros(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Replace physiological zeros with missing values.

    In the Pima file a glucose, blood pressure, BMI, insulin, or skin-thickness
    of 0 means the measurement was not taken. Leaving those zeros in would
    teach the model that a glucose of 0 is protective.
    """
    cleaned = frame.copy()
    for column in columns:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].replace(0, np.nan)
    return cleaned


def load_xy(spec: DatasetSpec) -> tuple[pd.DataFrame, pd.Series]:
    """Load a public CSV and return features plus a 0/1 label."""
    if not spec.csv_path.exists():
        raise FileNotFoundError(f"Missing dataset: {spec.csv_path}")
    frame = pd.read_csv(spec.csv_path)
    frame = frame.rename(columns={name: name.strip() for name in frame.columns})
    if "sex" in frame.columns and "male" not in frame.columns:
        frame = frame.rename(columns={"sex": "male"})
    frame = frame.drop(columns=[c for c in spec.drop_columns if c in frame.columns])
    if spec.target not in frame.columns:
        raise ValueError(f"{spec.csv_path.name} has no '{spec.target}' column")
    frame = mark_impossible_zeros(frame, spec.zero_as_missing)
    label = frame[spec.target].astype(int)
    features = frame.drop(columns=[spec.target])
    return features, label


def _pipelines(y_train: pd.Series) -> dict[str, Pipeline]:
    """Three classifiers. Median imputation is fit inside each training fold."""
    positives = int((y_train == 1).sum())
    negatives = int((y_train == 0).sum())
    scale_pos_weight = negatives / max(positives, 1)
    imputer = SimpleImputer(strategy="median")
    logistic = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    forest = Pipeline(
        [
            ("imputer", imputer),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    min_samples_leaf=5,
                    class_weight="balanced_subsample",
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    boosting = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clf",
                XGBClassifier(
                    n_estimators=200,
                    max_depth=3,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    scale_pos_weight=scale_pos_weight,
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    return {
        "logistic_regression": logistic,
        "random_forest": forest,
        "xgboost": boosting,
    }


def _holdout_row(name: str, y_true: pd.Series, proba: np.ndarray) -> dict[str, float | str]:
    """Score one probability vector on the untouched 20% holdout."""
    predicted = (proba >= 0.5).astype(int)
    return {
        "model": name,
        "auroc": float(roc_auc_score(y_true, proba)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "brier": float(brier_score_loss(y_true, proba)),
    }


def _shap_means(pipeline: Pipeline, x_sample: pd.DataFrame) -> dict[str, float]:
    """Mean absolute SHAP on a sample of the selected, uncalibrated model.

    Calibration is a monotone map of the probability. Feature direction is read
    from the model that actually sees the labs.
    """
    prep = Pipeline(pipeline.steps[:-1])
    clf = pipeline.named_steps["clf"]
    matrix = prep.transform(x_sample)
    if "scaler" in pipeline.named_steps:
        explainer = shap.LinearExplainer(clf, matrix)
    else:
        explainer = shap.TreeExplainer(clf)
    raw = explainer.shap_values(matrix)
    if hasattr(raw, "values"):
        values = np.asarray(raw.values)
    elif isinstance(raw, list):
        values = np.asarray(raw[1] if len(raw) > 1 else raw[0])
    else:
        values = np.asarray(raw)
    if values.ndim == 3:
        values = values[:, :, 1]
    means = np.abs(values).mean(axis=0)
    return {column: float(score) for column, score in zip(x_sample.columns, means, strict=True)}


def _save_figures(
    spec: DatasetSpec,
    y_test: pd.Series,
    proba: np.ndarray,
    shap_means: dict[str, float],
) -> dict[str, str]:
    """Write ROC, calibration, confusion, and SHAP bar charts for the viva slides."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    fpr, tpr, _ = roc_curve(y_test, proba)
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.plot(fpr, tpr, color="#2563eb", label=f"AUROC {roc_auc_score(y_test, proba):.3f}")
    ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(f"{spec.title} ROC (holdout)\nNot a diagnostic model")
    ax.legend(loc="lower right")
    fig.tight_layout()
    roc_path = FIGURES_DIR / f"{spec.key}_roc.png"
    fig.savefig(roc_path, dpi=120)
    plt.close(fig)
    paths["roc"] = str(roc_path)

    fraction, mean_pred = calibration_curve(y_test, proba, n_bins=8, strategy="quantile")
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.plot(mean_pred, fraction, marker="o", color="#2563eb", label="Calibrated model")
    ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--", label="Perfect")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title(f"{spec.title} calibration (holdout)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    cal_path = FIGURES_DIR / f"{spec.key}_calibration.png"
    fig.savefig(cal_path, dpi=120)
    plt.close(fig)
    paths["calibration"] = str(cal_path)

    matrix = confusion_matrix(y_test, (proba >= 0.5).astype(int))
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046)
    ax.set_xticks([0, 1], ["Predicted 0", "Predicted 1"])
    ax.set_yticks([0, 1], ["Actual 0", "Actual 1"])
    for row in range(2):
        for col in range(2):
            ax.text(col, row, str(matrix[row, col]), ha="center", va="center", color="#0f172a")
    ax.set_title(f"{spec.title} confusion matrix @ 0.5")
    fig.tight_layout()
    cm_path = FIGURES_DIR / f"{spec.key}_confusion.png"
    fig.savefig(cm_path, dpi=120)
    plt.close(fig)
    paths["confusion_matrix"] = str(cm_path)

    ordered = sorted(shap_means.items(), key=lambda item: item[1])
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    ax.barh([name for name, _ in ordered], [score for _, score in ordered], color="#2563eb")
    ax.set_xlabel("Mean |SHAP| on a training sample")
    ax.set_title(f"{spec.title} feature contribution")
    fig.tight_layout()
    shap_path = FIGURES_DIR / f"{spec.key}_shap.png"
    fig.savefig(shap_path, dpi=120)
    plt.close(fig)
    paths["shap"] = str(shap_path)
    return paths


def _merge_metrics(section: dict) -> None:
    """Insert one disease block into ml/models/metrics.json without dropping the other."""
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if METRICS_PATH.exists():
        existing = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    existing["disclaimer"] = DISCLAIMER
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    existing[section["key"]] = section
    METRICS_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def train_spec(spec: DatasetSpec) -> dict:
    """Train, compare, calibrate, and save one disease model.

    The 80/20 split is stratified. Five-fold AUROC on the training portion
    chooses the algorithm. The holdout is used only for the reported metrics.
    """
    features, label = load_xy(spec)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        label,
        test_size=TEST_SIZE,
        stratify=label,
        random_state=RANDOM_STATE,
    )
    models = _pipelines(y_train)
    folder = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    rows: list[dict[str, float | str]] = []
    cv_scores: dict[str, float] = {}
    for name, pipeline in models.items():
        # n_jobs=1: this Windows environment runs out of memory when joblib spawns workers.
        scores = cross_val_score(pipeline, x_train, y_train, cv=folder, scoring="roc_auc", n_jobs=1)
        cv_scores[name] = float(scores.mean())
        pipeline.fit(x_train, y_train)
        proba = pipeline.predict_proba(x_test)[:, 1]
        row = _holdout_row(name, y_test, proba)
        row["cv_auroc_mean"] = float(scores.mean())
        row["cv_auroc_std"] = float(scores.std())
        rows.append(row)

    selected = max(cv_scores, key=cv_scores.get)
    calibrated = CalibratedClassifierCV(models[selected], method=CALIBRATION_METHOD, cv=CV_FOLDS)
    calibrated.fit(x_train, y_train)
    calibrated_proba = calibrated.predict_proba(x_test)[:, 1]
    calibrated_row = _holdout_row(f"{selected}_calibrated", y_test, calibrated_proba)

    base = models[selected]
    base.fit(x_train, y_train)
    sample = x_train.sample(n=min(200, len(x_train)), random_state=RANDOM_STATE)
    shap_means = _shap_means(base, sample)
    figures = _save_figures(spec, y_test, calibrated_proba, shap_means)

    spec.model_path.parent.mkdir(parents=True, exist_ok=True)
    version = f"{spec.key}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    joblib.dump(
        {
            "model": calibrated,
            "features": list(features.columns),
            "version": version,
            "algorithm": selected,
            "calibration": CALIBRATION_METHOD,
            "dataset": spec.csv_path.name,
            "disclaimer": DISCLAIMER,
        },
        spec.model_path,
    )
    section = {
        "key": spec.key,
        "title": spec.title,
        "citation": spec.citation,
        "limitation": spec.limitation,
        "n_rows": int(len(features)),
        "n_positive": int(label.sum()),
        "features": list(features.columns),
        "selected_algorithm": selected,
        "selection_rule": "highest mean stratified 5-fold AUROC on the training split",
        "calibration": CALIBRATION_METHOD,
        "model_version": version,
        "model_path": str(spec.model_path),
        "comparison": rows,
        "calibrated_holdout": calibrated_row,
        "confusion_matrix_calibrated": confusion_matrix(
            y_test, (calibrated_proba >= 0.5).astype(int)
        ).tolist(),
        "shap_mean_abs": shap_means,
        "figures": figures,
        "threshold_note": (
            "Precision, recall, and F1 use a 0.5 cutoff. Calibration pulls probabilities "
            "toward the real event rate, so 0.5 is a high bar when events are uncommon. "
            "The risk score uses the probability itself. Quote AUROC and Brier."
        ),
    }
    _merge_metrics(section)
    table = pd.DataFrame(rows)
    print(f"\n{spec.title}  (n={len(features)}, events={int(label.sum())})")
    print(table.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(
        "Calibrated holdout: "
        + ", ".join(f"{key}={value:.3f}" for key, value in calibrated_row.items() if key != "model")
    )
    print(f"Saved {spec.model_path.name}  version={version}  selected={selected}")
    return section
