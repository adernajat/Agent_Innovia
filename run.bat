@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    HACKATHON IA - SYSTEME DE GESTION DES STOCKS
echo    Version avec Google Gemini
echo ============================================================
echo.

:: ── Activation du venv ────────────────────────────────────────────────
echo [1/5] Activation de l'environnement virtuel...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo       OK : venv active
) else (
    echo       INFO : Pas de venv trouve, utilisation de Python systeme
)

:: ── Vérification des dépendances ──────────────────────────────────────
echo.
echo [2/5] Verification des dependances Python...
python -c "import streamlit, flask, pandas, google.generativeai" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       Installation des dependances...
    pip install -r requirements.txt --quiet
    if %ERRORLEVEL% neq 0 (
        echo       ERREUR : Impossible d'installer les dependances.
        pause
        exit /b 1
    )
)
echo       OK : Dependances disponibles

:: ── Vérification de la clé API Gemini ─────────────────────────────────
echo.
echo [3/5] Verification de la configuration...
python -c "from dotenv import load_dotenv; import os; load_dotenv(); assert os.getenv('GEMINI_API_KEY'), 'Clé API manquante'" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       ATTENTION : Clé API Gemini non trouvée !
    echo       Créez un fichier .env avec GEMINI_API_KEY=votre_cle
    echo.
    echo       Le mode fallback (regles simples) sera utilise.
    timeout /t 5 /nobreak >nul
) else (
    echo       OK : Configuration Gemini trouvee
)

:: ── Initialisation de la base de données ─────────────────────────────
echo.
echo [4/5] Initialisation de la base de donnees SQLite...
python data_loader.py
if %ERRORLEVEL% neq 0 (
    echo       ERREUR lors de l'initialisation de la DB.
    pause
    exit /b 1
)

:: ── Démarrage API fournisseur ─────────────────────────────────────────
echo.
echo [5/5] Demarrage de l'API Fournisseur (port 5001)...
start "API Fournisseur" /B python supplier_api\server.py
timeout /t 3 /nobreak >nul
echo       OK : API Fournisseur lancee (http://localhost:5001)

:: ── Démarrage Dashboard Streamlit ────────────────────────────────────
echo.
echo ============================================================
echo   Dashboard : http://localhost:8501
echo   API Fourn : http://localhost:5001
echo   Modele    : Google Gemini
echo   Arret    