"""
supplier_api/server.py
======================
API fournisseur améliorée avec liste de fournisseurs réels
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json

from suppliers_data import SUPPLIERS, get_recommendations, calculate_price

app = Flask(__name__)
CORS(app)  # Permet les requêtes cross-origin

DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.db"


def _enregistrer_commande_fournisseur(
    matiere: str,
    quantite: float,
    fournisseur_id: int,
    fournisseur_nom: str,
    statut: str,
    delai_jours: int,
    date_livraison: str,
    prix_total: float,
    decision_ia_id: int | None,
):
    """Persiste la commande fournisseur dans SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """INSERT INTO commande_fournisseur
               (matiere, quantite, fournisseur_id, fournisseur_nom, statut, 
                delai_jours, date_livraison_prevue, prix_total, decision_ia_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (matiere, quantite, fournisseur_id, fournisseur_nom, statut, 
             delai_jours, date_livraison, prix_total, decision_ia_id),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️  Erreur SQLite fournisseur : {e}")


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de santé pour vérifier que l'API est up."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/fournisseurs", methods=["GET"])
def get_all_suppliers():
    """Retourne la liste de tous les fournisseurs"""
    return jsonify({"fournisseurs": SUPPLIERS, "total": len(SUPPLIERS)})


@app.route("/fournisseurs/<int:fournisseur_id>", methods=["GET"])
def get_supplier(fournisseur_id):
    """Retourne les détails d'un fournisseur"""
    supplier = next((s for s in SUPPLIERS if s["id"] == fournisseur_id), None)
    if supplier:
        return jsonify(supplier)
    return jsonify({"error": "Fournisseur non trouvé"}), 404


@app.route("/recommandations", methods=["POST"])
def get_recommendations_api():
    """
    Retourne une liste de fournisseurs recommandés pour une matière
    
    Corps JSON :
    {
        "matiere": "Acier",
        "quantite": 500,
        "urgence": "critique"
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    
    matiere = data.get("matiere")
    quantite = data.get("quantite")
    urgence = data.get("urgence", "moyenne")
    
    if not matiere or not quantite:
        return jsonify({"error": "Matière et quantité requises"}), 400
    
    recommendations = get_recommendations(matiere, quantite, urgence)
    
    return jsonify({
        "matiere": matiere,
        "quantite": quantite,
        "urgence": urgence,
        "recommandations": recommendations,
        "total": len(recommendations)
    })


@app.route("/passer_commande", methods=["POST"])
def passer_commande():
    """
    Passe une commande auprès d'un fournisseur spécifique
    
    Corps JSON :
    {
        "matiere": "Acier",
        "quantite": 500,
        "fournisseur_id": 1,
        "decision_ia_id": 12
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    
    matiere = data.get("matiere")
    quantite = float(data.get("quantite", 0))
    fournisseur_id = data.get("fournisseur_id")
    decision_ia_id = data.get("decision_ia_id")
    
    # Validation
    if quantite <= 0:
        return jsonify({"statut": "refusé", "message": "Quantité invalide"}), 400
    
    # Trouver le fournisseur
    supplier = next((s for s in SUPPLIERS if s["id"] == fournisseur_id), None)
    if not supplier:
        return jsonify({"statut": "refusé", "message": "Fournisseur non trouvé"}), 404
    
    # Simulation de réponse (pour plus de réalisme)
    tirage = random.random()
    
    if tirage < 0.8:  # 80% accepté
        statut = "accepté"
        # Délai selon l'urgence (si spécifié) ou standard
        delai_type = data.get("delai_type", "standard")
        delai_jours = supplier["delai_livraison"].get(delai_type, supplier["delai_livraison"]["standard"])
        
        # Ajouter un peu de variabilité aléatoire
        if random.random() < 0.3:
            delai_jours += random.randint(0, 2)
        
        message = f"Commande acceptée par {supplier['nom']}"
        
    elif tirage < 0.95:  # 15% retardé
        statut = "retardé"
        delai_jours = supplier["delai_livraison"]["standard"] + random.randint(2, 5)
        message = f"Commande acceptée avec retard par {supplier['nom']}"
        
    else:  # 5% refusé
        statut = "refusé"
        delai_jours = 0
        message = f"Commande refusée par {supplier['nom']} (stock insuffisant)"
    
    # Calculer le prix
    prix_total = calculate_price(supplier, matiere, quantite)
    
    date_livraison = (
        (datetime.now() + timedelta(days=delai_jours)).strftime("%Y-%m-%d")
        if delai_jours > 0 else None
    )
    
    # Persistance
    _enregistrer_commande_fournisseur(
        matiere, quantite, fournisseur_id, supplier["nom"],
        statut, delai_jours, date_livraison or "", prix_total, decision_ia_id
    )
    
    response_body = {
        "statut": statut,
        "fournisseur": supplier["nom"],
        "fournisseur_id": fournisseur_id,
        "delai_jours": delai_jours,
        "date_livraison_prevue": date_livraison,
        "prix_total": prix_total,
        "message": message,
        "matiere": matiere,
        "quantite": quantite,
        "timestamp": datetime.now().isoformat(),
    }
    
    http_code = 200 if statut != "refusé" else 422
    return jsonify(response_body), http_code


@app.route("/historique_commandes", methods=["GET"])
def historique_commandes():
    """Retourne les 50 dernières commandes fournisseur"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, matiere, quantite, fournisseur_nom, statut, delai_jours,
                   date_livraison_prevue, prix_total, created_at
            FROM commande_fournisseur
            ORDER BY id DESC LIMIT 50
        """)
        rows = cur.fetchall()
        conn.close()
        keys = ["id", "matiere", "quantite", "fournisseur", "statut", 
                "delai_jours", "date_livraison_prevue", "prix_total", "created_at"]
        return jsonify([dict(zip(keys, r)) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 API Fournisseur démarrée sur http://localhost:5001")
    print(f"📦 {len(SUPPLIERS)} fournisseurs disponibles")
    app.run(host="0.0.0.0", port=5001, debug=False)