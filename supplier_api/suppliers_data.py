"""
supplier_api/suppliers_data.py
===============================
Lecture des fournisseurs depuis un fichier CSV
"""

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import os

# Chemin du fichier CSV
BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "data" / "fournisseurs.csv"

def load_suppliers_from_csv():
    """
    Charge les fournisseurs depuis le fichier CSV
    Si le fichier n'existe pas, utilise les données par défaut
    """
    if not CSV_PATH.exists():
        print(f"⚠️ Fichier {CSV_PATH} non trouvé, utilisation des fournisseurs par défaut")
        return get_default_suppliers()
    
    try:
        df = pd.read_csv(CSV_PATH)
        suppliers_dict = {}
        
        for _, row in df.iterrows():
            supplier_id = int(row["id"])
            
            # Si le fournisseur n'existe pas encore, le créer
            if supplier_id not in suppliers_dict:
                suppliers_dict[supplier_id] = {
                    "id": supplier_id,
                    "nom": row["nom"],
                    "pays": row["pays"],
                    "ville": row["ville"],
                    "email": row["email"],
                    "telephone": row["telephone"],
                    "matieres": [],
                    "prix_unitaire": {},
                    "delai_livraison": {
                        "standard": int(row["delai_standard"]),
                        "express": int(row["delai_express"])
                    },
                    "qualite": float(row["qualite"]),
                    "fiable": True,
                    "description": row["description"]
                }
            
            # Ajouter la matière et son prix
            matiere = row["matiere"]
            prix = float(row["prix_unitaire"])
            
            suppliers_dict[supplier_id]["matieres"].append(matiere)
            suppliers_dict[supplier_id]["prix_unitaire"][matiere] = prix
        
        result = list(suppliers_dict.values())
        print(f"✅ {len(result)} fournisseurs chargés depuis CSV")
        
        # Debug: Afficher les matières disponibles
        all_matieres = set()
        for s in result:
            for m in s["matieres"]:
                all_matieres.add(m)
        print(f"📋 Matières disponibles: {sorted(all_matieres)}")
        
        return result
    
    except Exception as e:
        print(f"❌ Erreur lors du chargement du CSV: {e}")
        return get_default_suppliers()

def get_default_suppliers():
    """Fournisseurs par défaut (si CSV non trouvé)"""
    return [
        {
            "id": 1,
            "nom": "Acier France SAS",
            "pays": "France",
            "ville": "Lyon",
            "email": "contact@acierfrance.fr",
            "telephone": "+33 4 72 00 00 01",
            "matieres": ["Acier", "Métaux ferreux"],
            "prix_unitaire": {
                "Acier": 2.50,
                "Métaux ferreux": 1.80
            },
            "delai_livraison": {
                "standard": 3,
                "express": 1
            },
            "qualite": 4.5,
            "fiable": True,
            "description": "Leader français de l'acier depuis 1985"
        },
        {
            "id": 2,
            "nom": "EuroSteel GmbH",
            "pays": "Allemagne",
            "ville": "Düsseldorf",
            "email": "sales@eurosteel.de",
            "telephone": "+49 211 555 0123",
            "matieres": ["Acier", "Inox"],
            "prix_unitaire": {
                "Acier": 2.30,
                "Inox": 3.20
            },
            "delai_livraison": {
                "standard": 4,
                "express": 2
            },
            "qualite": 4.8,
            "fiable": True,
            "description": "Acier européen haute qualité"
        },
        {
            "id": 3,
            "nom": "Plastiques Modernes SA",
            "pays": "Belgique",
            "ville": "Bruxelles",
            "email": "info@plastiquesmodernes.be",
            "telephone": "+32 2 555 1234",
            "matieres": ["Plastique", "Polyéthylène"],
            "prix_unitaire": {
                "Plastique": 0.85,
                "Polyéthylène": 1.10
            },
            "delai_livraison": {
                "standard": 2,
                "express": 1
            },
            "qualite": 4.3,
            "fiable": True,
            "description": "Spécialiste des plastiques industriels"
        },
        {
            "id": 4,
            "nom": "Composants Electroniques SARL",
            "pays": "France",
            "ville": "Grenoble",
            "email": "commercial@composants-electroniques.fr",
            "telephone": "+33 4 76 00 00 01",
            "matieres": ["Composants", "Électronique"],
            "prix_unitaire": {
                "Composants": 12.50,
                "Électronique": 15.00
            },
            "delai_livraison": {
                "standard": 5,
                "express": 2
            },
            "qualite": 4.7,
            "fiable": True,
            "description": "Composants électroniques haute précision"
        },
        {
            "id": 5,
            "nom": "Peintures Industrielles Dupont",
            "pays": "France",
            "ville": "Marseille",
            "email": "ventes@peintures-dupont.fr",
            "telephone": "+33 4 91 00 00 01",
            "matieres": ["Peinture", "Revêtements"],
            "prix_unitaire": {
                "Peinture": 3.20,
                "Revêtements": 4.50
            },
            "delai_livraison": {
                "standard": 3,
                "express": 1
            },
            "qualite": 4.6,
            "fiable": True,
            "description": "Peintures industrielles depuis 1920"
        },
        {
            "id": 6,
            "nom": "Acier Premium Italia",
            "pays": "Italie",
            "ville": "Turin",
            "email": "sales@acierpremium.it",
            "telephone": "+39 011 555 6789",
            "matieres": ["Acier", "Métaux spéciaux"],
            "prix_unitaire": {
                "Acier": 2.70,
                "Métaux spéciaux": 5.00
            },
            "delai_livraison": {
                "standard": 5,
                "express": 3
            },
            "qualite": 4.9,
            "fiable": True,
            "description": "Acier premium pour applications critiques"
        },
        {
            "id": 7,
            "nom": "Plastics Iberia SL",
            "pays": "Espagne",
            "ville": "Barcelone",
            "email": "info@plasticsiberia.es",
            "telephone": "+34 93 555 0123",
            "matieres": ["Plastique", "Résines"],
            "prix_unitaire": {
                "Plastique": 0.75,
                "Résines": 2.80
            },
            "delai_livraison": {
                "standard": 3,
                "express": 2
            },
            "qualite": 4.2,
            "fiable": True,
            "description": "Solutions plastiques économiques"
        },
        {
            "id": 8,
            "nom": "EuroComponents BV",
            "pays": "Pays-Bas",
            "ville": "Amsterdam",
            "email": "sales@eurocomponents.nl",
            "telephone": "+31 20 555 6789",
            "matieres": ["Composants", "Électronique"],
            "prix_unitaire": {
                "Composants": 11.80,
                "Électronique": 14.50
            },
            "delai_livraison": {
                "standard": 4,
                "express": 2
            },
            "qualite": 4.4,
            "fiable": True,
            "description": "Distribution européenne de composants"
        }
    ]

