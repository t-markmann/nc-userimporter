import os
import sys
import time
import requests
import certifi
import csv
import string
from tabulate import tabulate
from bs4 import BeautifulSoup

# This tool creates Nextcloud users from a CSV file, which you exported from some other software.

# Copyright (C) 2019 Torsten Markmann
# Mail: info@uplinked.net 
# WWW: edudocs.org uplinked.net

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

print("")
print("NC USER IMPORTER Copyright (C) 2019 Torsten Markmann, edudocs.org & uplinked.net")
print("This program comes with ABSOLUTELY NO WARRANTY")
print("This is free software, and you are welcome to redistribute it under certain conditions.")
print("For details look into LICENSE file (GNU GPLv3).")
print("")

# Useful resources for contributors:
# Nextcloud user API https://docs.nextcloud.com/server/15/admin_manual/configuration_user/instruction_set_for_users.html
# CURL to Python request converter https://curl.trillworks.com/

# determine if running in a build package (frozen) or from seperate python script
frozen = 'not'
if getattr(sys, 'frozen', False):
  # we are running in a bundle
  appdir = os.path.dirname(os.path.abspath(sys.executable))
  ## print("Executable is in frozen state, appdir set to: " + appdir) # for debug
else:
  # we are running in a normal Python environment
  appdir = os.path.dirname(os.path.abspath(__file__))
  ## print("Executable is run in normal Python environment, appdir set to: " + appdir) # for debug

# read config from xml file
configfile = open(os.path.join(appdir,'config.xml'),mode='r')
config = configfile.read()
configfile.close()

# load config values into variables
config_xmlsoup = BeautifulSoup(config, "html.parser") # parse
config_ncUrl = config_xmlsoup.find('cloudurl').string
config_adminname = config_xmlsoup.find('adminname').string
config_adminpass = config_xmlsoup.find('adminpass').string
config_csvDelimiter = config_xmlsoup.find('csvdelimiter').string
config_csvDelimiterGroups = config_xmlsoup.find('csvdelimitergroups').string

# cut http and https from ncUrl, because people often just copy & paste including protocol
config_ncUrl = config_ncUrl.replace("http://", "")
config_ncUrl = config_ncUrl.replace("https://", "")

# TODO optional: read config from input() if config.xml empty
# print('Username of creator (admin?):') 
# config_adminname = input()
# print('Password of creator:')
# config_adminpass = input()

config_protocol = "https" # use a secure connection!
config_apiUrl = "/ocs/v1.php/cloud/users" # nextcloud API path, might change in the future

# Headers for CURL request, Nextcloud specific
requestheaders = {
  'OCS-APIRequest': 'true',
}

# display expected results before executing CURL
usertable = [["Username","Display name","Password","Email","Groups","Group admin for","Quota"]]
with open(os.path.join(appdir,'users.csv'),mode='r') as csvfile:
  readCSV = csv.reader(csvfile, delimiter=config_csvDelimiter)
  next(readCSV, None)  # skip the headers
  for row in readCSV:
    if (len(row) != 7): # check if number of columns is consistent
      print("ERROR: row for user",row[0],"has",len(row),"columns. Should be 7. Please correct your users.csv")
      input("Press [ANY KEY] to confirm and end the process.")
      sys.exit(1)
    pass_anon = row[2]
    if len(pass_anon) > 0:
      pass_anon = pass_anon[0] + "*" * (len(pass_anon)-1) # replace password for display on CLI
    currentuser = [row[0],row[1],pass_anon,row[3],row[4],row[5],row[6]]
    usertable.append(currentuser)
print(tabulate(usertable,headers="firstrow"))

# ask user to check values and continue
print("\nPlease check if the users above are as expected and should be created like that.")
input("If yes, press [ANY KEY] to continue. If not, press [CONTROL + C] to cancel.")
print("\nYou confirmed. I will now create the users. This can take a long time...\n")

# read rows from CSV file
with open(os.path.join(appdir,'users.csv'),mode='r') as csvfile:
  readCSV = csv.reader(csvfile, delimiter=config_csvDelimiter)
  next(readCSV, None)  # skip the headers
  for row in readCSV:
    print("Username:",row[0],"| Display name:",row[1],"| Password: ","*" * len(row[2]) + 
    "| Email:",row[3],"| Groups:",row[4],"| Group admin for:",row[5],"| Quota:",row[6],)

    # build the dataset for the request
    data = [
      ('userid', row[0]),
      ('displayName', row[1]), 
      ('password', row[2]),
      ('email', row[3]),
      ('quota', row[6])
    ]

    # if value exists: append single groups to data array/list for CURL
    if row[4]:
      grouplist = row[4].split(config_csvDelimiterGroups) # Groups in the CSV-file are split by semicolon --> load into list
      for group in grouplist: 
        data.append(('groups[]', group.strip())) # groups is parameter NC API

    # if value exists: append group admin values to data array/list for CURL
    if row[5]:
      groupadminlist = row[5].split(config_csvDelimiterGroups) # Groupadmin Values in the CSV-file are split by semicolon --> load into list
      for groupadmin in groupadminlist: 
        data.append(('subadmin[]', groupadmin.strip())) # subadmin is parameter NC API
    
    # perform the request
    try:
      response = requests.post(config_protocol + '://' + config_adminname + ':' + config_adminpass + '@' + 
        config_ncUrl + config_apiUrl, headers=requestheaders, data=data)
    except requests.exceptions.RequestException as e:  # handling errors
      print(e)
      print("The CURL request could not be performed.")
      input("Press [ANY KEY] to confirm and end the process.")
      sys.exit(1)

    # catch wrong config
    if response.status_code != 200:
      print("HTTP Status: " + str(response.status_code))
      print("Your config.xml is wrong or your cloud is not reachable.")
      input("Press [ANY KEY] to confirm and end the process.")
      sys.exit(1)

    # show detailed info of response
    response_xmlsoup = BeautifulSoup(response.text, "html.parser")
    print(response_xmlsoup.find('status').string + ' ' + response_xmlsoup.find('statuscode').string + 
      ' = ' + response_xmlsoup.find('message').string)

    # append detailed response to logfile
    logfile = open(os.path.join(appdir,'output.log'),mode='a')
    logfile.write("\nUSER: " + row[0] + "\nTIME: " + time.strftime("%d.%m.%Y %H:%M:%S",time.localtime(time.time())) + 
      "\nRESPONSE: " + response_xmlsoup.find('status').string + ' ' + response_xmlsoup.find('statuscode').string + 
      ' = ' + response_xmlsoup.find('message').string + "\n")
    logfile.close()

print("\nControl the status codes of the user creation above or in the output.log.")
print("You should as well see the users in your Nextcloud now.")
print("For security reasons: please delete your credentials from config.xml")
input("Press [ANY KEY] to confirm and end the process.")
