import json
import os

from analytics.service.json_service import parse_json, strip_openai_json
from analytics.service.llm_service import basic_chat


class AnalysisService:
    def __init__(self, model: str):
        self.temperatures = {
            "people": 0,
            "locations": 0,
            "organisations": 0,
            "summary": 0.5,
            "hyperlocation": 0,
            "user_need": 0.3,
            "tone": 0,
            "theme_and_topics": 0,
        }
        self.themes = self.load_data("../../prompts.json")["themes"]
        self.prompts = self.load_data("../../prompts.json")["prompts"]
        self.user_needs = self.load_data("../../prompts.json")["user_needs"]
        self.tone = self.load_data("../../prompts.json")["tone"]
        self.model = model

    # Load data from a file
    def load_data(self, filename):
        # Try to load from relative path first
        try:
            file_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), filename)
            )
            with open(file_path, "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            # If relative path fails, try absolute path
            try:
                project_root = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../../..")
                )
                file_path = os.path.join(
                    project_root, "backend_analytics", "prompts.json"
                )
                with open(file_path, "r") as file:
                    data = json.load(file)
                return data
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Could not find prompts.json file at {filename} or at {file_path}"
                )

    # Change the model in use for the service
    def change_model(self, model):
        self.model = model

    # Provides context for the LLM. This includes currently only the article that is given for the prompt
    def context(self, data):
        cleaned_data = {
            "title": data.title,
            "kicker": data.kicker,
            "ingress": data.ingress,
            "body": data.body.split("Lue myös:")[0].strip(),
        }
        return f'Artikkeli: "{cleaned_data}".\n\n'

    # Provides the prompts for the LLM. This includes currently only the article that is given for the prompt
    def build_prompt(self, article, prompt_name):
        if prompt_name == "theme":
            return f"{self.context(article)} {self.prompts['theme_and_topics']['theme']}\n\n Teemat: {self.themes}."
        elif prompt_name == "topics":
            return (
                f"{self.context(article)} {self.prompts['theme_and_topics']['topics']}"
            )
        elif prompt_name == "user_need":
            return f"{self.context(article)} {self.prompts['user_need']}\n\n Käyttäjätarpeet: {self.user_needs}."
        elif prompt_name == "tone":
            return f"{self.context(article)} {self.prompts['tone']}\n\n Sävyt: {self.tone}."
        else:
            return f"{self.context(article)} {self.prompts[prompt_name]}"

    # Analyses one aspect in the article, based on the prompt. Returns json.
    async def analyse_one(self, article, prompt_name, round=1):
        if prompt_name == "theme_and_topics":
            theme_prompt = self.build_prompt(article, "theme")
            message_theme = await basic_chat(
                theme_prompt,
                temperature=self.temperatures[prompt_name],
                model=self.model,
            )
            topic_prompt = self.build_prompt(article, "topics")
            message_topic = await basic_chat(
                topic_prompt,
                temperature=self.temperatures[prompt_name],
                model=self.model,
            )

            # Extract the JSON portion of the response
            json_str = strip_openai_json(message_topic)

            json_full = parse_json(json_str, message_topic)

            if type(json_full) == dict and "error" in json_full.keys() and round <= 3:
                return self.analyse_one(article, prompt_name, round=round + 1)
            else:
                return {
                    "theme": message_theme,
                    "topics": json_full,
                }
        else:
            full_prompt = self.build_prompt(article, prompt_name)
            message = await basic_chat(
                full_prompt,
                temperature=self.temperatures[prompt_name],
                model=self.model,
            )

            # Extract the JSON portion of the response
            json_str = strip_openai_json(message)

            # Parse the JSON string into a Python format
            json_full = parse_json(json_str, message)

            if type(json_full) == dict and "error" in json_full.keys() and round <= 3:
                return self.analyse_one(article, prompt_name, round=round + 1)
            else:
                return json_full

    # Analyses all aspects in the article. Returns json with the answers to all tasks.
    async def analyse_all(self, article):
        results = {}

        # Go through all prompts one by one and store the results.
        for prompt_name in self.prompts.keys():
            result = await self.analyse_one(article, prompt_name)
            results[prompt_name] = result

        return results

    # Returns the prompts for the article
    def get_prompts(self, article):
        prompts = {}
        for prompt_name in self.prompts.keys():
            if prompt_name == "theme_and_topics":
                prompts["theme"] = self.build_prompt(article, "theme")
                prompts["topics"] = self.build_prompt(article, "topics")
            else:
                prompts[prompt_name] = self.build_prompt(article, prompt_name)
        return prompts

    # Combines the prompts together to mkae less LLM calls during analysis
    async def combine_prompts(self, article):
        prompt = "Tehtävänäsi on analysoida artikkeli usealla eri tavalla, ja poimia tietoa artikkelista tehtävän mukaan. Jokaisen tehtävän kohdalla suorita se täysin ennen kuin siirryt seuraavaan. Älä siirry seuraavaan tehtävään ennen kuin nykyinen tehtävä on täysin valmis. Pidä artikkeli aina auki ja referoi siihen tarvittaessa. Tulosta JSON-tiedosto seuraavassa muodossa: {tehtävän nimi: [tehtävä 1:n tulos], tehtävän nimi: [tehtävä 2:n tulos], tehtävän nimi: [tehtävä 3:n tulos], ...}.\n\n"
        prompt += f"{self.context(article)}"
        for key in self.prompts.keys():
            if key == "theme_and_topics":
                prompt += f"\n\nTehtävä Theme: {self.prompts[key]['theme']}\n\n Teemat: {self.themes}."
                prompt += f"\n\nTehtävä Topics: {self.prompts[key]['topics']}"
            elif key == "user_need":
                prompt += f"\n\nTehtävä {key}: {self.prompts[key]}\n\n Käyttäjätarpeet: {self.user_needs}."
            elif key == "tone":
                prompt += (
                    f"\n\nTehtävä {key}: {self.prompts[key]}\n\n Sävy: {self.tone}"
                )
            else:
                prompt += f"\n\nTehtävä {key}: {self.prompts[key]}"

        message = await basic_chat(
            prompt,
            temperature=0,
            model=self.model,
        )

        # Extract the JSON portion of the response
        json_str = strip_openai_json(message)

        # Parse the JSON string into a Python format
        return parse_json(json_str, message)
