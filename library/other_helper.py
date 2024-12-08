import requests
from bs4 import BeautifulSoup

class OtherHelper:

    def __init__(self):
        initialized = True


    def get_rendered_text_for_arxiv_id(self, arxiv_id=None):
        """
        Fetches and extracts rendered text with better support for HTML5 and MathML.

        Args:
            arxiv_id (str): The arxiv id to get the text for.

        Returns:
            str: The extracted text from the html page.
        """

        url = "https://ar5iv.labs.arxiv.org/html/" + arxiv_id

        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful

        # Use 'lxml' or 'html5lib' for better parsing
        soup = BeautifulSoup(response.content, 'html5lib')
        # Remove <script> and <style> tags
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

            # Convert MathML to LaTeX
        for math in soup.find_all('math'):
            latex_annotation = math.find('annotation', {'encoding': 'application/x-tex'})
            if latex_annotation:
                # Replace MathML content with the LaTeX equivalent
                math.replace_with(f"${latex_annotation.get_text()}$")
            else:
                # If no LaTeX annotation exists, remove the MathML entirely
                math.decompose()

        # Extract and return the text content
        return soup.get_text(separator=' ', strip=True)
