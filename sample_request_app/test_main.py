import requests
from requests.api import post
from requests.models import PreparedRequest

# Define the URL for the API endpoints
BASE_URL = "http://localhost/:8000"

def send_file(file_path):
    url = f"{BASE_URL}/upload_file"
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            return response.headers["file-uuid"]
        else:
            raise Exception(f"Failed to upload file. Response: {response.text}")

video_path = "smiling1.mp4"
uuid = send_file(video_path)
print(f"UUID for uploaded file: {uuid}")

data_url = f"{BASE_URL}/data_by_uuid/0b2c23ff-906f-40bb-b65b-d24dddc05cee"
response = requests.get(data_url)
if response.status_code == 200:
    data = response.json()
    print(f"Data for uploaded file:\n{data}")
else:
    print(f"Failed to get data. Response: {response.text}")
