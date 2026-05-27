param(
    [Parameter(Mandatory = $true)]
    [string]$GatewayUrl,
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd is required to install OpenCLI"
}

if (-not (Get-Command opencli -ErrorAction SilentlyContinue)) {
    npm.cmd install -g @jackwener/opencli
}

$pluginPath = "file:///$((Get-Location).Path.Replace('\', '/'))"
try {
    opencli plugin install $pluginPath
} catch {
    opencli plugin update parquet
}

Write-Output ""
Write-Output "Client installation complete."
Write-Output ""
Write-Output "Set these in PowerShell:"
Write-Output ('  $env:PARQUET_GATEWAY_URL = "' + $GatewayUrl + '"')
if ($Token) {
    Write-Output ('  $env:PARQUET_GATEWAY_TOKEN = "' + $Token + '"')
} else {
    Write-Output '  $env:PARQUET_GATEWAY_TOKEN = "<token from your administrator>"'
}
Write-Output ""
Write-Output "Verify:"
Write-Output "  opencli parquet smoke-test"
Write-Output "  opencli parquet datasets"
