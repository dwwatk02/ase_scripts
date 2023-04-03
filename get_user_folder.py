#!/usr/bin/env python3

from scans import *

server=ase()
server.setServer('https://ec2amaz-44nu39t/ase') #Set the url for the enterprise server, don't end with a / 
server.logIn("EC2AMAZ-44NU39T\\appscanadmin","w@tchf1re@ppscan") #Set the user name and password, and log in

#folderlist = server.getFolderInfo('4')
#print(folderlist)

user_folder = server.getFolderItems('4')
print(user_folder)
