@echo off
cd /d "%~dp0"
title Ngrok Tunnel - Linh Ung Audio Guide

echo =====================================================================
echo  KHOI DONG NGROK TUNNEL (PORT 3000)
echo =====================================================================
echo [*] Dang ket noi va tao duong link HTTPS cong khai...
echo [*] Hay sao chep duong link o dong 'Forwarding' (https://...ngrok-free.app)

ngrok.exe http 3000

pause
