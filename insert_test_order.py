"""
Insert a test supplier order into the local SQLite database.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "warehouse.db"


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    now = datetime.now()
    date_livraison = (now + timedelta(days=3)).strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO commande_fournisseur
            (matiere, quantite, statut, delai_jours, date_livraison_prevue, decision_ia_id)
        VALUES (?,?,?,?,?,?)
        """,
        (
            "Acier",
            250.0,
            "accepte",
            3,
            date_livraison,
            None,
        ),
    )
    conn.commit()
    conn.close()

    print("Test order inserted.")


if __name__ == "__main__":
    main()
