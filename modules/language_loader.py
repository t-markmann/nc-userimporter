import os
import json
import logging

def load_language(config_reader):
    """
    Loads the language file based on the language setting in the configuration file (config.xml).
    
    If the specified language file is not found, it defaults to English ('ENG.json').
    
    :param config_reader: An instance of ConfigReader used to retrieve configuration settings.
    :return: A dictionary containing the language strings.
    """
    
    # Retrieve the script language from the configuration, defaulting to English if not set
    script_lang = config_reader.get('scriptlang', 'ENG')
    logging.debug(f"Attempting to load language: {script_lang}")
    
    # Construct the path to the language file based on the script language
    lang_file_path = os.path.join('lang', f"{script_lang}.json")
    
    try:
        # Attempt to open and load the specified language file
        with open(lang_file_path, 'r', encoding='utf-8') as lang_file:
            language_data = json.load(lang_file)
            logging.debug(f"Successfully loaded language file: {lang_file_path}")
            return language_data
    except FileNotFoundError:
        # Log an error if the specified language file is not found, then default to English
        logging.error(f"Language file '{lang_file_path}' not found. Defaulting to English.")
        
        # Path to the default English language file
        default_lang_file_path = os.path.join('lang', 'ENG.json')
        
        try:
            # Attempt to load the default English language file
            with open(default_lang_file_path, 'r', encoding='utf-8') as default_lang_file:
                default_language_data = json.load(default_lang_file)
                logging.info(f"Loaded default English language file: {default_lang_file_path}")
                return default_language_data
        except FileNotFoundError:
            # If the default language file is also not found, raise a critical error
            logging.critical(f"Default language file '{default_lang_file_path}' not found. Exiting program.")
            raise SystemExit(f"Critical Error: Default language file '{default_lang_file_path}' not found.")
