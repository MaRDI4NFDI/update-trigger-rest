import requests
import json


class LLMHelper:
    """
    Initializes the LLMHelper.

    Args:
        auth_bearer_token (str): Authorization bearer token for API requests.
    """

    def __init__(self, auth_bearer_token=""):
        self.AUTH_BEARER_TOKEN = auth_bearer_token
        self.LLM_TO_USE = "nemotron:latest"


    def clean_string(self, input_string):
        """
        Cleans the input string by removing leading/trailing whitespaces,
        vertical whitespaces, and tabs.
        """
        # Replace vertical whitespace (newlines) and tabs with single spaces
        cleaned = input_string.replace("\n", " ").replace("\t", " ")
        # Strip leading and trailing whitespaces
        cleaned = cleaned.strip()

        return cleaned


    def ask_llm(self, question, model="llama3.2:latest", debug=False):
        """
        Sends a question to the LLM and retrieves the response.

        Args:
            question (str): The question to ask the LLM.
            model (str): The model to use for the LLM (default is 'llama3.2:latest').
            debug (bool): Whether to print debug information (default is False).

        Returns:
            str: The response from the LLM, or an error message if the request fails.

        Raises:
            requests.exceptions.RequestException: If there is an issue with the HTTP request.
            json.JSONDecodeError: If there is an issue parsing the JSON response.
        """
        url = "https://ollama.zib.de/ollama/api/generate"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.AUTH_BEARER_TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model,
            "prompt": question
        }

        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_line = json.loads(line)
                    full_response += json_line.get("response", "")

            if debug:
                print("[ask_llm] " + full_response.strip())

            return full_response.strip()

        except requests.exceptions.Timeout:
            print("Error: Request timed out")
            return "Error: Timeout"
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return "Error generating response"
        except json.JSONDecodeError as e:
            print("JSON Parsing Error:", e)
            print("Raw Response:", response.text)
            return "Error generating response due to JSON format"


    def summarize_article(self, text):
        question1 = (" Write a summary about the following scientific article suitable for a mathematician. "
                     " The summary should describe the overall idea in a connected and coherent text. "
                     " Do not use bullet points, or enumeration or technical jargon that is not explained, "
                     " or references to the structure (e.g., sections, figures, or tables) of the article. "
                     " The summary should provide a readable and concise overview. "
                     " Ignore anything that seems not complete. "
                     " Start the summary with: \"This paper is about ... \". \n \n \n"
                     " This is the scientific article: \n \n \n")

        llm_query1 = question1 + text[:10000]

        summary_raw = self.ask_llm(llm_query1, model=self.LLM_TO_USE, debug=False)
        summary_raw = self.clean_string( summary_raw )

        question2 = (" Take the following text and make a new concise text starting with \"This article ... \" "
                     " with about 5 sentences out of it. Make sure to leave any Latex commands unchanged. Do not repeat the task in the beginning. This is the text: "
                     " \n \n \n")

        llm_query2 = question2 + summary_raw[:10000]

        summary = self.ask_llm(llm_query2, model=self.LLM_TO_USE)
        summary = self.clean_string(summary)

        return summary
