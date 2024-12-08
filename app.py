from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def hello():
    """
    Handles GET requests to the root URL ("/").
      - Prints the request headers to the console for debugging purposes.
      - Returns a simple "Hello World!" message as the response.
    """
    print( request.headers )
    return "Hello World!"

@app.route('/generate_article_summary', methods=['POST'])
def generate_article_summary():
    """
    Handles POST requests to the "/generate_article_summary" endpoint.
      - Expects the client to send a JSON payload in the request body.
      - Returns a 204 (No Content response) to indicate successful processing.
    """
    print( request.get_json() )
    return '', 204

if __name__ == "__main__":
    app.run()