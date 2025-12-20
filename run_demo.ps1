param(
    [switch]$Force,
    [switch]$DemoOnly,
    [string]$HostId = "H001",
    [int]$Port = 8000
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$resultsPath = Join-Path $root "rankings\$HostId"
$viewerPath = Join-Path $root "viewer\index.html"
$preferred = "results"

function Invoke-Pipeline {
    param([switch]$Force)
    $args = @("-m", "snakemake", "-s", "Snakefile", "--configfile", "config.yaml", "--cores", "1")
    if ($Force) { $args += "--forceall" }
    Write-Host "Running pipeline: python $($args -join ' ')" -ForegroundColor Cyan
    $p = Start-Process -FilePath "python" -ArgumentList $args -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -ne 0) {
        Write-Warning "Pipeline exited with code $($p.ExitCode). Viewer will fall back to demo outputs."
        return $false
    }
    return $true
}

function Start-Server {
    param([int]$Port,[string]$Root)
    $args = @("-m", "http.server", $Port, "--directory", $Root)
    try {
        $proc = Start-Process -FilePath "python" -ArgumentList $args -WindowStyle Hidden -PassThru
        Write-Host "Serving $Root at http://localhost:$Port (PID $($proc.Id)). Close the window or stop the process to end serving." -ForegroundColor DarkGray
        return $proc
    } catch {
        Write-Warning "Could not start local server on port $Port. Falling back to file:// URL."
        return $null
    }
}

if (-not $DemoOnly) {
    Invoke-Pipeline -Force:$Force | Out-Null
}

if (-not (Test-Path $resultsPath)) { $preferred = "demo" }

$server = Start-Server -Port $Port -Root $root

if ($server) {
    $url = "http://localhost:$Port/viewer/index.html?host=$HostId&preferred=$preferred"
    Write-Host "Opening viewer via local server..." -ForegroundColor Green
    Write-Host "If the browser does not open, copy-paste this into the address bar:" -ForegroundColor Yellow
    Write-Host $url -ForegroundColor White
    Start-Process $url | Out-Null
} else {
    $uriPath = ($viewerPath -replace "\\", "/")
    $query = "?host=$HostId&preferred=$preferred"
    $url = "file:///$uriPath$query"
    Write-Host "Opening viewer (file:// fallback)..." -ForegroundColor Green
    Write-Host $url -ForegroundColor White
    Start-Process $url | Out-Null
}
