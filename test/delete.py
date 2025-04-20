import requests

# API endpoints
SEARCH_API = "http://localhost:8000/api/files/search/"
DELETE_API_TEMPLATE = "http://localhost:8000/api/files/{}/"

def fetch_files():
    try:
        response = requests.get(SEARCH_API)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Return the JSON data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching files: {e}")
        return []

def delete_file(file_id):
    try:
        delete_url = DELETE_API_TEMPLATE.format(file_id)
        response = requests.delete(delete_url)
        if response.status_code == 204:
            print(f"Successfully deleted file with ID: {file_id}")
        else:
            print(f"Failed to delete file with ID: {file_id}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error deleting file with ID {file_id}: {e}")

def main():
    # Fetch all files
    files = fetch_files()
    
    if not files:
        print("No files found or failed to fetch files.")
        return
    
    # Iterate through each file and delete it
    for file in files:
        file_id = file.get("id")
        if file_id:
            delete_file(file_id)
        else:
            print("No ID found for a file, skipping.")

if __name__ == "__main__":
    main()