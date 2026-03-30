"""
seed_database.py
----------------
Generates every valid permutation of user preference fields and stores them
in a private SQLite database (or Postgres if DATABASE_URL env var is set).

Run ONCE before the first POST /train:
    python seed_database.py
    python seed_database.py --force   # re-seed from scratch
    DATABASE_URL=postgresql://... python seed_database.py
"""

import itertools
import json
import logging
import os
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# All valid discrete values — must stay in sync with portfolio_recommender.py
# ---------------------------------------------------------------------------
FIELD_VALUES = {
    "riskTolerance":        ["conservative", "moderate", "aggressive"],
    "investmentHorizon":    ["1-2 years", "3-5 years", "5-10 years", "10-20 years", "20+ years"],
    "primaryGoal":          ["growth", "income", "balanced", "preservation", "retirement", "tax-saving"],
    "hasEmergencyFund":     ["yes", "no"],
    "investmentExperience": ["beginner", "intermediate", "advanced", "expert"],
}

# Mid-point numeric samples (map from AIAdvisorForm range buckets)
INVESTMENT_AMOUNTS = [75_000, 175_000, 375_000, 750_000, 1_750_000, 2_500_000]
AGES               = [22, 30, 40, 50, 60, 65]
INCOMES            = [400_000, 750_000, 1_200_000, 2_000_000, 2_500_000]

# Sector short-codes (matching SECTOR_CODE_MAP in AIAdvisorForm.tsx)
ALL_SECTORS = [
    "IT", "Finance", "Oil & Gas", "FMCG", "Pharma",
    "Auto", "Metals", "Telecom", "Power",
    "Real Estate", "Textiles", "Chemicals",
]

# Single sectors + common pairs + empty (no preference)
SECTOR_COMBOS = (
    [[]]
    + [[s] for s in ALL_SECTORS]
    + [[a, b] for a, b in itertools.combinations(ALL_SECTORS, 2)]
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_connection(db_path: str = "investiq_profiles.db"):
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        import psycopg2
        conn = psycopg2.connect(database_url)
        logger.info("Connected to Postgres.")
        return conn
    conn = sqlite3.connect(db_path)
    logger.info("Connected to SQLite: %s", db_path)
    return conn


def setup_schema(conn) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS synthetic_profiles (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            riskTolerance        TEXT    NOT NULL,
            investmentHorizon    TEXT    NOT NULL,
            primaryGoal          TEXT    NOT NULL,
            hasEmergencyFund     TEXT    NOT NULL,
            investmentExperience TEXT    NOT NULL,
            sectors              TEXT    NOT NULL,
            investmentAmount     REAL    NOT NULL,
            age                  INTEGER NOT NULL,
            currentIncome        REAL    NOT NULL,
            created_at           TEXT    NOT NULL,
            version              INTEGER NOT NULL DEFAULT 1
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_risk ON synthetic_profiles (riskTolerance)")
    conn.commit()
    logger.info("Schema ready.")


def is_empty(conn) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM synthetic_profiles")
    return cur.fetchone()[0] == 0


def insert_profiles(conn, profiles: list) -> None:
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    rows = [
        (
            p["riskTolerance"], p["investmentHorizon"], p["primaryGoal"],
            p["hasEmergencyFund"], p["investmentExperience"],
            json.dumps(p["sectors"]),
            p["investmentAmount"], p["age"], p["currentIncome"],
            now, 1,
        )
        for p in profiles
    ]
    cur.executemany(
        """INSERT INTO synthetic_profiles
           (riskTolerance, investmentHorizon, primaryGoal, hasEmergencyFund,
            investmentExperience, sectors, investmentAmount, age, currentIncome,
            created_at, version)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    logger.info("Inserted %d profiles.", len(rows))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_profiles() -> list:
    """
    Cartesian product of all categorical fields × numeric samples × sector combos.
    Estimated total: 3×5×6×2×4 × 6×6×5 × 79 ≈ 51 million — too large.

    Strategy: iterate categorical combos × numeric samples, then assign ONE
    representative sector combo per categorical combo (cycling through SECTOR_COMBOS).
    This gives 3×5×6×2×4 × 6×6×5 = 64,800 rows — comprehensive and fast to train on.

    If you want the full sector sweep, set FULL_SECTOR_SWEEP=1 in your environment
    (warning: ~5 million rows, takes several minutes to insert).
    """
    full_sweep = os.environ.get("FULL_SECTOR_SWEEP") == "1"

    categorical_keys   = list(FIELD_VALUES.keys())
    categorical_combos = list(itertools.product(*FIELD_VALUES.values()))

    profiles = []
    sector_cycle = itertools.cycle(SECTOR_COMBOS)

    for cat_combo in categorical_combos:
        cat_dict = dict(zip(categorical_keys, cat_combo))
        for amount in INVESTMENT_AMOUNTS:
            for age in AGES:
                for income in INCOMES:
                    if full_sweep:
                        for sectors in SECTOR_COMBOS:
                            profiles.append({**cat_dict, "sectors": sectors,
                                             "investmentAmount": amount,
                                             "age": age, "currentIncome": income})
                    else:
                        profiles.append({**cat_dict, "sectors": next(sector_cycle),
                                         "investmentAmount": amount,
                                         "age": age, "currentIncome": income})

    logger.info("Generated %d synthetic profiles.", len(profiles))
    return profiles


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def seed(db_path: str = "investiq_profiles.db", force: bool = False) -> None:
    conn = get_connection(db_path)
    setup_schema(conn)

    if not force and not is_empty(conn):
        logger.info("Database already seeded. Use --force to re-seed.")
        conn.close()
        return

    if force:
        conn.cursor().execute("DELETE FROM synthetic_profiles")
        conn.commit()
        logger.info("Cleared existing profiles.")

    profiles = generate_profiles()
    insert_profiles(conn, profiles)
    conn.close()
    logger.info("Seeding complete.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db",    default="investiq_profiles.db")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    seed(db_path=args.db, force=args.force)