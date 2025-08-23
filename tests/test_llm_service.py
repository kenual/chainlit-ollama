from llm_service import get_available_models, Model

def test_get_available_models_live_no_mock():
    """
    Live test (no mocks) for get_available_models(). This test queries the Ollama API
    and/or checks for available SERVICE_MODELS depending on environment. To pass, must return a list[Model].
    """
    models = get_available_models()
    assert isinstance(models, list), "Result must be a list"
    for model in models:
        assert isinstance(model, Model), f"Each model must be of type Model, got {type(model)}"
        assert hasattr(model, "name")
        assert hasattr(model, "provider")
        assert hasattr(model, "model")
