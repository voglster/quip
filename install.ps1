# Quip - Frictionless thought capture tool installer for Windows
# Usage: powershell -ExecutionPolicy ByPass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "[*] Installing Quip - Frictionless thought capture tool" -ForegroundColor Cyan

# Check if running on Windows
if ($IsWindows -eq $false -and $PSVersionTable.PSVersion.Major -ge 6) {
    # This check works in PWSH 6+, for older PS it will just continue as it's likely Windows
}
elseif ($env:OS -notlike "*Windows*") {
    Write-Error "[!] This script is for Windows only. Use install.sh for Linux/macOS."
    exit 1
}

# Install uv if not present
if (!(Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Installing uv (Python package manager)..."
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    # Refresh PATH for the current session
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
}

# Set installation directory
$INSTALL_DIR = Join-Path $HOME ".quip"
$BIN_DIR = Join-Path $INSTALL_DIR "bin"
$NOTES_DIR = Join-Path $HOME "notes\Inbox"

# Create directories
if (!(Test-Path $INSTALL_DIR)) { New-Item -ItemType Directory -Path $INSTALL_DIR }
if (!(Test-Path $BIN_DIR)) { New-Item -ItemType Directory -Path $BIN_DIR }
if (!(Test-Path $NOTES_DIR)) { New-Item -ItemType Directory -Path $NOTES_DIR -Force }

# Copy project files to installation directory
Write-Host "[+] Setting up Quip files..."
$CurrentDir = Get-Location
# We assume we are running from the cloned repo
Copy-Item -Path "$CurrentDir\*" -Destination $INSTALL_DIR -Recurse -Force -Exclude ".git"

# Install dependencies
Write-Host "[+] Installing dependencies..."
Set-Location (Join-Path $INSTALL_DIR "desktop")
uv sync

# Download voice models if needed
Write-Host "[+] Setting up voice recognition..."
$MODELS_DIR = Join-Path $INSTALL_DIR "desktop\vosk-models"
$EN_MODEL_DIR = Join-Path $MODELS_DIR "vosk-model-small-en-us-0.15"

if (!(Test-Path $EN_MODEL_DIR)) {
    Write-Host "[+] Downloading voice recognition model (39MB)..."
    if (!(Test-Path $MODELS_DIR)) { New-Item -ItemType Directory -Path $MODELS_DIR }
    
    $ZipPath = Join-Path $MODELS_DIR "vosk-model-small-en-us-0.15.zip"
    try {
        Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile $ZipPath
        Write-Host "[+] Extracting voice model..."
        Expand-Archive -Path $ZipPath -DestinationPath $MODELS_DIR
        Remove-Item $ZipPath
        Write-Host "[OK] Voice recognition model installed" -ForegroundColor Green
    } catch {
        Write-Warning "[!] Voice model download failed - voice recording will use mock transcription"
        Write-Host "   You can manually download from: https://alphacephei.com/vosk/models"
        Write-Host "   and extract to: $MODELS_DIR"
    }
} else {
    Write-Host "[OK] Voice recognition model already installed" -ForegroundColor Green
}

# Create launcher scripts
Write-Host "[+] Creating launchers..."
$QuipBat = Join-Path $BIN_DIR "quip.bat"
$QuipDaemonBat = Join-Path $BIN_DIR "quip-daemon.bat"

"@echo off`npushd ""$INSTALL_DIR\desktop""`nuv run quip %*`npopd" | Out-File -FilePath $QuipBat -Encoding ascii
"@echo off`npushd ""$INSTALL_DIR\desktop""`nuv run quip-daemon %*`npopd" | Out-File -FilePath $QuipDaemonBat -Encoding ascii

# Add to PATH for current user if not already there
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BIN_DIR*") {
    Write-Host "[+] Adding $BIN_DIR to User PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BIN_DIR", "User")
    $env:PATH = "$env:PATH;$BIN_DIR"
}

# Set up autostart
Write-Host "[+] Setting up autostart..."
$StartupFolder = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = Join-Path $StartupFolder "Quip Daemon.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $QuipDaemonBat
$Shortcut.Arguments = "start"
$Shortcut.WorkingDirectory = Join-Path $INSTALL_DIR "desktop"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Description = "Quip background daemon for global hotkey handling"
$Shortcut.Save()

Write-Host "`n[OK] Quip installed successfully!" -ForegroundColor Green
Write-Host "`nQuick start:"
Write-Host "   quip                 # Launch GUI"
Write-Host "   quip-daemon start    # Start background daemon with global hotkey"
Write-Host "`nNotes saved to: $NOTES_DIR"
Write-Host "Global hotkey: Win+Space (when daemon is running)"
Write-Host "Voice recording: Hold Tab to record, release to transcribe"
Write-Host "`nNote: You may need to restart your terminal or log out/in for PATH changes to take effect."
