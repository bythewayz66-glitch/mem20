import pytest

from server.app.extract import extract_delta, extract_text


class TestExtractText:
    def test_plain_string(self):
        assert extract_text("hello") == "hello"
        assert extract_text("  hi  ") == "hi"
        assert extract_text("") is None
        assert extract_text(None) is None

    @pytest.mark.parametrize("key", ["reply", "text", "message", "content", "output", "output_text"])
    def test_simple_keys(self, key):
        assert extract_text({key: "hello"}) == "hello"

    def test_openai_chat_content_string(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "hi there"}}]}
        assert extract_text(payload) == "hi there"

    def test_openai_chat_content_parts(self):
        payload = {"choices": [{"message": {"content": [{"type": "text", "text": "part1"}, {"type": "text", "text": "part2"}]}}]}
        assert extract_text(payload) == "part1part2"

    def test_anthropic_shaped_content_blocks(self):
        # Regression: extract_text must not drop Anthropic-shaped content blocks
        payload = {"content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}]}
        assert extract_text(payload) == "Hello world"

    def test_anthropic_mixed_blocks_preserves_text(self):
        payload = {
            "content": [
                {"type": "thinking", "thinking": "hmm"},
                {"type": "text", "text": "Answer"},
                {"type": "tool_use", "id": "1", "name": "x", "input": {}},
                {"type": "text", "text": "!"},
            ]
        }
        assert extract_text(payload) == "Answer!"

    def test_top_level_content_list_of_strings(self):
        assert extract_text({"content": ["a", "b"]}) == "ab"

    def test_delta_content(self):
        payload = {"choices": [{"delta": {"content": "stream"}}]}
        assert extract_text(payload) == "stream"

    def test_responses_output_shape(self):
        payload = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "hi"}]}]}
        assert extract_text(payload) == "hi"

    def test_responses_output_text(self):
        assert extract_text({"output_text": "direct"}) == "direct"

    def test_unknown_payload(self):
        assert extract_text({"foo": "bar"}) is None
        assert extract_text(123) is None
        assert extract_text([1, 2, 3]) is None


class TestExtractDelta:
    def test_openai_delta(self):
        assert extract_delta({"choices": [{"delta": {"content": "hi"}}]}) == "hi"

    def test_openai_delta_parts(self):
        assert extract_delta({"choices": [{"delta": {"content": [{"type": "text", "text": "a"}]}}]}) == "a"

    def test_anthropic_content_block_delta(self):
        assert extract_delta({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "x"}}) == "x"

    def test_plain_string(self):
        assert extract_delta("chunk") == "chunk"

    def test_none(self):
        assert extract_delta(None) is None
