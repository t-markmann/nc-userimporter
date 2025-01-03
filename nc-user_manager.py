#!/usr/bin/env python3
import os
import sys
import html
import logging
from datetime import datetime
from tabulate import tabulate
from modules import ConfigReader, PasswordGenerator, NextcloudAPI, NextcloudUserManager, read_csv, generate_qr_code, generate_pdf, load_language, MAPPING

# Useful resources for contributors:
# Nextcloud user API https://docs.nextcloud.com/server/latest/admin_manual/configuration_user/instruction_set_for_users.html
# Nextcloud group API https://docs.nextcloud.com/server/latest/admin_manual/configuration_user/instruction_set_for_groups.html
# CURL to Python request converter https://curl.trillworks.com/

# Determine if running in a build package (frozen) or from a separate Python script
def get_app_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

appdir = get_app_directory()

# Set up logging configuration
def setup_logging(log_dir, log_file, config_loglevel):
    os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists
    log_file_path = os.path.join(log_dir, log_file)  # Combine log directory and log file name
    loglevel = getattr(logging, config_loglevel.upper(), logging.INFO)
    logging.basicConfig(
        level=loglevel,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
    )

# Load configuration settings from config.xml
def load_config(config_reader):
    try:
        return {
            'base_url': config_reader.get('cloudurl'),
            'admin_name': config_reader.get('adminname'),
            'admin_pass': config_reader.get('adminpass'),
            'pdf_one_file': config_reader.get('pdf_one_file', 'yes'),
            'pdf_single_files': config_reader.get('pdf_single_files', 'yes'),
            'ssl_verify': config_reader.get('sslverify', 'True'),
            'user_language': config_reader.get('language', 'en'),
            'csv_delimiter': config_reader.get('csvdelimiter', ';'),
            'group_delimiter': config_reader.get('csvdelimitergroups', ','),
            'password_length': int(config_reader.get('passwordlength', 12)),
            'generate_password': config_reader.get('generatepassword', 'yes'),
            'csv_file': config_reader.get('csvfile'),
            'log_level': config_reader.get('loglevel')
        }
    except KeyError as e:
        print(f"Critical Error: Missing configuration key: {e}")
        sys.exit(1)

# get path from csv-file
def get_csv_file_path(csv_file_name):
    # check if program is frozen
    if getattr(sys, 'frozen', False):
        # path to executable
        base_path = os.path.dirname(sys.executable)
    else:
        # use Python-Script path
        base_path = os.path.dirname(__file__)

    # combine base-path with filename of csv
    return os.path.join(base_path, csv_file_name)


# Clean up temporary files
def clean_tmp_files(tmp_dir):
    if os.path.exists(tmp_dir):
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))

# Initialize Nextcloud API
def initialize_nc_api(config):
    ssl_verify = config['ssl_verify'].lower() == 'true' if isinstance(config['ssl_verify'], str) else config['ssl_verify']
    try:
        return NextcloudAPI(
            config['base_url'],
            config['admin_name'],
            config['admin_pass'],
            ssl_verify
        )
    except KeyError as e:
        print(f"Critical Error: Missing configuration key: {e}")
        sys.exit(1)

# Display header information
def display_header():
    print("\n\n###################################################################################")
    print("# NEXTCLOUD-USER-MANAGER (IMPORT, UPDATE, DELETE)                                 #")
    print("###################################################################################")
    print("Copyright (C) 2019-2024 Torsten Markmann (t-markmann), edudocs.org & uplinked.net")
    print("Main Contributor: Johannes Schirge (Shen)")
    print("Thanks to all Contributors: https://github.com/t-markmann/nc-userimporter/graphs/contributors ")
    print("This program comes with ABSOLUTELY NO WARRANTY")
    print("This is free software, and you are welcome to redistribute it under certain conditions.")
    print("")

def display_info_create_user_and_groups():
    print("###################################################################################")
    print(f" {language.get('nc_userimporter_welcome', 'Missing translation string for: nc_userimporter_welcome')}")
    print(f" {language.get('nc_userimporter_process_preview', 'Missing translation string for: nc_userimporter_process_preview')}")
    print("###################################################################################")
    print("")
    
