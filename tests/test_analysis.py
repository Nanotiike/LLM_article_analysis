import json
import math
import os
import sys

import pytest

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.utils.transformer_service import (
    transform_to_content_request,
)

# Get the absolute path to the evaluation_dataset.json file and the prompts.json file
test_data_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "assets/Keskisuomalainen_esimerkki_artikkeleita.json"
    )
)
evaluation_data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "assets/evaluation_dataset.json")
)

# Open and read the test file
with open(test_data_path, "r") as file:
    test_data = json.load(file)

# Open and read the evaluation_dataset.json file
with open(evaluation_data_path, "r") as file:
    evaluation_data = json.load(file)

key = "select *\r\nfrom article_data.articles a\r\nwhere count_chars >= 3000\r\nand \"source\" <> 'STT'\r\nand publish_date::date >= '2025-1-1'\r\nlimit 100"


# Test the get one task with the 'people' prompt
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_mentioned_people(async_client, service):
    list_result = await service.analyse_one(
        transform_to_content_request(test_data[key][0], "Keskisuomalainen"), "people"
    )
    eval = evaluation_data["article 1"]["people"]
    scoring = 0
    hallucinations = 0
    for person in list_result:
        if person.lower() in eval:
            scoring += 1
        else:
            hallucinations += 1
    assert scoring / len(eval) >= 0.8
    assert hallucinations == 0


# Test the get one task with the 'locations' prompt
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_mentioned_locations(async_client, service):
    list_result = await service.analyse_one(
        transform_to_content_request(test_data[key][1], "Keskisuomalainen"), "locations"
    )
    eval = evaluation_data["article 2"]["locations"]
    scoring = 0
    hallucinations = 0
    for person in list_result:
        if person.lower() in eval:
            scoring += 1
        else:
            hallucinations += 1
    print(list_result)
    assert scoring / len(eval) >= 0.8
    assert hallucinations == 0


# Test the get one task with the 'organisations' prompt
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_mentioned_organisations(async_client, service):
    list_result = await service.analyse_one(
        transform_to_content_request(test_data[key][5], "Keskisuomalainen"),
        "organisations",
    )
    eval = evaluation_data["article 6"]["organisations"]
    scoring = 0
    hallucinations = 0
    for organisation in list_result:
        if organisation.lower() in eval:
            scoring += 1
        else:
            hallucinations += 1
    print(list_result)
    assert scoring / len(eval) >= 0.8
    assert hallucinations == 0


# Test the get one task with the 'hyperlocation' prompt
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_article_hyperlocation(async_client, service):
    dict_result = await service.analyse_one(
        transform_to_content_request(test_data[key][0], "Keskisuomalainen"),
        "hyperlocation",
    )
    eval = evaluation_data["article 1"]["hyperlocation"]
    scoring = 0
    hallucination_amount = 0
    for dict_key, value in dict_result.items():
        if value.lower() == eval[dict_key]:
            scoring += 1
        else:
            hallucination_amount += 1
    assert scoring / len(eval) >= 0.8
    assert hallucination_amount == 0


# Test the get one task with the 'summary' prompt. Only tests that it outputs the correct format. JSON list with 3 strings
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_article_summary(async_client, service):
    list_result = await service.analyse_one(
        transform_to_content_request(test_data[key][3], "Keskisuomalainen"), "summary"
    )
    assert len(list_result) == 3
    assert isinstance(list_result, list)
    for item in list_result:
        assert isinstance(item, str)


# Test the get one task with the 'user_need' prompt. Only tests that it outputs the correct format.
# JSON dictionary with 3 keys, analysis which is a string, scoring which is a dictionary and need which is a list
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_article_user_need(async_client, service):
    dict_result = await service.analyse_one(
        transform_to_content_request(test_data[key][0], "Keskisuomalainen"), "user_need"
    )
    print(dict_result)

    assert isinstance(dict_result, dict)
    assert len(dict_result) == 4
    assert isinstance(dict_result["analysis"], str)
    assert isinstance(dict_result["scoring"], dict)
    assert isinstance(dict_result["detailed_scoring"], dict)

    distance = math.sqrt(
        (dict_result["scoring"]["Tiedä"] - 30) ** 2
        + (dict_result["scoring"]["Ymmärrä"] - 35) ** 2
        + (dict_result["scoring"]["Tunne"] - 25) ** 2
        + (dict_result["scoring"]["Toimi"] - 10) ** 2
    )
    print(distance)


