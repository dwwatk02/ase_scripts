# Copyright 2023 HCL America
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

$aseHostname = "<your ASE host name>"
$aseApiKeyId ="<your key id>"
$aseApiKeySecret ="<your key secret>"
$aseAppName = "<name of app>"
$url = "<starting URL of scan>"
$scanTemplate = "573" # 573 = Regular Scan

write-host "======== Step: Running scan in $url ========"
# ASE Authentication
$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
# Get aseAppId
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
$aseAppId=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/applications/search?searchTerm=$aseAppName" -SkipCertificateCheck | ConvertFrom-Json).id;
write-host $aseAppId
write-host $sessionId
# Compose scanName with Gitlab repository name + Gitlab job Id 
$scanName="$aseAppName-scan";
write-host $scanName;
# Creating a new job in AppScan Enterprise
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
$jobId=$(Invoke-WebRequest -Method "POST" -WebSession $session -Headers @{"asc_xsrf_token"="$sessionId" ; "Accept"="application/json"} -ContentType "application/json" -Body "{`"testPolicyId`":`"3`",`"folderId`":`"4`",`"applicationId`":`"$aseAppId`",`"name`":`"$scanName`",`"description`":`"`",`"contact`":`"`"}" -Uri "https://$aseHostname`:9443/ase/api/jobs/$scanTemplate/dastconfig/createjob" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty Id);
# Writing 2 files jobId_var.txt scanName_var.txt with jobid and scanname strings. It will be used by others scripts.
write-output "$jobId" > jobId_var.txt;
write-output $scanName > scanName_var.txt;
write-host "Scan name will be $scanName. You can filter all issues found through Scan Name:$scanName ($jobId)";
write-host "The JobId was created, its name is $jobId and its located in ASE folder";
# Updating ASE jobId with URL scan target 
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
Invoke-WebRequest -Method "POST" -WebSession $session -Headers @{"asc_xsrf_token"="$sessionId" ; "Accept"="application/json"} -ContentType "application/json" -Body "{`"scantNodeXpath`":`"StartingUrl`",`"scantNodeNewValue`":`"$url`"}" -Uri "https://$aseHostname`:9443/ase/api/jobs/$jobId/dastconfig/updatescant" -SkipCertificateCheck | Out-Null;
write-host "The URL Target was updated in Job Id. It was updated to $url";

# Checking jobId integrity 
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
$eTag=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/jobs/$jobId" -SkipCertificateCheck).headers.Etag;
write-host "The Etag is $eTag. It is used to verify that is jobs state has not been changed or updated before making the changes to the job.";
# Starting scan
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
Invoke-WebRequest -Method "POST" -WebSession $session -Headers @{"asc_xsrf_token"="$sessionId" ; "Accept"="application/json" ; "If-Match"="$eTag"} -ContentType "application/json" -Body "{`"type`":`"run`"}" -Uri "https://$aseHostname`:9443/ase/api/jobs/$jobId/actions?isIncremental=false&isRetest=false&basejobId=-1" -SkipCertificateCheck | Out-Null;
sleep 60;
# Checking scan status
$scanStatus="Running";
while (("$scanStatus" -like "*Running*") -or ("$scanStatus" -like "*En*")){
  $scanStatus=$((Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/folderitems/$jobId/statistics" -SkipCertificateCheck).content | Convertfrom-json).statistics.status;
  write-host $scanStatus;
  # If ASE back Suspended status it means the scan is failed
  if ($scanStatus -like "*Suspended*" -or $scanStatus -like "*Suspendido*"){
    exit 1
    }
  sleep 60
  }
write-host "Scan finished."
