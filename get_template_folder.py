#!/usr/bin/env python3

from scans import *

server=ase()
server.setServer('https://ec2amaz-44nu39t/ase') #Set the url for the enterprise server, don't end with a / 
server.logIn("EC2AMAZ-44NU39T\\appscanadmin","w@tchf1re@ppscan") #Set the user name and password, and log in

#folderlist = server.getFoldersList()
#print(folderlist)

template_folder = server.getFolderItems('2')
print(template_folder)
