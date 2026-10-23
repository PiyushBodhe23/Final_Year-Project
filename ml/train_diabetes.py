"""Train the Pima diabetes baseline used in Layer A of the risk score.

The cohort is women of Pima heritage (UCI, n=768). That limit belongs in the
viva: the probability is a lab-sensitive signal, not an Indian population rate.
IDRS supplies the India-specific half of the diabetes baseline.
"""

from __future__ import annotations

from backend.app.core.config import DIABETES_MODEL_PATH, PIMA_CSV
from ml.training import DatasetSpec, train_spec


def main() -> None:
    """Fit logistic regression, random forest, and XGBoost, then calibrate the best."""
    train_spec(
        DatasetSpec(
            key="diabetes",
            title="Diabetes (Pima)",
            csv_path=PIMA_CSV,
            model_path=DIABETES_MODEL_PATH,
            target="Outcome",
            citation=(
                "Pima Indians Diabetes Database, UCI Machine Learning Repository. "
                "Smith et al., National Institute of Diabetes and Digestive and Kidney Diseases."
            ),
            limitation=(
                "Female Pima heritage only, n=768. Zeros in glucose, blood pressure, "
                "BMI, insulin, and skin thickness are treated as missing and median-imputed."
            ),
            zero_as_missing=["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"],
        )
    )


if __name__ == "__main__":
    main()
