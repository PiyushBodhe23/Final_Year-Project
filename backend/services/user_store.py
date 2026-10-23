"""Local user + credential store (SQLite). API keys/tokens stay on disk, never logged."""

from __future__ import annotations

import base64
import hashlib
import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "data" / "users.db"
KEY_PATH = PROJECT_ROOT / "data" / ".local_secret"
DEMOGRAPHICS_PATH = PROJECT_ROOT / "data" / "patient_demographics.csv"

OAUTH_SOURCES = ("fitbit", "google_fit", "polar", "wahoo", "huawei")
DEVICE_SOURCES = ("apple_health", "samsung_health")
ALL_SOURCES = OAUTH_SOURCES + DEVICE_SOURCES

GENDERS = ("female", "male")

_FIRST_FEMALE = (
    "Aanya", "Meera", "Priya", "Diya", "Ananya", "Isha", "Kavya", "Nisha",
    "Riya", "Sana", "Tara", "Zara", "Aditi", "Pooja", "Neha", "Sneha",
    "Anika", "Myra", "Kiara", "Aisha", "Fatima", "Leela", "Maya", "Nora",
    "Sara", "Amira", "Hana", "Lila", "Ira", "Veda",
)
_FIRST_MALE = (
    "Arjun", "Rohan", "Aarav", "Vihaan", "Kabir", "Ishaan", "Dev", "Neil",
    "Rahul", "Amit", "Karan", "Yash", "Aditya", "Siddharth", "Vikram", "Nikhil",
    "Omar", "Rehan", "Farhan", "Sameer", "Ansh", "Rudra", "Krish", "Jay",
    "Dhruv", "Harsh", "Mohit", "Tanish", "Ayaan", "Zayan",
)
_LAST = (
    "Sharma", "Patel", "Khan", "Reddy", "Nair", "Iyer", "Joshi", "Mehta",
    "Gupta", "Singh", "Das", "Roy", "Kapoor", "Malhotra", "Chopra", "Bose",
    "Desai", "Shah", "Verma", "Rao", "Pillai", "Banerjee", "Chawla", "Gill",
    "Kulkarni", "Jain", "Agarwal", "Shetty", "Menon", "Bhat",
)


