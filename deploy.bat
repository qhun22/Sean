@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  QHUN22 - Setup va Collectstatic
echo ========================================
echo.

REM Kich hoat virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo [1/4] Kich hoat virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [1/4] Tao moi virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Cai dat thu vien
echo.
echo [2/4] Cai dat thu vien...
pip install --upgrade pip
pip install -r requirements.txt

REM Chay migrations
echo.
echo [3/4] Kiem tra migrations...
python manage.py migrate --check

REM Collectstatic
echo.
echo [4/4] Collectstatic...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo  HOAN TAT! Hay chay: python manage.py runserver
echo ========================================
pause
