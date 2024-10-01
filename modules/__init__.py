"""
This package contains several utility modules for managing Nextcloud user imports, 
password generation, CSV handling, output generation, and API communication with Nextcloud.

Modules included:
- config: Provides the ConfigReader class for reading and parsing the XML configuration file.
- password: Provides the PasswordGenerator class for generating random secure passwords.
- csv_handler: Provides the read_csv function for handling CSV file imports.
- output_handler: Provides the generate_qr_code and generate_pdf functions for creating QR codes and PDF documents.
- mapping: Exports the MAPPING dictionary used for special character handling in usernames.
- nextcloud_api: Provides the NextcloudAPI class for interacting with the Nextcloud API.
"""

# Import specific classes and functions from the package modules for external use.
from .config import ConfigReader  # Handles reading and parsing XML configuration files
from .password import PasswordGenerator  # Generates secure random passwords
from .csv_handler import read_csv  # Reads and parses CSV files for user imports
from .output_handler import generate_qr_code, generate_pdf  # Generates QR codes and PDFs for user output
from .mapping import MAPPING  # Provides a dictionary for special character mapping (e.g., for username sanitization)
from .nextcloud_api import NextcloudAPI  # Manages interaction with the Nextcloud APIfrom .user_sync import NextcloudUserManager
from .user_sync import NextcloudUserManager
from .language_loader import load_language