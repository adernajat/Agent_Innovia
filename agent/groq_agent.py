"""
agent/groq_agent.py
======================
Agent IA principal utilisant Groq (Llama 3.3) pour les décisions LLM.
Gratuit et rapide !
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from groq import Groq
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# ─── Chemins des fichiers ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "warehouse.db"

# ─── Modèle Groq ─────────────────────────────────────────────────────────────
MODEL_ID = "llama-3.3-70b-versatile"  # Gratuit, 70B paramètres


class GroqAgent:
    """
    Agent intelligent de gestion des stocks utilisant Groq (gratuit).
    Lit les données CSV, calcule les besoins futurs, 
    interroge Groq, et propose des décisions logistiques.
    """

    def __init__(self, api_key: str = None):
        """Initialise le client Groq et charge les données CSV."""
        self.stocks_df = None
        self.consommation_df = None
        self.commandes_df = None
        self.groq_ok = False

        # Tentative de connexion à Groq
        try:
            # Priorité à la clé passée en paramètre, sinon celle du .env
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                raise ValueError("Clé API Groq manquante. Mettez-la dans .env")
            
            self.client = Groq(api_key=api_key)
            self.groq_ok = True
            print("✅ Groq initialisé avec succès (gratuit !)")
        except Exception as e:
            print(f"⚠️  Groq non disponible : {e}")
            print("   Mode fallback (règles simples) activé.")

        # Chargement immédiat des CSV
        self.charger_csv()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. CHARGEMENT DES DONNÉES
    # ─────────────────────────────────────────────────────────────────────────

    def charger_csv(self):
        """Lit les trois fichiers CSV depuis le dossier data/."""
        try:
            self.stocks_df = pd.read_csv(DATA_DIR / "stocks.csv")
            self.consommation_df = pd.read_csv(DATA_DIR / "consommation.csv")
            self.commandes_df = pd.read_csv(DATA_DIR / "commandes.csv")
            print(f"📂 CSV chargés : {len(self.stocks_df)} matières, "
                  f"{len(self.commandes_df)} commandes.")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"❌ Fichier CSV manquant : {e}")

    def get_matieres(self) -> list:
        """Retourne la liste des matières disponibles."""
        return self.stocks_df["nom"].tolist()

    def get_stock_info(self, matiere: str) -> dict:
        """Retourne les infos de stock pour une matière donnée."""
        row = self.stocks_df[self.stocks_df["nom"] == matiere]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            "nom": r["nom"],
            "stock_actuel": int(r["stock_actuel"]),
            "stock_securite": int(r["stock_securite"]),
            "seuil_reappro": int(r["seuil_reappro"]),
            "qte_reappro_defaut": int(r["qte_reappro_defaut"]),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. CALCULS PRÉVISIONNELS
    # ─────────────────────────────────────────────────────────────────────────

    def calculer_consommation_previsionnelle(self, matiere: str) -> float:
        """Calcule la consommation totale prévue pour une matière."""
        total = 0.0
        for _, cmd in self.commandes_df.iterrows():
            produit = cmd["produit"]
            qte_cmd = float(cmd["quantite"])

            match = self.consommation_df[
                (self.consommation_df["produit"] == produit) &
                (self.consommation_df["matiere"] == matiere)
            ]
            if not match.empty:
                qte_par_100 = float(match.iloc[0]["quantite_par_100_unites"])
                total += qte_cmd * (qte_par_100 / 100.0)

        return round(total, 2)

    def calculer_stock_futur(self, matiere: str) -> dict:
        """Calcule et retourne les prévisions de stock."""
        info = self.get_stock_info(matiere)
        conso = self.calculer_consommation_previsionnelle(matiere)
        futur = info["stock_actuel"] - conso

        return {
            **info,
            "conso_prevue": conso,
            "stock_futur": round(futur, 2),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DÉCISION VIA GROQ (LLM GRATUIT)
    # ─────────────────────────────────────────────────────────────────────────

    def proposer_decision_llm(self, matiere: str) -> dict:
        """Appelle Groq pour obtenir une recommandation."""
        if not self.groq_ok:
            print("⚠️  Groq non disponible → fallback règles.")
            return self.proposer_decision_regles(matiere)

        data = self.calculer_stock_futur(matiere)

        # Construction du prompt
        prompt = f"""Tu es un expert en logistique industrielle.
Réponds UNIQUEMENT au format JSON valide, sans texte avant ni après.

