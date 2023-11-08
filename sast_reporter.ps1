


$aseToken = "C:\ProgramData\HCL\AppScanSource\config\ounceautod.token"
$aseAppName = "xxxx"
$compiledArtifactFolder = "none"
$scanConfig = "Normal scan"
$sevSecGw = "highIssues"
$maxIssuesAllowed = 100
$aseApiKeyId = "xxxx"
$aseApiKeySecret = "xxxx"
$aseHostname = "xxxx"

$sessionId=$(Invoke-WebRequest -Method "POST" -Headers @{"Accept"="application/json"} -ContentType 'application/json' -Body "{`"keyId`": `"$aseApiKeyId`",`"keySecret`": `"$aseApiKeySecret`"}" -Uri "https://$aseHostname`:9443/ase/api/keylogin/apikeylogin" -SkipCertificateCheck | Select-Object -Expand Content | ConvertFrom-Json | select -ExpandProperty sessionId);
# Get the aseAppId from ASE
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession;
$session.Cookies.Add((New-Object System.Net.Cookie("asc_session_id", "$sessionId", "/", "$aseHostname")));
$aseAppId=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/applications/search?searchTerm=$aseAppName" -SkipCertificateCheck | ConvertFrom-Json).id;
# Request report generation based on scanName and status New, Fixed, Reopened, InProgress, Open and Passed. Ignoring status Noise.
$reportId=$(Invoke-WebRequest -Method "POST" -WebSession $session -Headers @{"asc_xsrf_token"="$sessionId" ; "Accept"="application/json"} -ContentType "application/json" -Body "{`"config`":{`"executiveSummaryIncluded`":false,`"advisoriesIncluded`":true,`"issueConfig`":{`"issueAttributeConfig`":{`"showEmptyValues`":true,`"attributeLookups`":[`"applicationname`",`"cvss`",`"comments`",`"description`",`"id`",`"location`",`"overdue`",`"scanname`",`"scanner`",`"severityvalue`",`"status`",`"datecreated`",`"fixeddate`",`"lastupdated`",`"accesscomplexity`",`"accessvector`",`"authentication`",`"availabilityimpact`",`"confidentialityimpact`",`"exploitability`",`"integrityimpact`",`"remediationlevel`",`"reportconfidence`",`"api`",`"callingline`",`"callingmethod`",`"class`",`"classification`",`"databasename`",`"databaseservicename`",`"databasetype`",`"databaseversion`",`"discoverymethod`",`"domain`",`"element`",`"externalid`",`"host`",`"line`",`"package`",`"path`",`"port`",`"projectid`",`"projectname`",`"projectversion`",`"projectversionid`",`"scheme`",`"sourcefile`",`"third-partyid`",`"username`"]},`"includeAdditionalInfo`":false},`"pdfPageBreakOnIssue`":false,`"sortByURL`":false},`"layout`":{`"reportOptionLayoutCoverPage`":{`"companyLogo`":`"`",`"additionalLogo`":`"`",`"includeDate`":true,`"includeReportType`":false,`"reportTitle`":`"`",`"description`":`"`"},`"reportOptionLayoutBody`":{`"header`":`"`",`"footer`":`"`"},`"includeTableOfContents`":false},`"reportFileType`":`"XML`",`"issueIdsAndQueries`":[`"scanname`=$scanName,status`=New,status`=Fixed,status`=Reopened,status`=InProgress,status`=Open,status`=Passed`"]}" -Uri "https://$aseHostname`:9443/ase/api/issues/reports/securitydetails?appId=$aseAppId" -SkipCertificateCheck | Select-Object -Expand Content | Select-String -Pattern "Report id: (Report\d+)" | % {$_.Matches.Groups[1].Value});
write-host "$reportId"
# Check report status generation
$reportStatus=$((Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status" -SkipCertificateCheck).content | ConvertFrom-Json).reportJobState
write-host "$reportStatus"
# Wait report generation finished
#while ($reportStatusCode -ne 201){
#  $reportStatusCode=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status" -SkipCertificateCheck).statusCode
#  write-host "Report being generated"
#}
while ($reportStatusCode -ne 201){
  try{
    $reportStatusCode=$(Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri https://$aseHostname`:9443/ase/api/issues/reports/$reportId/status -SkipCertificateCheck).statusCode;
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
Invoke-WebRequest -WebSession $session -Headers @{"Asc_xsrf_token"="$sessionId"} -Uri "https://$aseHostname`:9443/ase/api/issues/reports/$reportId" -SkipCertificateCheck -OutFile scan_report.zip -PassThru | Out-Null;

write-host "The scan name $scanName was exported from Appscan Enterprise."