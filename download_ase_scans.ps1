# === CONFIGURATION ===
$aseBaseUrl = "https://<domain>:9443/ase/api"  # <-- Change this
$apiKeyId = ""
$apiKeySecret = ""
$csvPath = "<path>\applications.csv"
$outputFolder = "<path>\downloadedScans"

# === ENSURE OUTPUT DIRECTORY EXISTS ===
if (-not (Test-Path $outputFolder)) {
    New-Item -ItemType Directory -Path $outputFolder | Out-Null
}

# === LOGIN USING API KEY ===
$loginUrl = "$aseBaseUrl/keylogin/apikeylogin"
$loginBody = @{
    keyId     = $apiKeyId
    keySecret = $apiKeySecret
} | ConvertTo-Json -Depth 2

# Create WebSession to store cookies
$webSession = New-Object Microsoft.PowerShell.Commands.WebRequestSession

try {
    $loginResponse = Invoke-RestMethod -Method Post -Uri $loginUrl -SkipCertificateCheck -Body $loginBody `
        -ContentType "application/json" -WebSession $webSession

    if (-not $loginResponse.loggedIn) {
        throw "Login failed."
    }

    $xsrfToken = $loginResponse.sessionId
    Write-Host "Logged in successfully. Session ID (XSRF Token): $xsrfToken"
} catch {
    Write-Error "Login failed: $_"
    exit 1
}

# === GET ALL APPLICATIONS ===
$applicationsUrl = "$aseBaseUrl/applications"
try {
    $applications = Invoke-RestMethod -Uri $applicationsUrl -SkipCertificateCheck -Method Get `
        -WebSession $webSession `
        -Headers @{ "asc_xsrf_token" = $xsrfToken; "Content-Type" = "application/json" }
} catch {
    Write-Error "Failed to retrieve application list: $_"
    exit 1
}

# === READ CSV AND PROCESS ===
$appList = Import-Csv -Path $csvPath

foreach ($app in $appList) {
    $appName = $app.Name.Trim()
    if (-not $appName) { continue }

    Write-Host "`nSearching for application ID for: $appName"

    Add-Type -AssemblyName System.Web
    $matchingApp = $applications | Where-Object { [System.Web.HttpUtility]::HtmlDecode($_.name) -eq $appName }

    if (-not $matchingApp) {
        Write-Warning "Application '$appName' not found in ASE."
        continue
    }

    $applicationId = $matchingApp.id
    Write-Host "Found Application ID: $applicationId for '$appName'"

    # === GET JOBS FOR APPLICATION ID ===
    $query = [uri]::EscapeDataString("ApplicationId=$applicationId")
    $searchUrl = "$aseBaseUrl/jobs/search?queryString=$query"

    try {
        $jobResults = Invoke-RestMethod -Uri $searchUrl -SkipCertificateCheck -Method Get `
            -WebSession $webSession `
            -Headers @{ "asc_xsrf_token" = $xsrfToken; "Content-Type" = "application/json" }
    } catch {
        Write-Warning "Failed to search jobs for $appName ($applicationId)  $_"
        continue
    }

    if (-not $jobResults -or $jobResults.Count -eq 0) {
        Write-Host "No jobs found for application '$appName'"
        continue
    }

    # === SELECT HIGHEST jobId ===
    $latestJob = $jobResults | Sort-Object id -Descending | Select-Object -First 1
    $jobId = $latestJob.id
    $jobName = $latestJob.name -replace '[\\/:*?"<>|]', '_'  # Clean for file name
    $scanDownloadUrl = "$aseBaseUrl/jobs/$jobId/downloadScanFile"
    $scanFilePath = Join-Path $outputFolder "$jobName-$jobId.scan"

    Write-Host "Downloading latest .scan file for Job ID: $jobId ($jobName)"

    try {
        Invoke-WebRequest -Uri $scanDownloadUrl -SkipCertificateCheck -Method Get `
            -WebSession $webSession `
            -Headers @{ "asc_xsrf_token" = $xsrfToken; "Content-Type" = "application/json" } `
            -OutFile $scanFilePath

        Write-Host "Downloaded: $scanFilePath"
    } catch {
        Write-Warning "Failed to download .scan file for Job ID $jobId  $_"
    }
}

Write-Host "`nCompleted downloads."
