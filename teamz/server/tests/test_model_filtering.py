import pytest

from server.app.providers.common import is_chat_model_id


@pytest.mark.parametrize(
    "model_id",
    [
        "gpt-4o",
        "gpt-4o-mini",
        "llama-3.1-70b-instruct",
        "Meta-Llama-3_1-70B-Instruct",
        "deepseek-chat",
        "openai-fast",
        "mistral-large",
    ],
)
def test_chat_models_allowed(model_id):
    assert is_chat_model_id(model_id) is True
    assert is_chat_model_id(model_id, keyless=True) is True


@pytest.mark.parametrize(
    "model_id",
    [
        "whisper-1",
        "whisper-large-v3",
        "distil-whisper-large-v3",
        "text-embedding-3-small",
        "embed-english-v3",
        "rerank-v3",
        "tts-1",
        "dall-e-3",
        "flux-schnell",
        "moderation-latest",
        "gpt-4o-transcribe",
    ],
)
def test_non_chat_models_excluded(model_id):
    # Probe learning must not route chat at whisper/embedding/tts/image/transcription models
    assert is_chat_model_id(model_id) is False
    assert is_chat_model_id(model_id, keyless=True) is False


@pytest.mark.parametrize(
    "model_id",
    [
        "gpt-5.4-pro",
        "o1-pro",
        "claude-opus-4-pro",
        "some-preview-pro-model",
    ],
)
def test_pro_tier_excluded_for_keyless_learning(model_id):
    # Regression: probe learned pro-tier models and routed chat at them (must not in keyless contexts)
    assert is_chat_model_id(model_id, keyless=True) is False
    # May be considered for keyed contexts if explicitly requested/available
    assert is_chat_model_id(model_id, keyless=False) is True


def test_empty_and_invalid():
    assert is_chat_model_id("") is False
    assert is_chat_model_id("   ") is False
