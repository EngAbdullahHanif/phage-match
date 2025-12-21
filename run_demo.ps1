param(
    [switch]$Force,
    [switch]$DemoOnly,
    [switch]$Reset,
    [switch]$UseConda,
    [switch]$NoBrowser,
    [string]$HostId = "H001",
    [int]$Port = 8000
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$resultsPath = Join-Path $root "results\$HostId"
$rankingsPath = Join-Path $root "rankings\$HostId"
$viewerPath = Join-Path $root "viewer\index.html"
$preferred = "results"

function Invoke-Pipeline {
    param(
        [switch]$Force,
        [string[]]$Targets = @(),
        [switch]$UseConda
    )
    $args = @("-m", "snakemake", "-s", "Snakefile", "--configfile", "config.yaml", "--cores", "1")
    if ($UseConda) { $args += "--use-conda" }
    if ($Force) { $args += "--forceall" }
    if ($Targets) { $args += $Targets }
    Write-Host "Running pipeline: python $($args -join ' ')" -ForegroundColor Cyan
    $p = Start-Process -FilePath "python" -ArgumentList $args -WorkingDirectory $root -NoNewWindow -Wait -PassThru
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

function Reset-Outputs {
    param([string]$HostId)
    $targets = @(
        (Join-Path -Path $root -ChildPath "results\$HostId")
        (Join-Path -Path $root -ChildPath "rankings\$HostId")
    )
    foreach ($target in $targets) {
        if (Test-Path $target) {
            Write-Host "Removing $target" -ForegroundColor Yellow
            Remove-Item -Recurse -Force $target
        }
    }
}

if (-not $DemoOnly) {
    if ($Reset) { Reset-Outputs -HostId $HostId }
    $rankingTargets = @(
        "rankings/$HostId/ranking.csv",
        "rankings/$HostId/evidence_bundle.json"
    )
    $publishTargets = @("results/$HostId/evidence_bundle.json")
    $built = Invoke-Pipeline -Force:$Force -Targets $rankingTargets -UseConda:$UseConda
    if ($built) {
        Invoke-Pipeline -Force:$Force -Targets $publishTargets -UseConda:$UseConda | Out-Null
    }
}

if (Test-Path $resultsPath) {
    $preferred = "results"
} elseif (Test-Path $rankingsPath) {
    $preferred = "rankings"
} else {
    $preferred = "demo"
}

$server = Start-Server -Port $Port -Root $root

if (-not $NoBrowser) {
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
}

if ($NoBrowser) {
    $rankingPath = Join-Path $root "$preferred\$HostId\ranking.csv"
    if (-not (Test-Path $rankingPath)) {
        $rankingPath = Join-Path $root "rankings\$HostId\ranking.csv"
    }
    if (Test-Path $rankingPath) {
        Write-Host "Ranking ($rankingPath):" -ForegroundColor Green
        Import-Csv $rankingPath | Format-Table -AutoSize
    } else {
        Write-Warning "No ranking.csv found for host $HostId in results/ or rankings/."
    }
}

Write-Host "Viewer source preference: $preferred" -ForegroundColor DarkGray
Write-Host "Outputs expected in:" -ForegroundColor DarkGray
Write-Host "  results\$HostId or rankings\$HostId (demo fallback: demo_outputs\$HostId)" -ForegroundColor DarkGray
