import json
import os
import subprocess
import time

import requests


# @pytest.mark.api
def test_analyse_endpoint():
    # Start the server using the module approach
    server_process = subprocess.Popen(
        ["poetry", "run", "python", "-m", "analytics.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Allow the server time to start up
        time.sleep(5)

        # Path to the example JSON file
        json_path = os.path.join("tests", "assets", "example_api_upload.json")

        # Load the JSON test data
        with open(json_path, "r") as file:
            test_data = json.load(file)

        # Send a POST request to the /analyse endpoint
        url = "http://127.0.0.1:8000/analyse"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=test_data, headers=headers)

        # Print response for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(
            f"Response content type: {response.headers.get('content-type', 'not specified')}"
        )
        print(f"Raw response (first 150 chars): {response.text[:150]}...")

        # Assert the response status code is 200 (OK)
        assert response.status_code == 200, (
            f"Expected status 200 but got {response.status_code}"
        )

        # Check for JSON content type in response headers
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Expected JSON response (application/json) but got: {content_type}"
        )

        # Try to parse the response as JSON with better error handling
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse response as JSON: {e}")
            print(f"Full response text: {response.text}")
            assert False, f"Response is not valid JSON: {e}"

        # Verify response_data is a dictionary (JSON object)
        assert isinstance(response_data, dict), (
            f"Expected JSON object but got {type(response_data)}: {response_data}"
        )

        # Print the structure of the response JSON
        print(f"Response JSON structure: {list(response_data.keys())}")

        # Basic structure assertion
        assert response_data is not None, "Response data is None"

    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.wait()

        # Print any stderr output from the server for debugging
        stderr = server_process.stderr.read().decode("utf-8")
        if stderr:
            print(f"Server stderr: {stderr}")
