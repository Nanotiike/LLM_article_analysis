import asyncio
import json
import os
import sys

# Add project root to path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.service.analysis_service import AnalysisService
from backend_analytics.analytics.service.llm_service import basic_chat
from backend_analytics.analytics.utils.transformer_service import (
    transform_to_content_request,
)


async def analyze_article(article, service, article_number):
    """
    Analyze a single article using the analysis service.

    Args:
        article (dict): The article to analyze
        service (AnalysisService): The analysis service instance
        article_number (int): The article number for identification

    Returns:
        dict: The analysis results in the evaluation dataset format
    """
    print(f"Analyzing article {article_number}...")

    # Transform the article to a ContentRequest object
    content_request = transform_to_content_request(article, "Keskisuomalainen")

    # Analyze people, locations, organizations, and hyperlocation
    people_result = await service.analyse_one(content_request, "people")
    locations_result = await service.analyse_one(content_request, "locations")
    organisations_result = await service.analyse_one(content_request, "organisations")
    hyperlocation_result = await service.analyse_one(content_request, "hyperlocation")

    # Format the results in the same structure as the evaluation dataset
    analysis_result = {
        "people": people_result,
        "locations": locations_result,
        "organisations": organisations_result,
        "hyperlocation": hyperlocation_result,
    }

    return analysis_result


async def verify_analysis(
    article, analysis_result, article_number, model="llama3.3:70b"
):
    """
    Verify the analysis results using LLM service.

    Args:
        article (dict): The original article
        analysis_result (dict): The analysis results
        article_number (int): The article number for identification
        model (str): The model to use for verification

    Returns:
        dict: The verified analysis results
    """
    print(f"Verifying analysis for article {article_number} using model {model}...")

    # Create a prompt for the LLM to verify the analysis
    prompt = f"""
    I have analyzed an article and extracted the following information:
    
    People mentioned: {analysis_result["people"]}
    Locations mentioned: {analysis_result["locations"]}
    Organizations mentioned: {analysis_result["organisations"]}
    Hyperlocation: {analysis_result["hyperlocation"]}
    
    Here is the article:
    Title: {article["title"]}
    Lead: {article["lead"]}
    Body: {article["body"]}
    
    Please verify if the extracted information is correct and complete. If there are any errors or missing information, please provide the corrected lists.
    
    Return your response in the following JSON format:
    {{
        "people": [list of people mentioned in the article],
        "locations": [list of locations mentioned in the article],
        "organisations": [list of organizations mentioned in the article],
        "hyperlocation": {{
            "country": "country name",
            "city": "city name",
            "neighborhood": "neighborhood name"
        }}
    }}
    """

    # Use the LLM service to verify the analysis
    verification_result = await basic_chat(prompt, temperature=0, model=model)

    # Extract the JSON portion from the response
    try:
        # Find the start and end of the JSON object
        start_idx = verification_result.find("{")
        end_idx = verification_result.rfind("}") + 1

        if start_idx != -1 and end_idx != -1:
            json_str = verification_result[start_idx:end_idx]
            verified_result = json.loads(json_str)
            return verified_result
        else:
            print(
                f"Warning: Could not extract JSON from verification result for article {article_number}"
            )
            return analysis_result
    except json.JSONDecodeError:
        print(
            f"Warning: Could not parse verification result as JSON for article {article_number}"
        )
        return analysis_result


async def main(start_index=12, num_articles=18, model="llama3.3:70b"):
    """
    Main function to analyze articles and update the evaluation dataset.

    Args:
        start_index (int): Starting index for article analysis (0-based, default: 12)
        num_articles (int): Number of articles to analyze (default: 18)
        model (str): Model to use for analysis (default: llama3.3:70b)
    """
    # Load the articles from the JSON file
    articles_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../tests/assets/Keskisuomalainen_esimerkki_artikkeleita.json",
        )
    )

    with open(articles_path, "r") as file:
        articles_data = json.load(file)

    # Load the existing evaluation dataset
    evaluation_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../tests/assets/evaluation_dataset.json"
        )
    )

    with open(evaluation_path, "r") as file:
        evaluation_data = json.load(file)

    # Initialize the analysis service
    service = AnalysisService(model=model)

    # Get the key for the articles
    key = list(articles_data.keys())[0]

    print(
        f"Starting analysis of {num_articles} articles from index {start_index} using model {model}"
    )

    # Analyze the next 18 articles
    for i in range(start_index, start_index + num_articles):
        if i >= len(articles_data[key]):
            print(
                f"Warning: Not enough articles in the dataset. Stopping at article {i}."
            )
            break

        article = articles_data[key][i]
        article_number = i + 1

        # Analyze the article
        analysis_result = await analyze_article(article, service, article_number)

        # Verify the analysis
        verified_result = await verify_analysis(
            article, analysis_result, article_number, model=model
        )

        # Add the results to the evaluation dataset
        evaluation_data[f"article {article_number}"] = verified_result

        # Save the updated evaluation dataset after each article (in case of interruption)
        with open(evaluation_path, "w") as file:
            json.dump(evaluation_data, file, indent=4)

        print(f"Article {article_number} analysis completed and saved.")

    print(f"Analysis completed for {num_articles} articles.")


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Analyze articles and update the evaluation dataset."
    )
    parser.add_argument(
        "--start",
        type=int,
        default=12,
        help="Starting index for article analysis (0-based, default: 12)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=18,
        help="Number of articles to analyze (default: 18)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.3:70b",
        help="Model to use for analysis (default: llama3.3:70b)",
    )

    args = parser.parse_args()

    # Run the analysis
    asyncio.run(main(start_index=args.start, num_articles=args.count, model=args.model))
