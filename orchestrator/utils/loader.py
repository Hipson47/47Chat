# orchestrator/utils/loader.py
"""
Utility for loading and preprocessing YAML files and other file types.
"""

import yaml

def load_meta_prompt(file_path):
    """
    Loads the meta_prompt.yaml file.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded YAML content.
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def preprocess_file(file_path):
    """
    Preprocesses a file by reading its content.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r') as f:
        return f.read()
