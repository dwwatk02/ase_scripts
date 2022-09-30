#!/usr/bin/env python3
  
#!! IMPORTANT NOTES:  
#1) - After receiving a response from the server remove the first 3 characters from it. (It's gibberish and generates a lot of unwanted errors)   
#       In order to remove them use this [3:] after your response.text/r.text or whatever else you are using. This does not apply to element attributes that look like response[0].text/r[0].text  
  
#2) - In order to start using the enterprise you need to set the starting url and then log in with your credentials.   
  
#3) - LOG OUT when you finish working with enterprise with the endSessions method.   
  
#4) - For some unknown reason "{http://www.ibm.com/Rational/AppScanEnterprise}" is appended to every piece of information coming back from ASE  
  
import requests
from requests.exceptions import ConnectionError
import xml.etree.ElementTree as ET  
import sys  
import re
import json
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
preTag="{http://www.ibm.com/Rational/AppScanEnterprise}"

  
  
#Debug stuff  
def dump(obj):  
   for attr in dir(obj):  
       if hasattr( obj, attr ):  
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))  
  
             
class ase(object):  
  
   def __init__ (self):  
      self.session=requests.Session() #Create a session object. We need this session to keep us logged in. Don't forget to logout when you finish, (check the  endSession method)  
      self.headers = headers={'content-type': 'application/x-www-form-urlencoded'} #We need this header to specify the type of data we send to the enterprise server via out post method  
      self.sessionId = ''
      self.asmServer = ''
      self.connectionErrors = 0
      
   def errorCodeExists(self, code, response):
      return code in response
      
    #Define the instance of the ase server. Default should be https://localhost/ase (!!Note: there is no / after ase)  
   def setServer(self,server):    
      self.server=server  #The ase server url.

   def setAsmServer(self, server):
      self.asmServer = server
       
   def logIn(self,user,passwd):  
      data={'userid': 'EC2AMAZ-44NU39T\\appscanadmin', #User name for login to the AppScan Enterprise Server  
                  'password': 'd@tchf1re@ppscan', #password for the user name provided above  
                  'featurekey': 'AppScanEnterpriseUser'}  # special parameter requested by the AppScan Enterprise server   
                    
      #Login to the Enterprise server. Logout with endSession() method once you finished working with the server.
      retries = 0
      for retries in range(5):
         try:
            r=self.session.post( self.server+'/services/login', data=data, headers=self.headers, verify = False) #The url for login is https://<machineurl>/ase/services/login    
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      return r.text #return the complete response in html format.   
   
   def asmLogin(self, user, passwd):
      headers = {'Accept':'application/json','Content-Type':'application/json','Connection':'close'}
      data={'userId': user, #User name for login to the AppScan Enterprise Server  
                  'password': passwd, #password for the user name provided above  
                  'featureKey': 'AppScanEnterpriseUser'}  # special parameter requested by the AppScan Enterprise server    
      r = requests.post(self.asmServer+'/api/login', data=json.dumps(data), headers=headers, verify = False) #The url for login is https://<machineurl>/ase/services/login   
      return r.text #return the complete response in html format.
      
    #Return all the templates in the enterprise server in an xml message
   def getTemplates(self):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/templates',verify=False)  
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      return r.text[3:]  
      
    #Use this method to return a list of templates in the format : [ID] - [Name of Template]  
    #To address it use list[id] to get the template name  
   def getTemplatesList(self):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/templates',verify=False)     
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      
      #print r.text[3:]  
      root = ET.fromstring(r.text[3:]) #Convert the response into a tree element.   
      list={} #create an empty list  
      for template in root: #Go through every sub element of the main response. Each element represents a template  
         list[template[0].text]=template[1].text  #template[0] is the first attribute of the element, the id, [1] is the name  
         #print item  
      return list  
      
    #Method for running various tasks( A task can be a scan or a report pack).    
   def runTask(self,type,id,waitTime):  
   #Start a new job  
      jobId=id # if for task (report/scan)  
      data={'action':'2'} #The action 2 tells the enterprise server to start this task

      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+jobId,data=data,verify=False) #Post this action to the ase  
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
         
          
      #The next section will wait for a task to start running. This could take up to a couple of minutes  

      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folderitems/'+jobId,verify=False) #Get information about the task 
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      
        
      #print(r.text[3:])  
      root=ET.fromstring(r.text[3:])  
          
      runTime=0  
          
      test=root.findall(preTag+"state/"+preTag+"name")  #Check the state of the application . Method returns an array  
      #Note the pretag variable in the above method. When exploring the tree element, for some reason the {http://www.ibm.com/Rational/AppScanEnterprise} string is added in front of all the attributes.   
      state=test.pop().text #Get the state  
      # print state  
      print(type + " starting", end="", flush=True)
