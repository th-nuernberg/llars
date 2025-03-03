import requests
import json
import os
from datetime import datetime
from colorama import Fore, Style, init
import time

init(autoreset=True)

shorten_output = True  # Set this to False if you do not want to shorten the data output
show_timestamps = False  # Set this to False if you do not want to show timestamps

# Dictionary to map file paths to the respective service
file_service_mapping = {
    "http/seeder/seed_user.http": "backend-flask-service",
    # "http/seeder/seed_ranking.http": "backend-flask-service",
    "http/seeder/seed_rating.http": "backend-flask-service",
    # "http/seeder/output_ranking.http": "backend-flask-service",
    #"http/seeder/output": "backend-flask-service",
    #"http/seeder/test_output": "backend-flask-service",
    #"http/seeder/mail_rating/4o": "backend-flask-service",
    #"http/seeder/mail_rating/claude": "backend-flask-service",
    "http/seeder/mail_rating/opensource": "backend-flask-service",
}

def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def print_with_timestamp(message, color=Fore.RESET, end='\n'):
    if show_timestamps:
        print(f"{color}{current_timestamp()} {message}{Style.RESET_ALL}", end=end)
    else:
        print(f"{color}{message}{Style.RESET_ALL}", end=end)

def shorten_data(data):
    if len(data) > 70:
        return f"{data[:35]}...{data[-35:]}"
    return data

def method_color(method):
    colors = {
        'GET': Fore.BLUE,
        'POST': Fore.GREEN,
        'PUT': Fore.YELLOW,
        'DELETE': Fore.RED
    }
    return colors.get(method, Fore.RESET)

def response_color(status_code):
    if 200 <= status_code < 300:
        return Fore.GREEN
    elif 300 <= status_code < 400:
        return Fore.YELLOW
    else:
        return Fore.RED

def execute_request(method, url, headers=None, data=None, service_replacement=None):
    try:
        # Replace 'localhost' in the URL if necessary
        if 'localhost' in url and service_replacement:
            url = url.replace('localhost', service_replacement)

        method_str = f"{method}"
        print_with_timestamp(
            f"Executing {Style.BRIGHT}{method_color(method)}{method_str}{Style.RESET_ALL} request to {url}")
        if headers:
            headers_str = json.dumps(headers, indent=2) if isinstance(headers, dict) else headers
            print_with_timestamp(f"Headers: {Fore.CYAN}{headers_str}{Style.RESET_ALL}")
        if data:
            data_str = json.dumps(data) if isinstance(data, dict) else data
            if shorten_output:
                print_with_timestamp(f"Data: {Fore.CYAN}{shorten_data(data_str)}{Style.RESET_ALL}")
            else:
                print_with_timestamp(f"Data: {Fore.CYAN}{data_str}{Style.RESET_ALL}")

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            print_with_timestamp(f"Unsupported HTTP method: {method}", Fore.RED)
            return

        status_color = response_color(response.status_code)
        print_with_timestamp(f"Response status code: {Style.BRIGHT}{status_color}{response.status_code}{Style.RESET_ALL}")
        print_with_timestamp(f"Response body: {status_color}{response.text}{Style.RESET_ALL}")

    except requests.exceptions.RequestException as e:
        print_with_timestamp(f"An error occurred: {e}", Fore.RED)


def parse_and_execute(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    method, url, headers, data = None, None, {}, None
    data_lines = []
    is_data_section = False

    for line in lines:
        line = line.strip()

        if line == '###':
            if method and url:
                if data_lines:
                    data = '\n'.join(data_lines)
                service_replacement = file_service_mapping.get(file_path)
                execute_request(method, url, headers, json.loads(data) if data else None, service_replacement)
            method, url = None, None
            headers, data_lines = {}, []
            is_data_section = False
            continue

        if line.startswith('GET') or line.startswith('POST') or line.startswith('PUT') or line.startswith('DELETE'):
            method, url = line.split(' ', 1)
            headers, data_lines = {}, []
            is_data_section = False

        elif line.startswith('Content-Type:'):
            headers['Content-Type'] = line.split(': ', 1)[1]

        elif line.startswith('Authorization:'):
            headers['Authorization'] = line.split(': ', 1)[1]

        elif line.startswith('{') or line.startswith('['):
            is_data_section = True
            data_lines.append(line)

        elif is_data_section:
            data_lines.append(line)

    if method and url:
        if data_lines:
            data = '\n'.join(data_lines)
        service_replacement = file_service_mapping.get(file_path)
        execute_request(method, url, headers, json.loads(data) if data else None, service_replacement)


def parse_and_execute_json(file_path, service_replacement=None):
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Define the endpoint to send the JSON data to
    url = "http://localhost:8081/api/email_threads"

    # Replace 'localhost' in the URL if necessary
    if service_replacement:
        url = url.replace('localhost', service_replacement)

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json"
    }

    # Execute the request
    execute_request('POST', url, headers=headers, data=data)

def process_files(file_service_mapping):
    for file_path, service_replacement in file_service_mapping.items():
        if os.path.isfile(file_path):
            if file_path.endswith('.json'):
                print_with_timestamp(f"Processing JSON file: {file_path}", Fore.BLUE)
                parse_and_execute_json(file_path, service_replacement)
            else:
                print_with_timestamp(f"Processing file: {file_path}", Fore.BLUE)
                parse_and_execute(file_path)
        elif os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file in files:
                    file_path_full = os.path.join(root, file)
                    if file.endswith('.json'):
                        print_with_timestamp(f"Processing JSON file: {file_path_full}", Fore.BLUE)
                        parse_and_execute_json(file_path_full, service_replacement)
                    else:
                        print_with_timestamp(f"Processing file: {file_path_full}", Fore.BLUE)
                        parse_and_execute(file_path_full)
        else:
            print_with_timestamp(f"Invalid path: {file_path}", Fore.RED)

def check_heatlh(interval=10):
    while True:
        try:
            response = requests.get('http://backend-flask-service:8081/auth/health_check')
            if response.status_code == 200:
                pass
                # print("Successfully processed notifications!")
            else:
                print(f"Error occurred: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"An error occurred while making the request: {e}")

        time.sleep(interval)  # Wartezeit vor der nächsten Anfrage


if __name__ == "__main__":
    process_files(file_service_mapping)
    print(f"{Fore.GREEN}{Style.BRIGHT}Successfully seeded data!{Style.RESET_ALL}")
    check_heatlh(60)