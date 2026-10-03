# PowerShell Helper fuer Audio Analysis API
# Einfache Funktionen fuer API-Nutzung

$ApiUrl = "http://localhost:8000"

function Compare-Audio {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath,

        [ValidateSet("dtw", "cosine", "embedding")]
        [string]$Method = "dtw"
    )

    if (-not (Test-Path $FilePath)) {
        Write-Error "Datei nicht gefunden: $FilePath"
        return
    }

    $file = Get-Item $FilePath
    $form = @{ file = $file }

    Write-Host "Vergleiche: $($file.Name) (Methode: $Method)..."

    $response = Invoke-WebRequest -Uri "$ApiUrl/compare?method=$Method" `
        -Method POST -Form $form

    $result = $response.Content | ConvertFrom-Json

    if ($result.success) {
        $similarity = [math]::Round($result.similarity * 100, 1)
        if ($result.match) { $matchText = "[OK] MATCH" } else { $matchText = "[NO] KEIN MATCH" }

        Write-Host "`nErgebnis:" -ForegroundColor Cyan
        Write-Host "  Aehnlichkeit: $similarity%" -ForegroundColor Yellow
        Write-Host "  Status:       $matchText" -ForegroundColor Green
        Write-Host "  Schwelle:     $($result.threshold * 100)%"
    } else {
        Write-Error "Fehler: $($result.detail)"
    }

    return $result
}

function Analyze-Audio {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        Write-Error "Datei nicht gefunden: $FilePath"
        return
    }

    $file = Get-Item $FilePath
    $form = @{ file = $file }

    Write-Host "Analysiere: $($file.Name) (Hybrid)..."

    $response = Invoke-WebRequest -Uri "$ApiUrl/analyze" `
        -Method POST -Form $form

    $result = $response.Content | ConvertFrom-Json

    if ($result.success) {
        Write-Host "`nErgebnis:" -ForegroundColor Cyan

        if ($result.yamnet) {
            $confidence = [math]::Round($result.yamnet.confidence * 100, 1)
            Write-Host "  YAMNET Klassifikation:"
            Write-Host "    Klasse: $($result.yamnet.class)"
            Write-Host "    Vertrauen: $confidence%"
        }

        if ($result.spektral) {
            $similarity = [math]::Round($result.spektral.similarity * 100, 1)
            if ($result.spektral.match) { $matchText = "[OK]" } else { $matchText = "[NO]" }
            Write-Host "  Spektral-Vergleich:"
            Write-Host "    Aehnlichkeit: $similarity% $matchText"
        }
    } else {
        Write-Error "Fehler: $($result.detail)"
    }

    return $result
}

function Get-AudioTemplate {
    Write-Host "Lade Vorlage-Status..."

    $response = Invoke-WebRequest -Uri "$ApiUrl/template_status"
    $result = $response.Content | ConvertFrom-Json

    if ($result.template_loaded) {
        Write-Host "`n[OK] Vorlage geladen:" -ForegroundColor Green
        Write-Host "  Datei: $($result.filename)"
        Write-Host "  Form:  $($result.shape -join ' x ')"
    } else {
        Write-Host "`n[NO] Keine Vorlage geladen" -ForegroundColor Red
    }

    return $result
}

function Upload-AudioTemplate {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )

    if (-not (Test-Path $FilePath)) {
        Write-Error "Datei nicht gefunden: $FilePath"
        return
    }

    $file = Get-Item $FilePath
    $form = @{ file = $file }

    Write-Host "Lade neue Vorlage hoch: $($file.Name)..."

    $response = Invoke-WebRequest -Uri "$ApiUrl/upload_template" `
        -Method POST -Form $form

    $result = $response.Content | ConvertFrom-Json

    if ($result.success) {
        Write-Host "[OK] Vorlage erfolgreich hochgeladen!" -ForegroundColor Green
        Write-Host "  Form: $($result.template.shape -join ' x ')"
    } else {
        Write-Error "Fehler: $($result.detail)"
    }

    return $result
}

function Invoke-BatchCompare {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$FilePaths
    )

    $files = @()
    foreach ($path in $FilePaths) {
        if (Test-Path $path) {
            $files += Get-Item $path
        } else {
            Write-Warning "Datei nicht gefunden: $path"
        }
    }

    if ($files.Count -eq 0) {
        Write-Error "Keine gültigen Dateien gefunden"
        return
    }

    Write-Host "Vergleiche $($files.Count) Dateien..."

    $form = @{
        files = $files
    }

    $response = Invoke-WebRequest -Uri "$ApiUrl/batch_compare" `
        -Method POST -Form $form

    $result = $response.Content | ConvertFrom-Json

    if ($result.success) {
        Write-Host "`n$($result.summary)" -ForegroundColor Cyan
        Write-Host ""

        foreach ($r in $result.results) {
            if ($r.error) {
                Write-Host "$($r.filename): [ERROR]" -ForegroundColor Red
            } else {
                $similarity = [math]::Round($r.similarity * 100, 1)
                if ($r.match) { $matchText = "[OK]" } else { $matchText = "[NO]" }
                Write-Host "$($r.filename): $similarity% $matchText"
            }
        }
    } else {
        Write-Error "Fehler: $($result.detail)"
    }

    return $result
}

function Test-AudioAPI {
    Write-Host "Teste Audio Analysis API..." -ForegroundColor Cyan

    $response = Invoke-WebRequest -Uri "$ApiUrl/health"
    $health = $response.Content | ConvertFrom-Json

    if ($health.template_loaded) { $templateText = "[OK] Geladen" } else { $templateText = "[NO] Fehlt" }

    Write-Host "  Server Status: $($health.status)"
    Write-Host "  Template:      $templateText"
    Write-Host ""
    Write-Host "API laeuft auf: $ApiUrl" -ForegroundColor Green
}

# Aliases fuer schnellere Nutzung
New-Alias -Name compare -Value Compare-Audio -ErrorAction SilentlyContinue
New-Alias -Name analyze -Value Analyze-Audio -ErrorAction SilentlyContinue
New-Alias -Name template -Value Get-AudioTemplate -ErrorAction SilentlyContinue
New-Alias -Name upload -Value Upload-AudioTemplate -ErrorAction SilentlyContinue
New-Alias -Name batch -Value Invoke-BatchCompare -ErrorAction SilentlyContinue

Write-Host "
========================================
  Audio Analysis API - PowerShell Tools
========================================

Verfuegbare Funktionen:

  template
     Zeigt Vorlage-Status

  upload 'path/to/audio.wav'
     Laed neue Vorlage hoch

  compare 'path/to/audio.wav' [-Method dtw|cosine|embedding]
     Vergleicht Audio mit Vorlage (dtw/cosine = Spektral, embedding = Semantisch)

  analyze 'path/to/audio.wav'
     Hybrid-Analyse (YAMNet + Spektral)

  batch 'file1.wav', 'file2.wav', 'file3.wav'
     Vergleicht mehrere Dateien

  Test-AudioAPI
     Testet API-Verbindung

Beispiele:
  template
  compare 'D:\audio\test.wav'
  analyze 'D:\audio\test.wav'
  batch 'file1.wav', 'file2.wav'

========================================
"
