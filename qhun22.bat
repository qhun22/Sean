@echo off
chcp 65001 >nul
title QHUN22 - Quản Lý Server

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PYTHON_EXE="
set "PYTHON_VERSION="
set "PY_MAJOR="
set "PY_MINOR="
set "TARGET_PYTHON_MINOR=10"
set "TARGET_PYTHON_DISPLAY=3.10"
set "IMPORTANT_PKGS=django allauth requests openpyxl dotenv"
set "AI_PKGS=numpy sklearn sentence_transformers faiss fastapi uvicorn pydantic"
set "VENV_DIR=.venv"

:: Tạo thư mục logs nếu chưa tồn tại
if not exist "logs" mkdir logs

:: ========================================
:: Tự động xin quyền Admin nếu chưa có
:: ========================================
net session >nul 2>&1
if errorlevel 1 (
    echo [i] Đang yêu cầu quyền Administrator...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && \"%~f0\" %*' -Verb RunAs" >nul 2>&1
    exit /b
)

:main_menu
cls
echo ╔════════════════════════════════════════╗
echo ║       QHUN22 - Menu Quản Lý           ║
echo ╠════════════════════════════════════════╣
echo ║                                        ║
echo ║  [0] Setup Full Tự Động (máy mới)     ║
echo ║  ─────────────────────────────────     ║
echo ║  [1] Khởi động Server                  ║
echo ║  [2] Khởi động Server (Port tùy chọn) ║
echo ║  [3] Chạy Migration                    ║
echo ║  [4] Tạo tài khoản Admin               ║
echo ║  [5] Thử nghiệm gửi Email              ║
echo ║  [6] Xem Log Chatbot                   ║
echo ║  [7] Xóa Log Chatbot                   ║
echo ║  [8] Xuất requirements.txt              ║
echo ║  [9] Thoát                              ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.
set /p choice="Chọn chức năng [0-9]: "

if "%choice%"=="0" goto setup_full_auto
if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto start_server_port
if "%choice%"=="3" goto run_migrate
if "%choice%"=="4" goto create_admin
if "%choice%"=="5" goto test_email
if "%choice%"=="6" goto view_log
if "%choice%"=="7" goto clear_log
if "%choice%"=="8" goto export_requirements
if "%choice%"=="9" goto exit

echo.
echo [!] Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto main_menu


:detect_python
py -%TARGET_PYTHON_DISPLAY% --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py -%TARGET_PYTHON_DISPLAY%"
    goto detect_python_version
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto detect_python_version
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py -3"
    goto detect_python_version
)

set "PYTHON_EXE="
goto :eof

:detect_python_version
for /f "tokens=*" %%v in ('%PYTHON_EXE% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2^>nul') do set "PYTHON_VERSION=%%v"
for /f "tokens=*" %%v in ('%PYTHON_EXE% -c "import sys; print(sys.version_info.major)" 2^>nul') do set "PY_MAJOR=%%v"
for /f "tokens=*" %%v in ('%PYTHON_EXE% -c "import sys; print(sys.version_info.minor)" 2^>nul') do set "PY_MINOR=%%v"

if not "%PY_MAJOR%"=="3" (
    set "PYTHON_EXE="
    set "PYTHON_VERSION="
    set "PY_MAJOR="
    set "PY_MINOR="
    goto :eof
)

if not defined PY_MINOR (
    set "PYTHON_EXE="
    set "PYTHON_VERSION="
    set "PY_MAJOR="
    set "PY_MINOR="
    goto :eof
)

if %PY_MINOR% LSS 10 (
    set "PYTHON_EXE="
    set "PYTHON_VERSION="
    set "PY_MAJOR="
    set "PY_MINOR="
)
goto :eof


