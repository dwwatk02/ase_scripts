write-host "======== Starting Script ========"
$aseApiKeyId = ""
$aseApiKeySecret = ""
$aseHostname = ""
$appName = ""
# ASE authentication
$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
# Looking for $aseAppName into ASE
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
write-host "======== Authenticated, querying issues ========"
$headers = @{"Asc_xsrf_token"="$sessionId"}
$headers.Add("Range","items=0-99")
Invoke-WebRequest -WebSession $session -Headers $headers -Uri "https://$aseHostname`:9443/ase/api/issues?query=Application%20Name=$appName`&compactResponse=false" -SkipCertificateCheck -OutFile out.json -PassThru | Out-Null;
write-host "======== Output file: out.json ========"