# PreventVital models

From the project root, with the CSVs in `data/raw/` (see `docs/datasets.md`):

```bash
python -m ml.train_diabetes
python -m ml.train_cardiac
```

Each script compares logistic regression, random forest, and XGBoost with stratified 5-fold AUROC, calibrates the winner with Platt scaling, and writes:

- `ml/models/diabetes.joblib` and `ml/models/cardiac.joblib`
- `ml/models/metrics.json`
- ROC, calibration, confusion, and SHAP figures in `docs/figures/`

Synthetic wearables, then the database:

```bash
python -m ml.generate_synthetic
python -m backend.app.seed
```

That writes `data/synthetic/profiles.csv` and `data/synthetic/demo_wearables.csv`, and loads Priya, Rahul, Suresh, plus 50 cohort patients into SQLite. Cite the datasets in `docs/datasets.md`.
