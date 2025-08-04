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
criteria_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "assets/eval_criteria.json")
)
prompts_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../prompts.json")
)

# Open and read the test file
with open(test_data_path, "r") as file:
    test_data = json.load(file)

# Open and read the criteria for evaluation
with open(criteria_path, "r") as file:
    criteria = json.load(file)

# Open and read the prompts for evaluation
with open(prompts_path, "r") as file:
    prompts = json.load(file)

key = "select *\r\nfrom article_data.articles a\r\nwhere count_chars >= 3000\r\nand \"source\" <> 'STT'\r\nand publish_date::date >= '2025-1-1'\r\nlimit 100"

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


def print_scores_and_avarage(evaluations):
    for article, evaluation in evaluations.items():
        if article == "avarage scores":
            print("Avarage scores:")
            for dict_key in evaluation.keys():
                print(dict_key, evaluation[dict_key])
        else:
            print(article)
            print("")
            print(evaluation["evaluation"])
            print("")
            print(evaluation["scoring"])
            print("")


# G-eval for summary creation
@pytest.mark.asyncio
@pytest.mark.geval
async def test_summary(async_client, service, writer):
    results_per_model = {}

    for model in models:
        service.change_model(model)

        n = 30

        evaluations = {}

        for i in range(n):
            document = test_data[key][i]

            result = await service.analyse_one(
                transform_to_content_request(document, "Keskisuomalainen"),
                "summary",
            )

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
            {result}
            Evaluation Form (scores ONLY):
            {list(criteria["summary"].keys())}
            """

            evaluation = await basic_chat(Eval_prompt, 0, "gpt-4o")

            json_str = strip_openai_json(evaluation)

            result_dict = parse_json(json_str, evaluation)

            total = {}

            for criteria_key, values in result_dict.items():
                total[criteria_key] = 0
                for dict_key, value in values.items():
                    total[criteria_key] += int(dict_key) * value

            evaluations[f"Article {i + 1}"] = {
                "evaluation": result_dict,
                "scoring": total,
            }

        avg = {key: 0 for key in evaluations["Article 1"]["scoring"].keys()}

        for article, evaluation in evaluations.items():
            for dict_key in evaluation["scoring"].keys():
                avg[dict_key] += evaluation["scoring"][dict_key]

        for dict_key in avg.keys():
            avg[dict_key] = avg[dict_key] / len(evaluations)

        evaluations["average scores"] = avg

        # print_scores_and_avarage(evaluations)

        results_per_model[model] = evaluations

    print(results_per_model)

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "summary")


# G-eval for user needs analysis
@pytest.mark.asyncio
@pytest.mark.geval
async def test_user_needs_analysis(async_client, service, writer):
    results_per_model = {}

    for model in models:
        service.change_model(model)

        n = 30

        evaluations = {}

        for i in range(n):
            document = test_data[key][i]

            result = await service.analyse_one(
                transform_to_content_request(document, "Keskisuomalainen"), "user_need"
            )

            Eval_prompt = f"""You will be given one analysis written
            of the user needs of an article. Your task is to rate the analysis on {len(criteria["user_need"])}
            metrics. Please make sure you read and understand these instructions carefully. Please
            keep this document open while reviewing, and refer to it as needed.

            Evaluation Criteria:
            {criteria["user_need"]}

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
            {prompts["prompts"]["user_need"]}
            Analysis:
            {result}
            Evaluation Form (scores ONLY):
            {list(criteria["user_need"].keys())}
            """

            evaluation = await basic_chat(Eval_prompt, 0, "gpt-4o")

            json_str = strip_openai_json(evaluation)

            result_dict = parse_json(json_str, evaluation)

            total = {}

            for criteria_key, values in result_dict.items():
                total[criteria_key] = 0
                for dict_key, value in values.items():
                    total[criteria_key] += int(dict_key) * value

            evaluations[f"Article {i + 1}"] = {
                "evaluation": result_dict,
                "scoring": total,
            }

        avg = {key: 0 for key in evaluations["Article 1"]["scoring"].keys()}

        for article, evaluation in evaluations.items():
            for dict_key in evaluation["scoring"].keys():
                avg[dict_key] += evaluation["scoring"][dict_key]

        for dict_key in avg.keys():
            avg[dict_key] = avg[dict_key] / len(evaluations)

        evaluations["average scores"] = avg

        results_per_model[model] = evaluations

        # print_scores_and_avarage(evaluations)

    print(results_per_model)

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "user_needs")


# G-eval for tone analysis
@pytest.mark.asyncio
@pytest.mark.geval
async def test_tone_analysis(async_client, service, writer):
    results_per_model = {}

    for model in models:
        service.change_model(model)

        n = 30

        evaluations = {}

        for i in range(n):
            document = test_data[key][i]

            result = await service.analyse_one(
                transform_to_content_request(document, "Keskisuomalainen"), "tone"
            )

            Eval_prompt = f"""You will be given one analysis written
            of the tone of an article. Your task is to rate the analysis on {len(criteria["tone"])}
            metrics. Please make sure you read and understand these instructions carefully. Please
            keep this document open while reviewing, and refer to it as needed.

            Evaluation Criteria:
            {criteria["tone"]}

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
            {prompts["prompts"]["tone"]}
            Analysis:
            {result}
            Evaluation Form (scores ONLY):
            {list(criteria["tone"].keys())}
            """

            evaluation = await basic_chat(Eval_prompt, 0, "gpt-4o")

            json_str = strip_openai_json(evaluation)

            result_dict = parse_json(json_str, evaluation)

            total = {}

            for criteria_key, values in result_dict.items():
                total[criteria_key] = 0
                for dict_key, value in values.items():
                    total[criteria_key] += int(dict_key) * value

            evaluations[f"Article {i + 1}"] = {
                "evaluation": result_dict,
                "scoring": total,
            }

        avg = {key: 0 for key in evaluations["Article 1"]["scoring"].keys()}

        for article, evaluation in evaluations.items():
            for dict_key in evaluation["scoring"].keys():
                avg[dict_key] += evaluation["scoring"][dict_key]

        for dict_key in avg.keys():
            avg[dict_key] = avg[dict_key] / len(evaluations)

        evaluations["average scores"] = avg

        results_per_model[model] = evaluations

        # print_scores_and_avarage(evaluations)

    print(results_per_model)

    writer.open_worksheet(results_per_model, "tone")

# G-eval for theme and topics
@pytest.mark.asyncio
@pytest.mark.geval
async def test_theme_and_topics(async_client, service, writer):
    results_per_model = {}

    for model in models:
        service.change_model(model)

        n = 30

        evaluations = {}

        for i in range(n):
            document = test_data[key][i]

            result = await service.analyse_one(
                transform_to_content_request(document, "Keskisuomalainen"),
                "theme_and_topics",
            )

            Eval_prompt = f"""You will be given a theme and a list of topics written
            for a news article. Your task is to rate the theme and the topics on {len(criteria["theme_and_topics"])}
            metrics. Please make sure you read and understand these instructions carefully. Please
            keep this document open while reviewing, and refer to it as needed.

            Evaluation Criteria:
            {criteria["theme_and_topics"]}

            Evaluation Steps:
            1. Read the news article carefully and
            identify the main topic and key points.
            2. Read the given theme and compare it to
            the news article. Check if matches closesly to the identified theme.
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
            {prompts["prompts"]["theme_and_topics"]}
            Summary:
            {result}
            Evaluation Form (scores ONLY):
            {list(criteria["theme_and_topics"].keys())}
            """

            evaluation = await basic_chat(Eval_prompt, 0, "gpt-4o")

            json_str = strip_openai_json(evaluation)

            result_dict = parse_json(json_str, evaluation)

            total = {}

            for criteria_key, values in result_dict.items():
                total[criteria_key] = 0
                for dict_key, value in values.items():
                    total[criteria_key] += int(dict_key) * value

            evaluations[f"Article {i + 1}"] = {
                "evaluation": result_dict,
                "scoring": total,
            }

        avg = {key: 0 for key in evaluations["Article 1"]["scoring"].keys()}

        for article, evaluation in evaluations.items():
            for dict_key in evaluation["scoring"].keys():
                avg[dict_key] += evaluation["scoring"][dict_key]

        for dict_key in avg.keys():
            avg[dict_key] = avg[dict_key] / len(evaluations)

        evaluations["average scores"] = avg

        # print_scores_and_avarage(evaluations)

        results_per_model[model] = evaluations

    print(results_per_model)

    if os.getenv("EXCEL_PATH") != "":
        writer.open_worksheet(results_per_model, "theme_and_topics")
