#!/usr/bin/python3

from scans import ase
import urllib3
import json
import time

urllib3.disable_warnings()

#API Key
keyId="yourid"
keySecret="yourkey"


    
server=ase()
server.setServer('https://<yourserver>/ase') #Set the url for the enterprise server, don't end with a / 
server.logIn('domain\\username','password') #Set the user name and password, and log in
#issues=server.getIssuesList('1769')
#print(str(issues))
#issuecounts = server.getIssueCount('1769')
#print(issuecounts)
logs = server.getScanLogs('321')
print(logs)