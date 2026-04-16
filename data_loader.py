"""
data_loader.py
==============
Initialise la base de données SQLite (warehouse.db) avec toutes les tables
nécessaires au projet. À lancer une fois avant de démarrer l'application.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "warehouse.db"


def init_database():
    """
    Crée (ou recrée) toutes les tables dans warehouse.db.
    Si les tables existent déjà, elles ne sont pas écrasées (IF NOT EXISTS).
    """
    print(f"🗄️  Initialisation de la base : {DB_PATH}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Table des matières (miroir de stocks.csv) ─────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matiere (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nom                 TEXT    NOT NULL UNIQUE,
            stock_actuel        REAL    NOT NULL DEFAULT 0,
            stock_securite      REAL    NOT NULL DEFAULT 0,
            seuil_reappro       REAL    NOT NULL DEFAULT 0,
            qte_reappro_defaut  REAL    NOT NULL DEFAULT 0,
            updated_at          TEXT
        )
    """)

    # ── Table des commandes production (miroir de commandes.csv) ─────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commande_prod (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            produit     TEXT    NOT NULL,
            quantite    REAL    NOT NULL,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table des commandes fournisseur (résultat des validations) ────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commande_fournisseur (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            matiere               TEXT    NOT NULL,
            quantite              REAL    NOT NULL,
            fournisseur_id        INTEGER,
            fournisseur_nom       TEXT,
            statut                TEXT    NOT NULL,   -- accepté/retardé/refusé
            delai_jours           INTEGER,
            date_livraison_prevue TEXT,
            prix_total            REAL,
            decision_ia_id        INTEGER,            -- FK vers ia_decisions
            created_at            TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    _ensure_commande_fournisseur_schema(conn)

    # ── Table des décisions IA ────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ia_decisions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            matiere       TEXT    NOT NULL,
            action        TEXT    NOT NULL,           -- commander/attendre
            quantite      REAL    NOT NULL DEFAULT 0,
            justification TEXT,
            urgence       TEXT,                       -- critique/élevée/moyenne/faible
            source        TEXT,                       -- bedrock_llm/regles_simples
            stock_actuel  REAL,
            conso_prevue  REAL,
            stock_futur   REAL,
            statut        TEXT    DEFAULT 'en_attente', -- validée/rejetée/modifiée
            timestamp     TEXT
        )
    """)

    conn.commit()
    print("✅ Tables créées : matiere, commande_prod, commande_fournisseur, ia_decisions")

    # ── Peuplement initial depuis les CSV ─────────────────────────────────
    _importer_stocks(conn)
    _importer_commandes(conn)

    conn.close()
    print("✅ Base de données prête.")


def _ensure_commande_fournisseur_schema(conn: sqlite3.Connection):
    """Ajoute les colonnes manquantes dans commande_fournisseur si besoin."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(commande_fournisseur)")
    existing = {row[1] for row in cur.fetchall()}

    missing_columns = [
        ("fournisseur_id", "INTEGER"),
        ("fournisseur_nom", "TEXT"),
        ("prix_total", "REAL"),
    ]

    for col_name, col_type in missing_columns:
        if col_name not in existing:
            cur.execute(f"ALTER TABLE commande_fournisseur ADD COLUMN {col_name} {col_type}")
    conn.commit()


def _importer_stocks(conn: sqlite3.Connection):
    """Importe stocks.csv dans la table matiere (UPSERT)."""
    csv_path = DATA_DIR / "stocks.csv"
    if not csv_path.exists():
        print(f"⚠️  {csv_path} introuvable, table matiere non peuplée.")
        return

    df = pd.read_csv(csv_path)
    now = datetime.now().isoformat()

    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO matiere (nom, stock_actuel, stock_securite, seuil_reappro,
                                  qte_reappro_defaut, updated_at)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(nom) DO UPDATE SET
                stock_actuel       = excluded.stock_actuel,
                stock_securite     = excluded.stock_securite,
                seuil_reappro      = excluded.seuil_reappro,
                qte_reappro_defaut = excluded.qte_reappro_defaut,
                updated_at         = excluded.updated_at
        """, (
            row["nom"], row["stock_actuel"], row["stock_securite"],
            row["seuil_reappro"], row["qte_reappro_defaut"], now,
        ))
    conn.commit()
    print(f"   📦 {len(df)} matières importées dans la table matiere.")


def _importer_commandes(conn: sqlite3.Connection):
    """Importe commandes.csv dans la table commande_prod."""
    csv_path = DATA_DIR / "commandes.csv"
    if not csv_path.exists():
        print(f"⚠️  {csv_path} introuvable, table commande_prod non peuplée.")
        return

    df = pd.read_csv(csv_path)
    # Évite les doublons si on relance le script
    conn.execute("DELETE FROM commande_prod")
    for _, row in df.iterrows():
        conn.execute(
            "INSERT INTO commande_prod (produit, quantite, date) VALUES (?,?,?)",
            (row["produit"], row["quantite"], row["date"]),
        )
    conn.commit()
    print(f"   📋 {len(df)} commandes de production importées.")


if __name__ == "__main__":
    init_database()