<#
.SYNOPSIS
    Secure local credential vault using Windows DPAPI encryption.

.DESCRIPTION
    Stores secrets encrypted with the current Windows user's DPAPI key.
    Each secret is a separate .sec file inside a .secure_vault/ folder
    with ACLs locked to the current user + SYSTEM only.

    This is for LOCAL DEV use. For production, use a real secret manager
    (Azure Key Vault, HashiCorp Vault, etc.).

.NOTES
    IMPORTANT: Secrets are bound to YOUR Windows user account on THIS machine.
    If you copy .sec files to another machine or user, they CANNOT be decrypted.
    There is no recovery — if the file is corrupted or moved, the secret is gone.

.EXAMPLE
    # Store a secret
    .\secure_vault.ps1 -Action set -Name API_KEY -Value "your-key-here"

    # Store a secret interactively (input hidden)
    .\secure_vault.ps1 -Action setprompt -Name API_KEY

    # Retrieve a secret
    .\secure_vault.ps1 -Action get -Name API_KEY

    # Check vault status
    .\secure_vault.ps1 -Action status

    # Repair file permissions if they got changed
    .\secure_vault.ps1 -Action doctor -Name API_KEY

.TROUBLESHOOTING
    "Secret is unreadable / garbled output"
        → You're on a different user account or machine than when the secret was saved.
          DPAPI encryption is user+machine-bound. Re-save the secret on this account.

    "ACL hardening skipped" warning
        → icacls.exe failed. Run: .\secure_vault.ps1 -Action doctor -Name <name>
          If that still fails, check that you have admin rights or the path isn't read-only.

    "setprompt doesn't show what I typed"
        → That's by design (secure input). After saving, run -Action get to verify.

    "Value is required" error on set
        → Pass -Value "your-secret" or use -Action setprompt for interactive entry.
#>
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

# ACL grants: (OI) = Object Inherit, (CI) = Container Inherit, F = Full Control
# This means the current user and SYSTEM get full access; everyone else is denied.
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