# Test the get one task with the 'tone' prompt. Only tests that it outputs the correct format. JSON dictionary with generaltone, that has analysis and tone
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_article_tone(async_client, service):
    result = await service.analyse_one(
        transform_to_content_request(test_data[key][0], "Keskisuomalainen"),
        "tone",
    )
    print(result)
    assert isinstance(result, dict)
    keys = list(result.keys())
    for result_key in keys:
        assert "analysis" in result[result_key]
        assert "tone" in result[result_key]
        assert isinstance(result[result_key]["analysis"], str)
        assert isinstance(result[result_key]["tone"], str)


# Test the get one task with the 'theme and topic' prompt. Only tests that it outputs the correct format. JSON dictionary that has theme and topic
@pytest.mark.asyncio
@pytest.mark.fast
async def test_get_article_theme_and_topics(async_client, service):
    for i in range(10):
        result = await service.analyse_one(
            transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
            "theme_and_topics",
        )
        print(result)
        assert isinstance(result, dict)
        assert "theme" in result
        assert "topics" in result
        assert isinstance(result["theme"], str)
        assert isinstance(result["topics"], list)


# ============== Long tests ==============


models = [
    # "gpt-4o",
    # "gpt-4o-mini",
    # "gpt-4.1",
    # "o4-mini",
    # "claude-3-7-sonnet-20250219",
    # "gemini-2.0-flash",
    "o3",
    # "claude-opus-4-20250514",
    # "claude-sonnet-4-20250514",
    # "llama3.3:70b",
    # "gemma3:27b",
    # "deepseek-r1:32b",
]


# Run the test multiple times and check the avarage score tests with each of the models in the testing list
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_analysis_people(async_client, service, writer):
    # list out the correct answers
    answers = []

    results_per_model = {}  # dictionary to store the results for each model

    for model in models:
        service.change_model(model)  # change the model to the one in the testing list
        results = []
        scoring_list = []
        hallucinations = []

        # test with each of the test data in the evaluation_dataset
        for i in range(len(evaluation_data)):
            # get the results from the LLM
            list_result = await service.analyse_one(
                transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
                "people",
            )

            results.append(list_result)  # write down the results

            # get the evaluation data and add it to the answers
            eval = evaluation_data[f"article {i + 1}"]["people"]
            answers.append(eval)

            # scoring for how many the llm got correct, and hallucinations for if it hallucinated any names
            scoring = 0
            hallucination_amount = 0
            hallucinated_names = []

            for person in list_result:
                if person.lower() in eval:
                    scoring += 1
                else:
                    hallucinated_names.append(person)
                    hallucination_amount += 1

            hallucinations.append(
                {"amount": hallucination_amount, "names": hallucinated_names}
            )  # how many hallucinations
            if (
                len(eval) == 0 and len(list_result) == 0
            ):  # Checking for the edge case that there are no people in the article
                scoring_list.append({"precision": 1, "recall": 1, "f1-score": 1})
            else:
                precision = (
                    scoring / (scoring + hallucination_amount)
                    if scoring + hallucination_amount > 0
                    else 0
                )
                recall = scoring / len(eval) if len(eval) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if precision + recall > 0
                    else 0
                )
                scoring_list.append(
                    {"precision": precision, "recall": recall, "f1-score": f1_score}
                )  # precentage of correct answers

        averages = {
            "precision": sum(item["precision"] for item in scoring_list)
            / len(scoring_list),
            "recall": sum(item["recall"] for item in scoring_list) / len(scoring_list),
            "f1-score": sum(item["f1-score"] for item in scoring_list)
            / len(scoring_list),
        }  # average of the scores

        hallucinations_total = sum(item["amount"] for item in hallucinations)

        results_per_model[model] = {
            "results": results,
            "average scores": averages,
            "scoring": scoring_list,
            "hallucinations_total": hallucinations_total,
            "hallucinations": hallucinations,
        }  # write down the results for each model

    print(answers)  # print the answers for viewing

    print(results_per_model)  # print the results for each model for viewing

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "people")


