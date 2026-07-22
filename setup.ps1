# Setup script for Lichess Bot Stockfish engine, NNUE, and Opening Books

$ErrorActionPreference = "Stop"
$enginesDir = ".\engines"
$booksDir = ".\engines\books"

# Create directories
New-Item -ItemType Directory -Force -Path $enginesDir | Out-Null
New-Item -ItemType Directory -Force -Path $booksDir | Out-Null

Write-Host "Downloading Stockfish 16.1 (AVX2)..."
$sfUrl = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
$sfZip = "$enginesDir\stockfish.zip"
Invoke-WebRequest -Uri $sfUrl -OutFile $sfZip
Write-Host "Extracting Stockfish..."
Expand-Archive -Path $sfZip -DestinationPath $enginesDir -Force
# Move and rename the exe
Move-Item -Path "$enginesDir\stockfish\stockfish-windows-x86-64-avx2.exe" -Destination "$enginesDir\stockfish.exe" -Force
Remove-Item -Recurse -Force "$enginesDir\stockfish"
Remove-Item -Force $sfZip

Write-Host "Downloading NNUE Network (nn-b1a57edbea57.nnue)..."
$nnueUrl = "https://tests.stockfishchess.org/api/nn/nn-b1a57edbea57.nnue"
Invoke-WebRequest -Uri $nnueUrl -OutFile "$enginesDir\nn-b1a57edbea57.nnue"

Write-Host "Downloading Polyglot Books..."

try {
    Write-Host "Downloading Cerebellum Light..."
    Invoke-WebRequest -Uri "https://zipproth.de/Brainfish/download/CerebellumLightPoly.zip" -OutFile "$booksDir\CerebellumLightPoly.zip"
    Expand-Archive -Path "$booksDir\CerebellumLightPoly.zip" -DestinationPath $booksDir -Force
    Remove-Item -Force "$booksDir\CerebellumLightPoly.zip"
} catch {
    Write-Host "Failed to download Cerebellum. Continuing..."
}

try {
    Write-Host "Downloading Balsa v2724..."
    Invoke-WebRequest -Uri "https://github.com/Balsa-project/Balsa/releases/download/v2724/Balsa_v2724.zip" -OutFile "$booksDir\balsa.zip"
    Expand-Archive -Path "$booksDir\balsa.zip" -DestinationPath "$booksDir\BalsaExtracted" -Force
    # Balsa often has multiple bins or one big one inside. The name is usually Balsa_v2724.bin
    if (Test-Path "$booksDir\BalsaExtracted\Balsa_v2724.bin") {
        Move-Item -Path "$booksDir\BalsaExtracted\Balsa_v2724.bin" -Destination "$booksDir\Balsa_v2724.bin" -Force
    } else {
        # If the structure is different, just move all .bin files up
        Get-ChildItem -Path "$booksDir\BalsaExtracted" -Filter "*.bin" | Move-Item -Destination $booksDir -Force
    }
    Remove-Item -Recurse -Force "$booksDir\BalsaExtracted"
    Remove-Item -Force "$booksDir\balsa.zip"
} catch {
    Write-Host "Failed to download Balsa. Continuing..."
}

Write-Host ""
Write-Host "==========================================================="
Write-Host "Setup almost complete! Stockfish, NNUE, Cerebellum and Balsa"
Write-Host "opening books have been processed."
Write-Host "==========================================================="
Write-Host "NOTE for GM2001, Titans, and Komodo:"
Write-Host "Please place the following files manually into engines\books\:"
Write-Host "  - GM2001.bin"
Write-Host "  - Titans.bin"
Write-Host "  - Komodo.bin"
Write-Host "These are typically commercial or require forum access."
