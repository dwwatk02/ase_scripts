param($csvfile);
$aseHostname=''
$aseApiKeyId=''
$aseApiKeySecret=''

# ASE authentication, grab sessionId
$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
# Add necessary cookies 
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
#write-host "session id is $sessionId"
#$apps=$(Invoke-WebRequest -Method GET -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId";"X-Requested-With"="XMLHttpRequest"}  -Uri "https://$aseHostname`:9443/ase/api/applications" -SkipCertificateCheck);

# create form element used for file upload to API POST, pulled from the command line parameter defining path to import csv file
$Form = [ordered]@{uploadedfile = Get-Item -Path $csvfile}
Invoke-WebRequest -Method Post -Form $Form -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"}  -Uri "https://$aseHostname`:9443/ase/api/appimport" -SkipCertificateCheck | Out-Null;
# wait 15 seconds for import to complete, then print out summary log
write-host "sleeping 15 seconds..."
Start-Sleep -Duration (New-TimeSpan -Seconds 15)
$importstatus=$(Invoke-WebRequest -Method GET -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId";"X-Requested-With"="XMLHttpRequest"}  -Uri "https://$aseHostname`:9443/ase/api/appimport/summarylog" -SkipCertificateCheck);
Invoke-WebRequest -Method GET -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId";"X-Requested-With"="XMLHttpRequest"}  -Uri "https://$aseHostname`:9443/ase/api/logout" -SkipCertificateCheck | Out-Null;
write-host "summary: $importstatus"