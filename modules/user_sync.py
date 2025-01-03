import logging
from lxml import etree
from tabulate import tabulate
from modules.mapping import MAPPING  # Import the mapping for special characters

class NextcloudUserManager:
    """
    Manages Nextcloud users by comparing CSV user data with Nextcloud's current user list 
    and applying changes such as adding, updating, or deleting users.
    """
    
    # Constructor and Helper Methods
    
    
    def __init__(self, api_instance, lang):
        """
        Initialize the class with an instance of NextcloudAPI and language handler.

        Args:
            api_instance (NextcloudAPI): An instance of the Nextcloud API handler.
            lang (dict): Language dictionary for translation strings.
        """
        self.api = api_instance
        self.lang = lang
        
    def apply_mapping(self, text):
        """
        Apply the special character and umlaut mapping to a given text.

        Args:
            text (str): The text to which the mapping should be applied.

        Returns:
            str: The text after applying the character mapping.
        """
        return text.translate(MAPPING) 
    
    
    # CSV Loading and User Data Preparation        


    def load_csv_users(self, csv_users):
        """
        Apply character mapping to the usernames in the given CSV user data and handle empty display names.
        
        Args:
            csv_users (list): A list of dictionaries representing CSV user data.

        Returns:
            list: The modified list of CSV user dictionaries with mapped usernames and filled display names.
        """
        # Apply mapping to usernames in the CSV and handle empty display names
        for user in csv_users:
            if not user.get('username'):
                logging.error(f"Missing or empty 'username' field for user: {user}")
            else:
                user['username_mapped'] = self.apply_mapping(user['username'])
            
            # Fill displayname with username if displayname is empty
            if not user.get('displayname'):
                logging.info(f"Displayname for user '{user['username']}' is empty. Using username as displayname.")
                user['displayname'] = user['username_mapped']
        
        return csv_users



    # CSV -> Nextcloud User Synchronization
 
 
    def check_for_modified_users(self, csv_users, nextcloud_users):
        nextcloud_user_dict = {user['id']: user for user in nextcloud_users}

        for csv_user in csv_users:
            username_mapped = csv_user['username_mapped'] 
            if username_mapped in nextcloud_user_dict:
                nextcloud_user = nextcloud_user_dict[username_mapped]
                changes = self.detect_changes(csv_user, nextcloud_user)
                if changes:
                    if self.compare_and_display_changes(csv_user, nextcloud_user):
                        self.apply_changes_to_user(username_mapped, changes)
    
    def compare_and_sync_users(self, csv_users):
        response = self.api.get_users()
        if not self.api.is_successful(response):
            logging.error("Failed to fetch Nextcloud users.")
            return

        nextcloud_users = self.api.parse_users_from_response(response['response'])

        for user in nextcloud_users:
            self.fetch_and_populate_user_details(user)

        # Perform comparison and sync operations
        self.check_for_deleted_users(csv_users, nextcloud_users)
        self.check_for_modified_users(csv_users, nextcloud_users)   
    
    def fetch_and_populate_user_details(self, nextcloud_user):
        try:
            response = self.api.get_user(nextcloud_user['id'])
            if self.api.is_successful(response):
                self.populate_user_details(nextcloud_user, response['response'])
            else:
                logging.error(f"Failed to fetch details for user '{nextcloud_user['id']}'.")
        except Exception as e:
            logging.error(f"Error fetching details for user '{nextcloud_user['id']}': {e}")   
    
    def populate_user_details(self, nextcloud_user, response):
        """
        Populate display name, email, groups, and subadmin groups for a Nextcloud user.

        Args:
            nextcloud_user (dict): The user dictionary to be populated.
            response (requests.Response): The API response containing user details.
        """
        root = etree.fromstring(response.content)
        logging.debug(f"Full API response for user {nextcloud_user['id']}: {etree.tostring(root, pretty_print=True).decode('utf-8')}")

        nextcloud_user['displayname'] = self.api.get_xml_value(root, ".//displayname", '')
        nextcloud_user['email'] = self.api.get_xml_value(root, ".//email", '')
        nextcloud_user['groups'] = self.api.get_user_groups(nextcloud_user['id'])
        nextcloud_user['subadmin'] = self.api.get_user_subadmin_groups(nextcloud_user['id'])
        
                
    # Modification Management  
    
    
    def detect_changes(self, csv_user, nextcloud_user):
        """
        Detect changes between CSV user and Nextcloud user.

        Args:
            csv_user (dict): A user from the CSV file.
            nextcloud_user (dict): A user from Nextcloud.

        Returns:
            dict: A dictionary of changes to be applied, or an empty dictionary if no changes are detected.
        """
        changes = {}

        # Email comparison
        csv_email = csv_user['email'].strip().lower()
        nextcloud_email = nextcloud_user.get('email', '').strip().lower()
        if csv_email != nextcloud_email:
            changes['email'] = csv_email

        # Displayname comparison and fallback to username if empty
        csv_displayname = csv_user['displayname'].strip()
        #if not csv_displayname:  # If displayname is empty, use the username
        #    csv_displayname = csv_user['username_mapped']
        nextcloud_displayname = nextcloud_user.get('displayname', '').strip()
        if csv_displayname != nextcloud_displayname:
            changes['displayname'] = csv_displayname

        # Groups comparison
        csv_groups = set(group.strip() for group in csv_user['groups'].split(',') if group.strip())
        nextcloud_groups = set(group.strip() for group in nextcloud_user['groups'])
        if csv_groups != nextcloud_groups:
            changes['groups'] = csv_groups

        # Subadmin groups comparison
        csv_subadmin = set(group.strip() for group in csv_user['subadmin'].split(',') if group.strip())
        nextcloud_subadmin = set(group.strip() for group in nextcloud_user.get('subadmin', []))
        if csv_subadmin != nextcloud_subadmin:
            changes['subadmin'] = csv_subadmin

        return changes


    def compare_and_display_changes(self, csv_user, nextcloud_user):
        """
        Display a table comparing the CSV user and the Nextcloud user for potential changes.

        Args:
            csv_user (dict): The user data from the CSV file.
            nextcloud_user (dict): The user data fetched from Nextcloud.
        """
        csv_email = csv_user['email'].strip() if csv_user['email'].strip() else ''
        nextcloud_email = nextcloud_user.get('email', '').strip()

        table_data = [
            [self.lang.get('user_sync_field', 'Missing translation string for: user_sync_field'), self.lang.get('user_sync_csv_user', 'Missing translation string for: user_sync_csv_user'), self.lang.get('user_sync_nc_user', 'Missing translation string for: user_sync_nc_user')],
            [self.lang.get('user_sync_username', 'Missing translation string for: user_sync_username'), csv_user['username_mapped'], nextcloud_user['id']],
            [self.lang.get('user_sync_display_name', 'Missing translation string for: user_sync_display_name'), csv_user['displayname'], nextcloud_user.get('displayname', '')],
            [self.lang.get('user_sync_email', 'Missing translation string for: user_sync_email'), csv_email, nextcloud_email],
            [self.lang.get('user_sync_groups', 'Missing translation string for: user_sync_groups'), csv_user['groups'], ', '.join(nextcloud_user.get('groups', []))],
            [self.lang.get('user_sync_subadmin_groups', 'Missing translation string for: user_sync_subadmin_groups'), csv_user['subadmin'], ', '.join(nextcloud_user.get('subadmin', []))]
        ]

        print("")
        print(f"{self.lang.get('user_sync_changes_detected', 'Missing translation string for: user_sync_changes_detected')}")
        print(tabulate(table_data, headers="firstrow", tablefmt="grid"))

        apply_changes = input(f"{self.lang.get('user_sync_prompt_changes', 'Missing translation string for: user_sync_prompt_changes')}").lower()
        return apply_changes == 'y'
    
    def apply_changes_to_user(self, username, changes):
        """
        Apply detected changes to a Nextcloud user.

        Args:
            username (str): The username of the user to update.
            changes (dict): A dictionary of changes to apply.
        """
        for key, value in changes.items():
            if key == 'groups':
                self.api.sync_groups(username, value)
            elif key == 'subadmin':
                self.api.sync_subadmin_groups(username, value)
            else:
                self.api.edit_user(username, key, value)     
   
   
    # User Deletion Management
 
 
    def check_for_deleted_users(self, csv_users, nextcloud_users):
        csv_usernames = {user['username_mapped'] for user in csv_users}
        nextcloud_usernames = {user['id'] for user in nextcloud_users}

        deleted_users = nextcloud_usernames - csv_usernames
        logging.info(f"Deleted users detected: {deleted_users}")

        for username in deleted_users:
            # Benutzergruppen und Subadmin-Gruppen könnten bereits vorhanden sein
            nextcloud_user = next(user for user in nextcloud_users if user['id'] == username)

            if 'admin' in nextcloud_user['groups']:
                logging.info(f"Skipping admin user: '{username}'")
                continue

            self.prompt_user_deletion(username)           
            
    def prompt_user_deletion(self, username):
        """
        Prompt the user for deletion confirmation and proceed based on user input.

        Args:
            username (str): The user ID to potentially delete.
        """
        user_details_response = self.api.get_user(username)
        if not self.api.is_successful(user_details_response):
            logging.error(f"Failed to fetch details for user '{username}'.")
            return

        nextcloud_user = {
            'id': username,
            'displayname': self.api.get_xml_value(etree.fromstring(user_details_response['response'].content), ".//displayname", ''),
            'email': self.api.get_xml_value(etree.fromstring(user_details_response['response'].content), ".//email", ''),
            'groups': ', '.join(self.api.get_user_groups(username)),
            'subadmin': ', '.join(self.api.get_user_subadmin_groups(username)),
        }

        table_data = [
            ["ID", "Display name", "Email", "Groups", "Group admin for"],
            [nextcloud_user['id'], nextcloud_user['displayname'], nextcloud_user['email'],
             nextcloud_user['groups'], nextcloud_user['subadmin']]
        ]
        print("")
        print(f"{self.lang.get('user_sync_prompt_delete', 'Missing translation string for: user_sync_prompt_delete')}")
        print(tabulate(table_data, headers="firstrow", tablefmt="grid"))

        if input(f"{self.lang.get('user_sync_prompt_deletion', 'Missing translation string for: user_sync_prompt_deletion')}").lower() == 'y':
            response = self.api.delete_user(username)
            if self.api.is_successful(response):
                logging.info(f"{self.lang.get('user_sync_successful_deletion', 'Missing translation string for: user_sync_successful_deletion')}: '{username}'")
            else:
                logging.error(f"Failed to delete user '{username}'.")