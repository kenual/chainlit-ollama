import pytest
from template_utils import TEMPLATES_DIR, extract_template_name, extract_template_vars, get_template_content, get_template_file_name, render_template_with_vars


def test_get_template_file_name() -> None:
    result = get_template_file_name('Summarize Content')
    assert result == f'{TEMPLATES_DIR}/Summarize Content.jinja'


def test_get_template_content() -> None:
    content = get_template_content('Summarize Content')
    assert content is not None


def test_extract_template_vars() -> None:
    vars = extract_template_vars('Summarize Content')
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


def test_render_template_with_vars() -> None:
    test_content = 'The quick brown fox jumps over the lazy dog.'
    result = render_template_with_vars(
        name='Summarize Content',
        context={'content': test_content,
                 'output_language': 'English'}
    )
    assert '{#' not in result
    assert '{{' not in result
    assert test_content in result
