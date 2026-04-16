"""
agent/bedrock_agent.py
======================
Agent IA principal : lit les CSV, calcule les stocks futurs,
interroge AWS Bedrock (Claude Haiku), et enregistre les décisions dans SQLite.
"""

import boto3
import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# ─── Chemins des fichiers ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "warehouse.db"

# ─── Modèle AWS Bedrock ──────────────────────────────────────────────────────
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


class BedrockAgent:
    """
    Agent intelligent de gestion des stocks.
    Lit les données CSV, calcule les besoins futurs, 
    interroge Claude via AWS Bedrock, et propose des décisions logistiques.
    """

    def __init__(self):
        self.stocks_df = None
        self.consommation_df = None
        self.commandes_df = None

        self.llm_ok = False  # remplace bedrock_ok

        try:
            self.client = OpenAI(
                api_key="sk-fc3bdcd4578b4bf39ad9f14c37f4d918",
                base_url="https://api.deepseek.com"
            )
            self.llm_ok = True
            print("✅ DeepSeek initialisé avec succès.")
        except Exception as e:
            print(f"⚠️ DeepSeek non disponible : {e}")
            print("Mode fallback activé.")

        self.charger_csv()
    # ─────────────────────────────────────────────────────────────────────────
    # 1. CHARGEMENT DES DONNÉES
    # ─────────────────────────────────────────────────────────────────────────

    def charger_csv(self):
        """
        Lit les trois fichiers CSV depuis le dossier data/.
        Lève une exception explicite si un fichier est absent.
        """
        try:
            self.stocks_df       = pd.read_csv(DATA_DIR / "stocks.csv")
            self.consommation_df = pd.read_csv(DATA_DIR / "consommation.csv")
            self.commandes_df    = pd.read_csv(DATA_DIR / "commandes.csv")
            print(f"📂 CSV chargés : {len(self.stocks_df)} matières, "
                  f"{len(self.commandes_df)} commandes.")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"❌ Fichier CSV manquant : {e}")

    def get_matieres(self) -> list[str]:
        """Retourne la liste des matières disponibles dans stocks.csv."""
        return self.stocks_df["nom"].tolist()

    def get_stock_info(self, matiere: str) -> dict:
        """
        Retourne les infos de stock pour une matière donnée.
        Retourne {} si la matière n'existe pas.
        """
        row = self.stocks_df[self.stocks_df["nom"] == matiere]
        if row.empty:
            return {}
        r = row.iloc[0]
        return {
            "nom":              r["nom"],
            "stock_actuel":     int(r["stock_actuel"]),
            "stock_securite":   int(r["stock_securite"]),
            "seuil_reappro":    int(r["seuil_reappro"]),
            "qte_reappro_defaut": int(r["qte_reappro_defaut"]),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. CALCULS PRÉVISIONNELS
    # ─────────────────────────────────────────────────────────────────────────

    def calculer_consommation_previsionnelle(self, matiere: str) -> float:
        """
        Calcule la consommation totale prévue pour une matière
        en croisant commandes.csv et consommation.csv.

        Formule : Σ (quantité_commande × (quantite_par_100_unites / 100))
        """
        total = 0.0
        for _, cmd in self.commandes_df.iterrows():
            produit  = cmd["produit"]
            qte_cmd  = float(cmd["quantite"])

            # Cherche la ligne (produit, matiere) dans consommation.csv
            match = self.consommation_df[
                (self.consommation_df["produit"] == produit) &
                (self.consommation_df["matiere"] == matiere)
            ]
            if not match.empty:
                qte_par_100 = float(match.iloc[0]["quantite_par_100_unites"])
                total += qte_cmd * (qte_par_100 / 100.0)

        return round(total, 2)

    def calculer_stock_futur(self, matiere: str) -> dict:
        """
        Calcule et retourne un dictionnaire complet avec :
          - stock_actuel, conso_prevue, stock_futur
          - stock_securite, seuil_reappro, qte_reappro_defaut
        """
        info  = self.get_stock_info(matiere)
        conso = self.calculer_consommation_previsionnelle(matiere)
        futur = info["stock_actuel"] - conso

        return {
            **info,
            "conso_prevue":  conso,
            "stock_futur":   round(futur, 2),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DÉCISION VIA AWS BEDROCK (LLM)
    # ─────────────────────────────────────────────────────────────────────────
    def proposer_decision_llm(self, matiere: str) -> dict:

        if not self.llm_ok:
            return self.proposer_decision_regles(matiere)

        data = self.calculer_stock_futur(matiere)

        prompt = f"""
            Tu es un expert en logistique industrielle.

            Réponds UNIQUEMENT en JSON valide :

            {{
            "action": "commander" ou "attendre",
            "quantite": <entier>,
            "justification": "<explication courte>",
            "urgence": "critique" ou "élevée" ou "moyenne" ou "faible"
            }}

            Données:
            Matière: {data['nom']}
            Stock actuel: {data['stock_actuel']}
            Stock sécurité: {data['stock_securite']}
            Seuil: {data['seuil_reappro']}
            Conso prévue: {data['conso_prevue']}
            Stock futur: {data['stock_futur']}
            """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            raw_text = response.choices[0].message.content.strip()

            # Nettoyage JSON
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]

            decision = json.loads(raw_text)

            decision.update({
                "matiere": matiere,
                "source": "deepseek_llm",
                "stock_actuel": data["stock_actuel"],
                "conso_prevue": data["conso_prevue"],
                "stock_futur": data["stock_futur"],
                "timestamp": datetime.now().isoformat(),
            })

            return decision

        except Exception as e:
            print(f"⚠️ Erreur DeepSeek ({e}) → fallback.")
            return self.proposer_decision_regles(matiere)
    # ─────────────────────────────────────────────────────────────────────────
    # 4. FALLBACK : RÈGLES SIMPLES (sans LLM)
    # ─────────────────────────────────────────────────────────────────────────

    def proposer_decision_regles(self, matiere: str) -> dict:
        """
        Logique déterministe de secours quand Bedrock est indisponible.
        Règles :
          - stock_futur < 0          → commander, urgence critique
          - stock_futur < seuil      → commander, urgence élevée/moyenne
          - stock_futur >= seuil     → attendre, urgence faible
        """
        data   = self.calculer_stock_futur(matiere)
        futur  = data["stock_futur"]
        seuil  = data["seuil_reappro"]
        defaut = data["qte_reappro_defaut"]
        secu   = data["stock_securite"]

        if futur < 0:
            # Rupture garantie → commande urgente
            qte     = max(defaut, int(seuil - futur + secu))
            urgence = "critique"
            justif  = (f"Stock futur négatif ({futur:.0f}). "
                       "Rupture certaine sans réapprovisionnement immédiat.")
            action  = "commander"

        elif futur < seuil:
            # Sous le seuil → commande préventive
            qte     = max(defaut, int(seuil - futur + secu))
            urgence = "élevée" if futur < seuil * 0.5 else "moyenne"
            justif  = (f"Stock futur ({futur:.0f}) sous le seuil ({seuil}). "
                       "Réapprovisionnement préventif recommandé.")
            action  = "commander"

        else:
            # Stock suffisant
            qte     = 0
            urgence = "faible"
            justif  = (f"Stock futur ({futur:.0f}) supérieur au seuil ({seuil}). "
                       "Aucune action requise.")
            action  = "attendre"

        return {
            "matiere":      matiere,
            "action":       action,
            "quantite":     qte,
            "justification": justif,
            "urgence":      urgence,
            "source":       "regles_simples",
            "stock_actuel": data["stock_actuel"],
            "conso_prevue": data["conso_prevue"],
            "stock_futur":  futur,
            "timestamp":    datetime.now().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. PERSISTANCE SQLITE
    # ─────────────────────────────────────────────────────────────────────────

    def enregistrer_proposition(self, decision: dict) -> int:
        """
        Sauvegarde la proposition IA dans la table ia_decisions.
        Retourne l'id de la ligne insérée.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur  = conn.cursor()
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
            print(f"❌ Erreur SQLite enregistrement : {e}")
            return -1

    def maj_statut_decision(self, decision_id: int, statut: str):
        """
        Met à jour le statut d'une décision (validée, rejetée, modifiée).
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE ia_decisions SET statut=? WHERE id=?",
                (statut, decision_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erreur mise à jour statut : {e}")

    def get_historique(self, limit: int = 50) -> pd.DataFrame:
        """Retourne les N dernières décisions enregistrées."""
        try:
            conn = sqlite3.connect(DB_PATH)
            df   = pd.read_sql_query(
                "SELECT * FROM ia_decisions ORDER BY id DESC LIMIT ?",
                conn, params=(limit,)
            )
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Erreur lecture historique : {e}")
            return pd.DataFrame()