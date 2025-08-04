import xlsxwriter


class ExcelWriter:
    """
    A class to write data to an Excel file using xlsxwriter.
    """

    def __init__(self, file_path: str):
        """
        Initialize the ExcelWriter with a file path.

        Args:
            file_path (str): The path to the Excel file.
        """
        self.file_path = file_path
        self.workbook = xlsxwriter.Workbook(file_path)
        self.collection = {
            "models": [],
            "results": {},
            "hallucinations": {},
            "results_geval": {},
        }

    def open_worksheet(self, data: dict, prompt: str) -> None:
        """
        Open a new worksheet in the workbook.

        Args:
            sheet_name (str): The name of the worksheet.
        """
        self.worksheet = self.workbook.add_worksheet(prompt)

        fscore = ["people", "locations", "organisations", "hyperlocation"]
        geval = ["summary", "user_needs", "tone", "theme_and_topics"]

        if prompt in fscore:
            self.write_data_fscore(data, prompt)
        elif prompt in geval:
            self.write_data_geval(data, prompt)

    def write_data_fscore(self, data: dict, prompt: str) -> None:
        self.worksheet.write(0, 0, "LLM model testing for bachelors thesis")
        self.worksheet.write(0, 1, prompt)
        self.worksheet.write(2, 0, "Model name")

        self.collection["results"][prompt] = []
        self.collection["hallucinations"][prompt] = []

        for num, model in enumerate(data.keys()):
            article_num = len(data[model]["results"]) + 2

            self.worksheet.write(3, 0 + article_num * num, model)
            self.worksheet.write(4, 0 + article_num * num, "avg precision:")
            self.worksheet.write(
                4, 1 + article_num * num, data[model]["average scores"]["precision"]
            )
            self.worksheet.write(4, 2 + article_num * num, "avg recall:")
            self.worksheet.write(
                4, 3 + article_num * num, data[model]["average scores"]["recall"]
            )
            self.worksheet.write(4, 4 + article_num * num, "avg f1-score:")
            self.worksheet.write(
                4, 5 + article_num * num, data[model]["average scores"]["f1-score"]
            )
            self.worksheet.write(5, 0 + article_num * num, "total hallucinations:")
            self.worksheet.write(
                5, 1 + article_num * num, data[model]["hallucinations_total"]
            )

            self.worksheet.write(8, 0 + article_num * num, "precision:")
            self.worksheet.write(9, 0 + article_num * num, "recall:")
            self.worksheet.write(10, 0 + article_num * num, "f1-score:")
            self.worksheet.write(12, 0 + article_num * num, "results:")
            longest_result = max([len(i) for i in data[model]["results"]])
            self.worksheet.write(
                13 + longest_result, 0 + article_num * num, "hallucinations:"
            )

            if model not in self.collection["models"]:
                self.collection["models"].append(model)
            self.collection["results"][prompt].append(
                {
                    "precision": data[model]["average scores"]["precision"],
                    "recall": data[model]["average scores"]["recall"],
                    "f1-score": data[model]["average scores"]["f1-score"],
                }
            )
            self.collection["hallucinations"][prompt].append(
                data[model]["hallucinations_total"]
            )

            for i in range(len(data[model]["results"])):
                self.worksheet.write(7, 1 + article_num * num + i, f"Article: {i + 1}")
                self.worksheet.write(
                    8, 1 + article_num * num + i, data[model]["scoring"][i]["precision"]
                )
                self.worksheet.write(
                    9, 1 + article_num * num + i, data[model]["scoring"][i]["recall"]
                )
                self.worksheet.write(
                    10, 1 + article_num * num + i, data[model]["scoring"][i]["f1-score"]
                )
                if prompt == "hyperlocation":
                    for location, name in data[model]["results"][i].items():
                        ind = {
                            k: i for i, k in enumerate(data[model]["results"][i].keys())
                        }
                        self.worksheet.write(
                            11 + ind[location],
                            1 + article_num * num + i,
                            f"{location}: {name}",
                        )
                    self.worksheet.write(
                        13 + longest_result,
                        1 + article_num * num + i,
                        data[model]["hallucinations"][i]["amount"],
                    )
                    for location, name in data[model]["hallucinations"][i][
                        "locations"
                    ].items():
                        ind = {
                            k: i
                            for i, k in enumerate(
                                data[model]["hallucinations"][i]["locations"].keys()
                            )
                        }
                        self.worksheet.write(
                            14 + longest_result + ind[location],
                            1 + article_num * num + i,
                            f"{location}: {name}",
                        )
                else:
                    for name in data[model]["results"][i]:
                        self.worksheet.write(
                            12 + data[model]["results"][i].index(name),
                            1 + article_num * num + i,
                            name,
                        )
                    self.worksheet.write(
                        13 + longest_result,
                        1 + article_num * num + i,
                        data[model]["hallucinations"][i]["amount"],
                    )
                    second = list(data[model]["hallucinations"][i].keys())[1]
                    for item in data[model]["hallucinations"][i][second]:
                        self.worksheet.write(
                            14
                            + longest_result
                            + data[model]["hallucinations"][i][second].index(item),
                            1 + article_num * num + i,
                            item,
                        )

    def write_data_geval(self, data: dict, prompt: str) -> None:
        self.worksheet.write(0, 0, "LLM model testing for bachelors thesis")
        self.worksheet.write(0, 1, prompt)
        self.worksheet.write(2, 0, "Model name")

        self.collection["results_geval"][prompt] = []

        for num, model in enumerate(data.keys()):
            article_num = len(data[model].keys()) + 2
            self.worksheet.write(3, 0 + article_num * num, model)
            criteria = list(data[model]["average scores"].keys())
            for item in criteria:
                self.worksheet.write(
                    4, 0 + article_num * num + criteria.index(item) * 2, f"avg {item}:"
                )
                self.worksheet.write(
                    4,
                    1 + article_num * num + criteria.index(item) * 2,
                    data[model]["average scores"][item],
                )

            self.worksheet.write(6, 0 + article_num * num, "scoring:")
            for item in criteria:
                self.worksheet.write(
                    7 + criteria.index(item), 0 + article_num * num, f"{item}:"
                )
            self.worksheet.write(11, 0 + article_num * num, "evaluation")
            for item in criteria:
                self.worksheet.write(
                    12 + criteria.index(item) * 6, 0 + article_num * num, f"{item}:"
                )

            if model not in self.collection["models"]:
                self.collection["models"].append(model)

            scores = {k: data[model]["average scores"][k] for k in criteria}

            self.collection["results_geval"][prompt].append(scores)

            article_keys = [k for k in data[model].keys() if k != "average scores"]
            ind = {art: i for i, art in enumerate(article_keys)}

            for article, evaluation in data[model].items():
                if article == "average scores":
                    continue
                else:
                    self.worksheet.write(
                        6, 1 + article_num * num + ind[article], article
                    )
                    for item in criteria:
                        self.worksheet.write(
                            7 + criteria.index(item),
                            1 + article_num * num + ind[article],
                            evaluation["scoring"][item],
                        )

                    ind2 = {
                        k: i
                        for i, k in enumerate(evaluation["evaluation"][item].keys())
                    }

                    for item in criteria:
                        for key, value in evaluation["evaluation"][item].items():
                            self.worksheet.write(
                                12 + criteria.index(item) * 6 + ind2[key],
                                1 + article_num * num + ind[article],
                                f"{key}:{value}",
                            )

    def close(self):
        """
        Close the workbook.
        """
        try:
            # Try to add the abstract worksheet
            self.worksheet = self.workbook.add_worksheet("abstract")

            self.worksheet.write(0, 0, "LLM model testing for bachelors thesis")
            self.worksheet.write(0, 1, "abstract")
            self.worksheet.write(3, 0, "Model name")

            second_start = 0

            for num, model in enumerate(self.collection["models"]):
                self.worksheet.write(4 + num, 0, model)

            for prompt in self.collection["results"].keys():
                ind = {k: i for i, k in enumerate(self.collection["results"].keys())}
                second_start = len(ind) * 5
                self.worksheet.write(2, 1 + ind[prompt] * 5, prompt)
                self.worksheet.write(3, 1 + ind[prompt] * 5, "precision:")
                self.worksheet.write(3, 2 + ind[prompt] * 5, "recall:")
                self.worksheet.write(3, 3 + ind[prompt] * 5, "f1-score:")
                self.worksheet.write(3, 4 + ind[prompt] * 5, "total hallucinations:")

                for item in self.collection["results"][prompt]:
                    self.worksheet.write(
                        4 + self.collection["results"][prompt].index(item),
                        1 + ind[prompt] * 5,
                        item["precision"],
                    )
                    self.worksheet.write(
                        4 + self.collection["results"][prompt].index(item),
                        2 + ind[prompt] * 5,
                        item["recall"],
                    )
                    self.worksheet.write(
                        4 + self.collection["results"][prompt].index(item),
                        3 + ind[prompt] * 5,
                        item["f1-score"],
                    )

                for item in self.collection["hallucinations"][prompt]:
                    self.worksheet.write(
                        4 + self.collection["hallucinations"][prompt].index(item),
                        4 + ind[prompt] * 5,
                        item,
                    )

            for prompt in self.collection["results_geval"].keys():
                ind = {
                    k: i for i, k in enumerate(self.collection["results_geval"].keys())
                }
                if (
                    self.collection["results_geval"][prompt]
                    and len(self.collection["results_geval"][prompt]) > 0
                ):
                    criteria = list(self.collection["results_geval"][prompt][0].keys())
                    self.worksheet.write(2, second_start + ind[prompt] * 4, prompt)
                    for item in criteria:
                        self.worksheet.write(
                            3, 1 + ind[prompt] * 4 + criteria.index(item), item
                        )

                    for result in self.collection["results_geval"][prompt]:
                        for item in criteria:
                            self.worksheet.write(
                                4
                                + self.collection["results_geval"][prompt].index(
                                    result
                                ),
                                1
                                + second_start
                                + ind[prompt] * 4
                                + criteria.index(item),
                                result[item],
                            )
        except xlsxwriter.exceptions.DuplicateWorksheetName:
            # If the summary worksheet already exists, we can skip creating it
            print("Summary worksheet already exists, skipping creation.")
        finally:
            # Always close the workbook
            self.workbook.close()