:activate_venv
:: Thử .venv trước, rồi venv
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call %VENV_DIR%\Scripts\activate.bat >nul 2>&1
    if errorlevel 1 goto activate_venv_fail
    exit /b 0
)
if exist "venv\Scripts\activate.bat" (
    set "VENV_DIR=venv"
    call venv\Scripts\activate.bat >nul 2>&1
    if errorlevel 1 goto activate_venv_fail
    exit /b 0
)
echo [!] Không tìm thấy venv! Hãy chạy [0] Setup Full trước.
exit /b 1

:activate_venv_fail
echo [!] Không thể kích hoạt Virtual Environment.
echo     Venv có thể bị lỗi. Chạy [0] Setup Full để tạo lại.
exit /b 1


:verify_package
set "PKG_NAME=%~1"
python -c "import importlib, sys; importlib.import_module('%PKG_NAME%')" >nul 2>&1
if errorlevel 1 (
    echo    [THIẾU] %PKG_NAME%
    set /a MISSING_COUNT+=1
) else (
    echo    [OK] %PKG_NAME%
)
goto :eof


:start_server
cls
echo ========================================
echo   Khởi Động Server
echo ========================================
echo.
call :activate_venv
if errorlevel 1 (
    echo.
    echo [!] Không thể kích hoạt Virtual Environment!
    echo    Đảm bảo thư mục venv tồn tại.
    timeout /t 3 >nul
    goto main_menu
)

echo.
echo [i] Đang kiểm tra database...
python manage.py migrate --run-syncdb

echo.
echo [OK] Database sẵn sàng!
echo.
echo [i] Đang khởi động server tại http://127.0.0.1:8000/
echo [i] Log server se hien thi truc tiep tren terminal
echo [i] Log chatbot: logs\chatbot.log
echo [i] Bấm Ctrl+C để dừng server
echo.
set "DJANGO_LOG_LEVEL=INFO"
set "QH_CHATBOT_LOG_LEVEL=INFO"
python manage.py runserver
goto main_menu


:start_server_port
cls
echo ========================================
echo   Khởi Động Server - Port Tùy Chọn
echo ========================================
echo.
set /p port="Nhập port (mặc định 8000): "
if "%port%"=="" set port=8000

call :activate_venv
if errorlevel 1 goto main_menu

echo.
echo [i] Đang khởi động server tại http://127.0.0.1:%port%/
echo [i] Log server se hien thi truc tiep tren terminal
echo [i] Log chatbot: logs\chatbot.log
echo [i] Bấm Ctrl+C để dừng server
echo.
set "DJANGO_LOG_LEVEL=INFO"
set "QH_CHATBOT_LOG_LEVEL=INFO"
python manage.py runserver %port%
goto main_menu


:run_migrate
cls
echo ========================================
echo   Chạy Migration
echo ========================================
echo.
call :activate_venv
if errorlevel 1 goto main_menu

echo [i] Đang chạy migrations...
python manage.py migrate --run-syncdb

echo.
pause
goto main_menu


:create_admin
cls
echo ========================================
echo   Tạo Tài Khoản Admin
echo ========================================
echo.
call :activate_venv
if errorlevel 1 goto main_menu

echo [i] Đang tạo tài khoản admin...
python manage.py createsuperuser

echo.
pause
goto main_menu


:test_email
cls
echo ========================================
echo   Thử Nghiệm Gửi Email
echo ========================================
echo.
echo  [1] Email Đăng Ký
echo  [2] Email Quên Mật Khẩu
echo  [3] Email Xác Thực Student/Teacher
echo  [0] Quay lại
echo.
set /p email_choice="Chọn loại email [0-3]: "

if "%email_choice%"=="0" goto main_menu
if "%email_choice%"=="1" goto test_email_register
if "%email_choice%"=="2" goto test_email_forgot
if "%email_choice%"=="3" goto test_email_student
goto test_email


