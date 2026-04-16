# 🏭 StockIA

> Système intelligent de gestion des stocks avec IA, validation humaine et génération PDF

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Fonctionnalités

- 🤖 **IA gratuite** - Groq (Llama 3.3) - 0€
- 📊 **Analyse prédictive** - Calcul des besoins futurs
- ✅ **Validation humaine** - Accepter/Modifier/Rejeter
- 🏢 **Sélection fournisseurs** - Comparaison prix/délais/score
- 📄 **Génération PDF** - Bons de commande professionnels
- 🔄 **Modification temps réel** - Ajustez les quantités

## 🚀 Démarrage rapide

```bash
# Cloner
git clone https://github.com/votre-username/stockia.git
cd stockia

# Installer
pip install -r requirements.txt

# Configurer la clé Groq
echo GROQ_API_KEY="votre_clé" > .env

# Lancer
python data_loader.py
streamlit run app.py
# + python supplier_api/server.py (autre terminal)
