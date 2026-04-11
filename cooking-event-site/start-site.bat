@echo off
cd /d "%~dp0"
echo Starting World Cooking Challenge site on http://127.0.0.1:5000
echo Keep this window open while you use the site.
python app.py
if errorlevel 1 (
    echo.
    echo The site stopped because of an error.
    pause
)