def display_info_synchronize_user():
    print("###################################################################################")
    print(f" {language.get('nc_userimporter_welcome_sync', 'Missing translation string for: nc_userimporter_welcome_sync')}")
    print(f" {language.get('nc_userimporter_process_preview_sync', 'Missing translation string for: nc_userimporter_process_preview_sync')}")
    print("###################################################################################")
    print("")

display_header()

# Create Users and Groups
def create_users_and_groups(csv_data, config, nc_api):
    logging.info("Begin user creation process...")
    users_to_process = []

    for row in csv_data:
        try:
            username = row['username']
            password = row['password']
            displayname = row['displayname'] if row['displayname'] else username
            email = row['email']
            groups = row['groups'].split(config['group_delimiter'])
            subadmin = row['subadmin'].split(config['group_delimiter']) if row['subadmin'] else []
            quota = row.get('quota', '1GB')

            if not password and config['generate_password'] == 'yes':
                password = PasswordGenerator(config['password_length'])

            logging.info(f"Creating user '{username}' with display name '{displayname}' and email '{email}'")
            response = nc_api.add_user(username, password, displayname, email, groups, quota, config['user_language'])

            if response:
                logging.info(f"User '{username}' created successfully.")
                users_to_process.append({'username': username, 'password': password, 'displayname': displayname})

                if groups:
                    nc_api.sync_groups(username, set(groups))
                if subadmin:
                    nc_api.sync_subadmin_groups(username, set(subadmin))
            else:
                logging.error(f"Failed to create user '{username}'")

        except Exception as e:
            logging.error(f"Error while processing user '{username}': {str(e)}")

    logging.info("User creation process completed.")
    return users_to_process

# Generate PDF-files
def generate_pdf_files(users_to_process, config, tmp_dir, output_dir):
    if not users_to_process:
        logging.info("No users to process. PDF generation skipped.")
        return

    today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if config['pdf_single_files'] == 'yes':
        for user in users_to_process:
            qr_code_path = generate_qr_code(f"nc://login/user:{user['username']}&password:{user['password']}&server:{config['base_url']}", tmp_dir, user['username'])
            if qr_code_path:
                output_filepath = os.path.join(output_dir, f"{user['username']}_{today}.pdf")
                generate_pdf({'username': user['username'], 'password': user['password'], 'displayname': user['displayname']}, qr_code_path, output_filepath, config['base_url'], language)
            else:
                logging.error(f"Failed to generate QR code for user {user['username']}. PDF generation skipped.")

    if config['pdf_one_file'] == 'yes' or (config['pdf_one_file'] == 'no' and config['pdf_single_files'] == 'no'):
        output_filename = f"userlist_{today}.pdf"
        output_filepath = os.path.join(output_dir, output_filename)
        for user in users_to_process:
            user['qr_code_path'] = generate_qr_code(f"nc://login/user:{user['username']}&password:{user['password']}&server:{config['base_url']}", tmp_dir, user['username'])
        generate_pdf({'users': users_to_process}, "", output_filepath, config['base_url'], language, multi_user=True)

