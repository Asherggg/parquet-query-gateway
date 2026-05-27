param(
    [string]$DataRoot = "/home/ai_ds/sd_data_center",
    [string]$Config = "config/production.yml",
    [int]$Port = 8080,
    [switch]$OverwriteConfig,
    [switch]$SkipOpenCLI
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python is required"
}

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

$initArgs = @("init-config", "--data-root", $DataRoot, "--output", $Config)
if ($OverwriteConfig) {
    $initArgs += "--overwrite"
}

$initOutput = & .\.venv\Scripts\python.exe -m parquet_gateway.cli @initArgs
Write-Output $initOutput
$parsed = $initOutput | ConvertFrom-Json
$adminToken = $parsed.admin_token

if (-not $SkipOpenCLI) {
    if (-not (Get-Command opencli -ErrorAction SilentlyContinue)) {
        if (Get-Command npm.cmd -ErrorAction SilentlyContinue) {
            npm.cmd install -g @jackwener/opencli
        } else {
            Write-Warning "npm.cmd is not installed; skipping OpenCLI installation"
            $SkipOpenCLI = $true
        }
    }
    if (-not $SkipOpenCLI) {
        opencli plugin install "file:///$((Get-Location).Path.Replace('\', '/'))"
    }
}

Write-Output ""
Write-Output "Installation complete."
Write-Output ""
Write-Output "Start the gateway:"
Write-Output '  $env:PARQUET_GATEWAY_CONFIG = "' + $Config + '"'
Write-Output '  $env:PARQUET_GATEWAY_AUDIT_DB = "audit.sqlite3"'
Write-Output "  .\.venv\Scripts\parquet-gateway.exe"
Write-Output ""
Write-Output "In another shell, verify with:"
Write-Output '  $env:PARQUET_GATEWAY_URL = "http://127.0.0.1:' + $Port + '"'
Write-Output '  $env:PARQUET_GATEWAY_TOKEN = "' + $adminToken + '"'
Write-Output "  .\.venv\Scripts\parquet-gw.exe smoke-test"
