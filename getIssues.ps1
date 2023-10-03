write-host "======== Step: Starting Script ========"
$aseApiKeyId = ""
$aseApiKeySecret = ""
$aseHostname = ""
#$appName = "AltoroJ_Example"
# ASE authentication
$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
write-host "======== Step: Authenticating to AppScan Enterprise ========"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
#write-host $sessionId
$headers = @{"Asc_xsrf_token"="$sessionId"}
$headers.Add("Range","items=0-99")
write-host "======== Step: Grabbing all Applications from AppScan Enterprise ========"
$apps = $(Invoke-WebRequest -WebSession $session -Headers $headers -Uri "https://$aseHostname`:9443/ase/api/applications?columns=name" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty name);
foreach ($appName in $apps) {
	Invoke-WebRequest -WebSession $session -Headers $headers -Uri "https://$aseHostname`:9443/ase/api/issues?query=Application%20Name=$appName`&compactResponse=false" -SkipCertificateCheck -OutFile C:\temp\$appName`.json -PassThru | Out-Null;
	write-host "======== Step: Wrote output file for $appName` ========"
}