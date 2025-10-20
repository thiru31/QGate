@echo off
setlocal enabledelayedexpansion

REM === Ask user for the changing part ===
set /p NUM=Enter target number (e.g. sa304610): 
set TARGET=%NUM%.sa.svc.cluster.local

REM === Generate one random port (1024-65535), making sure they differ ===
:genPorts
set /a PORT1=(%random% * 64512 / 32768) + 1024
set /a PORT2=7373
if %PORT1%==%PORT2% goto genPorts

echo Using SSH port forward: %PORT1%
echo Using RDP port forward: %PORT2%

REM === Path to key ===
set KEY=C:\Users\%USERNAME%\Downloads\qdc123.pem

REM === Launch Windows Terminal with 2 SSH tunnels ===
start "" wt.exe ^
    --title "Tunnel1" cmd /k ssh -i "%KEY%" -L %PORT1%:%TARGET%:22 -N sshtunnel@ssh.qdc.qualcomm.com ^
    ; new-tab --title "Tunnel2" cmd /k "echo RDP forwarded to localhost:%PORT2% && ssh -i "%KEY%" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -L %PORT2%:localhost:3389 -p %PORT1% hcktest@localhost"

REM Give tunnels a few seconds to establish
timeout /t 5 /nobreak >nul

REM === Open RDP client ===
start "" mstsc /v:localhost:%PORT2%

REM === Say done and close this terminal ===
echo RDP done
timeout /t 2 >nul
exit
