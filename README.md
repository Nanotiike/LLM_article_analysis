# Analytics for the Archive Database
### By Harri Gävert

Folder for the analytics of the articles for the Archive database. 

## Running with Docker

To run the analytics service with Docker, you need to have [Docker](https://www.docker.com/products/docker-desktop/) installed on your machine. Run the following command in the root of the repository to build and run the Docker image:
```shell
docker build -t ark-backend-analytics:latest -f backend_analytics/Dockerfile . 
```
After that, you can run a container from the image with the following command:
```shell
docker run -it -p 8000:8000 ark-backend-analytics
```

__Note that the build context needs to be the root of the repository, since the shared library needs to be included as well. The Rest of the setup is handled by the Dockerfile.__

## Running with Poetry

To run the analytics service with Poetry, you need to have [Poetry](https://python-poetry.org/docs/#installation) installed on your machine. 

You need to have set up the following environmental variables in .env:
```
AZURE_OPENAI_CHAT_ENDPOINT = "your_azure_endpoint"

AZURE_OPENAI_API_KEY = "your_azure_api_key"
```
Run the following command inside this folder to install the dependencies:
```shell
source .venv/bin/activate
poetry install --no-root
poetry run uvicorn analytics.main:app --host 0.0.0.0 --port 8000 --reload
```

## Whats in the folder currently:
```
backend_analytics
    |   
    +----> /notebooks (the initial notebooks used for prompt development)
    |
    +--+-> /analytics (the actual code)
    |  +---> main.py (putting it all together)
    |  +---> app_init.py (initialising the FastApi)
    |  +---> config.py (settings for the FastApi)
    |  +---> custom_logging.py (logger)
    |  +---> errors.py (error handling)
    |  |
    |  +-+-> /api
    |  | +---> analysis_router.py (api endpoint)
    |  |
    |  +-+-> /service
    |  | +---> llm_service.py (function to call the LLM)
    |  | +---> analysis_service.py (uses the prompts to call LLM_fun)
    |  | +---> json_service.py (functions to transform LLM output into json)
    |  |
    |  +-+-> /utils
    |  | +---> transformer_service.py (transforms articles to the class format)
    |  | +---> articles_service.py (get articles from A-Lehti api)
    |  | +---> excel_writer.py (used for writing the results of longer tests into a single excel file for better analysis)
    |  |
    |  +-+-> /middleware (the middlewares used in the api)
    |
    +--+-> /tests (testing for the code and prompts)
    |  +---> conftest.py (for configuring the different tests)
    |  +---> test_LLM.py (basic testing for the LLM call)
    |  +---> test_analysis.py (testing for the analysis functions)
    |  +---> test_analysis_geval.py (testing based on the g-eval framework)
    |  +---> test_analyse_endpoint.py (tests the analyse endpoint that it works)
    |  +---> test_analyse_endpoint_with_dataset.py (tests the analyse endpoint with actual data) 
    |  +---> test_user_needs_reference.py (tests user needs based on data from A-Lehti)
    |  |
    |  +-+-> /assets (assets needed for testing)
    |  | +---> example_api_upload.json (can be used to test the api)
    |  | +---> Keskisuomalainen_esimerkki_artikkeleita.json (example articles from Keskisuomalainen)
    |  | +---> evaluation_dataset.json (handpicked answers for 10 example articles from the above file)
    |  | +---> eval_criteria.json (criteria for the g-eval framework)
    |  | +---> Alehti_esimerkki_artikkeleita.json (example articles from A-Lehti)
    |  | +---> Baseline Report - A-lehder User Needs.pdf (analysis of user needs for A-Lehti articles done by Smartocto)
    |  |
    |  +-+-> /logs (holds the logs from the tests)
    |    +---> test_results.log (the last test results written out, if called with tee)
    |
    +---> prompts.json (has the prompts for the analysis)
    +---> pytest.ini (pytest configurations)
    +---> pyproject.toml (project configurations)
    +---> Dockerfile (docker configurations)
    +---> poetry.lock (packages)
    +---> README.md (This file)
```

### Prompts

The prompts for the analysis are all located in the prompts.json file. The prompts can be adjusted to match the needs of individual mediahouses. To adjust the prompts, simply adjust the text for the specific prompt. You should avoid changing the end of the prompt that specifies how the prompt will output its results, as changing that would often require changing the analysis schema in backend_shared. Some prompts are also partially split. user needs, tone, and themes have a list of options that they use for the prompt. These lists can be changed as long as the general sturcture isn't. So for user needs, base needs can be added or removed and their descriptions can be changed. Same for the more specific needs. For tone, multiple options can be added as a dictionary with the possible options as the keys and the descriptions for the options as values, following the example with the "yleissävy" tone. And finally themes are a list that is used when the theme of an article is analysed, and can be freely added or removed from. 

### FastAPI

There is a rest api made with FastAPI that can take in an article in the format of the class in ingestion_schema.py, and it will run all analysis on the article before returning results in JSON format.

The following endpoint is for analysing the articles: http://localhost:8000/analyse

### Testing

Testing is done with pytest

The prompts are tested against the evaluation_dataset.json, which has the handpicked answers to the first 10 articles in the Keskisuomalainen_esimerkki_artikkeleita.json file given for testing.

There are four types of tests. Those marked with "fast" just test the basic functionality of the prompt, calling it against a single article. Those marked with "slow" test the prompts much more comprehensively. The test the prompt with multiple models and against 10 articles, checing for how well they do and whether they hallucinate. There is also tests for the user needs prompt, which use articles from A-Lehti. Those marked with "api" test the api endpoint. And those marked with "geval" use the g-eval framework to test more subjective outputs. They use the eval_criteria.json for the criteria for evaluation.

The g-eval framework is base on the paper: [G-EVAL: NLG Evaluation using GPT-4 with Better Human Alignment](https://aclanthology.org/2023.emnlp-main.153.pdf)

by adding "-m fast", "-m slow", "-m api", or "-m geval" to the pytest command you can choose which type of test to run.

by adding "| tee tests/test_results.log" you can log the results in a file to view later. Only contains the latest results. The path depends on where you run the tests from. This assumes you run them from analytics directory.

The API can be tested manually with the example_api_upload.json file by giving it to curl with the following command.
```
curl -X POST http://localhost:8000/analyse -H "Content-Type: application/json" --data @tests/assets/example_api_upload.json
```
