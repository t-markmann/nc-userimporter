import requests
import logging
from lxml import etree
import certifi


class NextcloudAPI:
    def __init__(self, base_url, adminname, adminpass, ssl_verify=True):
        """
        Initialize the NextcloudAPI class with base URL, admin username, password, and SSL verification setting.
        
        :param base_url: The base URL of the Nextcloud server.
        :param adminname: The username of the admin account.
        :param adminpass: The password of the admin account.
        :param ssl_verify: Boolean indicating whether to verify SSL certificates.
        """
        self.logger = logging.getLogger(__name__)  # Logger specific to this class
        
        # Ensure the base URL starts with https:// and remove trailing slash if present
        if not base_url.startswith("https://"):
            base_url = f"https://{base_url}"
        self.base_url = base_url.rstrip('/')
        
        self.adminname = adminname
        self.adminpass = adminpass
        self.headers = {
            'OCS-APIRequest': 'true',  # Required for Nextcloud OCS API requests
            'Accept-Language': 'en'    # Force English response
        }
        self.auth = (self.adminname, self.adminpass)  # Basic authentication for Nextcloud API
        
        if ssl_verify is True:
            self.ssl_verify = certifi.where()
            self.logger.debug(f"Using certifi bundle: {self.ssl_verify}")  # Gib den Pfad von certifi.where() aus
        else:
            self.ssl_verify = False
            self.logger.info("SSL verification disabled")

    def _request(self, method, endpoint, data=None, headers=None):
        """
        Helper method to send requests to the Nextcloud API.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE).
            endpoint (str): API endpoint.
            data (dict): Optional data to send in the request.
            headers (dict): Optional headers for the request.
            
        Returns:
            dict: Parsed response dictionary, or False if the request failed.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = headers or self.headers

        try:
            self.logger.debug(f"Requesting {method} {url} with data: {data}")
            if method in ['POST', 'PUT']:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                auth=self.auth,
                data=data,
                verify=self.ssl_verify
            )
            response.raise_for_status()

            if response.headers.get('Content-Type') == 'application/xml' or response.text.startswith('<?xml'):
                return self._parse_xml_response(response)

            self.logger.debug(f"Response Status: {response.status_code} - {response.text[:200]}...")
            if response.status_code == 200:
                return {'status_code': 100, 'message': 'Success', 'response': response}
            else:
                return {'status_code': response.status_code, 'message': response.text, 'response': response}

        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return False


    def _parse_xml_response(self, response):
        """
        Parse XML response from the Nextcloud API and extract status information.
        
        :param response: The raw HTTP response containing XML data.
        :return: A dictionary with parsed status, message, and original response.
        """
        root = etree.fromstring(response.content)
        status_code = root.find('.//statuscode').text
        status = root.find('.//status').text
        message = root.find('.//message').text

        # Log and handle non-successful API responses
        if status != "ok" and status_code != "102":
            self.logger.debug(f"Nextcloud API Info - Status: {status}, Status Code: {status_code}, Message: {message}")
            return {
                'status_code': int(status_code),
                'message': message,
                'response': response
            }
        # Log successful response
        self.logger.debug(f"Nextcloud API Success - Status: {status}, Status Code: {status_code}")
        return {
            'status_code': int(status_code),
            'message': message,
            'response': response
        }
        
    def get_xml_value(self, root, xpath, default_value):
        """
        Extract text from an XML element or return a default value if the element does not exist.

        Args:
            root (etree.Element): The root XML element.
            xpath (str): The XPath to search for.
            default_value (str): The value to return if the element is not found.

        Returns:
            str: The extracted text or the default value.
        """
        element = root.find(xpath)
        if element is not None and element.text:
            return element.text.strip()
        return default_value
    
    
    # Success Checking and Response Parsing
    
    
    def is_successful(self, response):
        """
        Check if the response from the API is successful.
        
        Args:
            response (dict): The API response dictionary.
        
        Returns:
            bool: True if the request was successful, False otherwise.
        """
        if isinstance(response, dict) and response.get('status_code') == 100:
            return True
        return False   

    def parse_groups_from_response(self, response):
        """
        Parse groups from the API response.
        """
        try:
            root = etree.fromstring(response.content)
            groups = [group.text for group in root.findall('.//element')]
            return groups
        except Exception as e:
            logging.error(f"Error parsing groups from response: {e}")
            return []
    
    def parse_users_from_response(self, response):
        """
        Parse the XML response to extract user information.

        Args:
            response (requests.Response): The API response containing user information.

        Returns:
            list: A list of user dictionaries with basic info (id, displayname, email, etc.).
        """
        root = etree.fromstring(response.content)
        return [{'id': element.text, 'email': None, 'displayname': None, 'subadmin': [], 'groups': []}
                for element in root.findall('.//element') if element.text]


    # User Management Methods
    
    
    def get_users(self):
        """Retrieve a list of all users from the Nextcloud server."""
        return self._request('GET', 'ocs/v1.php/cloud/users')

    def get_user(self, username):
        """Retrieve details of a specific user by username."""
        return self._request('GET', f'ocs/v1.php/cloud/users/{username}')

    def add_user(self, username, password, display_name, email, groups, quota, language):
        """
        Add a new user only if they do not already exist.
        """
        # Check if user already exists
        existing_user = self.get_user(username)
        
        if existing_user and existing_user['status_code'] == 100:
            self.logger.info(f"User '{username}' already exists. Skipping user creation.")
            return False

        data = {
            'userid': username,
            'password': password,
            'displayName': display_name,
            'email': email,
            'quota': quota,
            'language': language
        }

        # Ensure the groups exist before adding the user
        if not self.ensure_groups_exist(groups):
            self.logger.error(f"Failed to create necessary groups for user '{username}'.")
            return False

        # Now that the groups are ensured, add the user
        response = self._request('POST', 'ocs/v1.php/cloud/users', data=data)

        if self.is_successful(response):
            self.logger.info(f"User '{username}' successfully added.")
            return True
        else:
            self.logger.error(f"Failed to add user '{username}': {response.get('message')}")
            return False

    def edit_user(self, username, key, value):
        """
        Edit the specified user's information based on the provided key-value pair.

        Args:
            username (str): The username of the user to update.
            key (str): The field to update (e.g., 'email', 'displayname', 'quota').
            value (str): The new value for the field.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        # Format the data payload to match the API's expectations (key and value parameters)
        data = {
            'key': key,  # Key to update (e.g., 'email')
            'value': value  # New value for the field (e.g., 'newemail@example.com')
        }
        
        # Perform the API request using the correct endpoint for user updates
        response = self._request('PUT', f'ocs/v1.php/cloud/users/{username}', data=data)

        # Handle the response based on type and content
        if isinstance(response, dict):
            status_code = response.get('status_code')
            if status_code == 100:
                logging.info(f"User '{username}' successfully updated: {key} -> {value}")
                return True
            elif status_code == 101:
                logging.error(f"Failed to update user '{username}': User not found.")
            elif status_code == 102:
                logging.error(f"Failed to update user '{username}': Invalid input data for {key}.")
            else:
                logging.error(f"Failed to update user '{username}': Unexpected status code {status_code}.")
        else:
            logging.error(f"Failed to update user '{username}': Unexpected response type: {response}")

        return False

    def disable_user(self, username):
        """Disable the specified user by username."""
        return self._request('PUT', f'ocs/v1.php/cloud/users/{username}/disable')

    def enable_user(self, username):
        """Enable the specified user by username."""
        return self._request('PUT', f'ocs/v1.php/cloud/users/{username}/enable')

    def delete_user(self, username):
        """Delete the specified user by username."""
        return self._request('DELETE', f'ocs/v1.php/cloud/users/{username}')
    
    
    # Group Management Functions
 
    def get_groups(self):
        """Retrieve a list of all groups from the Nextcloud server."""
        return self._request('GET', 'ocs/v1.php/cloud/groups') 
    
    def get_user_groups(self, username):
        """
        Retrieve the groups a specific user belongs to by username and return them as a list.
        """
        response = self._request('GET', f'ocs/v1.php/cloud/users/{username}/groups')
        if self.is_successful(response):
            return self.parse_groups_from_response(response['response'])
        else:
            self.logger.error(f"Failed to fetch groups for user '{username}'")
            return []
 
    def create_groups(self, groups):
        """Create new groups on the Nextcloud server."""
        return [self._request('POST', 'ocs/v1.php/cloud/groups', data={'groupid': group}) for group in groups]
           
    def ensure_groups_exist(self, groups):
        """
        Ensure that the specified groups exist in Nextcloud. If any group doesn't exist, create it.

        Args:
            groups (list): List of groups to check and create if necessary.
            
        Returns:
            bool: True if all groups exist or were successfully created, False otherwise.
        """
        # Fetch existing groups
        existing_groups_response = self.get_groups()
        if not self.is_successful(existing_groups_response):
            self.logger.error("Failed to fetch existing groups.")
            return False
        
        # Parse the existing groups
        existing_groups = set(self.parse_groups_from_response(existing_groups_response['response']))

        # Create groups that don't exist
        for group in groups:
            if group not in existing_groups:
                self.logger.info(f"Group '{group}' does not exist. Creating it...")
                group_creation_response = self.create_groups([group])
                if not self.is_successful(group_creation_response[0]):
                    self.logger.info(f"Failed to create group '{group}': {group_creation_response[0].get('message')}")
                    return False
                else:
                    self.logger.info(f"Group '{group}' created successfully.")
        
        return True

    def add_user_to_groups(self, username, groups):
        """Add the specified user to one or more groups."""
        responses = [self._request('POST', f'ocs/v1.php/cloud/users/{username}/groups', data={'groupid': group}) for group in groups]
        return all(self.is_successful(response) for response in responses)

    def remove_user_from_groups(self, username, groups):
        """
        Remove the specified user from one or more groups.

        Args:
            username (str): The username of the user to remove from groups.
            groups (list): A list of group IDs to remove the user from.
            
        Returns:
            bool: True if the user was successfully removed from all groups, False otherwise.
        """
        for group in groups:
            response = self._request('DELETE', f'ocs/v1.php/cloud/users/{username}/groups?groupid={group}')
            if not self.is_successful(response):
                self.logger.error(f"Failed to remove {username} from group '{group}': {response.get('message')}")
                return False
        return True

    def sync_user_to_groups(self, username, current_groups, new_groups):
        """
        Synchronize a user to groups by adding or removing them as necessary.
        
        Args:
            username (str): The username of the user.
            current_groups (set): The current set of groups the user belongs to.
            new_groups (set): The new set of groups the user should belong to.
        
        Returns:
            bool: True if the synchronization is successful, False otherwise.
        """
        groups_to_add = new_groups - current_groups
        groups_to_remove = current_groups - new_groups

        # Ensure that all groups to add exist, create them if necessary
        if groups_to_add:
            logging.info(f"Ensuring that the following groups exist: {groups_to_add}")
            if not self.ensure_groups_exist(groups_to_add):
                logging.error(f"Failed to ensure all groups exist for {username}.")
                return False

        # Add the user to new groups
        if groups_to_add:
            logging.info(f"Adding {username} to groups: {groups_to_add}")
            if not self.add_user_to_groups(username, groups_to_add):
                logging.error(f"Failed to add {username} to groups.")
                return False

        # Remove the user from groups that are no longer assigned
        if groups_to_remove:
            logging.info(f"Removing {username} from groups: {groups_to_remove}")
            if not self.remove_user_from_groups(username, groups_to_remove):
                logging.error(f"Failed to remove {username} from groups.")
                return False

        return True

    def sync_groups(self, username, new_groups):
        current_groups = set(self.get_user_groups(username))
        return self.sync_user_to_groups(username, current_groups, new_groups)
    
    
    # Subadmin-Group Management Functions
        
    
    def get_user_subadmin_groups(self, username):
        """Retrieve the groups in which the specified user is a subadmin."""
        response = self._request('GET', f'ocs/v1.php/cloud/users/{username}/subadmins')
        if self.is_successful(response):
            return self.parse_groups_from_response(response['response'])
        else:
            self.logger.error(f"Failed to fetch subadmin groups for user '{username}'")
            return []

    def promote_user_in_group(self, username, groups):
        """
        Promote the specified user to subadmin in one or more groups.

        Args:
            username (str): The username of the user to promote.
            groups (list): A list of group IDs to promote the user to subadmin.
            
        Returns:
            bool: True if the user was successfully promoted to subadmin in all groups, False otherwise.
        """
        # Ensure that all groups exist before promoting the user
        if not self.ensure_groups_exist(groups):
            self.logger.error(f"Failed to ensure all groups exist for promoting {username} to subadmin.")
            return False

        # Proceed to promote the user to subadmin in each group
        for group in groups:
            response = self._request('POST', f'ocs/v1.php/cloud/users/{username}/subadmins', data={'groupid': group})
            if not self.is_successful(response):
                self.logger.error(f"Failed to promote {username} to subadmin in group '{group}': {response.get('message')}")
                return False
        return True
 
    def demote_user_in_group(self, username, groups):
        """Demote the specified user from subadmin in one or more groups."""
        # DELETE requests should send groupid in the URL, not as data
        return [self._request('DELETE', f'ocs/v1.php/cloud/users/{username}/subadmins?groupid={group}') for group in groups]   
    
    def sync_subadmin_groups(self, username, new_subadmin_groups):
        """
        Synchronize the user's subadmin status for groups.

        Args:
            username (str): The username of the user to sync subadmin groups for.
            new_subadmin_groups (set): The new set of subadmin groups for the user.
            
        Returns:
            bool: True if the synchronization was successful, False otherwise.
        """
        current_subadmin_groups = set(self.get_user_subadmin_groups(username))
        subadmin_to_add = new_subadmin_groups - current_subadmin_groups
        subadmin_to_remove = current_subadmin_groups - new_subadmin_groups

        # Ensure all groups to add exist
        if subadmin_to_add:
            self.logger.info(f"Ensuring that the following groups exist for subadmin promotion: {subadmin_to_add}")
            if not self.ensure_groups_exist(subadmin_to_add):
                self.logger.error(f"Failed to ensure groups exist for subadmin promotion for {username}.")
                return False

        if subadmin_to_add:
            self.logger.info(f"Promoting {username} to subadmin of groups: {subadmin_to_add}")
            if not self.promote_user_in_group(username, subadmin_to_add):
                self.logger.error(f"Failed to promote {username} to subadmin.")
                return False

        if subadmin_to_remove:
            self.logger.info(f"Demoting {username} from subadmin of groups: {subadmin_to_remove}")
            if not self.demote_user_in_group(username, subadmin_to_remove):
                self.logger.error(f"Failed to demote {username} from subadmin.")
                return False

        return True


    # Circle Management Functions
    
    
    def get_circles(self):
        """List all circles available in Nextcloud."""
        return self._request('GET', 'apps/circles/circles')


    # Other Operations

    def resend_welcome_mail(self, username):
        """Resend the welcome email to the specified user."""
        return self._request('POST', f'ocs/v1.php/cloud/users/{username}/welcome')

