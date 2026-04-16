"""
Script de vérification des prérequis OpenAI avant le lancement du projet.
À exécuter une seule fois avec : python setup_openai.py

Vérifie :
  1. Que openai est installé
  2. Que la clé API OpenAI est configurée
  3. Qu'un appel test à GPT-4o-mini aboutit
"""

import os
import sys


def check(label: str, fn):
    """Exécute fn(), affiche ✅ ou ❌ + message d'erreur."""
    try:
        result = fn()
        print(f"  ✅ {label}" + (f" → {result}" if result else ""))
        return True
    except Exception as e:
        print(f"  ❌ {label}")
        print(f"     Erreur : {e}")
        return False


def main():
    print("=" * 60)
    print("   VÉRIFICATION DES PRÉREQUIS OPENAI")
    print("=" * 60)
    print()

    # ── 1. Import openai ───────────────────────────────────────────────────
    print("▶ 1. Vérification de la bibliothèque OpenAI")
    try:
        import openai
        ok_openai = check("openai importable", lambda: openai.__version__)
    except ImportError:
        print("  ❌ openai non installé")
        print("\n  💡 Installez openai : pip install openai")
        sys.exit(1)

    # ── 2. Clé API OpenAI ────────────────────────────────────────────────
    print("\n▶ 2. Vérification de la clé API OpenAI")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("  ❌ Clé API OpenAI manquante")
        print("\n  💡 Configurez votre clé API :")
        print("     - Windows (PowerShell) : $env:OPENAI_API_KEY='votre_clé'")
        print("     - Windows (CMD) : set OPENAI_API_KEY=votre_clé")
        print("     - Linux/Mac : export OPENAI_API_KEY='votre_clé'")
        print("     - Ou passez-la directement dans le code")
        sys.exit(1)
    
    ok_key = check("Clé API présente", lambda: f"{api_key[:10]}...")

    # ── 3. Test d'appel à OpenAI ───────────────────────────────────────────
    print("\n▶ 3. Test d'appel à GPT-4o-mini (coût estimé : ~$0.0001)")
    
    def test_invoke():
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Réponds uniquement par 'OK'"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    ok_invoke = check("Appel test GPT-4o-mini", test_invoke)

    # ── Résumé ────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    all_ok = ok_openai and ok_key and ok_invoke
    if all_ok:
        print("  🎉 Tous les prérequis sont satisfaits !")
        print("  Vous pouvez lancer le projet avec : run_openai.bat")
    else:
        print("  ⚠️  Certains prérequis sont manquants.")
        print("  Corrigez les erreurs ci-dessus avant de continuer.")
    print("=" * 60)


if __name__ == "__main__":
    main()