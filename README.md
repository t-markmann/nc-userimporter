# About nc-userimporter

This tool creates Nextcloud users from a CSV file, which you exported from some other software or created with a spreadsheet software.

Screenshot input:
![Screenshot from Windows commandline](https://github.com/t-markmann/nc-userimporter/blob/master/assets/screenshot.png)

## Instructions

1. Download and extract the zip-file
   * in the repository: click "code"--> "download zip"
   * OR: https://github.com/t-markmann/nc-userimporter/archive/refs/heads/main.zip

3. Insert data:
    * __config.xml__: Insert your cloud-admin credentials into file _config.xml_. The user must have admin permissions in your Nextcloud.
    * __users.csv__: Insert the user data into the file _users.csv_ or recreate it with the same columns in a spreadsheet software.

4. Start the tool:
    * __Windows__: doubleclick _nc-userimporter.exe_.
    * __Linux__ / __Mac__: install all dependencies (https://github.com/t-markmann/nc-userimporter/wiki#install-dependencies-for-running-py-script) and run: python3 nc-userimporter.py
    	* __Troubleshooting__: Make sure the file is executable (https://www.qwant.com/?q=make%20file%20executable%20linux / https://www.qwant.com/?q=make%20file%20executable%20mac)

5. Follow the interactive commandline instructions. Check output.log ("output"-folder in script-directory) and your user overview in Nextcloud.


## Output

Screenshot output:

![Generated PDF file with user credentials](https://github.com/t-markmann/nc-userimporter/blob/master/assets/screenshot_pdfoutput.png)

---

## ToDo

* improve documentation of features https://github.com/t-markmann/nc-userimporter/wiki#todo-documentation
* refactoring / clean code

Open features, not yet implemented (help appreciated): 
* read config from CLI-input if config-file is empty; update config.xml with input values?
* ask if users exists first: https://docs.nextcloud.com/server/15/admin_manual/configuration_user/instruction_set_for_users.html
* add other userdata
* delete users
