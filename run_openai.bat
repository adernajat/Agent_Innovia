@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    HACKATHON IA - SYSTEME DE GESTION DES STOCKS (OpenAI)
echo ============================================================
echo.

:: ── Vérification de la clé API OpenAI ──────────────────────────────────
echo [0/5] Verification de la cle API OpenAI...
if "%OPENAI_API_KEY%"=="" (
    echo       ATTENTION : Variable OPENAI_API_KEY non definie
    echo       Veuillez configurer votre cle API OpenAI
    echo.
    echo       Exemple : set OPENAI_API_KEY=votre_cle_ici
    echo.
    set /p OPENAI_API_KEY="Entrez votre cle API OpenAI : "
)

:: ── Activation du venv ────────────────────────────────────────────────
echo.
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
python -c "import streamlit, flask, openai, pandas, requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       Installation des dependances...
    pip install streamlit flask openai pandas requests --quiet
    if %ERRORLEVEL% neq 0 (
        echo       ERREUR : Impossible d'installer les dependances.
        pause
        exit /b 1
    )
)
echo       OK : Dependances disponibles

:: ── Initialisation de la base de données ─────────────────────────────
echo.
echo [3/5] Initialisation de la base de donnees SQLite...
python data_loader.py
if %ERRORLEVEL% neq 0 (
    echo       ERREUR lors de l'initialisation de la DB.
    pause
    exit /b 1
)

:: ── Démarrage API fournisseur ─────────────────────────────────────────
echo.
echo [4/5] Demarrage de l'API Fournisseur (port 5001)...
start "API Fournisseur" /B python supplier_api\server.py
timeout /t 3 /nobreak >nul
echo       OK : API Fournisseur lancee (http://localhost:5001)

:: ── Démarrage Dashboard Streamlit ────────────────────────────────────
echo.
echo [5/5] Lancement du Dashboard Streamlit...
echo.
echo ============================================================
echo   Dashboard : http://localhost:8501
echo   API Fourn : http://localhost:5001
echo   Arret     : Ctrl+C dans cette fenetre
echo ============================================================
echo.
streamlit run dashboard\app.py --server.port 8501 --server.headless false

:: ── Nettoyage à la fermeture ─────────────────────────────────────────
echo.
echo Arret de l'API fournisseur...
taskkill /F /FI "WINDOWTITLE eq API Fournisseur*" >nul 2>&1
echo Au revoir !
pause