:test_email_register
echo.
set /p test_email="Nhập địa chỉ email nhận: "
if "%test_email%"=="" (
    echo [!] Email không được để trống!
    timeout /t 2 >nul
    goto test_email_register
)
call :activate_venv
if errorlevel 1 goto main_menu
python -c "import os, sys, requests, random; otp = str(random.randint(100000, 999999)); api_key = os.getenv('SENDGRID_API_KEY', ''); from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com'); html = '''<div style=\"font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5;\"><div style=\"background:#fff;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);\"><h2 style=\"color:#333;text-align:center;\">Xac minh tai khoan QHUN22</h2><p style=\"color:#666;\">Ma OTP cua ban la:</p><div style=\"background:#f0f0f0;padding:15px;text-align:center;font-size:32px;font-weight:bold;letter-spacing:8px;color:#333;\">%%s</div><p style=\"color:#999;font-size:12px;\">Ma co hieu luc trong 5 phut. Vui long khong chia se ma nay cho ai.</p></div></div>''' %% otp; data = {'personalizations': [{'to': [{'email': '%test_email%'}]}], 'from': {'email': from_email}, 'subject': 'Xac minh OTP - QHUN22', 'content': [{'type': 'text/html', 'value': html}]}; r = requests.post('https://api.sendgrid.com/v3/mail/send', json=data, headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, timeout=10); print('[OK] Email da gui thanh cong!') if r.status_code in [200, 201, 202] else print('[!] Loi: ' + str(r.status_code))"
echo.
pause
goto main_menu


:test_email_forgot
echo.
set /p test_email="Nhập địa chỉ email nhận: "
if "%test_email%"=="" (
    echo [!] Email không được để trống!
    timeout /t 2 >nul
    goto test_email_forgot
)
call :activate_venv
if errorlevel 1 goto main_menu
python -c "import os, sys, requests, random; otp = str(random.randint(100000, 999999)); api_key = os.getenv('SENDGRID_API_KEY', ''); from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com'); html = '''<div style=\"font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5;\"><div style=\"background:#fff;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);\"><h2 style=\"color:#d9534f;text-align:center;\">Dat Lai Mat Khau QHUN22</h2><p style=\"color:#666;\">Ma OTP cua ban de dat lai mat khau la:</p><div style=\"background:#f0f0f0;padding:15px;text-align:center;font-size:32px;font-weight:bold;letter-spacing:8px;color:#333;\">%%s</div><p style=\"color:#999;font-size:12px;\">Ma co hieu luc trong 5 phut. Neu ban khong yeu cau, vui long bo qua.</p></div></div>''' %% otp; data = {'personalizations': [{'to': [{'email': '%test_email%'}]}], 'from': {'email': from_email}, 'subject': 'OTP Quen Mat Khau - QHUN22', 'content': [{'type': 'text/html', 'value': html}]}; r = requests.post('https://api.sendgrid.com/v3/mail/send', json=data, headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, timeout=10); print('[OK] Email da gui thanh cong!') if r.status_code in [200, 201, 202] else print('[!] Loi: ' + str(r.status_code))"
echo.
pause
goto main_menu


:test_email_student
echo.
set /p test_email="Nhập địa chỉ email nhận: "
if "%test_email%"=="" (
    echo [!] Email không được để trống!
    timeout /t 2 >nul
    goto test_email_student
)
call :activate_venv
if errorlevel 1 goto main_menu
python -c "import os, sys, requests, random; otp = str(random.randint(100000, 999999)); api_key = os.getenv('SENDGRID_API_KEY', ''); from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@qhun22.com'); html = '''<div style=\"font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f5f5f5;\"><div style=\"background:#fff;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);\"><h2 style=\"color:#5bc0de;text-align:center;\">Xac Thuc Student/Teacher - QHUN22</h2><p style=\"color:#666;\">Ma xac thuc cua ban la:</p><div style=\"background:#e8f4fd;padding:15px;text-align:center;font-size:32px;font-weight:bold;letter-spacing:8px;color:#A9CCF0;\">%%s</div><p style=\"color:#999;font-size:12px;\">Ma co hieu luc trong 5 phut. Vui long khong chia se ma nay cho ai.</p></div></div>''' %% otp; data = {'personalizations': [{'to': [{'email': '%test_email%'}]}], 'from': {'email': from_email}, 'subject': 'Ma Xac Thuc Student/Teacher - QHUN22', 'content': [{'type': 'text/html', 'value': html}]}; r = requests.post('https://api.sendgrid.com/v3/mail/send', json=data, headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, timeout=10); print('[OK] Email da gui thanh cong!') if r.status_code in [200, 201, 202] else print('[!] Loi: ' + str(r.status_code))"
echo.
pause
goto main_menu