# Run the test multiple times and check the avarage score tests with each of the models in the testing list
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_analysis_locations(async_client, service, writer):
    # list out the correct answers
    answers = []

    results_per_model = {}  # dictionary to store the results for each model

    for model in models:
        service.change_model(model)  # change the model to the one in the testing list
        results = []
        scoring_list = []
        hallucinations = []
        hallucinations_total = 0

        # test with each of the test data in the evaluation_dataset
        for i in range(len(evaluation_data)):
            # get the results from the LLM
            list_result = await service.analyse_one(
                transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
                "locations",
            )

            results.append(list_result)  # write down the results

            # get the evaluation data
            eval = evaluation_data[f"article {i + 1}"]["locations"]
            answers.append(eval)

            # scoring for how many the llm got correct, and hallucinations for if it hallucinated any names
            scoring = 0
            hallucination_amount = 0
            hallucinated_locations = []

            for location in list_result:
                if location.lower() in eval:
                    scoring += 1
                else:
                    hallucinated_locations.append(location)
                    hallucination_amount += 1

            hallucinations.append(
                {"amount": hallucination_amount, "locations": hallucinated_locations}
            )  # how many hallucinations
            hallucinations_total += hallucination_amount
            if (
                len(eval) == 0 and len(list_result) == 0
            ):  # Checking for the edge case that there are no people in the article
                scoring_list.append({"precision": 1, "recall": 1, "f1-score": 1})
            else:
                precision = (
                    scoring / (scoring + hallucination_amount)
                    if scoring + hallucination_amount > 0
                    else 0
                )
                recall = scoring / len(eval) if len(eval) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if precision + recall > 0
                    else 0
                )
                scoring_list.append(
                    {"precision": precision, "recall": recall, "f1-score": f1_score}
                )  # precentage of correct answers

        averages = {
            "precision": sum(item["precision"] for item in scoring_list)
            / len(scoring_list),
            "recall": sum(item["recall"] for item in scoring_list) / len(scoring_list),
            "f1-score": sum(item["f1-score"] for item in scoring_list)
            / len(scoring_list),
        }  # average of the scores

        hallucinations_total = sum(item["amount"] for item in hallucinations)

        results_per_model[model] = {
            "results": results,
            "average scores": averages,
            "scoring": scoring_list,
            "hallucinations_total": hallucinations_total,
            "hallucinations": hallucinations,
        }

    print(answers)  # print the answers for viewing

    print(results_per_model)  # print the results for each model for viewing

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "locations")


# Run the test multiple times and check the avarage score tests with each of the models in the testing list
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_analysis_organisations(async_client, service, writer):
    # get the answers from the evaluation data
    answers = []

    results_per_model = {}  # dictionary to store the results for each model

    for model in models:
        service.change_model(model)  # change the model to the one in the testing list
        results = []
        scoring_list = []
        hallucinations = []

        # test with each of the test data in the evaluation_dataset
        for i in range(len(evaluation_data)):
            # get the results from the LLM
            list_result = await service.analyse_one(
                transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
                "organisations",
            )

            results.append(list_result)  # write down the results

            # get the evaluation data
            eval = evaluation_data[f"article {i + 1}"]["organisations"]
            answers.append(eval)

            # scoring for how many the llm got correct, and hallucinations for if it hallucinated any names
            scoring = 0
            hallucination_amount = 0
            hallucinated_names = []

            for organisation in list_result:
                if organisation.lower() in eval:
                    scoring += 1
                else:
                    hallucinated_names.append(organisation)
                    hallucination_amount += 1

            hallucinations.append(
                {"amount": hallucination_amount, "names": hallucinated_names}
            )  # how many hallucinations
            if (
                len(eval) == 0 and len(list_result) == 0
            ):  # Checking for the edge case that there are no people in the article
                scoring_list.append({"precision": 1, "recall": 1, "f1-score": 1})
            else:
                precision = (
                    scoring / (scoring + hallucination_amount)
                    if scoring + hallucination_amount > 0
                    else 0
                )
                recall = scoring / len(eval) if len(eval) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if precision + recall > 0
                    else 0
                )
                scoring_list.append(
                    {"precision": precision, "recall": recall, "f1-score": f1_score}
                )  # precentage of correct answers

        averages = {
            "precision": sum(item["precision"] for item in scoring_list)
            / len(scoring_list),
            "recall": sum(item["recall"] for item in scoring_list) / len(scoring_list),
            "f1-score": sum(item["f1-score"] for item in scoring_list)
            / len(scoring_list),
        }  # average of the scores

        hallucinations_total = sum(item["amount"] for item in hallucinations)

        results_per_model[model] = {
            "results": results,
            "average scores": averages,
            "scoring": scoring_list,
            "hallucinations_total": hallucinations_total,
            "hallucinations": hallucinations,
        }  # write down the results for each model

    print(answers)  # print the answers for viewing

    print(results_per_model)  # print the results for each model for viewing

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "organisations")


