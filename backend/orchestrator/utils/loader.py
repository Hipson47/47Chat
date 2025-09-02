# orchestrator/utils/loader.py
"""
Utility for loading and preprocessing YAML files and other file types.
"""

import os
from typing import Any

import yaml


def load_meta_prompt(file_path: str) -> dict[str, Any]:
    """
    Loads the meta_prompt.yaml file.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded YAML content.
    """
    # Compute common roots
    utils_dir = os.path.dirname(__file__)
    orchestrator_dir = os.path.dirname(utils_dir)  # .../backend/orchestrator
    backend_dir = os.path.dirname(orchestrator_dir)  # .../backend
    project_root = os.path.dirname(backend_dir)  # project root

    # If the provided path contains a 'backend/' prefix, also try without it
    stripped = file_path
    backend_prefix = "backend/"
    if file_path.startswith(backend_prefix):
        stripped = file_path[len(backend_prefix) :]

    # Try given path and several robust fallbacks
    candidate_paths = [
        file_path,  # as given (relative to CWD or absolute)
        os.path.join(os.getcwd(), file_path),  # CWD + given
        os.path.join(project_root, file_path),  # project_root + given
        os.path.join(project_root, stripped),  # project_root + stripped
        os.path.join(
            orchestrator_dir, "meta_prompt.yaml"
        ),  # directly next to orchestrator package
        os.path.join(backend_dir, file_path),  # backend + given
        os.path.join(backend_dir, stripped),  # backend + stripped
    ]
    for path in candidate_paths:
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        f"meta_prompt.yaml not found in any candidate paths: {candidate_paths}"
    )


def preprocess_file(file_path: str) -> str:
    """
    Preprocesses a file by reading its content.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path) as f:
        return f.read()