:view_log
cls
echo ========================================
echo   Xem Log Chatbot
echo ========================================
echo.
if not exist "logs\chatbot.log" (
    echo [!] Chua co file logs\chatbot.log !
    timeout /t 2 >nul
    goto main_menu
)

echo [i] Log server dang hien thi truc tiep tren terminal khi ban chay [1] hoac [2].
echo [i] Noi dung file log chatbot:
echo.
type logs\chatbot.log
echo.
pause
goto main_menu


:clear_log
cls
echo ========================================
echo   Xóa Log Chatbot
echo ========================================
echo.
if exist "logs\chatbot.log" (
    del logs\chatbot.log
    echo [OK] Da xoa logs\chatbot.log !
) else (
    echo [!] Chua co file logs\chatbot.log !
)
echo.
timeout /t 2 >nul
goto main_menu


:setup_full_auto
cls
echo ╔════════════════════════════════════════╗
echo ║   SETUP FULL TỰ ĐỘNG - QHUN22         ║
echo ╠════════════════════════════════════════╣
echo ║                                        ║
echo ║  Script sẽ tự động:                    ║
echo ║  1. Kiểm tra Python                    ║
echo ║  2. Xóa venv lỗi + tạo venv mới       ║
echo ║  3. Cài tất cả thư viện                ║
echo ║  4. Chạy database migration             ║
echo ║  5. Kiểm tra .env                       ║
echo ║                                        ║
echo ║  Không cần thao tác thêm — chờ xong!   ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.

set "MISSING_COUNT=0"
set "SETUP_ERRORS=0"

:: ──── BƯỚC 1: Kiểm tra Python ────
echo ────────────────────────────────────────
echo  [1/6] Kiểm tra Python...
echo ────────────────────────────────────────
call :detect_python
if "%PYTHON_EXE%"=="" (
    echo.
    echo  [THẤT BẠI] Không tìm thấy Python phù hợp!
    echo.
    echo  Vui lòng cài Python 3.10+ từ:
    echo     https://www.python.org/downloads/
    echo.
    echo  QUAN TRỌNG: Khi cài, tick ☑ "Add Python to PATH"
    echo             và tick ☑ "Install py launcher"
    echo.
    echo  Sau khi cài xong, đóng cửa sổ này và chạy lại bat.
    echo.
    pause
    goto main_menu
)
for /f "tokens=*" %%v in ('%PYTHON_EXE% --version 2^>^&1') do echo  Phiên bản: %%v
echo  [OK] Python hợp lệ!
if not "%PY_MINOR%"=="%TARGET_PYTHON_MINOR%" (
    echo  [CẢNH BÁO] Máy đang dùng Python %PYTHON_VERSION%.
    echo           Khuyến nghị dùng Python %TARGET_PYTHON_DISPLAY% để ổn định nhất.
)
echo.

:: ──── BƯỚC 2: Kiểm tra + Tạo venv ────
echo ────────────────────────────────────────
echo  [2/6] Kiểm tra Virtual Environment...
echo ────────────────────────────────────────

set "VENV_NEED_CREATE=0"

:: Kiểm tra venv có tồn tại không
if not exist "%VENV_DIR%\Scripts\python.exe" (
    if not exist "venv\Scripts\python.exe" (
        echo  [i] Chưa có venv — sẽ tạo mới.
        set "VENV_NEED_CREATE=1"
    ) else (
        set "VENV_DIR=venv"
    )
)

