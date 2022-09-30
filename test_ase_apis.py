#!/usr/bin/python3

from ase_api import ASE
from scans import ase
import urllib3
import json
import time

urllib3.disable_warnings()




    
server=ase()
server.setServer('https://EC2AMAZ-44NU39T/ase/') #Set the url for the enterprise server, don't end with a / 
server.logIn('domain\user','pass') #Set the user name and password, and log in
issues=server.getIssuesList('1769')

print(str(issues))
#schema = server.getSchema()
#print(schema)
#issuecounts = server.getIssues('1769')
#print(issuecounts)
#folders=server.getFolderItemsList('1')
#print(folders)

# Returns 
#stats = server.getScanLogs('321')
#print(stats)
reportpack = server.getReportPack('322')
print(str(reportpack))
#getit = server.bigReport()
#print(str(getit))

#applications = asmServer.getAppList()
#print(applications)