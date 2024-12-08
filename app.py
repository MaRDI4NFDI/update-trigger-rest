from flask import Flask, request, jsonify

from library.other_helper import OtherHelper
from library.wiki_helper import WikiHelper
from library.llm_helper import LLMHelper
from library.secrets_helper import load_secrets

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("update-trigger-rest")

app = Flask(__name__)

# Load secrets
secrets = load_secrets()
llm_api_key = secrets.get("llm_api_key")

# Initialize helpers
llm = LLMHelper( auth_bearer_token=llm_api_key)
wiki = WikiHelper( wiki_api_url="https://portal.mardi4nfdi.de/api.php" )
other = OtherHelper()

logger.info('Loading finished.')

@app.route("/")
def hello():
    """
    Handles GET requests to the root URL ("/").
      - Prints the request headers to the console for debugging purposes.
      - Returns a simple "Hello World!" message as the response.
    """
    print( request.headers )
    return "Hello World!"


@app.route('/generate_article_summary', methods=['GET'])
def generate_article_summary():
    """
    Handles GET requests to the "/generate_article_summary" endpoint.
      - Expects the client to send a JSON payload in the request body.
      - Returns a 204 (No Content response) to indicate successful processing.
    """
    logger.debug("called: /generate_article_summary")

    # Extract QID from query parameters
    qid = request.args.get('QID', "")
    if not qid:
        return {"error": "Missing 'QID' in query parameters"}, 400

    logger.debug(f"QID: {qid}")

    # Get arXiv id
    arxivid = wiki.get_arxivid_from_qid( qid )

    logger.debug(f"arXiv ID: {arxivid}")

    if( arxivid is None ):
        return {"error": "Invalid QID"}, 400

    # Get article text
    logger.debug("Getting article text...")
    article_text = other.get_rendered_text_for_arxiv_id( arxivid )

    # Generate summary
    logger.debug("Calling LLM to summarize...")
    summary = llm.summarize_article( article_text )

    logger.debug( summary )

    # Check if summary is None
    if summary is None:
        return "Error: Summary generation failed.", 500

    return jsonify({"summary": summary}), 200



if __name__ == "__main__":
    app.run()