:: Kiểm tra venv có bị lỗi user khác không (lỗi phổ biến nhất!)
if "%VENV_NEED_CREATE%"=="0" (
    %VENV_DIR%\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo  [!] Venv bị lỗi (Python path không khớp máy hiện tại^)
        echo      Đây là lỗi phổ biến khi copy project giữa các máy.
        echo      Đang xóa venv cũ và tạo lại...
        set "VENV_NEED_CREATE=1"
    ) else (
        echo  [OK] Venv hoạt động bình thường.
    )
)

:: Tạo venv mới nếu cần
if "%VENV_NEED_CREATE%"=="1" (
    echo.
    echo  [i] Đang dọn dẹp venv cũ...
    if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" >nul 2>&1
    if exist "venv" rmdir /s /q "venv" >nul 2>&1
    set "VENV_DIR=.venv"
    echo  [i] Đang tạo venv mới bằng %PYTHON_EXE%...
    %PYTHON_EXE% -m venv %VENV_DIR% >nul 2>&1
    if errorlevel 1 (
        echo  [THẤT BẠI] Không thể tạo venv!
        echo             Thử chạy thủ công: %PYTHON_EXE% -m venv .venv
        set /a SETUP_ERRORS+=1
        pause
        goto main_menu
    )
    echo  [OK] Đã tạo venv mới tại %VENV_DIR%\
)
echo.

:: ──── BƯỚC 3: Kích hoạt venv + nâng cấp pip ────
echo ────────────────────────────────────────
echo  [3/6] Kích hoạt venv + nâng cấp pip...
echo ────────────────────────────────────────
call :activate_venv
if errorlevel 1 (
    set /a SETUP_ERRORS+=1
    pause
    goto main_menu
)
python -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check --no-warn-script-location
if errorlevel 1 (
    echo  [CẢNH BÁO] Không thể cập nhật pip — tiếp tục cài thư viện.
) else (
    echo  [OK] pip/setuptools/wheel đã cập nhật.
)
echo.

:: ──── BƯỚC 4: Cài thư viện ────
echo ────────────────────────────────────────
echo  [4/6] Cài đặt thư viện...
echo ────────────────────────────────────────
echo.

:: 4a: Core requirements
if not exist "requirements.txt" (
    echo  [THẤT BẠI] Không tìm thấy requirements.txt
    set /a SETUP_ERRORS+=1
    pause
    goto main_menu
)

echo  [i] Đang cài core packages (requirements.txt)...
pip install -r requirements.txt --disable-pip-version-check --no-warn-script-location
if errorlevel 1 (
    echo.
    echo  [THẤT BẠI] Cài đặt core requirements gặp lỗi!
    echo  Kiểm tra kết nối mạng rồi chạy lại [0].
    set /a SETUP_ERRORS+=1
) else (
    echo  [OK] Core packages đã cài xong.
)
echo.

:: 4b: Packages thường thiếu (không có trong requirements.txt nhưng cần)
echo  [i] Đang cài packages bổ sung (Pillow, PyJWT, cryptography)...
pip install Pillow PyJWT cryptography --disable-pip-version-check --no-warn-script-location --quiet
if errorlevel 1 (
    echo  [CẢNH BÁO] Một số package bổ sung cài lỗi — có thể cần cài thủ công.
) else (
    echo  [OK] Packages bổ sung đã cài xong.
)
echo.

:: 4c: AI requirements (tùy chọn)
if exist "ai\ai_requirements.txt" (
    echo  [i] Phát hiện ai\ai_requirements.txt — đang cài thư viện AI...
    pip install -r ai\ai_requirements.txt --disable-pip-version-check --no-warn-script-location
    if errorlevel 1 (
        echo  [CẢNH BÁO] Cài AI packages có lỗi — web app vẫn chạy được.
    ) else (
        echo  [OK] AI packages đã cài xong.
    )
) else (
    echo  [i] Không có ai\ai_requirements.txt — bỏ qua AI.
)
echo.

:: 4d: Kiểm tra packages quan trọng
echo  [i] Kiểm tra nhanh packages quan trọng...
for %%p in (%IMPORTANT_PKGS%) do call :verify_package %%p

