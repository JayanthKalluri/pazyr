# setup.ps1
$networks = @("data-network", "platform-network", "coe-network", "dns-network")

# Detect runtime
$runtime = $null
if (Get-Command podman -ErrorAction SilentlyContinue) {
    $runtime = "podman"
} elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    $runtime = "docker"
} else {
    Write-Error "	Neither Podman nor Docker found in PATH."
    exit 1
}

foreach ($net in $networks) {
    $exists = & $runtime network ls --format '{{.Name}}' | Select-String "^$net$"
    if (-not $exists) {
        Write-Host "	Creating network $net with $runtime..."
        & $runtime network create $net
    } else {
        Write-Host "	Network $net already exists."
    }
}
