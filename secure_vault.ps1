param(
    [ValidateSet("set", "setprompt", "get", "status", "doctor")]
    [string]$Action = "status",
    [string]$Name = "BANKR_API_KEY",
    [string]$Value = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Security
$VaultDir = Join-Path $PSScriptRoot ".secure_vault"
$SecretFile = Join-Path $VaultDir ("{0}.sec" -f $Name)
$CurrentUser = "{0}\{1}" -f $env:USERDOMAIN, $env:USERNAME

function Set-CurrentUserOnlyAcl {
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        $grantUser = "{0}:(OI)(CI)F" -f $CurrentUser
        $grantSystem = "SYSTEM:(OI)(CI)F"
        $icaclsArgs = @($Path, '/inheritance:r', '/grant:r', $grantUser, $grantSystem)
        $p = Start-Process -FilePath 'icacls.exe' -ArgumentList $icaclsArgs -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -ne 0) {
            Write-Warning "Directory ACL hardening skipped (icacls exit code $($p.ExitCode))."
        }
    }
    catch {
        Write-Warning "Directory ACL hardening skipped: $($_.Exception.Message)"
    }
}

function Set-CurrentUserOnlyFileAcl {
    param([Parameter(Mandatory = $true)][string]$Path)

    try {
        $grantUser = "{0}:F" -f $CurrentUser
        $grantSystem = "SYSTEM:F"
        $icaclsArgs = @($Path, '/inheritance:r', '/grant:r', $grantUser, $grantSystem)
        $p = Start-Process -FilePath 'icacls.exe' -ArgumentList $icaclsArgs -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -ne 0) {
            Write-Warning "File ACL hardening skipped (icacls exit code $($p.ExitCode))."
        }
    }
    catch {
        Write-Warning "File ACL hardening skipped: $($_.Exception.Message)"
    }
}

function Initialize-Vault {
    if (-not (Test-Path $VaultDir)) {
        New-Item -ItemType Directory -Path $VaultDir -Force | Out-Null
    }
    Set-CurrentUserOnlyAcl -Path $VaultDir
}

function Set-Secret {
    Initialize-Vault
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Value is required for -Action set"
    }

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    $encrypted = [System.Security.Cryptography.ProtectedData]::Protect($bytes, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
    $encoded = [Convert]::ToBase64String($encrypted)
    Set-Content -Path $SecretFile -Value $encoded -Encoding ascii -NoNewline
    Set-CurrentUserOnlyFileAcl -Path $SecretFile
    Write-Output "Saved secret '$Name' in secure vault."
}

function Set-SecretPrompt {
    Initialize-Vault
    $secure = Read-Host -AsSecureString -Prompt "Enter value for $Name"
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        if ([string]::IsNullOrWhiteSpace($plain)) {
            throw "Value is required for -Action setprompt"
        }
        $Value = $plain
        Set-Secret
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Get-Secret {
    if (-not (Test-Path $SecretFile)) {
        exit 1
    }

    $encoded = Get-Content -Path $SecretFile -Raw
    $encrypted = [Convert]::FromBase64String($encoded.Trim())
    $bytes = [System.Security.Cryptography.ProtectedData]::Unprotect($encrypted, $null, [System.Security.Cryptography.DataProtectionScope]::CurrentUser)
    ([System.Text.Encoding]::UTF8.GetString($bytes)).Trim()
}

function Get-Status {
    Initialize-Vault
    $exists = Test-Path $SecretFile
    if ($exists) {
        Write-Output "Vault: READY | Secret '$Name': PRESENT"
    }
    else {
        Write-Output "Vault: READY | Secret '$Name': MISSING"
    }
}

function Repair-VaultAcl {
    Initialize-Vault
    if (Test-Path $SecretFile) {
        Set-CurrentUserOnlyFileAcl -Path $SecretFile
    }
    Write-Output "Vault ACL repair complete for '$Name'."
}

switch ($Action) {
    "set" { Set-Secret; break }
    "setprompt" { Set-SecretPrompt; break }
    "get" { Get-Secret; break }
    "status" { Get-Status; break }
    "doctor" { Repair-VaultAcl; break }
}
