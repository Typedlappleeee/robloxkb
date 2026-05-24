@echo off
title Macro Recorder - Roblox
cd /d "%~dp0"

echo ============================================
echo        MACRO RECORDER - Demarrage
echo ============================================
echo.

REM --- Cherche Python (py puis python) ---
set PYCMD=
where py >nul 2>&1 && set PYCMD=py
if not defined PYCMD (
    where python >nul 2>&1 && set PYCMD=python
)

if not defined PYCMD (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo.
    echo   1. Va sur https://www.python.org/downloads/
    echo   2. Telecharge et installe Python
    echo   3. COCHE la case "Add python.exe to PATH" pendant l'install
    echo   4. Relance ce fichier
    echo.
    pause
    exit /b 1
)

echo Python detecte : %PYCMD%
echo.

REM --- Verifie / installe pynput ---
%PYCMD% -c "import pynput" >nul 2>&1
if errorlevel 1 (
    echo Installation de la dependance "pynput"...
    %PYCMD% -m pip install pynput
    echo.
)

echo Lancement du menu...
echo.
%PYCMD% "%~dp0macro_recorder.py"

REM --- Garde la fenetre ouverte si erreur ---
if errorlevel 1 (
    echo.
    echo [ERREUR] Le script s'est arrete avec une erreur.
    pause
)
