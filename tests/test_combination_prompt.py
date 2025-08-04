import json
import os
import sys

import pytest

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.service.json_service import (
    parse_json,
    strip_openai_json,
)
from backend_analytics.analytics.service.llm_service import basic_chat
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
criteria_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "assets/eval_criteria.json")
)
prompts_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../prompts.json")
)

# Open and read the test file
with open(test_data_path, "r") as file:
    test_data = json.load(file)

# Open and read the evaluation_dataset.json file
with open(evaluation_data_path, "r") as file:
    evaluation_data = json.load(file)

# Open and read the criteria for evaluation
with open(criteria_path, "r") as file:
    criteria = json.load(file)

# Open and read the prompts for evaluation
with open(prompts_path, "r") as file:
    prompts = json.load(file)

key = "select *\r\nfrom article_data.articles a\r\nwhere count_chars >= 3000\r\nand \"source\" <> 'STT'\r\nand publish_date::date >= '2025-1-1'\r\nlimit 100"


# Test the get one task with the 'people' prompt
@pytest.mark.asyncio
async def test_combination_prompt(async_client, service):
    full_result = await service.combine_prompts(
        transform_to_content_request(test_data[key][1], "Keskisuomalainen")
    )
    print(full_result)

    print("-----------------------------")

    full_result_2 = await service.analyse_all(
        transform_to_content_request(test_data[key][1], "Keskisuomalainen")
    )
    print(full_result_2)


