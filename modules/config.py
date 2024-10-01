from bs4 import BeautifulSoup
import codecs
import logging

class ConfigReader:
    """
    ConfigReader is responsible for loading and parsing an XML-based configuration file.
    It provides an interface for accessing configuration values stored in the XML file.
    Values are read once during initialization and can be accessed via the `get` method.
    """

    def __init__(self, config_file):
        """
        Initializes the ConfigReader and loads the configuration file.

        Args:
            config_file (str): The path to the XML configuration file.
        """
        self.config_file = config_file
        self.config_values = self._load_config()

    def _load_config(self):
        """
        Reads and parses the XML configuration file using BeautifulSoup.

        Returns:
            dict: A dictionary of configuration keys and their corresponding values.
        
        Raises:
            FileNotFoundError: If the config file does not exist.
            UnicodeDecodeError: If there is an issue reading the file in UTF-8 encoding.
        """
        try:
            # Open the config file with UTF-8 encoding using the codecs module
            with codecs.open(self.config_file, mode='r', encoding='utf-8') as configfile:
                config_content = configfile.read()
        except FileNotFoundError:
            logging.error(f"Configuration file '{self.config_file}' not found.")
            raise
        except UnicodeDecodeError:
            logging.error(f"Error reading '{self.config_file}' with UTF-8 encoding.")
            raise

        # Parse the XML content using BeautifulSoup with the 'lxml-xml' parser
        config_xmlsoup = BeautifulSoup(config_content, "lxml-xml")

        # Define the expected configuration keys in the XML file
        config_keys = [
            'cloudurl', 'adminname', 'adminpass', 'csvfile', 'csvdelimiter',
            'csvdelimitergroups', 'generatepassword', 'passwordlength',
            'sslverify', 'language', 'pdf_one_file', 'pdf_single_files', 'loglevel', 'scriptlang'
        ]

        # Dictionary to hold key-value pairs from the XML configuration file
        config_values = {}

        # Extract values for the expected configuration keys from the XML
        for key in config_keys:
            element = config_xmlsoup.find(key)  # Find the XML tag by key name
            if element and element.string:  # Check if the element exists and contains text
                config_values[key] = element.string.strip()  # Store value without surrounding whitespace
            else:
                logging.warning(f"Element <{key}> not found or has no text content.")

        return config_values

    def get(self, key, fallback=None):
        """
        Retrieves the value for a given configuration key.

        Args:
            key (str): The name of the configuration key.
            fallback (str, optional): A fallback value to return if the key is not found.
                                      Defaults to None.

        Returns:
            str: The value associated with the key, or the fallback value if the key is not found.

        Raises:
            KeyError: If the key is not found and no fallback is provided.
        """
        value = self.config_values.get(key)

        if value is None:
            if fallback is not None:
                # Log a warning if we fall back to the default value
                logging.warning(f"Configuration key '{key}' not found. Using fallback value '{fallback}'.")
                return fallback
            else:
                # Log an error and raise an exception if no fallback is provided
                logging.error(f"Configuration key '{key}' is missing and no fallback was provided.")
                raise KeyError(f"Missing configuration key: {key}")
        return value
