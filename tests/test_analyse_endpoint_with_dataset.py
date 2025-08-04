import json
import os
import subprocess
import time

import requests

from backend_analytics.analytics.utils.transformer_service import (
    transform_to_content_request,
)


# @pytest.mark.api
def test_analyse_endpoint_with_dataset():
    """
    Test the /analyse endpoint with a dataset of articles and compare
    the results with expected outputs.
    """
    # Start the server using the module approach
    server_process = subprocess.Popen(
        ["poetry", "run", "python", "-m", "analytics.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Allow the server time to start up
        time.sleep(5)

        # Load the input articles
        input_path = os.path.join(
            "tests", "assets", "Keskisuomalainen_esimerkki_artikkeleita.json"
        )
        with open(input_path, "r", encoding="utf-8") as file:
            input_data = json.load(file)

        # Extract the articles - they're stored in an array under a single key (SQL query)
        sql_query_key = next(
            iter(input_data)
        )  # Get the first (and only) key in the JSON
        articles = input_data[sql_query_key]

        # Load the expected results
        expected_path = os.path.join("tests", "assets", "evaluation_dataset.json")
        with open(expected_path, "r", encoding="utf-8") as file:
            expected_data = json.load(file)

        # Define how many articles to test
        max_articles = 6  # Adjust as needed for test runtime
        articles_to_test = min(len(expected_data), max_articles)

        for i in range(5, articles_to_test):
            article = articles[i]
            article_id = f"article {i + 1}"

            print(f"\nTesting API with {article_id}: {article['title'][:50]}...")

            # Convert the article to the request format expected by the API
            api_request = transform_to_content_request(article, "Keskisuomalainen")

            # Send a POST request to the /analyse endpoint
            url = "http://127.0.0.1:8000/analyse"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=api_request.json(), headers=headers)

            # Print response for debugging
            print(f"Status code: {response.status_code}")

            # Assert the response status code is 200 (OK)
            assert response.status_code == 200, (
                f"Expected status 200 but got {response.status_code}"
            )

            # Parse the response
            response_data = response.json()
            print(f"Response structure: {list(response_data.keys())}")

            # Get the expected result
            expected_result = expected_data[article_id]

            # Assertions for the people list
            if "people" in response_data and "people" in expected_result:
                print(f"Expected people: {sorted(expected_result['people'])}")
                print(f"Actual people: {sorted(response_data['people'])}")
                assert set(p.lower() for p in response_data["people"]) == set(
                    p.lower() for p in expected_result["people"]
                ), f"People don't match for {article_id}"

            # Assertions for location data
            if "location" in response_data and "location" in expected_result:
                print(f"Expected location: {expected_result['location']}")
                print(f"Actual location: {response_data['location']}")
                # Check each location field separately
                for field in ["country", "city", "neighborhood"]:
                    if (
                        field in response_data["location"]
                        and field in expected_result["location"]
                    ):
                        assert (
                            response_data["location"][field].lower()
                            == expected_result["location"][field].lower()
                        ), f"Location {field} doesn't match for {article_id}"

            # Assertions for organizations list
            if "organisations" in response_data and "organisations" in expected_result:
                print(
                    f"Expected organisations: {sorted(expected_result['organisations'])}"
                )
                print(f"Actual organisations: {sorted(response_data['organisations'])}")
                assert set(
                    org.lower() for org in response_data["organisations"]
                ) == set(org.lower() for org in expected_result["organisations"]), (
                    f"Organisations don't match for {article_id}"
                )

            print(f"{article_id} API test validated successfully")

    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.wait()

        # Print any stderr output from the server for debugging
        stderr = server_process.stderr.read().decode("utf-8")
        if stderr:
            print(f"Server stderr: {stderr}")
