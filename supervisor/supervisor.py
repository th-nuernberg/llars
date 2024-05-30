import requests
import json
import os
from datetime import datetime

shorten_output = True  # Set this to False if you do not want to shorten the data output

def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def shorten_data(data):
    if len(data) > 70:
        return f"{data[:35]}...{data[-35:]}"
    return data

def execute_request(method, url, headers=None, data=None):
    try:
        print(f"{current_timestamp()} Executing {method} request to {url}")
        if headers:
            print(f"{current_timestamp()} Headers: {json.dumps(headers, indent=2)}")
        if data:
            if shorten_output:
                print(f"{current_timestamp()} Data: {shorten_data(data)}")
            else:
                print(f"{current_timestamp()} Data: {data}")

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            print(f"{current_timestamp()} Unsupported HTTP method: {method}")
            return

        print(f"{current_timestamp()} Response status code: {response.status_code}")
        print(f"{current_timestamp()} Response body: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"{current_timestamp()} An error occurred: {e}")

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
                execute_request(method, url, headers, json.loads(data) if data else None)
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
        execute_request(method, url, headers, json.loads(data) if data else None)

def process_files(file_paths):
    for path in file_paths:
        if os.path.isfile(path):
            print(f"{current_timestamp()} Processing file: {path}")
            parse_and_execute(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    print(f"{current_timestamp()} Processing file: {file_path}")
                    parse_and_execute(file_path)
        else:
            print(f"{current_timestamp()} Invalid path: {path}")

if __name__ == "__main__":
    file_paths = [
        "http/seed_user.http",
        "http/seed_ranking.http",
        "http/seed_rating.http",
    ]
    process_files(file_paths)

    while True:
        pass
