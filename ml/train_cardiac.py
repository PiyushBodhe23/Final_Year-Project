"""Train the Framingham 10-year CHD baseline used in Layer A of the cardiac score.

This is the public teaching extract (Kaggle / course mirrors), not the restricted
NHLBI Framingham files. Education is omitted because the patient profile does not
collect it and it is not a factor the dashboard explains.
"""

from __future__ import annotations

from backend.app.core.config import CARDIAC_MODEL_PATH, FRAMINGHAM_CSV
from ml.training import DatasetSpec, train_spec


def main() -> None:
    """Fit logistic regression, random forest, and XGBoost, then calibrate the best."""
    train_spec(
        DatasetSpec(
            key="cardiac",
            title="Cardiovascular 10-year CHD (Framingham teaching extract)",
            csv_path=FRAMINGHAM_CSV,
            model_path=CARDIAC_MODEL_PATH,
            target="TenYearCHD",
            citation=(
                "Framingham Heart Study teaching extract, as distributed for coursework "
                "and Kaggle (TenYearCHD). Cite the Framingham Heart Study and the mirror used."
            ),
            limitation=(
                "Historic US cohort teaching file, about 4,000 exams. Not an Indian "
                "population model and not the restricted NHLBI release."
            ),
            zero_as_missing=["totChol", "sysBP", "diaBP", "BMI", "heartRate", "glucose"],
            drop_columns=["education"],
        )
    )


if __name__ == "__main__":
    main()