# Chargement global des fournisseurs
SUPPLIERS = load_suppliers_from_csv()

def get_suppliers_by_matiere(matiere: str):
    """
    Retourne les fournisseurs proposant une matière donnée
    Recherche insensible à la casse et exacte
    """
    if not matiere:
        return []
    
    matiere_lower = matiere.lower().strip()
    results = []
    
    for supplier in SUPPLIERS:
        for m in supplier["matieres"]:
            # Comparaison exacte insensible à la casse
            if matiere_lower == m.lower():
                results.append(supplier)
                break
    
    # Debug
    print(f"🔍 Recherche fournisseurs pour '{matiere}' -> {len(results)} trouvés")
    if results:
        for r in results:
            print(f"   ✅ {r['nom']} - {r['prix_unitaire'].get(matiere, 'N/A')}€/unité")
    
    return results

def calculate_price(supplier: dict, matiere: str, quantite: float) -> float:
    """Calcule le prix total pour une commande"""
    # Chercher le prix pour la matière exacte
    price_per_unit = supplier["prix_unitaire"].get(matiere)
    
    if not price_per_unit:
        # Essayer de trouver une matière similaire
        for key in supplier["prix_unitaire"]:
            if matiere.lower() in key.lower() or key.lower() in matiere.lower():
                price_per_unit = supplier["prix_unitaire"][key]
                break
        else:
            # Prix par défaut si rien trouvé
            price_per_unit = 10.0
            print(f"⚠️ Prix par défaut pour {matiere} chez {supplier['nom']}: 10.00€")
    
    total = price_per_unit * quantite
    
    # Remise pour grande quantité
    if quantite > 1000:
        total *= 0.95  # 5% de remise
        print(f"   💰 Remise 5% appliquée pour quantité > 1000")
    elif quantite > 500:
        total *= 0.97  # 3% de remise
        print(f"   💰 Remise 3% appliquée pour quantité > 500")
    
    return round(total, 2)

def get_recommendations(matiere: str, quantite: float, urgence: str) -> list:
    """
    Retourne une liste de fournisseurs recommandés avec leurs offres
    """
    suppliers = get_suppliers_by_matiere(matiere)
    
    # Si aucun fournisseur trouvé, retourner une liste vide avec un message
    if not suppliers:
        print(f"⚠️ Aucun fournisseur trouvé pour la matière: '{matiere}'")
        print(f"   Matières disponibles: {list(set([m for s in SUPPLIERS for m in s['matieres']]))}")
        return []
    
    recommendations = []
    for supplier in suppliers:
        # Déterminer le délai selon l'urgence
        if urgence == "critique":
            delai_type = "express"
        else:
            delai_type = "standard"
        
        delai = supplier["delai_livraison"].get(delai_type, supplier["delai_livraison"]["standard"])
        price = calculate_price(supplier, matiere, quantite)
        
        # Score de recommandation
        score = supplier["qualite"]
        if delai <= 2:
            score += 0.5
        if price < 1000:
            score += 0.3
        elif price < 5000:
            score += 0.1
        
        recommendations.append({
            "fournisseur": supplier,
            "prix_total": price,
            "prix_unitaire": round(price / quantite, 2) if quantite > 0 else 0,
            "delai_jours": delai,
            "delai_type": delai_type,
            "date_livraison_prevue": (datetime.now() + timedelta(days=delai)).strftime("%Y-%m-%d"),
            "score": round(score, 1),
            "matiere": matiere,
            "quantite": quantite
        })
    
    # Trier par score décroissant
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"📊 {len(recommendations)} recommandations générées pour {matiere}")
    return recommendations[:5]  # Top 5 recommandations

def reload_suppliers():
    """Recharge les fournisseurs depuis le CSV (utile pour le rechargement dynamique)"""
    global SUPPLIERS
    SUPPLIERS = load_suppliers_from_csv()
    print(f"✅ Fournisseurs rechargés: {len(SUPPLIERS)} disponibles")
    return SUPPLIERS

# Afficher les statistiques au démarrage
print(f"🚀 Module suppliers_data chargé")
print(f"📦 {len(SUPPLIERS)} fournisseurs disponibles")