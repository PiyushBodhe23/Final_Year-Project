"""Download PhysioNet Challenge 2019 sepsis data and write flat CSV."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PARQUET = DATA / "_sepsis_tmp.parquet"
OUT = DATA / "sepsis_dataset.csv"
URL = (
    "https://huggingface.co/datasets/legomaheggo/physionet-sepsis-2019"
    "/resolve/main/data/train-00000-of-00001.parquet"
)

VITAL_COLS = ["HR", "SBP", "DBP", "MAP", "Resp", "Temp", "O2Sat", "SepsisLabel"]


def download() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if PARQUET.exists() and PARQUET.stat().st_size > 1_000_000:
        print(f"Using existing {PARQUET}")
        return
    print(f"Downloading {URL}")
    subprocess.run(
        ["curl.exe", "-L", "--http1.1", "-A", "Mozilla/5.0", "-o", str(PARQUET), URL],
        check=True,
    )
    print(f"Saved {PARQUET} ({PARQUET.stat().st_size} bytes)")


def explode_patient_row(row: pd.Series) -> pd.DataFrame:
    series = {c: list(row[c]) for c in VITAL_COLS}
    n = max(len(v) for v in series.values())
    for c, vals in series.items():
        if len(vals) < n:
            vals = vals + [None] * (n - len(vals))
            series[c] = vals
    frame = pd.DataFrame(series)
    frame.insert(0, "Hour", range(n))
    frame.insert(0, "patient_id", row["patient_id"])
    frame["Age"] = row["age"]
    frame["Gender"] = row["gender"]
    frame["has_sepsis"] = bool(row["has_sepsis"])
    frame["icu_hours"] = row["icu_hours"]
    return frame


def main() -> None:
    download()
    print("Reading parquet…")
    df = pd.read_parquet(PARQUET)
    print(f"Patients: {len(df)}")

    chunks: list[pd.DataFrame] = []
    for i, (_, row) in enumerate(df.iterrows()):
        chunks.append(explode_patient_row(row))
        if (i + 1) % 2000 == 0:
            print(f"  expanded {i + 1}/{len(df)} patients")

    flat = pd.concat(chunks, ignore_index=True)
    # PhysioNet-style column order
    cols = [
        "patient_id",
        "Hour",
        "HR",
        "O2Sat",
        "Temp",
        "SBP",
        "MAP",
        "DBP",
        "Resp",
        "Age",
        "Gender",
        "icu_hours",
        "has_sepsis",
        "SepsisLabel",
    ]
    flat = flat[cols]
    flat.to_csv(OUT, index=False)
    print(f"Wrote {OUT} rows={len(flat)} cols={list(flat.columns)}")
    print("SepsisLabel counts:", flat["SepsisLabel"].value_counts(dropna=False).to_dict())
    PARQUET.unlink(missing_ok=True)
    print("Done.")


if __name__ == "__main__":
    main()
