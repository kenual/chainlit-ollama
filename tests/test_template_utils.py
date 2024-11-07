import pytest
from template_utils import extract_template_name, extract_template_vars, get_template


def test_get_template() -> None:
    template = get_template('Summarize Article')
    assert template is not None

def test_extract_template_vars() -> None:
    vars = extract_template_vars('Summarize Article')
    assert len(vars) == 2
    assert 'content' in vars
    assert 'output_language' in vars


@pytest.mark.parametrize("command", [
    "condense text using template Summarize Content",
    'Use the template "Summarize Content" to summarize text',
    "summarize this article using template Summarize Content",
    "Open template 'Summarize Content' to help me summarize text"
])
def test_extract_template_name(command: str) -> None:
    assert extract_template_name(command=command) == "Summarize Content"
