import os
import random

import pandas as pd
import requests
import tabula

pdf_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../tests/assets/Baseline Report - A-lehdet User Needs.pdf",
    )
)


def get_article_apu360(url):
    # Find the position of the last slash in the URL
    last_slash_index = url.rfind("/")

    # Extract the desired segment by slicing the URL
    segment = url[last_slash_index + 1 :]

    # Define the GraphQL endpoint
    graphql_endpoint = "https://api-proxy.apu.fi/graphql"

    # Define your GraphQL query
    query_abridged = """
    query GetArticle($slug: Slug!) {
      article(slug: $slug) {
        id
        title
        body {
          plain,
          html,
          raw
        }
        publishedAt
      }
    }
    """

    query_full = """
    query GetArticle($slug: Slug!) {
      article(slug: $slug) {
        __typename
        type
        id
        slug
        title
        kicker
        body {
          plain
          html
          raw
        }
        restrictAccessBy
        readingTime
        audioUrl
        containsAudio
        publishedAt
        category {
          id
          title
        }
        brand {
          id
          name
          slug
        }
        partner {
          id
          name
        }
        image {
          id
          url
          width
          height
          frameright {
            crops {
              defId
              x
              y
              outWidth
              outHeight
              width
              height
            }
            metadataFormat
          }
        }
        coverVideo {
          url
        }
        metadata {
          commercialType
        }
        writers {
          __typename
          name
          slug
          image {
            id
            url
            width
            height
            frameright {
              crops {
                defId
                x
                y
                outWidth
                outHeight
                width
                height
              }
              metadataFormat
            }
          }
        }
      }
    }
    """

    # Define your variables
    variables = {"slug": segment}

    # Send the POST request
    response = requests.post(
        graphql_endpoint, json={"query": query_full, "variables": variables}
    )

    # Check the response
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"


def get_urls_alehti():
    # Extract tables from the PDF: Baseline report - A-lehdet User Needs
    tables = tabula.read_pdf(pdf_path, pages="all", lattice=True)
    # print(f"Found {len(tables)} tables in the PDF")

    # Process each table to ensure consistent columns before concatenation
    processed_tables = []
    for i, table in enumerate(tables):
        # Ensure table has the expected columns
        if len(table.columns) == 2:
            # Rename columns to standard names if needed
            if table.columns.tolist() != ["Url", "User Needs"]:
                table.columns = ["Url", "User Needs"]
            processed_tables.append(table)
        else:
            print(
                f"Table {i + 1} has unexpected column structure: {table.columns.tolist()}"
            )

    # Concatenate processed tables
    if processed_tables:
        combined_table = pd.concat(processed_tables, ignore_index=True)
        # print(f"Combined table has {len(combined_table)} rows and {len(combined_table.columns)} columns")

        # Clean the data - remove any rows with NaN in Url column
        combined_table = combined_table.dropna(subset=["Url"])
        # print(f"After cleaning, combined table has {len(combined_table)} rows")

        # Convert to list of dictionaries (cleaner format)
        result_list = combined_table.to_dict("records")

        # print(f"\nTotal entries: {len(result_list)}")
    else:
        print("No tables with the expected structure were found")

    return result_list


def get_n_random_article_urls(n):
    # Get the list of URLs from the PDF
    urls = get_urls_alehti()

    # Randomly select n URLs
    random_urls = random.sample(urls, n)

    return random_urls
