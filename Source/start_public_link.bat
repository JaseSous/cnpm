@echo off
cd /d "%~dp0"
title Public HTTPS Link - Cloudflare Tunnel

echo =====================================================================
echo  DANG TAO DUONG LINK HTTPS CONG KHAI CHO DIEN THOAI / GIANG VIEN
echo  (Khong can dang ky, khong can token, mien phi 100%%)
echo =====================================================================
echo [*] Vui long cho 3-5 giay de ket noi...
echo [*] Hay sao chep duong link dang: https://...trycloudflare.com
echo =====================================================================
echo.

cloudflared.exe tunnel --url http://localhost:3000

pause
