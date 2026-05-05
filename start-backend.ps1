param(
    [switch]$SkipInstall,
    [switch]$NoDb
)

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$venvDir = Join-Path $backendDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$requirementsFile = Join-Path $backendDir "requirements.txt"
$envFile = Join-Path $backendDir ".env"

if (-not (Test-Path $backendDir)) {
    throw "Could not find backend directory at: $backendDir"
}

if (-not $NoDb) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "Starting backend database container..."
        Push-Location $backendDir
        try {
            docker compose up -d db
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Warning "Docker is not available. Skipping DB startup. Use -NoDb to hide this warning."
    }
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating backend virtual environment at backend/.venv..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvDir
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvDir
    }
    else {
        throw "Python 3 is required but was not found in PATH."
    }
}

if (-not $SkipInstall) {
    Write-Host "Installing backend dependencies..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r $requirementsFile
}

if (-not (Test-Path $envFile)) {
    Write-Warning "Missing backend/.env. Create it with OPENAI_API_KEY and DATABASE_URL before sending chat requests."
}

# Load env file values into the current process environment so the Python uvicorn process inherits them
if (Test-Path $envFile) {
    Write-Host "Loading environment variables from $envFile"
    Get-Content $envFile | ForEach-Object {
        if ($_ -and -not ($_ -match '^\s*#')) {
            $parts = $_ -split '='; if ($parts.Length -ge 2) {
                $name = $parts[0].Trim();
                $value = ($parts[1..($parts.Length-1)] -join '=').Trim();
                try {
                    Set-Item -Path "Env:$name" -Value $value -ErrorAction Stop
                } catch {
                    [System.Environment]::SetEnvironmentVariable($name, $value)
                }
            }
        }
    }
}

# If running the backend locally (not inside Docker) and the DATABASE_URL points
# to the container host `db`, rewrite it to `localhost` so local Python process can connect.
if ($env:DATABASE_URL) {
    if ($env:DATABASE_URL -match '@db:') {
        Write-Host "Adjusting DATABASE_URL host 'db' -> 'localhost' for local backend run"
        $newUrl = $env:DATABASE_URL -replace '@db:', '@localhost:'
        try {
            Set-Item -Path "Env:DATABASE_URL" -Value $newUrl -ErrorAction Stop
        } catch {
            [System.Environment]::SetEnvironmentVariable('DATABASE_URL', $newUrl)
        }
    }
}

Write-Host "Starting backend API at http://localhost:8000 ..."
Push-Location $repoRoot
try {
    & $venvPython -m uvicorn backend.main:app --reload --port 8000
}
finally {
    Pop-Location
}
