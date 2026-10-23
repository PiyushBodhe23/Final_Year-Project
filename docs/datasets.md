# Datasets used for training

These files are downloaded into `data/raw/` and are gitignored. Re-download before training if the folder is empty.

| File | Source | Role |
|---|---|---|
| `pima_diabetes.csv` | Pima Indians Diabetes Database, UCI Machine Learning Repository (Smith et al., NIDDK). Mirror used for the demo: Plotly public datasets. | Diabetes labels and lab features. Women of Pima heritage, 768 rows. |
| `framingham.csv` | Framingham Heart Study teaching extract circulated for courses and Kaggle (`TenYearCHD`). Mirror used for the demo: a public course copy that already drops `education`. This is not the restricted NHLBI data release. | 10-year coronary heart disease labels. |

Both sets are public teaching data. They are demographically narrow. The report and the UI must say the models are not clinically validated.

## Linking labs to wearables

No public file has the same person's labs, months of wearable data, and a disease outcome. `ml/generate_synthetic.py` keeps the Framingham exam (or the three typed personas) as the clinical row, then simulates 180 daily wearable rows conditioned on that profile. HbA1c, HDL, triglycerides, waist, and family history on cohort rows are filled in for the demo. They are not measurements from Framingham. Wearable ranges follow published adult bands. They are not a fit to the LifeSnaps or Fitbit public dumps.
