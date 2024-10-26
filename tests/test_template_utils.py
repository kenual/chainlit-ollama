from template_utils import extract_template_vars, get_template


def test_get_template() -> None:
    template = get_template('Summarize Article')
    assert template is not None

def test_extract_template_vars() -> None:
    vars = extract_template_vars('Summarize Article')
    assert len(vars) == 2
    assert 'article' in vars
    assert 'output_language' in vars