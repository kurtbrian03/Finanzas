Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-LogFilePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Name
    )
    return (Join-Path $Root $Name)
}

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -FilePath $FilePath -Encoding utf8 -Append
}