Matière: {data['nom']}
Stock actuel: {data['stock_actuel']}
Stock sécurité: {data['stock_securite']}
Seuil réapprovisionnement: {data['seuil_reappro']}
Consommation prévue: {data['conso_prevue']}
Stock futur estimé: {data['stock_futur']}

Retourne exactement ce JSON :
{{"action": "commander" ou "attendre", "quantite": entier, 
"justification": "explication courte en français", 
"urgence": "critique" ou "élevée" ou "moyenne" ou "faible"}}"""

        try:
            response = self.client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "Tu es un expert en logistique. Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )

            # Lecture de la réponse
            raw_text = response.choices[0].message.content.strip()

            # Extraction du JSON (suppression des backticks si présents)
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            
            decision = json.loads(raw_text)

            # Validation des champs requis
            required_fields = ["action", "quantite", "justification", "urgence"]
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Champ '{field}' manquant")

            # Ajout des métadonnées
            decision.update({
                "matiere": matiere,
                "source": "groq_llm",
                "stock_actuel": data["stock_actuel"],
                "conso_prevue": data["conso_prevue"],
                "stock_futur": data["stock_futur"],
                "timestamp": datetime.now().isoformat(),
            })
            print(f"✅ Décision Groq pour {matiere}: {decision['action']}")
            return decision

        except Exception as e:
            print(f"⚠️  Erreur Groq ({e}) → fallback règles.")
            return self.proposer_decision_regles(matiere)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. FALLBACK : RÈGLES SIMPLES (sans LLM)
    # ─────────────────────────────────────────────────────────────────────────

    def proposer_decision_regles(self, matiere: str) -> dict:
        """Logique déterministe de secours."""
        data = self.calculer_stock_futur(matiere)
        futur = data["stock_futur"]
        seuil = data["seuil_reappro"]
        defaut = data["qte_reappro_defaut"]
        secu = data["stock_securite"]

        if futur < 0:
            qte = max(defaut, int(seuil - futur + secu))
            urgence = "critique"
            justif = f"Stock futur négatif ({futur:.0f}). Rupture certaine."
            action = "commander"
        elif futur < seuil:
            qte = max(defaut, int(seuil - futur + secu))
            urgence = "élevée" if futur < seuil * 0.5 else "moyenne"
            justif = f"Stock futur ({futur:.0f}) sous le seuil ({seuil})."
            action = "commander"
        else:
            qte = 0
            urgence = "faible"
            justif = f"Stock futur ({futur:.0f}) supérieur au seuil ({seuil})."
            action = "attendre"

        return {
            "matiere": matiere,
            "action": action,
            "quantite": qte,
            "justification": justif,
            "urgence": urgence,
            "source": "regles_simples",
            "stock_actuel": data["stock_actuel"],
            "conso_prevue": data["conso_prevue"],
            "stock_futur": futur,
            "timestamp": datetime.now().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. PERSISTANCE SQLITE
    # ─────────────────────────────────────────────────────────────────────────

    def enregistrer_proposition(self, decision: dict) -> int:
        """Sauvegarde la proposition dans la table ia_decisions."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO ia_decisions
                    (matiere, action, quantite, justification, urgence,
                     source, stock_actuel, conso_prevue, stock_futur,
                     statut, timestamp)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                decision.get("matiere"),
                decision.get("action"),
                decision.get("quantite", 0),
                decision.get("justification"),
                decision.get("urgence"),
                decision.get("source", "inconnu"),
                decision.get("stock_actuel", 0),
                decision.get("conso_prevue", 0),
                decision.get("stock_futur", 0),
                "en_attente",
                decision.get("timestamp", datetime.now().isoformat()),
            ))
            conn.commit()
            row_id = cur.lastrowid
            conn.close()
            return row_id
        except Exception as e:
            print(f"❌ Erreur SQLite : {e}")
            return -1

    def maj_statut_decision(self, decision_id: int, statut: str):
        """Met à jour le statut d'une décision."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE ia_decisions SET statut=? WHERE id=?",
                (statut, decision_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erreur mise à jour : {e}")

    def get_historique(self, limit: int = 50) -> pd.DataFrame:
        """Retourne les N dernières décisions."""
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(
                "SELECT * FROM ia_decisions ORDER BY id DESC LIMIT ?",
                conn, params=(limit,)
            )
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Erreur lecture : {e}")
            return pd.DataFrame()