##      while state != 'Running':  #If the application is not yet running wait for  waitTime second then check again.   
##         print(".", end="", flush=True) 
##         time.sleep(waitTime)  
##         runTime+=waitTime
##
##         retries = 0
##         for retries in range(5):
##            try:
##               r=self.session.get(self.server+'/services/folderitems/'+jobId,verify=False)  #Get the task information  
##            except (Exception) as e:
##               self.connectionErrors += 1
##               time.sleep(2)
##               continue
##            break
##         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
##          
##         root=ET.fromstring(r.text[3:])  
##         test=root.findall(preTag+"state/"+preTag+"name")  #Get the state of the task (Method returns an array)   
##         state=test.pop().text  
##      print("Done")
      time.sleep(60)
      #End section responsible with waiting for the task to start  
      
      #The next section will wait for the task to finish. Section works just like the one that waits for the task to start.   
              
      runTime=0  
      print(type + " running", end="", flush=True)
      while state == 'Running':  
         print(".", end="", flush=True)
         time.sleep(waitTime)  
         runTime+=waitTime

         retries = 0
         for retries in range(5):
            try:
               r=self.session.get(self.server+'/services/folderitems/'+jobId,verify=False) 
            except (Exception) as e:
               self.connectionErrors += 1
               time.sleep(2)
               continue
            break
         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
         
         root=ET.fromstring(r.text[3:])  
         test=root.findall(preTag+"state/"+preTag+"name")  
         state=test.pop().text  
      print("Done")
      mins = int(runTime/60)
      print("Task Run Time: " + str(mins) + "m " + str(runTime-(mins*60)) + "s")
      return state  
      #print type+" ended with action:" + root[7][1].text  
      
   #Get information about a report pack. (Things contained are the reports contained, with name, id and some properties)  
   def getReportPack(self,id):  
      reportPack=id
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folderitems/'+reportPack+'/reports/',verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      response = r.text[3:]  
      return response

   def getReportPackList(self, id):
      response = self.getReportPack(id)
      root = ET.fromstring(response)
      list={} #create an empty list  
      for item in root:
         list[item[0].text]=item[1].text
      return list
      
    #Read executive summary about a specific report( Reports could be "OWASP top 10", "Security issues" and others). The reports contains name and number of high,medium,low,informational findings  
   def readReport(self,id):  
      reportId=id
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/reports/'+reportId,verify=False) 
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
         
      response=r.text[3:]  
      # print response  
      #root = ET.fromstring(response)  
      return response  

   def getIssuesList(self, reportId):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/reports/'+reportId+'/data',verify=False) 
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      response=r.text[3:]  
      root = ET.fromstring(response)
      
      list={} #Create an empty list  
      for item in root: #Cycle through all the items returned by the Enterprise server.  
         #for el in item:
            #print(str(el))
         list[item[2].text]=[item[0].text, item[8].text, item[4].text]  #Add the items to the list. The [0] attribute is the id, the [1] is the name and [2] is the type  

      return list

   def getIssueCount(self, reportId):
      issues = self.getIssuesList(reportId)
      
      issueCount = {}
      issueCount['Critical'] = 0
      issueCount['High'] = 0
      issueCount['Medium'] = 0
      issueCount['Low'] = 0
      issueCount['Information'] = 0
      
      for issue in issues:
         for iType in issueCount:
            if(iType == issues[issue][0]):
               issueCount[iType] += 1
      return issueCount
      
    #Get details about the issues contained in a report pack  
   def getIssues(self,id):  
      reportId=id

      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/reports/'+reportId+'/issues',verify=False) 
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      response=r.text[3:]  
      # print response  
      #root = ET.fromstring(response)  
      return response  
      
    #Change the starting URL for a scan. This only works when the login method is set to automatic.   
   def changeURL(self,scanId, newURL):  #1st parameter is the scan id, 2nd parameter is the new url  
      #Delete old url  
      data={'value':newURL}  
      #Before adding a new starting url we need to delete the first one, otherwise we'll end up with 2 or more starting urls. (Note the delete=1 at the end of the REST url)   

      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+scanId+'/options/epcsCOTListOfStartingUrls?delete=1',verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      #response=r.text[3:]  
      #After the previous url was deleted we can safely add a new starting url. This will be the new starting url for our scan.   

      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+scanId+'/options/epcsCOTListOfStartingUrls?put=1',data=data,verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      response=r.text[3:]  
      return response
   
   def bigReport(self): # default value is 'Automatic' login  
      data={'__EVENTTARGET=ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24ExportButton&__EVENTARGUMENT=&__VIEWSTATE=qKFiEJPVGqaFZsEXEUYY7YIBCkzt%2Bmko%2B5RgawXomD2%2BakUW1D%2BULYRm8Q6TrDlW%2BS%2BXyQs0bHPfbOf23NIHgBtZK0OwPrp7B4jtsBCy%2B3l4xUtP06w62YN62QjwpuKlCouMhqrQKji%2F9LeE0CNCycXtFsyzoo8aujei3u6wL0ajNcC0cszVWa7MwXcmfe0pj57N43U1bgaiRwHruSQp3H4oQJixgptx4gNME2yPvR8KdhzRSxHmVwF76aV1rdqhXIw4VQ4aIzRuy3ngaNGwZSdMi8RA4FFnbFd25kAPbzQ4014bTdY6HiNFj4PEFIIrEdekiRgxvdq3BTwBNpkHbQBzSxdKu%2FGfW97Caww2ltz2L1hQZ%2FMRLWqnqsVCI1Yd92K4s924OeFhzcGvUc%2FaXqfpa%2Fc3GbKS4WVIn1e5XjOsoWux%2FczWJhesWl8Uth9ACImyGwR%2F0TQ9uWY%2BXyGBMv3%2BJiSf%2FP%2FL8lUcVlpgtNuP%2FedE8hiWU3YfiV6eifbSdDFJrlbJDEbRlqOhoA%2FeXYnWVf%2BG5M90fcy8MiBUXDBat3B0mc%2B17Ml8MhmY54kdt2tST0E7YRd7AtFWqHT%2BvEUk69C7YfHks3MPJJhI1TbYhZaHKz0v6e6SUh%2FRSCNmiphtwuiQjwAMXAmPwgf8Bo%2Fdu5yRAD6if6DMsQruIxwHpHxt1TXIZ2E9y24yDxSkk1UhQMHvq2M%2Fxv2rfBhxnPiIyFHLrYiIuyERonc9Zq%2FcKbdHmc7XoE%2B0Jf5zYznYomrRDulPzX4Id1pB21aNsbrRP0RO48NqBHlt%2FHD%2BZvSJeflbu23naDD%2Fic65vXFemtdDWQOz3%2FqJ3dYSf%2Fimf3Ns2NxoNyhHPQOMvHAyKJoLggxPZcb7Pg0uZRk%2F9OVkq1KjYjcJ96F20iRv7fjf81%2FnUOXByTMWRxJu2yjiEJ6rOdVasNR%2B%2FCpmS1SHZPdgKMyWMv7uAlEDNhBBsD1errmrjdBmKc8PD9wmlFIDih7oeDj50%2BdCL%2FpKNJNEvrBXSfww1DgWS0mheb8PJlXjMRccIfdWzP4LYEsy0u8pSWANcw05UVMBc799KeIa8yWzylItMBnSPCSVWQGXFH12QnnL9LdhU2qjT4wtpRuUydgZiAVRE2NlXoMAHHa7K12RNqpnsmVtbbtBpW1NShAckv4OwniOotFcJ3p3L1VLft8dB9Jx8CSAFidvBdbEvBePZ28LCNkpAaIrwqOKazIJouuiKvbLUEWW%2F97fRFw6UpdmjSW%2BC%2BQ10HxX3MLlaDBuP%2FYFXqzafclJZBbfM7yBi4QWpH8WlCJepcgYUEaxHgcVvCaPhgmmjxEZzJMDdk7Uk%2FHNvMqRlmUDbfa1R8UuIBsc3zU5SY1DX9PxR0%2B278NwjGrI441rBO8%2FlHUYNYBLZT4rflxtxHmKSliV5HSNJAI0npOCNmD%2FVb7ZxsmB5eLg5K34F6B8Lo%2BHHwSmHxD4BJ%2B%2BlSNs01LUoKGzBWr8nrzE2qYuCVp2eHKORKLjz861jfnJor9xKUQZRifI1nZX%2BWQAYoT897sKGFt6G1nztT7TH1nw870%2F9VgFhxQ7l4wrx1zLSbCSCxdbgrV0VnXB4yWWMftGFrVxPsgjbY%2FoHyTBeAWIsssTdSKcbTCe6aYY8cutFif7OcSiXaNDO0hgiGQcatB0srtnracnaa233jjd%2BH4kBbWxU1kON%2B7aBKKOfldqPZeKoum8DFznva%2FckcfguMUSzqLkPcJqYl%2F9gegOLMTAIzwmvN4XqO%2FTmdecdeMTw7jX4LOwEEEYrfJqJhOHXATUoS%2F2P2BbpQN4GLV0HY73JMHsmDnQfocYZI6MRJ7WpLdPFGKTylwHZiXSx639KGbxXJz82ck9HS7kn0Y%2FvBX0AcqQsvxY8oCSW36NrgGizgERCuTNItYF9%2BUxlDXUI1pyGvIglP7ejDJ8PlAC5vWzn0xWdIiW%2BPo2YUNLbMLnXp0kAJT0d0BRJ9kY7LoQFI5IeA3S38HMzSk4Mzn%2B5CkBP2jIyuoDBo%2Fpm%2BRxpscIgXrSJOzDhMXe0Jkm648rP7HV6rSap7qotBktGY8w0PVJH1dqg9N%2FxE4pdKQUWlV0d9pkh9n6o6srNVYS3LEt3BmQg9IjEUIoj5a7%2FofhAQpaJlf9j2wpsEQjbOQk0R4ZDOjbHAUx5baKSiSxbQhEnKk2DZOkNQ76PTC494ty0%2FpQdWw%2FPFcmC1regnL7FHg08BInT4UNjGvIk%2BhvgtjVvqKRKKaX7cNxMCRQfFMqsozr%2F9%2FuHds5fZAZddXBuK2tl5YFKd8rBA8wfw31ZnDqYJ%2BOic93wi82o%2Fc%2FzImD0LMvDyfdDF5hiuEgqxjQLMO%2BOvAHCxwuPkvUC6Qv2oFfiLkRz80KTAz25cuRU5vAHWMzQJumBstW4a3S%2FrE8EGWBD%2BJwJ3WH8QxDmTOs5jMOAez9MUeeDwqFCo2KimNaekhzUMvDpV6vc26obP%2B23pG7cYmUg0Az7Q9rRUBg9dm1x4t95PPqMB6oSW90QxB2iDbxgCxYBPHXPwqLZjwqffZatRsc%2Bkl4bAkvz1cbmHkE0IbjpLdZALZrGu1%2FLUvMP5p%2FRxiATzpK4S4f0sJ7X9Sj9U9TZBPvU5Fp4b4x3CzLoATF6ojo3lLc1ztSY27LDCKetveiG0ELzn0CNHpK%2FYRIy%2BKvVfHV3pZtPoz4slLOO1r4JOwbRg0jFjW1JjSooccj8MBBL%2FkHCzZdfDDU7hetMF%2FRqQMKZGmwP60VAFtEXHEIu82Km1uIIgMXAkTMPawME4fHC7FQnF%2BTcri%2Fn3QKTLdyxsgNdZLpJyudw8LUCcxLf%2Bsauf8kPxZC7bmU4rSYUsPr221kIjc9PMktcgkNlleDkGsL7gcPaNizi%2F8ko1ePfYGWEsu0DqMoc6WnM%2BGnosvL32NiNpsYcBXvwyh%2F3b0OHrt2Jepa27JHhSQyHeCD3aq1vFmTO5uyGVaVyfV5qmGHTV548f6PBYqPG7aDNnjuoi4o2KTV9JE9xetYHfJIrncc9g4DPLxQ63ebl8wDxyOwJt1ydPPKRZisXduBQ1aNsBND%2BbflSjkz4PV%2BJX5kOBjQ5E2mC0bKkA9rvZYXwbbfs2U5qC54vCXgSQN171BfRJiA5Zo1WqWTs3Vnzv0bzAb2hzeX%2BQyRmmMcASzCi21U%2Bg9t1sYSRZdN2T3Uzn8x1dZOXYf7gZLyMngdJzoo5CQnVWVPR8ouL08xaHs2FnixdZH3A1Grj1qjpB%2BHwPl1B1eOvilmDwj%2FIPOvh3duTRh6pZbe%2FESLSXifGQ2Meg1dBG2f4Db%2B0nVCeaFLUDnmjisM9YZsHMTcEm19AbWybXBuVgidt72bUG8Hvp6yU4T121zqztvqUMHzj8GuLVkibWhFBK8EOD1GaNI6L7tZ%2FrI7RAf%2B1mv%2FzL70yUPBUfhii7bIJXe0G1YJEZ8UugzUTh5XRvii1EOZgJ7NGpOm7WIjCmYb%2Fa%2FSsMTlFLRUujbhsjF28R9UlwMyiUM5Sh09nCtxX1VUQkhbTi8op1doDP8ZjIby9vEPybMRq8RZnX5GwfrnJvTy1MM3vNWaMTrgQY%2BCdBuW9HSucBjWzThMcdfY0LNeBKSI4%2BsA2x9hHx2czk%2Fj4bmnSe0VYpGCaaGWWL4Gy7jw899S18AixRGoOvvyIKECgqG%2BTOLhlaeRK%2BNd99IeouKff44o%2FEzf12gcXqulTaVQrNU%2Fc59KKJRWG7VHVxv4aT8%2Boafvq7R4M%2Ba%2BViuXpibM1xkAzoB0lW9dBIHwUrXRg32O8N5%2B1NXd%2B5l0xiI9IdV2eVUHEzWxjzMlIlKgKVA%2BXkiwivWIp4En7Jf%2BMNdwZ2ROIZKur2%2BHBQ9N2nNjYWHdbJdHsRPZfby11xw1pRyYkigEhRHWRWa9w88ecGOy09l208ncliEc2sohqAI%2FkBgA7ZgMLZnG5mLDPP%2F3GLJJGaZCq3XV&__VIEWSTATEGENERATOR=954EC34A&ctl00%24ScrollerLeft=0&ctl00%24ScrollerTop=0&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24SummaryCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24TOCCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24VariantsCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24RequestResponseCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24LimitVarintsCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24MaxVariantsTextBox=3&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24AdvisoriesCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24RemediationCheckBox=on&ctl00%24ContentPanePlaceHolder%24PDFExportSettingsControl%24UserCommentsCheckBox=on'}  
      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/Reports/PDFSettings.aspx?fiid=322&fid=1&rid=1769&viewid=8&exportformat=pdfdetailed&exportdelivery=download',data=data,verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      response=r.text  
      return response  
    #Change login credentials. These credentials work with automatic login method.
   def changeLoginType(self,scanId, loginType = '3'): # default value is 'Automatic' login  
      data={'value':loginType}  
      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+scanId+'/options/elCOTLoginSequenceType',data=data,verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")

      response=r.text[3:]  
      return response  
   def changeCredentials(self,scanId,username,password):  
      #Change username  
      data={'value':username}   
      #Set a new username

      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+scanId+'/options/esCOTAutoFormFillUserNameValue',data=data,verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
          
      response=r.text[3:]  
      #Change Password  
      data={'value':password}  
      #Set a new password
      retries = 0
      for retries in range(5):
         try:
            r=self.session.post(self.server+'/services/folderitems/'+scanId+'/options/esCOTAutoFormFillPasswordValue',data=data,verify=False)
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      
      response=response+r.text[3:]  
      return response  
      
    #Create a scan based on an existing template. Templates can be retrieved with the getTemplates/getTemplatesList method.
    #Added AppID Parameter
   def createScan(self,name,description,templateid,folderId='0', appId = '0'):  
      data={'name':name, #Name for the new scan  
            'description':description} #Description for the new scan   
      if(folderId=='0'):
         retries = 0
         for retries in range(5):
            try:
               r=self.session.post(self.server+'/services/folderitems?templateid='+templateid+'&appid='+appId,data=data,headers=self.headers,verify=False) #to create in root folder 
            except (Exception) as e:
               self.connectionErrors += 1
               time.sleep(2)
               continue
            break
         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")  
      else:
         retries = 0
         for retries in range(5):
            try:
               r=self.session.post(self.server+'/services/folders/'+folderId+'/folderitems?templateid='+templateid+'&appid='+appId,data=data,headers=self.headers,verify=False)  #to create in specific folder
            except (Exception) as e:
               self.connectionErrors += 1
               time.sleep(2)
               continue
            break
         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")   
      response = r.text[3:]  
          
      #For more information see documentation :  
      # http://www-01.ibm.com/support/knowledgecenter/SSW2NF_9.0.1/com.ibm.ase.help.doc/topics/t_create_job_based_templates.html?lang=en  
          
      return response  
      
    #This method does not interact with the Enterprise server.  
    #It takes the results from the getReportPack and searches for a specific Report pack in there. The it will return the pack if for that report.   
    #Blank is there to capture one of the objects encapsulated in the response sent back by the getReportPack method.   
   def getReportId(blank,reportsET,reportName):  
      reports=ET.fromstring(reportsET)  
      for i in range(11):  
         if reports[i][1].text==reportName: #There are 12 reports generated by default. From 0 to 11. If there are more or less please adjust the range  
            reportId=reports[i][0].text  #Select the repost for OWASP Top 10   
            break  
         #To see a full list of the reports open the report pack in either enterprise or via the rest API  
      return reportId  
      
    #Get the folders from a parent folder. If no parent is specified extract all the folders in the root one.  
    #The message returned is in xml format  
   def getFolders(self,parentFolder='-1'):  
      if(parentFolder=='-1'):
         retries = 0
         for retries in range(5):
            try:
               r=self.session.get(self.server+'/services/folders',verify=False)  #Get information about the root directory
            except (Exception) as e:
               self.connectionErrors += 1
               time.sleep(2)
               continue
            break
         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
            
         root=ET.fromstring(r.text[3:]) #Convert the response into an element tree  
         parentFolder=root[0].text #Get the id of the root directory and convert it to string
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folders/'+parentFolder+'/folders/',verify=False) #Use the previously obtained id to list all the folders.
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
        
      return r.text[3:] #Return the response as a string.  
  
    #Get a list of  folders from a parent folder. If no parent is specified extract all the folders from the root one.   
    #The list returned is of type [id] - [Name]  
   def getFoldersList(self,parentFolder='-1'):
      list={} #create an empty list 
      if(parentFolder=='-1'):
         retries = 0
         for retries in range(5):
            try:
               r=self.session.get(self.server+'/services/folders',verify=False)  #Get information about the root directory
               #r=self.session.get(self.server+'/services/schema',verify=False)  #Get information about the root directory
            except (Exception) as e:
               self.connectionErrors += 1
               time.sleep(2)
               continue
            break
         if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
         root=ET.fromstring(r.text[3:]) #Convert the response into an element tree  
         parentFolder=root[0].text #Get the id of the root directory and convert it to string
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folders/'+parentFolder+'/folders/',verify=False) #Use the previously obtained id to list all the folders.
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
        
      if(self.errorCodeExists('CRWAE2439E', r.text[3:])): #folder not found error check
         return list
      root=ET.fromstring(r.text[3:]) #Convert the response into an element tree   
      for folder in root: #Cycle through every sub-element in the main element. Each sub-element is a folder.  
         list[folder[0].text]=folder[1].text # The first attribute [0] is the id while [1] is the name  
      return list

           
   def getAllFoldersList(self, parentFolder='-1'):
      folders = self.getFoldersList(parentFolder)
      masterList = {}
      for f in folders:
         masterList[f] = folders[f]
         temp = self.getAllFoldersList(f)
         for item in temp:
            masterList[item] = temp[item]
      return masterList
      
   def findFolderByName(self, folderName):
      folderList = self.getAllFoldersList()
      for folder in folderList:
         if(folderList[folder] == folderName):
            return folder
      return -1
       
    #Return information about a folder in an xml format.   
   def getFolderInfo(self,folderId):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folders/'+folderId,verify=False)   
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      
      return r.text[3:] #Convert the response into an element tree  
      
    #Get all the items in a folder. The items could be scans, report packs, dashboards or imported jobs.  
    #The result will be in XML format  
    #This returns the items in the subFolders if the subFolders parameter is set to 1  
   def getFolderItems(self,folderId,subFolders='0'):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folders/'+folderId+'/folderitems?flatten='+subFolders,verify=False)  #Get the content of the folder    
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      return r.text[3:] #Return the response in string format
   def getScanLogs(self,folderId):
        retries = 0
        for retries in range(5):
            try:
                r=self.session.get(self.server+'/services/folderitems/'+folderId+'/statistics',verify=False)  #Get the content of the folder    
            except (Exception) as e:
                self.connectionErrors += 1
                time.sleep(2)
                continue
            break
        if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
        return r.text #Return the response in string format  
      
    #Get all the items in a folder. The items could be scans, report packs, dashboards or imported jobs.  
    #The result will be in a list format. Type will be list[id] - [name][type]   
    #To address the values use list[id][0] - for name, and list[id][1] for type  
    #This returns the items in the subFolders if the subFolders parameter is set to 1  
   def getFolderItemsList(self,folderId,subFolders='0'):
      retries = 0
      for retries in range(5):
         try:
            r=self.session.get(self.server+'/services/folders/'+folderId+'/folderitems?flatten='+subFolders,verify=False)  #Get the content of the folder      
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      #root=ET.fromstring(r.text[3:])  
      list={} #Create an empty list  
      #for item in root: #Cycle through all the items returned by the Enterprise server.  
         #list[item[0].text]=[item[1].text, item.tag[47:]]  #Add the items to the list. The [0] attribute is the id, the [1] is the name and [2] is the type  
          
      return r.text  
    
    #Get information about an app in the ASM  
   def getAppInfo(self,id):
      retries = 0
      for retries in range(5):
         try:
            r = self.session.get(self.server+'api/applications/'+id,verify=False)#get information about the application     
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")  
      #root = ET.fromstring(r)  
      return r
      
   def getAppList(self):
        additionalHeaders = { 
            "Content-Type": "application/json",
            "Range":"items=0-99"
        }
        self.session.headers.update(additionalHeaders)
        r = self.session.get(self.asmServer+'api/applications?columns=name%2Cid',headers=self.session.headers,verify=False)
        print(r.text)
       
   def getSchema(self):
      retries = 0
      for retries in range(5):
         try:
            r = self.session.get(self.server+'/services/schema',verify=False)#get information about the application    
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      return r.text
      
    #Upload and replace Manual Explore Data in Scan Job
   def uploadHTD(self, htdPath, folderItemId):
      #/services/folderitems/<fiid./httptrafficdata?includeformfills=1
      htdData = open(htdPath, 'rb').read()
      retries = 0
      for retries in range(5):
         try:
            r = self.session.post(url=self.server+'/services/folderitems/'+folderItemId+'/httptrafficdata?includeformfills=1&delete=1', data=htdData, headers={'Content-Type': 'application/octet-stream'})     
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      response = r.text[3:]  
      return response

    #Verify Folder Item Exists, Return Folder Item ID if found, 0 otherwise
    #itemType [0 = content scan job, 1 = report pack, 2 = import job]
   def verifyFolderItemExists(self, fiName, folderId, itemType = 0):
      itemTypeStr = 'Unknown'
      if(itemType == 0):
         itemTypeStr = 'content-scan-job'
      if(itemType == 1):
         itemTypeStr = 'report-pack'
      if(itemType == 2):
         itemTypeStr = 'import-job'
      
      folderItems = self.getFolderItemsList(folderId, '0')
      for fi in folderItems:
         #print('Current folder item: '+ fi + " Current folder item name: " + folderItems[fi][0])
         if(folderItems[fi][0] == fiName and folderItems[fi][1] == itemTypeStr):
            return fi
      return 0
            
    #Log out from enterprise and end the session. PLEASE LOG OUT  
   def endSession(self):
      retries = 0
      for retries in range(5):
         try:
            r = self.session.get(self.server+'/services/logout',verify=False)     
         except (Exception) as e:
            self.connectionErrors += 1
            time.sleep(2)
            continue
         break
      if(retries >= 4): sys.exit("Cannot communitcate with ASE, Max retries attempted")
      return r.text  
