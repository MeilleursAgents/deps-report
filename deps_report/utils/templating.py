import os
from string import Template


def expand_template_string_with_env(input_str: str) -> str:
    """Expand a given templated string with environment variables."""
    input_template = Template(input_str)
    return input_template.safe_substitute(os.environ)
