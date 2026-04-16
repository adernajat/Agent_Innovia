"""
test_agent.py
=============
Tests complets de l'agent IA.
Lance avec : python test_agent.py

Teste :
  1. Lecture des CSV
  2. Calcul de consommation prévisionnelle
  3. Calcul du stock futur
  4. Décision par règles simples (toujours disponible)
  5. Décision via AWS Bedrock (si disponible)
  6. Enregistrement en base SQLite
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Initialise la DB avant tout
from data_loader import init_database
init_database()

from agent.bedrock_agent import BedrockAgent


def titre(texte: str):
    print(f"\n{'─' * 55}")
    print(f"  {texte}")
    print('─' * 55)


def ok(msg: str):
    print(f"  ✅ {msg}")


def ko(msg: str):
    print(f"  ❌ {msg}")
    sys.exit(1)


def main():
    print("\n" + "=" * 55)
    print("   TEST COMPLET DE L'AGENT IA")
    print("=" * 55)

    agent = BedrockAgent()

    # ── 1. Lecture CSV ────────────────────────────────────────────────────
    titre("TEST 1 : Lecture des fichiers CSV")
    assert agent.stocks_df      is not None, "stocks_df vide"
    assert agent.consommation_df is not None, "consommation_df vide"
    assert agent.commandes_df   is not None, "commandes_df vide"
    ok(f"{len(agent.stocks_df)} matières chargées depuis stocks.csv")
    ok(f"{len(agent.consommation_df)} lignes dans consommation.csv")
    ok(f"{len(agent.commandes_df)} commandes dans commandes.csv")
    print("  Matières disponibles :", agent.get_matieres())

    # ── 2. Calcul consommation ────────────────────────────────────────────
    titre("TEST 2 : Calcul de consommation prévisionnelle")
    for matiere in agent.get_matieres():
        conso = agent.calculer_consommation_previsionnelle(matiere)
        ok(f"{matiere} → consommation prévue = {conso:.2f} unités")

    # ── 3. Calcul stock futur ─────────────────────────────────────────────
    titre("TEST 3 : Calcul du stock futur")
    for matiere in agent.get_matieres():
        data = agent.calculer_stock_futur(matiere)
        statut = "⚠️ RUPTURE" if data["stock_futur"] < 0 else \
                 "⚠️ SOUS SEUIL" if data["stock_futur"] < data["seuil_reappro"] else "✅ OK"
        ok(f"{matiere} : actuel={data['stock_actuel']}, "
           f"conso={data['conso_prevue']}, "
           f"futur={data['stock_futur']} [{statut}]")

    # ── 4. Vérification calcul Acier ──────────────────────────────────────
    titre("TEST 4 : Vérification du calcul Acier (référence cahier des charges)")
    data_acier = agent.calculer_stock_futur("Acier")
    # Acier = Produit A(200)×0.5 + Produit B(150)×0.3 + Produit A(100)×0.5
    #       = 100 + 45 + 50 = 195
    assert abs(data_acier["conso_prevue"] - 195.0) < 0.1, \
        f"Conso Acier attendue 195, obtenue {data_acier['conso_prevue']}"
    ok(f"Consommation Acier = {data_acier['conso_prevue']} ✓ (attendu: 195)")
    # Stock futur = 150 - 195 = -45
    assert abs(data_acier["stock_futur"] - (-45.0)) < 0.1, \
        f"Stock futur Acier attendu -45, obtenu {data_acier['stock_futur']}"
    ok(f"Stock futur Acier = {data_acier['stock_futur']} ✓ (attendu: -45)")

    # ── 5. Décision règles simples ────────────────────────────────────────
    titre("TEST 5 : Décision par règles simples (fallback)")
    for matiere in agent.get_matieres():
        dec = agent.proposer_decision_regles(matiere)
        ok(f"{matiere} → action={dec['action']}, "
           f"qte={dec['quantite']}, urgence={dec['urgence']}")
        # Acier doit être 'commander' car stock futur < 0
        if matiere == "Acier":
            assert dec["action"] == "commander", \
                "Acier doit déclencher 'commander' (stock futur négatif)"
            ok("Acier : action 'commander' correctement déclenchée ✓")

    # ── 6. Enregistrement SQLite ──────────────────────────────────────────
    titre("TEST 6 : Enregistrement en base SQLite")
    dec_test = agent.proposer_decision_regles("Acier")
    row_id   = agent.enregistrer_proposition(dec_test)
    assert row_id > 0, f"Enregistrement échoué (id={row_id})"
    ok(f"Proposition enregistrée avec id={row_id}")

    # Vérifie la relecture
    historique = agent.get_historique(5)
    assert not historique.empty, "Historique vide après enregistrement"
    ok(f"Historique lisible : {len(historique)} entrée(s)")

    # ── 7. Test AWS Bedrock (optionnel) ───────────────────────────────────
    titre("TEST 7 : Décision via AWS Bedrock (optionnel)")
    if agent.bedrock_ok:
        print("  ⏳ Appel AWS Bedrock en cours...")
        dec_llm = agent.proposer_decision_llm("Acier")
        ok(f"Réponse Bedrock reçue → source={dec_llm.get('source')}, "
           f"action={dec_llm.get('action')}, urgence={dec_llm.get('urgence')}")
        ok(f"Justification : {dec_llm.get('justification', '')[:80]}…")
    else:
        print("  ⏭️  Bedrock non disponible, test ignoré (fallback déjà testé).")

    # ── Résumé ────────────────────────────────────────────────────────────
    print()
    print("=" * 55)
    print("  🎉 Tous les tests sont passés avec succès !")
    print("=" * 55)


if __name__ == "__main__":
    main()