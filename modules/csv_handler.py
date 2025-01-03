import csv
import codecs
import logging

def read_csv(filepath, delimiter=','):
    """
    Reads a CSV file and returns the data as a list of dictionaries.
    Each dictionary represents a row with keys as the CSV header.

    :param filepath: The path to the CSV file.
    :param delimiter: The delimiter used in the CSV file (default is ',').
    :return: A list of dictionaries where each dictionary represents a row in the CSV.
    """
    try:
        # Open the CSV file with UTF-8 encoding to ensure proper handling of special characters
        with codecs.open(filepath, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Read all rows into a list of dictionaries
            data = [row for row in reader]
            
            # Check if the CSV file is empty or improperly formatted
            if not data:
                logging.warning(f"CSV file '{filepath}' is empty or improperly formatted.")
            
            return data

    except FileNotFoundError as e:
        # Log and raise an error if the CSV file is not found
        logging.error(f"CSV file not found: {e}")
        raise

    except csv.Error as e:
        # Log and raise an error if there is an issue with CSV formatting
        logging.error(f"Error reading CSV file '{filepath}': {e}")
        raise

    except Exception as e:
        # Catch and log any other unexpected exceptions
        logging.error(f"An unexpected error occurred while reading the CSV file '{filepath}': {e}")
        raise
