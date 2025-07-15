@echo off
TITLE 47Chat Launcher

ECHO.
ECHO  **************************************************
ECHO  * Uruchamianie aplikacji 47Chat          *
ECHO  * (Backend: FastAPI, Frontend: Streamlit)   *
ECHO  **************************************************
ECHO.

REM --- Sprawdzenie, czy srodowisko wirtualne istnieje ---
IF NOT EXIST rag_env (
    ECHO Tworzenie srodowiska wirtualnego...
    python -m venv rag_env
)

REM --- Uruchomienie serwera Backend w nowym oknie ---
ECHO [1/2] Uruchamianie serwera Backend (FastAPI)...
START "Backend - 47Chat" cmd /k "rag_env\Scripts\activate.bat && cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000"

REM --- Czekamy chwile, zeby backend mial czas sie uruchomic ---
ECHO Czekam 5 sekund na start backendu...
timeout /t 5 /nobreak > NUL

REM --- Uruchomienie serwera Frontend w drugim nowym oknie ---
ECHO [2/2] Uruchamianie interfejsu Frontend (Streamlit)...
START "Frontend - 47Chat" cmd /k "rag_env\Scripts\activate.bat && cd frontend && pip install -r requirements.txt && streamlit run app.py"

ECHO.
ECHO Gotowe! Aplikacja zostala uruchomiona w dwoch osobnych oknach.
ECHO To okno mozna teraz zamknac.
ECHO.
pause