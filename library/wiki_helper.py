import requests
import json
import logging


# CONSTANTS
WIKI_PID_FOR_ARXIV_ID = "P21"
WIKI_PID_FOR_SUMMARY = "P1638"
WIKI_PID_FOR_SUMMARY_SIMPLE = "P1639"
WIKI_PID_FOR_GENERATED_BY = "P1642"

class WikiHelper:
    """
    A helper class to interact with the Wikibase API. This class provides methods for
    CSRF token retrieval, fetching properties, and updating existing statements.
    """

    def __init__(self, wiki_api_url=None, username=None, password=None, proxy_ip=None):
        """
        Initializes the WikiHelper.

        Args:
            wiki_api_url (str): Url to the wiki api
            username (str): Username
            password (str): Password
            proxy_ip (str): IP and port of proxy, e.g. "47.254.131.67:3128"
        """
        self.WIKI_API_URL = wiki_api_url
        self.USERNAME = username
        self.PASSWORD = password

        # https://spys.one/free-proxy-list/DE/
        self.PROXY_IP = proxy_ip
        self.SESSION = self.start_session()

    def start_session(self):
        """
        Starts a session for making API calls and configures proxy settings, if given.

        Returns:
            requests.Session: A configured session object.
        """

        # Start a session
        self.SESSION = requests.Session()

        if self.PROXY_IP:
            # Define your proxy settings
            PROXIES = {
                "http": self.PROXY_IP,
                "https": self.PROXY_IP,
            }
            # Set proxy for the session
            self.SESSION.proxies.update(PROXIES)
            print("Using proxy:", self.SESSION.proxies)

        return self.SESSION

    def get_csrf_token(self):
        """
        Retrieves a CSRF token for authenticating API requests.

        Returns:
            str: The retrieved CSRF token.

        Raises:
            Exception: If login fails or the response is invalid.
        """

        # Step 1: Get Login Token
        print("Get login token ...")
        login_token_response = self.SESSION.get(
            self.WIKI_API_URL,
            params={
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            }
        )
        login_token = login_token_response.json()['query']['tokens']['logintoken']
        print(login_token)

        # Step 2: Log in
        print("Login ...")
        login_response = self.SESSION.post(
            self.WIKI_API_URL,
            data={
                'action': 'login',
                'lgname': self.USERNAME,
                'lgpassword': self.PASSWORD,
                'lgtoken': login_token,
                'format': 'json'
            }
        )

        if login_response.json()['login']['result'] != "Success":
            raise Exception("Login failed!")

        print(login_response)

        # Step 3: Get CSRF Token
        print("Get CSRF token ...")
        csrf_token_response = self.SESSION.get(
            self.WIKI_API_URL,
            params={
                'action': 'query',
                'meta': 'tokens',
                'type': 'csrf',
                'format': 'json'
            }
        )

        csrf_token = csrf_token_response.json()['query']['tokens']['csrftoken']

        print("Done.")

        return csrf_token

    def get_property(self, item_id, property_id):
        """
        Retrieves the property values of a specific item.

        Args:
            item_id (str): The ID of the item
            property_id (str): The ID of the property

        Returns:
            list: A list of claims for the given property, or None if the property is not found.
        """
        response = self.SESSION.get(
            self.WIKI_API_URL,
            params={
                'action': 'wbgetclaims',
                'entity': item_id,
                'property': property_id,
                'format': 'json'
            }
        )
        claims = response.json().get('claims', {})
        if property_id in claims:
            return claims[property_id]
        else:
            return None

    def get_property_value(self, item_id, property_id):
        """
        Retrieves the value of a specific property from an item.

        Args:
            item_id (str): The ID of the item.
            property_id (str): The ID of the property.

        Returns:
            str: The value of the property, or None if not found.
        """
        response = self.SESSION.get(
            self.WIKI_API_URL,
            params={
                'action': 'wbgetclaims',
                'entity': item_id,
                'property': property_id,
                'format': 'json'
            }
        )
        claims = response.json().get('claims', {}).get(property_id, [])

        # Check if claims exist for the property
        if claims:
            # Extract the first claim's mainsnak
            mainsnak = claims[0].get('mainsnak', {})
            datavalue = mainsnak.get('datavalue', {})
            value = datavalue.get('value')

            # Handle different datatypes
            if isinstance(value, dict) and 'text' in value:
                # For monolingualtext
                return value['text']
            elif isinstance(value, str):
                # For plain string values
                return value

        return None

    def get_property_statement_id(self, item_id, property_id):
        """
        Retrieves the statement ID for a specific property of an item.

        Parameters:
          item_id: ID of the item
          property_id: ID of the property

        Returns:
          list: A list of statement IDs for the specified property.
        """
        response = self.SESSION.get(
            self.WIKI_API_URL,
            params={
                'action': 'wbgetclaims',
                'entity': item_id,
                'property': property_id,
                'format': 'json'
            }
        )
        claims = response.json().get('claims', {}).get(property_id, [])
        statement_ids = [claim['id'] for claim in claims]

        # Return "None" if list is empty
        return statement_ids if statement_ids else None

    def update_or_add_property_monolingual_text(self,
                                                csrf_token=None, statement_id=None,
                                                item_id=None, property_id=None,
                                                new_value_text=None, new_value_language=None):
        """
        Updates the value of an existing statement or adds a new statement for a property in Wikibase.

        Args:
            item_id (str): The ID of the item.
            property_id (str): The ID of the property to update or add.
            new_value_text (str): The new text value for the statement.
            new_value_language (str): The language code for the text value (e.g., "en").
            csrf_token (str): The CSRF token for authentication.
            statement_id (str, optional): The ID of the statement to update. If None, a new statement is added.

        Returns:
            bool: True if update was successful
        """
        if statement_id:
            # Update existing statement
            data = {
                'action': 'wbsetclaimvalue',
                'claim': statement_id,  # The ID of the statement being updated
                'snaktype': 'value',
                'value': json.dumps({
                    'text': new_value_text,  # New text value
                    'language': new_value_language  # Language code
                }),
                'token': csrf_token,
                'format': 'json'
            }
            response = self.SESSION.post(self.WIKI_API_URL, data=data)
        else:
            # Create a new statement
            data = {
                'action': 'wbcreateclaim',
                'entity': item_id,
                'property': property_id,
                'snaktype': 'value',
                'value': json.dumps({
                    'text': new_value_text,  # New text value
                    'language': new_value_language  # Language code
                }),
                'token': csrf_token,
                'format': 'json'
            }
            response = self.SESSION.post(self.WIKI_API_URL, data=data)

        # Parse response and determine success
        response_data = response.json()
        if 'success' in response_data and response_data['success'] == 1:
            return True
        else:
            return False

    def update_existing_property_statement_monolingual_text(self, csrf_token=None, statement_id=None, item_id=None,
                                                            new_value_text=None, new_value_language=None):
        """
        Updates the value of an existing statement in Wikibase.

        Args:
            item_id (str): The ID of the item
            statement_id (str): The ID of the statement to update.
            new_value_text (str): The new text value for the statement.
            new_value_language (str): The language code for the text value (e.g., "en").
            csrf_token (str): The CSRF token for authentication.

        Returns:
            dict: The response JSON from the API after updating the statement.
        """
        data = {
            'action': 'wbsetclaimvalue',
            'claim': statement_id,  # The ID of the statement being updated
            'snaktype': 'value',
            'value': json.dumps({
                'text': new_value_text,  # New text value
                'language': new_value_language  # Language code
            }),
            'token': csrf_token,
            'format': 'json'
        }
        response = self.SESSION.post(self.WIKI_API_URL, data=data)
        return response.json()

    def add_or_replace_qualifier(self, csrf_token=None, statement_id=None, qualifier_property_id=None,
                                 qualifier_value=None, qualifier_language=None):
        """
        Adds or replaces a qualifier for a statement in Wikibase.

        Args:
            csrf_token (str): The CSRF token for authentication.
            statement_id (str): The ID of the statement to which the qualifier is added or updated.
            qualifier_property_id (str): The property ID for the qualifier.
            qualifier_value (str or dict): The value for the qualifier. Must match the property's data type.
            qualifier_language (str, optional): The language code if the qualifier is monolingual text.

        Returns:
            bool: True if the qualifier was added, updated, or already exists with the same value. False if an error occurred.
        """
        if not statement_id:
            logging.debug("Statement ID is NONE. Cannot proceed.")
            return False

        try:
            # logging.debug(f"Getting statement details for statement: {statement_id}")

            # Fetch the current statement details
            response = self.SESSION.get(
                self.WIKI_API_URL,
                params={
                    'action': 'wbgetclaims',
                    'claim': statement_id,
                    'format': 'json'
                }
            )

            # Parse API response
            response_data = response.json()
            # logging.debug(f"API response: {json.dumps(response_data, indent=2)}")

            # Extract all claims into a single list
            all_claims = []
            claims_dict = response_data.get('claims', {})
            for property_id, property_claims in claims_dict.items():
                all_claims.extend(property_claims)

            # logging.debug(f"All claims: {json.dumps(all_claims, indent=2)}")

            # Check if the qualifier already exists
            for claim in all_claims:

                # logging.debug(f"Processing claim: {json.dumps(claim, indent=2)}")

                if 'qualifiers' in claim and qualifier_property_id in claim['qualifiers']:
                    for qualifier in claim['qualifiers'][qualifier_property_id]:
                        datavalue = qualifier.get('datavalue', {}).get('value')
                        qualifier_hash = qualifier.get('hash')  # Get the hash of the existing qualifier
                        logging.debug(f"Qualifier datavalue: {datavalue}, hash: {qualifier_hash}")

                        # Check if the value matches
                        if isinstance(qualifier_value, str) and qualifier_value.startswith("Q"):
                            # For Wikibase items
                            if isinstance(datavalue, dict) and datavalue.get('id') == qualifier_value:
                                logging.debug("Qualifier already exists with the same value (Wikibase item).")
                                return True
                        elif qualifier_language:
                            # For monolingual text
                            if isinstance(datavalue, dict) and datavalue.get(
                                    'text') == qualifier_value and datavalue.get('language') == qualifier_language:
                                logging.debug("Qualifier already exists with the same value (monolingual text).")
                                return True
                        elif datavalue == qualifier_value:
                            # For plain string or other types
                            logging.debug("Qualifier already exists with the same value (plain string or other).")
                            return True

                        # Update the existing qualifier if the value is different
                        logging.debug("Updating qualifier with a new value.")
                        data = {
                            'action': 'wbsetqualifier',
                            'claim': statement_id,
                            'property': qualifier_property_id,
                            'snakhash': qualifier_hash,
                            'snaktype': 'value',
                            'value': json.dumps(
                                {"entity-type": "item", "id": qualifier_value} if qualifier_value.startswith("Q") else
                                {"text": qualifier_value, "language": qualifier_language} if qualifier_language else
                                qualifier_value
                            ),
                            'token': csrf_token,
                            'format': 'json'
                        }
                        # logging.debug(f"Update request data: {json.dumps(data, indent=2)}")
                        update_response = self.SESSION.post(self.WIKI_API_URL, data=data).json()
                        # logging.debug(f"Update response: {json.dumps(update_response, indent=2)}")

                        if 'success' in update_response and update_response['success'] == 1:
                            logging.debug("Qualifier updated successfully.")
                            return True
                        else:
                            raise Exception(f"Failed to update qualifier: {json.dumps(update_response, indent=2)}")

            # Add a new qualifier if it doesn't exist
            value = (
                {"entity-type": "item", "id": qualifier_value} if isinstance(qualifier_value,
                                                                             str) and qualifier_value.startswith(
                    "Q") else
                {"text": qualifier_value, "language": qualifier_language} if qualifier_language else
                qualifier_value
            )

            # Prepare the data for adding a new qualifier
            data = {
                'action': 'wbsetqualifier',
                'claim': statement_id,
                'property': qualifier_property_id,
                'snaktype': 'value',
                'value': json.dumps(value),
                'token': csrf_token,
                'format': 'json'
            }
            # logging.debug(f"Adding new qualifier with data: {json.dumps(data, indent=2)}")

            # Make the API request to add a new qualifier
            add_response = self.SESSION.post(self.WIKI_API_URL, data=data).json()
            logging.debug(f"Add response: {json.dumps(add_response, indent=2)}")

            # Check for success
            if 'success' in add_response and add_response['success'] == 1:
                logging.debug("Qualifier added successfully.")
                return True
            else:
                raise Exception(f"Failed to add qualifier: {json.dumps(add_response, indent=2)}")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return False  # Return False on any error


    def get_arxivid_from_qid(self, qid):
        """
        Returns the arXiv id for a given QID from the Wiki.

        Args:
            qid (str): The QID.

        Returns:
            str: The arXiv id.
        """

        arXiv_id = self.get_property_value( qid, WIKI_PID_FOR_ARXIV_ID )
        return arXiv_id
