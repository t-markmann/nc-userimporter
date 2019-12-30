import os
import sys
import time
import requests
import certifi
import csv
import string
import qrcode
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
config_school = config_xmlsoup.find('school').string
config_schoolgroup = config_xmlsoup.find('schoolgroup').string

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
config_apiUrlGroups = "/ocs/v1.php/cloud/groups" # nextcloud API path (groups), might change in the future

# Headers for CURL request, Nextcloud specific
requestheaders = {
  'OCS-APIRequest': 'true',
}

# Mapping for umlauts and and special characters. The listed umlauts and special characters are automatically converted to a compatible spelling for the user name.
mapping = {
           ord(u"Ä"): u"Ae",
           ord(u"ä"): u"ae",
           ord(u"Ë"): u"E",
           ord(u"ë"): u"e",
           ord(u"Ï"): u"I",
           ord(u"ï"): u"i",
           ord(u"Ö"): u"Oe",
           ord(u"ö"): u"oe",           
           ord(u"Ü"): u"Ue",
           ord(u"ü"): u"ue",
           ord(u"Ÿ"): u"Y",
           ord(u"ÿ"): u"y",
           ord(u"ß"): u"ss",
           ord(u"À"): u"A",
           ord(u"Á"): u"A",
           ord(u"Â"): u"A",
           ord(u"Ã"): u"A",
           ord(u"Å"): u"A",
           ord(u"Æ"): u"Ae",
           ord(u"Ç"): u"C",
           ord(u"È"): u"E",
           ord(u"É"): u"E",
           ord(u"Ê"): u"E",
           ord(u"Ì"): u"I",
           ord(u"Í"): u"I",
           ord(u"Î"): u"I",
           ord(u"Ð"): u"D",
           ord(u"Ñ"): u"N",
           ord(u"Ò"): u"O",
           ord(u"Ó"): u"O",
           ord(u"Ô"): u"O",
           ord(u"Õ"): u"O",
           ord(u"Ø"): u"Oe",
           ord(u"Œ"): u"Oe",
           ord(u"Ù"): u"U",
           ord(u"Ú"): u"U",
           ord(u"Û"): u"U",
           ord(u"Ý"): u"Y",
           ord(u"Þ"): u"Th",
           ord(u"à"): u"a",
           ord(u"á"): u"a",
           ord(u"â"): u"a",
           ord(u"ã"): u"a",
           ord(u"å"): u"a",
           ord(u"æ"): u"ae",
           ord(u"ç"): u"c",
           ord(u"è"): u"e",
           ord(u"é"): u"e",
           ord(u"ê"): u"e",
           ord(u"ì"): u"i",
           ord(u"í"): u"i",
           ord(u"î"): u"i",
           ord(u"ð"): u"d",
           ord(u"ñ"): u"n",
           ord(u"ò"): u"o",
           ord(u"ó"): u"o",
           ord(u"ô"): u"o",
           ord(u"õ"): u"o",
           ord(u"ø"): u"oe",
           ord(u"œ"): u"oe",
           ord(u"ù"): u"u",
           ord(u"ú"): u"u",
           ord(u"û"): u"u",
           ord(u"ý"): u"y",
           ord(u"þ"): u"Th",
           ord(u"Š"): u"S",
           ord(u"š"): u"s",
           ord(u"Č"): u"C",
           ord(u"č"): u"c"
           }

# QR-Code class
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

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
    line = row[0]
    row[0] = line.translate(mapping) # convert special characters and umlauts
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
    line = row[0]
    row[0] = line.translate(mapping) # convert special characters and umlauts    
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
          # if variable 'school' = yes, remove value 'SchuelerInnen' and 'Lehrkraefte' from groups
      if config_school == 'yes':
        if grouplist:
          if "SchuelerInnen" in grouplist:
            grouplist.remove('SchuelerInnen')
          if "Lehrkraefte" in grouplist:
            grouplist.remove('Lehrkraefte')
        # add usergroup which is set in config-file (config_schoolgroup)
          grouplist.append(config_schoolgroup)
    else:
      grouplist = []
      grouplist.append(config_schoolgroup)
      # TODO: Check if groups exists, if not: create groups
      # https://docs.nextcloud.com/server/13.0.0/admin_manual/configuration_user/instruction_set_for_groups.html

    for group in grouplist: 
     data.append(('groups[]', group.strip())) # groups is parameter NC API

    # if value exists: append group admin values to data array/list for CURL
    if not config_schoolgroup == 'SchuelerInnen':
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

    # A QR code and a PDF file are only generated if the user has been successfully created.
    if response_xmlsoup.find('statuscode').string == "100":
      # generate qr-code
      qr.add_data("nc://login/user:" + row[0] + "&password:" + row[2] + "&server:https://" + config_ncUrl)
      img = qr.make_image(fill_color="black", back_color="white")
      img.save(row[0] + ".jpg")
      qr.clear()

      # generate pdf
      doc = SimpleDocTemplate(row[0] + ".pdf",pagesize=letter,
                              rightMargin=72,leftMargin=72,
                              topMargin=72,bottomMargin=18)
      Story=[]
      nclogo = "Nextcloud_Logo.jpg" # nextcloud-logo
      ncusername = row[1] # username
      ncpassword = row[2] # password
      nclink = config_protocol + "://" + config_ncUrl # adds nextcloud-url
        # adds nextcloud-logo to pdf-file 
      im = Image(nclogo, 150, 106)
      Story.append(im)
      Story.append(Spacer(1, 12))

      styles=getSampleStyleSheet()
      styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        # adds text to pdf-file
      ptext = '<font size=14>Hello %s,</font>' % ncusername
      Story.append(Paragraph(ptext, styles["Justify"]))
      Story.append(Spacer(1, 12))

      ptext = '<font size=14>a Nextcloud-account has been generated for you.</font>'
      Story.append(Paragraph(ptext, styles["Justify"]))
      Story.append(Spacer(1, 12))    

      ptext = '<font size=14>You can login with the following user data:</font>'
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 36))

      ptext = '<font size=14>Link to your Nextcloud:</font>'
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 12))    

      ptext = '<font size=14>%s</font>' % nclink
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 24))

      ptext = '<font size=14>Username:</font>'
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 12))    

      ptext = '<font size=14>%s</font>' % ncusername
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 24))

      ptext = '<font size=14>Password:</font>'
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 12))    

      ptext = '<font size=14>%s</font>' % ncpassword
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 24))

      ptext = '<font size=14>Alternatively, you can scan the following QR-Code in the Nextcloud app:</font>'
      Story.append(Paragraph(ptext, styles["Normal"]))
      Story.append(Spacer(1, 24))       
        # adds qr-code to pdf-file
      im2 = Image(row[0] + ".jpg", 200, 200)
      Story.append(im2)
        # create pdf-file
      doc.build(Story)

      # TODO:
      # delete temporary qr-code-file
      #os.remove(row[0] + ".jpg")     
      #save pdf-file in subfolder
    
print("\nControl the status codes of the user creation above or in the output.log.")
print("You should as well see the users in your Nextcloud now.")
print("PDF-Files with login-info and qr-code has been generated for every user.")
print("For security reasons: please delete your credentials from config.xml")
input("Press [ANY KEY] to confirm and end the process.")
