"""
core/database.py
----------------
Wrapper SQLite minimale.
Nessun ORM, nessun SQL nelle finestre.

API pubblica:
    db = Database()
    db.save_test(test_result)   → int (id assegnato)
    db.load_tests()             → list[dict]
    db.load_test(id)            → dict | None
    db.delete_test(id)          → None
"""

import sqlite3
import json
import logging
from pathlib import Path
from model.test_result import TestResult
from model.sample import Sample

log = logging.getLogger(__name__)


class Database:
    """
    Gestisce la persistenza dei risultati di collaudo su SQLite.
    Il file del database viene creato automaticamente se non esiste.
    """

    def __init__(self, db_path: str | Path):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        log.debug("Database aperto: %s", self._path)

    # ─── Schema ─────────────────────────────────────────────────────────────

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    date             TEXT    NOT NULL,
                    operator         TEXT    NOT NULL,
                    mould            TEXT    NOT NULL,
                    production_lot   TEXT    NOT NULL,
                    raw_material_lot TEXT    NOT NULL,
                    qty              INTEGER NOT NULL,
                    min_mn           REAL    NOT NULL,
                    mean_mn          REAL    NOT NULL,
                    max_mn           REAL    NOT NULL,
                    std_mn           REAL    NOT NULL,
                    range_mn         REAL    NOT NULL,
                    lower_limit      REAL    NOT NULL,
                    upper_limit      REAL    NOT NULL,
                    result           TEXT    NOT NULL,
                    pdf_path         TEXT    NOT NULL DEFAULT '',
                    samples_json     TEXT    NOT NULL DEFAULT '[]'
                );
                
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

            # Insert default password if not exists
            conn.execute(
                "INSERT OR IGNORE INTO app_settings (key, value) VALUES ('password', '1234')"
            )

    # ─── CRUD ────────────────────────────────────────────────────────────────

    def save_test(self, result: TestResult) -> int:
        """
        Inserisce un TestResult nel database.

        Returns:
            ID assegnato dalla base dati (int).
        """
        samples_json = json.dumps(
            [{"force_mn": s.force_mn,
              "piece_idx": s.piece_idx,
              "in_range": s.in_range,
              "timestamp": s.timestamp.isoformat()}
             for s in result.samples]
        )

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO test_results
                    (date, operator, mould, production_lot, raw_material_lot,
                     qty, min_mn, mean_mn, max_mn, std_mn, range_mn,
                     lower_limit, upper_limit, result, pdf_path, samples_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.date.isoformat(),
                    result.operator,
                    result.mould,
                    result.production_lot,
                    result.raw_material_lot,
                    result.qty,
                    result.min_mn,
                    result.mean_mn,
                    result.max_mn,
                    result.std_mn,
                    result.range_mn,
                    result.lower_limit,
                    result.upper_limit,
                    result.result,
                    result.pdf_path,
                    samples_json,
                ),
            )
            return cursor.lastrowid

    def update_pdf_path(self, test_id: int, pdf_path: str) -> None:
        """Aggiorna il percorso PDF di un collaudo già salvato."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE test_results SET pdf_path = ? WHERE id = ?",
                (pdf_path, test_id),
            )

    def load_tests(self) -> list[dict]:
        """
        Restituisce tutti i collaudi in ordine cronologico inverso.
        Ogni elemento è un dict con le colonne principali (no samples_json).
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, date, operator, mould, production_lot, raw_material_lot,
                       qty, min_mn, mean_mn, max_mn, std_mn, range_mn,
                       lower_limit, upper_limit, result, pdf_path
                FROM test_results
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def load_test(self, test_id: int) -> dict | None:
        """
        Restituisce un singolo collaudo completo, inclusi i campioni deserializzati.

        Returns:
            dict con tutti i campi + 'samples' (list[dict]) | None se non trovato.
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM test_results WHERE id = ?", (test_id,)
            ).fetchone()

        if row is None:
            return None

        record = dict(row)
        record["samples"] = json.loads(record.pop("samples_json", "[]"))
        return record

    def delete_test(self, test_id: int) -> None:
        """Elimina un collaudo dal database."""
        with self._connect() as conn:
            conn.execute("DELETE FROM test_results WHERE id = ?", (test_id,))

    # ─── Impostazioni ────────────────────────────────────────────────────────

    def get_password(self) -> str:
        """Legge la password dal database."""
        with self._connect() as conn:
            cursor = conn.execute("SELECT value FROM app_settings WHERE key='password'")
            row = cursor.fetchone()
            if row:
                return row[0]
            return "1234"

    def set_password(self, new_password: str) -> None:
        """Aggiorna la password nel database."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('password', ?)",
                (new_password,)
            )

    # ─── Helper ─────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)
