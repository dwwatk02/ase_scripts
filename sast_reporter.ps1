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


$aseToken = "C:\ProgramData\HCL\AppScanSource\config\ounceautod.token"
$aseAppName = ""
$aseApiKeyId = ""
$aseApiKeySecret = ""
$aseHostname = ""
$unknownCounter = 0;
$highCounter = 0;
$medCounter = 0;
$lowCounter = 0;
$infoCounter = 0;

$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin"  | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
# Get the aseAppId from ASE
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
$aseAppId=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/applications/search?searchTerm=$aseAppName" | ConvertFrom-Json).id;
# Request report generation based on scanName and status New, Fixed, Reopened, InProgress, Open and Passed. Ignoring status Noise.
$reportId=$(Invoke-WebRequest -Method "POST" -WebSession $session -Headers @{"asc_xsrf_token"="$sessionId" ; "Accept"="application/json"} -ContentType "application/json" -Body "{`"config`":{`"executiveSummaryIncluded`":true,`"advisoriesIncluded`":true,`"issueConfig`":{`"issueAttributeConfig`":{`"showEmptyValues`":true,`"attributeLookups`":[`"applicationname`",`"cvss`",`"comments`",`"description`",`"id`",`"location`",`"overdue`",`"scanname`",`"scanner`",`"severityvalue`",`"status`",`"datecreated`",`"fixeddate`",`"lastupdated`",`"accesscomplexity`",`"accessvector`",`"authentication`",`"availabilityimpact`",`"confidentialityimpact`",`"exploitability`",`"integrityimpact`",`"remediationlevel`",`"reportconfidence`",`"api`",`"callingline`",`"callingmethod`",`"class`",`"classification`",`"databasename`",`"databaseservicename`",`"databasetype`",`"databaseversion`",`"discoverymethod`",`"domain`",`"element`",`"externalid`",`"host`",`"line`",`"package`",`"path`",`"port`",`"projectid`",`"projectname`",`"projectversion`",`"projectversionid`",`"scheme`",`"sourcefile`",`"third-partyid`",`"username`"]},`"includeAdditionalInfo`":false},`"pdfPageBreakOnIssue`":false,`"sortByURL`":false},`"layout`":{`"reportOptionLayoutCoverPage`":{`"companyLogo`":`"`",`"additionalLogo`":`"`",`"includeDate`":true,`"includeReportType`":false,`"reportTitle`":`"`",`"description`":`"`"},`"reportOptionLayoutBody`":{`"header`":`"`",`"footer`":`"`"},`"includeTableOfContents`":false},`"reportFileType`":`"XML`",`"issueIdsAndQueries`":[`"status`=New,status`=Fixed,status`=Reopened,status`=InProgress,status`=Open,status`=Passed`"]}" -Uri "https://$aseHostname`:9443/ase/api/issues/reports/securitydetails?appId=$aseAppId" -SkipCertificateCheck | Select-Object -Expand Content | Select-String -Pattern "Report id: (Report\d+)" | % {$_.Matches.Groups[1].Value});
write-host "$reportId"
# Check report status generation
$reportStatus=$((Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status").content | ConvertFrom-Json).reportJobState
write-host "$reportStatus"
# Wait report generation finished
#while ($reportStatusCode -ne 201){
#  $reportStatusCode=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status").statusCode
#  write-host "Report being generated"
#}
while ($reportStatusCode -ne 201){
  try{
    $reportStatusCode=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status).statusCode;
    sleep 10;
  }
  catch{
    write-Host $_;
  }
  write-host "Report being generated";
}
sleep 10;
# Request download report file zipped
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId"  -OutFile scan_report.zip -PassThru | Out-Null;

write-host "The scan name $scanName was exported from Appscan Enterprise."

write-host "======== Step: Reading ASE SAST XML  ========"
# Unzip scan_report.zip and open the folder
Expand-Archive .\scan_report.zip
cd .\scan_report\

# Load list of ase xml files
$files=$(Get-Item -Path *.xml);
# For each XML file extract vulnerabilities items
ForEach ($file in $files){
  [XML]$xml = Get-Content $file;
    # If there is just 1 vulnerability item in the XML file
    if ($xml.'xml-report'.'issue-group'.item.count -eq 1){
      $ErrorActionPreference = 'SilentlyContinue';
      $nameMessageDescriptionCode=$xml.'xml-report'.'issue-group'.item.'issue-type'.ref;
      
      $sevValue=($xml.'xml-report'.'issue-group'.item.'attributes-group'.attribute | Where-Object{$_.name -eq 'Severity Value:'}).value.Replace('Use CVSS','Unknown');
    if($sevValue -eq "Unknown"){
      $unknownCounter++;
    }
    if($sevValue -eq "High"){
      $highCounter++;
    }
    if($sevValue -eq "Medium"){
      $medCounter++;
    }
    if($sevValue -eq "Low"){
      $lowCounter++;
    }
    if($sevValue -eq "Information"){
      $infoCounter++;
    }
    }
    else{
      $countIssues=$xml.'xml-report'.'issue-group'.item.count-1
      [array]$totalIssues=@(0..$countIssues);
      ForEach ($i in $totalIssues) {
        $ErrorActionPreference = 'SilentlyContinue';
        $nameMessageDescriptionCode=$xml.'xml-report'.'issue-group'.item[$i].'issue-type'.ref;
        
        $sevValue=($xml.'xml-report'.'issue-group'.item[$i].'attributes-group'.attribute | Where-Object{$_.name -eq 'Severity Value:'}).value.Replace('Use CVSS','Unknown');
    
    if($sevValue -eq "Unknown"){
      $unknownCounter++;
    }
    if($sevValue -eq "High"){
      $highCounter++;
    }
    if($sevValue -eq "Medium"){
      $medCounter++;
    }
    if($sevValue -eq "Low"){
      $lowCounter++;
    }
    if($sevValue -eq "Information"){
      $infoCounter++;
    }
      }
    }
  }
write-host "# Unknown Issues: $unknownCounter"
write-host "# High Issues: $highCounter"
write-host "# Medium Issues: $medCounter"
write-host "# Low Issues: $lowCounter"
write-host "# Information Issues: $infoCounter"
# Remove the last comma
# Back to root folderr
cd..