#!/usr/bin/env pwsh
Write-Host "Creating virtual environment and installing dependencies..."
if (-Not (Test-Path -Path '.venv')) {
    python -m venv .venv
}
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Setup complete. Use .\run.ps1 to start the app."
