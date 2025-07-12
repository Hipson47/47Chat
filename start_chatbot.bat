@echo off
REM --- Automatyczny skrypt startowy dla Chatbota RAG ---
REM --- 1. Aktywuje srodowisko wirtualne                 ---
REM --- 2. Instaluje potrzebne biblioteki                ---
REM --- 3. Uruchamia aplikacje                         ---

echo Startowanie...

REM --- Upewnij sie, ze ponizsza sciezka jest poprawna ---
set PROJECT_PATH=C:\Users\marci\Desktop\RAGZCHATEM

echo.
echo === Krok 1: Aktywacja srodowiska wirtualnego ===
call %PROJECT_PATH%\rag_env\Scripts\activate.bat

echo.
echo === Krok 2: Sprawdzanie i instalacja bibliotek ===
pip install -r %PROJECT_PATH%\requirements.txt

echo.
echo === Krok 3: Uruchamianie aplikacji Chatbota ===
echo Aplikacja otworzy sie w nowej karcie przegladarki...
streamlit run %PROJECT_PATH%\app.py

echo.
echo Aplikacja zostala zamknieta. Nacisnij dowolny klawisz, aby zakonczyc.
pause