echo.
echo  [i] Packages bổ sung...
for %%p in (PIL jwt cryptography) do call :verify_package %%p

if exist "ai\ai_requirements.txt" (
    echo.
    echo  [i] Packages AI...
    for %%p in (%AI_PKGS%) do call :verify_package %%p
)

echo.
if "%MISSING_COUNT%"=="0" (
    echo  [OK] Tất cả packages đều sẵn sàng!
) else (
    echo  [CẢNH BÁO] Còn %MISSING_COUNT% package chưa import được.
    echo           Nếu lỗi thuộc nhóm AI, app web vẫn chạy bình thường.
)
echo.

:: ──── BƯỚC 5: Database migration ────
echo ────────────────────────────────────────
echo  [5/6] Chạy database migration...
echo ────────────────────────────────────────
echo.
python manage.py migrate --run-syncdb
if errorlevel 1 (
    echo.
    echo  [CẢNH BÁO] Migration gặp vấn đề — có thể cần cấu hình .env trước.
    set /a SETUP_ERRORS+=1
) else (
    echo.
    echo  [OK] Database sẵn sàng.
)
echo.

:: ──── BƯỚC 6: Kiểm tra .env ────
echo ────────────────────────────────────────
echo  [6/6] Kiểm tra file .env...
echo ────────────────────────────────────────
echo.
if not exist ".env" (
    echo  [CẢNH BÁO] Chưa có file .env!
    echo.
    echo  Tạo file .env trong thư mục gốc với nội dung tối thiểu:
    echo.
    echo    SECRET_KEY=your-secret-key
    echo    DEBUG=True
    echo    ALLOWED_HOSTS=127.0.0.1,localhost
    echo    ANTHROPIC_API_KEY=your-api-key  (cho chatbot)
    echo.
    echo  Xem đầy đủ trong SETUP.md hoặc README.md
) else (
    echo  [OK] File .env đã có sẵn.
)
echo.

:: ──── TỔNG KẾT ────
echo.
if "%SETUP_ERRORS%"=="0" (
    echo ╔════════════════════════════════════════╗
    echo ║   SETUP HOÀN TẤT THÀNH CÔNG!          ║
    echo ╠════════════════════════════════════════╣
    echo ║                                        ║
    echo ║  Bước tiếp theo:                       ║
    echo ║    Chọn [1] để khởi động server        ║
    echo ║    Truy cập: http://127.0.0.1:8000/    ║
    echo ║                                        ║
    echo ║  Tạo admin (nếu cần):                  ║
    echo ║    Chọn [4] để tạo tài khoản admin     ║
    echo ║                                        ║
    echo ╚════════════════════════════════════════╝
) else (
    echo ╔════════════════════════════════════════╗
    echo ║   SETUP HOÀN TẤT (có %SETUP_ERRORS% cảnh báo)      ║
    echo ╠════════════════════════════════════════╣
    echo ║                                        ║
    echo ║  Có một số lỗi nhỏ, kiểm tra lại:     ║
    echo ║    - File .env đã tạo chưa?            ║
    echo ║    - Kết nối Internet ổn không?         ║
    echo ║    - Thử chạy lại [0] sau khi fix      ║
    echo ║                                        ║
    echo ╚════════════════════════════════════════╝
)
echo.
pause
goto main_menu


:export_requirements
cls
echo ========================================
echo   Xuất requirements.txt
echo ========================================
echo.
call :activate_venv
if errorlevel 1 (
    pause
    goto main_menu
)
pip freeze > requirements_freeze.txt
echo [OK] Đã xuất ra file: requirements_freeze.txt
echo     (Đây là snapshot chính xác, dùng để debug xung đột phiên bản)
echo.
pause
goto main_menu


:exit
cls
echo ========================================
echo   Tạm Biệt!
echo ========================================
echo.
echo [i] Hẹn gặp lại!
echo.
timeout /t 2 >nul
exit
