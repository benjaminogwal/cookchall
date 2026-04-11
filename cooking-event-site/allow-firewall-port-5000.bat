@echo off
echo This must be run as Administrator.
netsh advfirewall firewall add rule name="World Cooking Challenge 5000" dir=in action=allow protocol=TCP localport=5000 profile=private
if errorlevel 1 (
    echo.
    echo Firewall rule was not added.
    echo Right-click this file and choose "Run as administrator".
    pause
    exit /b 1
)
echo.
echo Firewall rule added for TCP port 5000 on private networks.
pause
