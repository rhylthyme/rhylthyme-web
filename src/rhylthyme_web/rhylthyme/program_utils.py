#!/usr/bin/env python3
"""
Program file loading utilities.
"""

import os
import json

try:
    import yaml
except ImportError:
    yaml = None


def load_program_file(file_path: str) -> dict:
    """
    Load and parse a program file (JSON or YAML).

    Args:
        file_path: Path to the program file

    Returns:
        The parsed program as a dictionary
    """
    _, ext = os.path.splitext(file_path)

    with open(file_path, 'r') as file:
        if ext.lower() in ['.yaml', '.yml']:
            if yaml is None:
                raise ImportError("PyYAML is required for YAML file support")
            return yaml.safe_load(file)
        else:
            return json.load(file)