@pytest.mark.asyncio
async def test_combination_prompt_long(async_client, service):
    results = {}
    scoring_list = {
        "people": [],
        "locations": [],
        "organisations": [],
        "hyperlocation": [],
        "summary": [],
        "user_need": [],
        "tone": [],
    }
    hallucinations = {
        "people": [],
        "locations": [],
        "organisations": [],
        "hyperlocation": [],
    }

    for i in range(10):
        document = test_data[key][i]

        full_result = await service.combine_prompts(
            transform_to_content_request(document, "Keskisuomalainen")
        )
        print(full_result)

        results[f"Article {i + 1}"] = full_result

        eval = evaluation_data[f"article {i + 1}"]

        for task in full_result.keys():
            if task == "people" or task == "locations" or task == "organisations":
                scoring = 0
                hallucination_amount = 0
                hallucinated_items = []

                for item in full_result[task]:
                    if item.lower() in eval[task]:
                        scoring += 1
                    else:
                        hallucinated_items.append(item)
                        hallucination_amount += 1

                hallucinations[task].append(
                    {"amount": hallucination_amount, "items": hallucinated_items}
                )  # how many hallucinations
                if (
                    len(eval) == 0 and len(full_result[task]) == 0
                ):  # Checking for the edge case that there are no people in the article
                    scoring_list[task].append(
                        {"precision": 1, "recall": 1, "f1-score": 1}
                    )
                else:
                    precision = (
                        scoring / (scoring + hallucination_amount)
                        if scoring + hallucination_amount > 0
                        else 0
                    )
                    recall = scoring / len(eval[task]) if len(eval[task]) > 0 else 0
                    f1_score = (
                        2 * (precision * recall) / (precision + recall)
                        if precision + recall > 0
                        else 0
                    )
                    scoring_list[task].append(
                        {"precision": precision, "recall": recall, "f1-score": f1_score}
                    )

            elif task == "hyperlocation":
                scoring = 0
                hallucination_amount = 0
                hallucinated_locations = {}

                for dict_key, value in full_result[task].items():
                    if value.lower() == eval[task][dict_key]:
                        scoring += 1
                    elif value.lower() == "":
                        pass
                    else:
                        hallucinated_locations[dict_key] = value
                        hallucination_amount += 1

                hallucinations[task].append(
                    {
                        "amount": hallucination_amount,
                        "locations": hallucinated_locations,
                    }
                )
                precision = (
                    scoring / (scoring + hallucination_amount)
                    if scoring + hallucination_amount > 0
                    else 0
                )
                recall = scoring / len(eval[task]) if len(eval[task]) > 0 else 0
                f1_score = (
                    2 * (precision * recall) / (precision + recall)
                    if precision + recall > 0
                    else 0
                )
                scoring_list[task].append(
                    {"precision": precision, "recall": recall, "f1-score": f1_score}
                )  # precentage of correct answers

            elif task == "user_need" or task == "tone" or task == "summary":
                if task == "summary":
                    Eval_prompt = f"""You will be given one summary written
                    for a news article. Your task is to rate the summary on {len(criteria["summary"])}
                    metrics. Please make sure you read and understand these instructions carefully. Please
                    keep this document open while reviewing, and refer to it as needed.

                    Evaluation Criteria:
                    {criteria["summary"]}

                    Evaluation Steps:
                    1. Read the news article carefully and
                    identify the main topic and key points.
                    2. Read the summary and compare it to
                    the news article. Check if the summary
                    covers the main topic and key points of
                    the news article, and if it presents them
                    in a clear and logical order.
                    3. For each criteria evaluate the probability
                    for each score of 1 to 5, 
                    assign a probability of 0 to 1 to that score.
                    Give all scores and their probabilities
                    for all criteria as a JSON dictionary 
                    in the format of:
                    {{Criteria: {{1:p(1), 2:p(2), 3:p(3), 4:p(4), 5:p(5)}},
                    ...
                    }}
                    4. Ensure that your evaluation is thorough, fair, 
                    and based solely on the input text and LLM output provided. 
                    Do not make assumptions about information not present in the given text.

                    Source Text:
                    {document}
                    Task prompt:
                    {prompts["prompts"]["summary"]}
                    Summary:
                    {full_result["summary"]}
                    Evaluation Form (scores ONLY):
                    {list(criteria["summary"].keys())}
                    """
                else:
                    Eval_prompt = f"""You will be given one analysis written
                    of the user needs of an article. Your task is to rate the analysis on {len(criteria[task])}
                    metrics. Please make sure you read and understand these instructions carefully. Please
                    keep this document open while reviewing, and refer to it as needed.

                    Evaluation Criteria:
                    {criteria[task]}

                    Evaluation Steps:
                    1. Read the news article carefully and
                    identify the main topic and key points.
                    2. Read the analysis and compare it to
                    the news article. Check if the analysis
                    covers the main topic and key points of
                    the news article, and if the user needs
                    presented are relevant and accurate to 
                    the main topics and key points discussed
                    in the article.
                    3. For each criteria evaluate the probability
                    for each score of 1 to 5, 
                    assign a probability of 0 to 1 to that score.
                    Give all scores and their probabilities
                    for all criteria as a JSON dictionary 
                    in the format of:
                    {{Criteria: {{1:p(1), 2:p(2), 3:p(3), 4:p(4), 5:p(5)}},
                    ...
                    }}
                    4. Ensure that your evaluation is thorough, fair, 
                    and based solely on the input text and LLM output provided. 
                    Do not make assumptions about information not present in the given text.

                    Source Text:
                    {document}
                    Task prompt:
                    {prompts["prompts"][task]}
                    Analysis:
                    {full_result[task]}
                    Evaluation Form (scores ONLY):
                    {list(criteria[task].keys())}
                    """

                evaluation = await basic_chat(Eval_prompt, 0)

                json_str = strip_openai_json(evaluation)

                result_dict = parse_json(json_str, evaluation)

                total = {}

                for criteria_key, values in result_dict.items():
                    total[criteria_key] = 0
                    for dict_key, value in values.items():
                        total[criteria_key] += int(dict_key) * value

                scoring_list[task].append({"evaluation": result_dict, "scoring": total})

    # print("results: ",results,"\n\n")
    print("scoring_list: ", scoring_list, "\n\n")
    print("hallucinations: ", hallucinations, "\n\n")

    average_scoring = {
        "people": {},
        "locations": {},
        "organisations": {},
        "hyperlocation": {},
        "summary": {},
        "user_need": {},
        "tone": {},
    }

    for prompt in average_scoring.keys():
        if (
            prompt == "people"
            or prompt == "locations"
            or prompt == "organisations"
            or prompt == "hyperlocation"
        ):
            averages = {
                "precision": sum(item["precision"] for item in scoring_list[prompt])
                / len(scoring_list[prompt]),
                "recall": sum(item["recall"] for item in scoring_list[prompt])
                / len(scoring_list[prompt]),
                "f1-score": sum(item["f1-score"] for item in scoring_list[prompt])
                / len(scoring_list[prompt]),
            }
        else:
            averages = {k: 0 for k in scoring_list[prompt][0]["scoring"].keys()}

            for evaluation in scoring_list[prompt]:
                for dict_key in evaluation["scoring"].keys():
                    averages[dict_key] += evaluation["scoring"][dict_key]

            for dict_key in averages.keys():
                averages[dict_key] = averages[dict_key] / len(scoring_list[prompt])

        average_scoring[prompt] = averages

    print(average_scoring)
