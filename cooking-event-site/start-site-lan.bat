@echo off
cd /d "%~dp0"
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5000
set SITE_IP=
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    if not defined SITE_IP set SITE_IP=%%A
)
if defined SITE_IP set SITE_IP=%SITE_IP: =%
echo Starting World Cooking Challenge site for local network access on port 5000
if defined SITE_IP echo Open this address on other devices: http://%SITE_IP%:5000
echo Keep this window open while attendees use the site.
python app.py
if errorlevel 1 (
    echo.
    echo The site stopped because of an error.
    pause
)