# Import new users from CSV
def import_users(config, nc_api):
    try:
        display_info_create_user_and_groups()
        print(f"{language.get('nc_userimporter_press_continue', 'Missing translation string for: nc_userimporter_press_continue')}")
        input(f"{language.get('nc_userimporter_any_key', 'Missing translation string for: nc_userimporter_any_key')}")

        output_dir = 'output'
        tmp_dir = 'tmp'
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)

        # use the function get_csv_file_path() to get the csv-path
        csv_file_path = get_csv_file_path(config['csv_file'])
        csv_data = read_csv(csv_file_path, config['csv_delimiter'])

        usertable = [["Username", "Display name", "Password", "Email", "Groups", "Group admin for", "Quota"]]
        for row in csv_data:
            pass_anon = "*" * len(html.escape(row['password'])) if row['password'] else "Not set"
            row['username'] = html.escape(row['username']).translate(MAPPING)
            quota = html.escape(row['quota']) if row['quota'] is not None else ''
            usertable.append([row['username'], row['displayname'], pass_anon, row['email'], row['groups'], row['subadmin'], quota])

        print(tabulate(usertable, headers="firstrow"))
        input(f"{language.get('nc_userimporter_any_key', 'Missing translation string for: nc_userimporter_any_key')}")

        users_to_process = create_users_and_groups(csv_data, config, nc_api)
        generate_pdf_files(users_to_process, config, tmp_dir, output_dir)
        print(f"\n{language.get('nc_userimporter_user_creation_completed', 'Missing translation string for: nc_userimporter_user_creation_completed')}")

    except KeyboardInterrupt:
        print(f"\n{language.get('nc_userimporter_exit_program', 'Missing translation string for: nc_userimporter_exit_program')}")
        sys.exit(0)

    finally:
        clean_tmp_files(tmp_dir)

# Synchronize existing users (update and delete)
def synchronize_users(config, user_manager):
    display_info_synchronize_user()
    print(f"{language.get('nc_userimporter_press_continue_sync', 'Missing translation string for: nc_userimporter_press_continue_sync')}")
    input(f"{language.get('nc_userimporter_any_key_sync', 'Missing translation string for: nc_userimporter_any_key_sync')}")
    logging.info(f"{language.get('nc_userimporter_sync_start', 'Missing translation string for: nc_userimporter_sync_start')}")

    try:
        # Verwende die Funktion get_csv_file_path() anstelle von os.path.dirname(__file__)
        csv_file_path = get_csv_file_path(config['csv_file'])
        csv_data = read_csv(csv_file_path, config['csv_delimiter'])
        mapped_csv_data = user_manager.load_csv_users(csv_data)
        user_manager.compare_and_sync_users(mapped_csv_data)
        logging.info(f"{language.get('nc_userimporter_sync_completed', 'Missing translation string for: nc_userimporter_sync_completed')}")
    except KeyError as e:
        print(f"Critical Error: Missing configuration key: {e}")
        sys.exit(1)


# Main menu
def main_menu(config, nc_api, user_manager):
    while True:
        print(f"\n{language.get('nc_userimporter_select_option', 'Missing translation string for: nc_userimporter_select_option')}")
        print(f"1) {language.get('nc_userimporter_import_option', 'Missing translation string for: nc_userimporter_import_option')}")
        print(f"2) {language.get('nc_userimporter_sync_option', 'Missing translation string for: nc_userimporter_sync_option')}")
        print(f"3) {language.get('nc_userimporter_exit_option', 'Missing translation string for: nc_userimporter_exit_option')}")

        choice = input(f"{language.get('nc_userimporter_enter_choice', 'Missing translation string for: nc_userimporter_enter_choice')}").strip()

        if choice == '1':
            import_users(config, nc_api)
        elif choice == '2':
            synchronize_users(config, user_manager)
        elif choice == '3':
            print(f"{language.get('nc_userimporter_exit_program', 'Missing translation string for: nc_userimporter_exit_program')}")
            break
        else:
            print(f"{language.get('nc_userimporter_invalid_choice', 'Missing translation string for: nc_userimporter_invalid_choice')}")

# Main program execution
if __name__ == "__main__":
    try:
        config_reader = ConfigReader(os.path.join(appdir, 'config.xml'))
        config = load_config(config_reader)
        setup_logging('logs', 'output.log', config['log_level'])  # logs/output.log will be used now
        language = load_language(config_reader)
        nc_api = initialize_nc_api(config)
        user_manager = NextcloudUserManager(nc_api, language)
        main_menu(config, nc_api, user_manager)
    except KeyboardInterrupt:
        print(f"\n{language.get('nc_userimporter_exit_program', 'Missing translation string for: nc_userimporter_exit_program')}")
        sys.exit(0)
