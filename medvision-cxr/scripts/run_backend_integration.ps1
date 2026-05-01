param(
    [string]$PythonExe = "",
    [string]$PgDataDir = "",
    [string]$PgLogPath = "",
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 5433,
    [string]$DbName = "medvision_cxr",
    [string]$DbUser = "postgres",
    [string]$DbPassword = "",
    [int]$BackendPort = 8000,
    [string]$RedisUrl = "redis://127.0.0.1:6379/0",
    [string]$MinioEndpoint = "127.0.0.1:9000",
    [string]$MinioAccessKey = "minioadmin",
    [string]$MinioSecretKey = "minioadmin",
    [string]$TestPath = "tests/integration",
    [switch]$SkipDependencyInstall,
    [switch]$KeepBackendRunning
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspaceRoot = (Resolve-Path (Join-Path $repoRoot "..")).Path
$backendDir = Join-Path $repoRoot "backend"

if (-not $PythonExe) {
    $PythonExe = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
}

if (-not $PgDataDir) {
    $PgDataDir = Join-Path $workspaceRoot ".pgdata-dev"
}

if (-not $PgLogPath) {
    $PgLogPath = Join-Path $workspaceRoot "postgres-dev.log"
}

$apiBaseUrl = "http://127.0.0.1:$BackendPort/api/v1"

function Ensure-Command {
    param([string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $postgresRoot = Join-Path ${env:ProgramFiles} "PostgreSQL"
    if (Test-Path $postgresRoot) {
        $candidate = Get-ChildItem $postgresRoot -Directory | Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\$Name.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }

    throw "Required command '$Name' was not found in PATH or the default PostgreSQL install directory."
}

function Get-DatabaseUrl {
    $passwordPart = if ($DbPassword) { ":$([System.Uri]::EscapeDataString($DbPassword))" } else { "" }
    return "postgresql+psycopg2://$DbUser$passwordPart@${DbHost}:${DbPort}/$DbName"
}

function Test-DatabaseConnection {
    $pythonSnippet = @"
import psycopg2

try:
    conn = psycopg2.connect(
        dbname=r'''$DbName''',
        user=r'''$DbUser''',
        password=r'''$DbPassword''',
        host=r'''$DbHost''',
        port=$DbPort,
    )
    conn.close()
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
"@

    & $PythonExe -c $pythonSnippet | Out-Null
    return $LASTEXITCODE -eq 0
}

function Wait-ForPostgres {
    param([int]$MaxAttempts = 20)

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        if (Test-DatabaseConnection) {
            return
        }
        Start-Sleep -Seconds 1
    }

    throw "PostgreSQL did not become ready on ${DbHost}:${DbPort}."
}

function Wait-ForBackend {
    param([int]$MaxAttempts = 20)

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $health = Invoke-RestMethod "$apiBaseUrl/health" -TimeoutSec 5
            if ($health.status -eq "ok" -and $health.db -eq "up") {
                return
            }
        }
        catch {
        }
        Start-Sleep -Seconds 1
    }

    throw "Backend did not become ready at $apiBaseUrl/health."
}

function Ensure-DatabaseExists {
    $exists = (& $script:psqlExe -h $DbHost -p $DbPort -U $DbUser -d postgres -tAc "select 1 from pg_database where datname = '$DbName'").Trim()
    if ($exists -ne "1") {
        & $script:createdbExe -h $DbHost -p $DbPort -U $DbUser $DbName
    }
}

function Set-SharedEnvironment {
    $databaseUrl = Get-DatabaseUrl

    $env:DATABASE_URL = $databaseUrl
    $env:MEDVISION_TEST_DATABASE_URL = $databaseUrl
    $env:MEDVISION_API_BASE_URL = $apiBaseUrl
    $env:REDIS_URL = $RedisUrl
    $env:MINIO_ENDPOINT = $MinioEndpoint
    $env:MINIO_ACCESS_KEY = $MinioAccessKey
    $env:MINIO_SECRET_KEY = $MinioSecretKey
    $env:MINIO_SECURE = "false"
}

function Start-BackendProcess {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $PythonExe
    $startInfo.Arguments = "-m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
    $startInfo.WorkingDirectory = $backendDir
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.Environment["DATABASE_URL"] = $env:DATABASE_URL
    $startInfo.Environment["REDIS_URL"] = $env:REDIS_URL
    $startInfo.Environment["MINIO_ENDPOINT"] = $env:MINIO_ENDPOINT
    $startInfo.Environment["MINIO_ACCESS_KEY"] = $env:MINIO_ACCESS_KEY
    $startInfo.Environment["MINIO_SECRET_KEY"] = $env:MINIO_SECRET_KEY
    $startInfo.Environment["MINIO_SECURE"] = $env:MINIO_SECURE

    return [System.Diagnostics.Process]::Start($startInfo)
}

$script:pgIsReadyExe = Ensure-Command "pg_isready"
$script:pgCtlExe = Ensure-Command "pg_ctl"
$script:psqlExe = Ensure-Command "psql"
$script:createdbExe = Ensure-Command "createdb"

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found at $PythonExe"
}

if ($DbPassword) {
    $env:PGPASSWORD = $DbPassword
}
else {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

if (-not (Test-DatabaseConnection)) {
    if (-not (Test-Path $PgDataDir)) {
        throw "PostgreSQL is not running and data directory was not found at $PgDataDir"
    }

    & $script:pgCtlExe -D $PgDataDir -l $PgLogPath -o "-p $DbPort" start | Out-Null
    Wait-ForPostgres
}

Ensure-DatabaseExists
Set-SharedEnvironment

$openApiScript = Join-Path $repoRoot "scripts\generate_openapi.py"
if (Test-Path $openApiScript) {
    & $PythonExe $openApiScript
}

if (-not $SkipDependencyInstall) {
    Push-Location $backendDir
    try {
        & $PythonExe -m pip install -r requirements.txt
    }
    finally {
        Pop-Location
    }
}

Push-Location $backendDir
try {
    & $PythonExe -m alembic upgrade head
}
finally {
    Pop-Location
}

$backendProcess = $null
$startedBackend = $false

try {
    try {
        $health = Invoke-RestMethod "$apiBaseUrl/health" -TimeoutSec 5
        if ($health.status -ne "ok" -or $health.db -ne "up") {
            throw "Backend health check returned unexpected status."
        }
    }
    catch {
        $backendProcess = Start-BackendProcess
        $startedBackend = $true
        Wait-ForBackend
    }

    Push-Location $backendDir
    try {
        & $PythonExe -m pytest -m integration $TestPath
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($startedBackend -and -not $KeepBackendRunning -and $backendProcess -and -not $backendProcess.HasExited) {
        $backendProcess.Kill()
        $backendProcess.WaitForExit()
    }
}