# Run the test multiple times and check the avarage score tests with each of the models in the testing list
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_analysis_hyperlocations(async_client, service, writer):
    # list out the correct answers
    answers = []

    results_per_model = {}  # dictionary to store the results for each model

    for model in models:
        service.change_model(model)  # change the model to the one in the testing list
        results = []
        scoring_list = []
        hallucinations = []

        # test with each of the test data in the evaluation_dataset
        for i in range(len(evaluation_data)):
            # get the results from the LLM
            dict_result = await service.analyse_one(
                transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
                "hyperlocation",
            )

            results.append(dict_result)  # write down the results

            # get the evaluation data
            eval = evaluation_data[f"article {i + 1}"]["hyperlocation"]
            answers.append(eval)

            # scoring for how many the llm got correct, and hallucinations for if it hallucinated any names
            scoring = 0
            hallucination_amount = 0
            hallucinated_locations = {}

            for dict_key, value in dict_result.items():
                if value.lower() == eval[dict_key]:
                    scoring += 1
                elif value.lower() == "":
                    pass
                else:
                    hallucinated_locations[dict_key] = value
                    hallucination_amount += 1

            hallucinations.append(
                {"amount": hallucination_amount, "locations": hallucinated_locations}
            )
            precision = (
                scoring / (scoring + hallucination_amount)
                if scoring + hallucination_amount > 0
                else 0
            )
            recall = scoring / len(eval) if len(eval) > 0 else 0
            f1_score = (
                2 * (precision * recall) / (precision + recall)
                if precision + recall > 0
                else 0
            )
            scoring_list.append(
                {"precision": precision, "recall": recall, "f1-score": f1_score}
            )  # precentage of correct answers

        averages = {
            "precision": sum(item["precision"] for item in scoring_list)
            / len(scoring_list),
            "recall": sum(item["recall"] for item in scoring_list) / len(scoring_list),
            "f1-score": sum(item["f1-score"] for item in scoring_list)
            / len(scoring_list),
        }  # average of the scores

        hallucinations_total = sum(item["amount"] for item in hallucinations)

        results_per_model[model] = {
            "results": results,
            "average scores": averages,
            "scoring": scoring_list,
            "hallucinations_total": hallucinations_total,
            "hallucinations": hallucinations,
        }  # write down the results for each model

    print(answers)  # print the answers for viewing

    print(results_per_model)  # print the results for each model for viewing

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "hyperlocation")


# Run the test multiple times and check the avarage score tests with each of the models in the testing list
@pytest.mark.asyncio
# @pytest.mark.slow
async def test_full_analysis_theme_and_topics(async_client, service, writer):
    # get the answers from the evaluation data
    answers = []

    results_per_model = {}  # dictionary to store the results for each model

    for model in models:
        service.change_model(model)  # change the model to the one in the testing list
        results = []
        scoring_list = []
        hallucinations = []

        # test with each of the test data in the evaluation_dataset
        for i in range(len(evaluation_data)):
            # get the results from the LLM
            dict_result = await service.analyse_one(
                transform_to_content_request(test_data[key][i], "Keskisuomalainen"),
                "theme_and_topics",
            )

            results.append(dict_result)  # write down the results

            """result = {"theme": <theme>, "topics": [<list of topics]}"""

            # get the evaluation data
            eval = evaluation_data[f"article {i + 1}"]["theme_and_topics"]
            answers.append(eval)

            # scoring for how many the llm got correct, and hallucinations for if it hallucinated any names
            scoring = 0
            hallucination_amount = 0
            hallucinated_names = []

            hallucinations.append(
                {"amount": hallucination_amount, "names": hallucinated_names}
            )  # how many hallucinations
            if (
                len(eval) == 0 and len(dict_result) == 0
            ):  # Checking for the edge case that there are no people in the article
                scoring_list.append({"precision": 1, "recall": 1, "f1-score": 1})
            else:
                precision = (
                    scoring / (scoring + hallucination_amount)
                    if scoring + hallucination_amount > 0
                    else 0
                )
                recall = scoring / len(eval) if len(eval) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if precision + recall > 0
                    else 0
                )
                scoring_list.append(
                    {"precision": precision, "recall": recall, "f1-score": f1_score}
                )  # precentage of correct answers

        averages = {
            "precision": sum(item["precision"] for item in scoring_list)
            / len(scoring_list),
            "recall": sum(item["recall"] for item in scoring_list) / len(scoring_list),
            "f1-score": sum(item["f1-score"] for item in scoring_list)
            / len(scoring_list),
        }  # average of the scores

        hallucinations_total = sum(item["amount"] for item in hallucinations)

        results_per_model[model] = {
            "results": results,
            "average scores": averages,
            "scoring": scoring_list,
            "hallucinations_total": hallucinations_total,
            "hallucinations": hallucinations,
        }  # write down the results for each model

    print(answers)  # print the answers for viewing

    print(results_per_model)  # print the results for each model for viewing

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "theme_and_topics")
