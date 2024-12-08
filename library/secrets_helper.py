import json

def load_secrets(file_path="secrets.json"):
    """
    Load secrets from a secure JSON file.

    Args:
        file_path (str): Path to the secrets file (default: "secrets.json").

    Returns:
        dict: A dictionary containing the secrets.

    Raises:
        FileNotFoundError: If the secrets file is missing.
        PermissionError: If the file permissions are insufficient.
    """
    try:
        with open(file_path, 'r') as file:
            secrets = json.load(file)
        return secrets
    except FileNotFoundError:
        raise FileNotFoundError(f"Secrets file '{file_path}' not found. Please check the file path.")
    except PermissionError:
        raise PermissionError(f"Insufficient permissions to access the secrets file '{file_path}'.")
