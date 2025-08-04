import json
import math
import os
import sys

import pandas as pd
import pytest

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.utils.articles_service import (
    get_article_apu360,
    get_n_random_article_urls,
)
from backend_analytics.analytics.utils.transformer_service import (
    transform_to_content_request,
)

test_data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "assets/Alehti_esimerkki_artikkeleita.json")
)

# Open and read the test file
with open(test_data_path, "r") as file:
    test_data = json.load(file)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_random_articles_user_needs(async_client, service):
    # Get 10 random article URLs
    urls = get_n_random_article_urls(20)

    errors = []

    # Get the articles from the URLs
    articles = []
    for url in urls:
        if url["User Needs"].lower() == "fact":
            url["User Needs"] = "tiedä"
        elif url["User Needs"].lower() == "context":
            url["User Needs"] = "ymmärrä"
        elif url["User Needs"].lower() == "emotion":
            url["User Needs"] = "tunne"
        elif url["User Needs"].lower() == "action":
            url["User Needs"] = "toimi"
        print(urls.index(url))
        print(url)
        article = get_article_apu360(url["Url"])
        print(article)
        if "errors" in article:
            print("Error: ", article["errors"])
            errors.append(url)
            continue
        else:
            # print(f"Article: {article}")
            articles.append(
                transform_to_content_request(article["data"]["article"], "A-lehti")
            )

    score = 0
    results = []

    for article in articles:
        # get the results from the LLM
        dict_result = await service.analyse_one((article), "user_need")

        print("RESULTS: ", dict_result)

        result_user_need = dict_result["drive"]

        if (
            result_user_need.lower()
            == urls[articles.index(article)]["User Needs"].lower()
        ):
            score += 1
        results.append(
            {
                "result": result_user_need,
                "correct": urls[articles.index(article)]["User Needs"],
            }
        )

    # Print the results
    print(f"Score: {score}/{len(articles)}")

    print("Results: ", results)
    print("Errors: ", errors)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_references_user_needs(async_client, service):
    # list out the correct answers
    scoring = 0
    answers = []
    results = []
    distance_list = []

    # test with each of the test data in Alehti_esimerkki_artikkeleita.json
    for article in test_data:
        # get the results from the LLM
        dict_result = await service.analyse_one(
            transform_to_content_request(article, "A-lehti"), "user_need"
        )

        print("RESULTS: ", dict_result)

        # get the evaluation data and add it to the answers
        answers.append(article["user needs"])

        # Get the most likely user need and compare to correct answer
        # user_need = max(article["user needs"]["scoring"], key=article["user needs"]["scoring"].get)
        user_need = article["user needs"]["main drive"]
        if user_need.lower() == "fact":
            user_need = "tiedä"
        elif user_need.lower() == "context":
            user_need = "ymmärrä"
        elif user_need.lower() == "emotion":
            user_need = "tunne"
        elif user_need.lower() == "action":
            user_need = "toimi"
        print("Correct user need:", user_need)
        result_user_need = dict_result["drive"]
        print("Result user need:", result_user_need)

        if result_user_need.lower() == user_need.lower():
            scoring += 1

        print("Correct specific needs:", article["user needs"]["specific needs"])
        print("Result specific needs:", dict_result["need"])

        # scoring for the distance between LLM answer and correct answer
        distance = math.sqrt(
            (dict_result["scoring"]["Tiedä"] - article["user needs"]["scoring"]["fact"])
            ** 2
            + (
                dict_result["scoring"]["Ymmärrä"]
                - article["user needs"]["scoring"]["context"]
            )
            ** 2
            + (
                dict_result["scoring"]["Tunne"]
                - article["user needs"]["scoring"]["emotion"]
            )
            ** 2
            + (
                dict_result["scoring"]["Toimi"]
                - article["user needs"]["scoring"]["action"]
            )
            ** 2
        )
        print(distance)

        results.append(
            {
                "user_need": result_user_need,
                "scoring": dict_result["scoring"],
                "specific_need": dict_result["need"],
            }
        )  # write down the results
        distance_list.append(distance)  # distance to correct answers

    avg_distance = sum(distance_list) / len(
        distance_list
    )  # write down the results for each model

    print(answers)  # print the answers for viewing

    print(avg_distance)  # print the average distance for viewing

    print(scoring, "/", len(test_data))  # print the scoring for viewing

    print(results)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_references_user_needs_keskisuomalainen(async_client, service):
    # Read the Excel file from assets folder
    excel_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "assets/user_needs_SavonSanomat_kaikki_tiedot.xlsx",
        )
    )
    dataframe = pd.read_excel(excel_path)

    print(dataframe)
    # Convert the dataframe to a dictionary with each article having its own dictionary
    # Use the top row as keys and values from each article row as values
    articles_data = []
    for index, row in dataframe.iterrows():
        article_dict = {}
        for column in dataframe.columns:
            article_dict[column] = row[column]
        articles_data.append(article_dict)

    # Print the total number of articles
    print(f"Total articles: {len(articles_data)}")
    print(articles_data)

    # Scoring variables
    scoring_main = 0
    scoring_sub = 0
    results = []

    # Test with each article in the Excel data
    for article in articles_data:
        for key, value in article.items():
            if isinstance(value, float) and math.isnan(value):
                article[key] = ""

        # Get the results from the LLM
        dict_result = await service.analyse_one(
            transform_to_content_request(article, "Keskisuomalainen"), "user_need"
        )

        print("RESULTS: ", dict_result)

        # Get the correct user need from the Excel data
        user_need = article.get("USER NEED -PÄÄMALLI", "")
        if user_need.lower() == "know":
            user_need = "tiedä"
        elif user_need.lower() == "understand":
            user_need = "ymmärrä"
        elif user_need.lower() == "feel":
            user_need = "tunne"
        elif user_need.lower() == "do":
            user_need = "toimi"

        print("Correct user need:", user_need)
        result_user_need = dict_result["drive"]
        print("Result user need:", result_user_need)

        # Check if the result matches the correct user need
        if result_user_need.lower() == user_need.lower():
            scoring_main += 1

        user_need_specific = article.get("USER NEEDS -ALAMALLI", "")
        if user_need_specific.lower() == "update me":
            user_need_specific = "Kerro mitä tapahtui"
        elif (
            user_need_specific.lower() == "give me perspective"
            or user_need_specific.lower() == "give me perspectice"
        ):
            user_need_specific = "Aseta mittasuhteisiin, anna näkökulmaa"
        elif user_need_specific.lower() == "inspire me":
            user_need_specific = "Inspiroi"
        elif user_need_specific.lower() == "connect me":
            user_need_specific = "Luo yhteyksiä muihin"
        elif user_need_specific.lower() == "help me":
            user_need_specific = "Anna neuvoja"
        elif user_need_specific.lower() == "educate me":
            user_need_specific = "Sivistä"
        elif user_need_specific.lower() == "divert me":
            user_need_specific = "Virkistä"
        elif user_need_specific.lower() == "update me/keep me engaged":
            user_need_specific = "Pidä minut ajan tasalla keskustelussa"

        print("Correct specific user need:", user_need_specific)
        result_user_need_specific = ""
        highest_specific_need = 0
        for drive, need in dict_result["detailed_scoring"].items():
            for specific_need, score in need.items():
                if score > highest_specific_need:
                    highest_specific_need = score
                    result_user_need_specific = specific_need
        print("Result user need:", result_user_need_specific)

        # Check if the result matches the correct user need
        if result_user_need_specific.lower() == user_need_specific.lower():
            scoring_sub += 1

        # Store the results
        results.append(
            {
                "user_need": result_user_need,
                "correct_user_need": user_need,
                "specific_user_need": result_user_need_specific,
                "correct_specific_user_need": user_need_specific,
            }
        )

    # Print the final score
    print(f"Score: {scoring_main}/{len(articles_data)}")
    print(f"Specific score: {scoring_sub}/{len(articles_data)}")

    # Print the detailed results
    print("Results:", results)