def synthetic_display_name(patient_id: str, gender: str) -> str:
    digits = "".join(ch for ch in str(patient_id) if ch.isdigit())
    n = int(digits or 0)
    firsts = _FIRST_FEMALE if str(gender).lower() == "female" else _FIRST_MALE
    first = firsts[n % len(firsts)]
    last = _LAST[(n // len(firsts)) % len(_LAST)]
    return f"{first} {last}"


def _secret() -> bytes:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(hashlib.sha256(uuid.uuid4().bytes).digest())
    return KEY_PATH.read_bytes()


def _encrypt(plain: str) -> str:
    if not plain:
        return ""
    key = _secret()
    raw = plain.encode("utf-8")
    mixed = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(mixed).decode("ascii")


def _decrypt(token: str) -> str:
    if not token:
        return ""
    key = _secret()
    mixed = base64.urlsafe_b64decode(token.encode("ascii"))
    raw = bytes(b ^ key[i % len(key)] for i, b in enumerate(mixed))
    return raw.decode("utf-8")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS credentials (
            user_id TEXT NOT NULL,
            source TEXT NOT NULL,
            api_key_enc TEXT DEFAULT '',
            access_token_enc TEXT DEFAULT '',
            refresh_token_enc TEXT DEFAULT '',
            token_type TEXT DEFAULT 'Bearer',
            auth_mode TEXT DEFAULT 'oauth2',
            connected INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, source)
        )
        """
    )
    return con


def random_age_gender(rng: random.Random | None = None) -> tuple[int, str]:
    r = rng or random.Random()
    return r.randint(18, 90), r.choice(GENDERS)


def _training_patient_ids() -> list[str]:
    import pandas as pd

    from backend.config import PATIENT_TRAINING_PATH

    if not PATIENT_TRAINING_PATH.exists():
        return []
    try:
        train = pd.read_excel(PATIENT_TRAINING_PATH, usecols=["patient_id"])
        return train["patient_id"].astype(str).unique().tolist()
    except Exception:
        return []


def ensure_demographics_file() -> Path:
    """Assign age, gender, and a display name to every synthetic patient once."""
    import pandas as pd

    from backend.config import PATIENT_HISTORY_PATH

    ids: list[str] = []
    if PATIENT_HISTORY_PATH.exists():
        hist = pd.read_csv(PATIENT_HISTORY_PATH, usecols=["patient_id"])
        ids.extend(hist["patient_id"].astype(str).unique().tolist())
    ids.extend(_training_patient_ids())
    ids = sorted(set(ids))

    existing: dict[str, dict[str, Any]] = {}
    if DEMOGRAPHICS_PATH.exists():
        old = pd.read_csv(DEMOGRAPHICS_PATH)
        for _, row in old.iterrows():
            pid = str(row["patient_id"])
            name = pid
            if "display_name" in old.columns and pd.notna(row.get("display_name")):
                name = str(row["display_name"]).strip() or pid
            if name == pid or name.upper() == pid.upper():
                name = synthetic_display_name(pid, str(row["gender"]))
            existing[pid] = {
                "patient_id": pid,
                "age": int(row["age"]),
                "gender": str(row["gender"]),
                "display_name": name,
            }

    rng = random.Random(42)
    rows = []
    for pid in ids:
        if pid in existing:
            rec = existing[pid]
            rec.setdefault("display_name", synthetic_display_name(pid, rec.get("gender", "female")))
            rows.append(rec)
        else:
            age, gender = random_age_gender(rng)
            rows.append({"patient_id": pid, "age": age, "gender": gender, "display_name": synthetic_display_name(pid, gender)})
    for pid, rec in existing.items():
        if pid not in {r["patient_id"] for r in rows}:
            rec.setdefault("display_name", pid)
            rows.append(rec)
    pd.DataFrame(rows).to_csv(DEMOGRAPHICS_PATH, index=False)
    return DEMOGRAPHICS_PATH


def list_demographics_roster() -> list[dict[str, Any]]:
    """All patients with names — one CSV read, used by the demo dropdown."""
    import pandas as pd

    if not DEMOGRAPHICS_PATH.exists():
        ensure_demographics_file()
    df = pd.read_csv(DEMOGRAPHICS_PATH)
    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        pid = str(row["patient_id"])
        name = pid
        if "display_name" in df.columns and pd.notna(row.get("display_name")):
            name = str(row["display_name"]).strip() or pid
        out.append(
            {
                "patient_id": pid,
                "display_name": name,
                "age": int(row["age"]) if pd.notna(row.get("age")) else None,
                "gender": str(row["gender"]) if pd.notna(row.get("gender")) else "",
            }
        )
    return out


def next_patient_id() -> str:
    """Continue P001, P002, … from everyone already in the dataset."""
    import pandas as pd

    from backend.config import PATIENT_HISTORY_PATH

    nums: list[int] = []

    def _collect(values: list[str]) -> None:
        for pid in values:
            digits = "".join(ch for ch in str(pid) if ch.isdigit())
            if digits:
                nums.append(int(digits))

    if DEMOGRAPHICS_PATH.exists():
        demo = pd.read_csv(DEMOGRAPHICS_PATH, usecols=["patient_id"])
        _collect(demo["patient_id"].astype(str).tolist())
    if PATIENT_HISTORY_PATH.exists():
        hist = pd.read_csv(PATIENT_HISTORY_PATH, usecols=["patient_id"])
        _collect(hist["patient_id"].astype(str).unique().tolist())
    _collect(_training_patient_ids())
    with _conn() as con:
        _collect([r["user_id"] for r in con.execute("SELECT user_id FROM users").fetchall()])
    n = max(nums) if nums else 0
    return f"P{n + 1:03d}"


def get_demographics(patient_id: str) -> dict[str, Any]:
    import pandas as pd

    if not DEMOGRAPHICS_PATH.exists():
        ensure_demographics_file()
    df = pd.read_csv(DEMOGRAPHICS_PATH)
    match = df[df["patient_id"].astype(str) == str(patient_id)]
    if match.empty:
        age, gender = random_age_gender(random.Random(hash(patient_id) % (2**32)))
        rec = {
            "patient_id": str(patient_id),
            "age": age,
            "gender": gender,
            "display_name": synthetic_display_name(patient_id, gender),
        }
        df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
        df.to_csv(DEMOGRAPHICS_PATH, index=False)
        return rec
    row = match.iloc[0]
    name = str(patient_id)
    if "display_name" in match.columns and pd.notna(row.get("display_name")):
        name = str(row["display_name"]).strip() or name
    return {
        "patient_id": str(row["patient_id"]),
        "age": int(row["age"]),
        "gender": str(row["gender"]),
        "display_name": name,
    }


def upsert_demographics(patient_id: str, age: int, gender: str, display_name: str | None = None) -> None:
    import pandas as pd

    ensure_demographics_file()
    df = pd.read_csv(DEMOGRAPHICS_PATH)
    df["patient_id"] = df["patient_id"].astype(str)
    if "display_name" not in df.columns:
        df["display_name"] = df["patient_id"]
    name = (display_name or "").strip() or str(patient_id)
    rec = {"patient_id": str(patient_id), "age": int(age), "gender": str(gender), "display_name": name}
    if str(patient_id) in set(df["patient_id"]):
        df.loc[df["patient_id"] == str(patient_id), ["age", "gender", "display_name"]] = [age, gender, name]
    else:
        df = pd.concat([df, pd.DataFrame([rec])], ignore_index=True)
    df.to_csv(DEMOGRAPHICS_PATH, index=False)


def create_user(display_name: str, age: int | None = None, gender: str | None = None, keys: dict[str, str] | None = None) -> dict[str, Any]:
    name = display_name.strip()
    if not name:
        raise ValueError("Display name is required")
    gender_v = str(gender or "").strip().lower()
    if gender_v not in GENDERS:
        raise ValueError("Gender must be male or female")
    if age is None:
        raise ValueError("Age is required")
    age_v = int(age)
    if age_v < 1 or age_v > 120:
        raise ValueError("Enter a valid age")
    user_id = next_patient_id()
    with _conn() as con:
        while con.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone():
            digits = "".join(ch for ch in user_id if ch.isdigit())
            user_id = f"P{int(digits or 0) + 1:03d}"
        now = datetime.now(timezone.utc).isoformat()
        con.execute(
            "INSERT INTO users (user_id, display_name, age, gender, created_at) VALUES (?,?,?,?,?)",
            (user_id, name, age_v, gender_v, now),
        )
        con.commit()
    upsert_demographics(user_id, age_v, gender_v, display_name=name)
    if keys:
        save_api_keys(user_id, keys)
    return public_user(user_id)


def public_user(user_id: str) -> dict[str, Any]:
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            demo = get_demographics(user_id)
            return {
                "user_id": user_id,
                "display_name": user_id,
                "age": demo["age"],
                "gender": demo["gender"],
                "created_at": None,
                "credentials": credential_status(user_id),
            }
        return {
            "user_id": row["user_id"],
            "display_name": row["display_name"],
            "age": row["age"],
            "gender": row["gender"],
            "created_at": row["created_at"],
            "credentials": credential_status(user_id),
        }


def list_users() -> list[dict[str, Any]]:
    with _conn() as con:
        rows = con.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()
    return [public_user(r["user_id"]) for r in rows]


def save_api_keys(user_id: str, keys: dict[str, str]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        for source, key in keys.items():
            if source not in ALL_SOURCES or not str(key).strip():
                continue
            mode = "device_permission" if source in DEVICE_SOURCES else "api_key"
            con.execute(
                """
                INSERT INTO credentials (user_id, source, api_key_enc, access_token_enc, refresh_token_enc,
                    token_type, auth_mode, connected, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id, source) DO UPDATE SET
                    api_key_enc=excluded.api_key_enc,
                    auth_mode=excluded.auth_mode,
                    updated_at=excluded.updated_at
                """,
                (user_id, source, _encrypt(str(key).strip()), "", "", "Bearer", mode, 0, now),
            )
        con.commit()
    return credential_status(user_id)


def store_oauth_tokens(user_id: str, source: str, access: str, refresh: str, api_key: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    mode = "device_permission" if source in DEVICE_SOURCES else "oauth2"
    with _conn() as con:
        existing = con.execute(
            "SELECT api_key_enc FROM credentials WHERE user_id=? AND source=?",
            (user_id, source),
        ).fetchone()
        key_enc = existing["api_key_enc"] if existing and not api_key else _encrypt(api_key)
        con.execute(
            """
            INSERT INTO credentials (user_id, source, api_key_enc, access_token_enc, refresh_token_enc,
                token_type, auth_mode, connected, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(user_id, source) DO UPDATE SET
                access_token_enc=excluded.access_token_enc,
                refresh_token_enc=excluded.refresh_token_enc,
                auth_mode=excluded.auth_mode,
                connected=1,
                updated_at=excluded.updated_at
            """,
            (user_id, source, key_enc, _encrypt(access), _encrypt(refresh), "Bearer", mode, 1, now),
        )
        con.commit()


def mark_disconnected(user_id: str, source: str) -> None:
    with _conn() as con:
        con.execute(
            "UPDATE credentials SET connected=0, access_token_enc='', refresh_token_enc='', updated_at=? WHERE user_id=? AND source=?",
            (datetime.now(timezone.utc).isoformat(), user_id, source),
        )
        con.commit()


def credential_status(user_id: str) -> list[dict[str, Any]]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM credentials WHERE user_id=?", (user_id,)).fetchall()
    by_src = {r["source"]: r for r in rows}
    out = []
    for src in ALL_SOURCES:
        row = by_src.get(src)
        has_key = bool(row and row["api_key_enc"])
        connected = bool(row and row["connected"])
        out.append(
            {
                "source": src,
                "has_api_key": has_key,
                "connected": connected,
                "auth_mode": (row["auth_mode"] if row else ("device_permission" if src in DEVICE_SOURCES else "oauth2")),
                "key_fingerprint": _fingerprint(row["api_key_enc"]) if row and row["api_key_enc"] else None,
            }
        )
    return out


def _fingerprint(enc: str) -> str:
    try:
        plain = _decrypt(enc)
    except Exception:
        return "****"
    if len(plain) < 6:
        return "****"
    return plain[:3] + "…" + plain[-2:]


def has_connection(user_id: str, source: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT connected FROM credentials WHERE user_id=? AND source=?",
            (user_id, source),
        ).fetchone()
    return bool(row and row["connected"])


def connected_source_ids(user_id: str) -> list[str]:
    with _conn() as con:
        rows = con.execute(
            "SELECT source FROM credentials WHERE user_id=? AND connected=1",
            (user_id,),
        ).fetchall()
    return [r["source"] for r in rows]
