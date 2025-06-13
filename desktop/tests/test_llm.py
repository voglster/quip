"""Tests for LLM integration module."""

import json
import urllib.error
from unittest.mock import Mock, patch

import pytest

from llm import LLMClient, LLMError, llm_client


class TestLLMClient:
    """Test LLMClient functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch("llm.config") as mock_config:
            mock_config.llm_enabled = True
            mock_config.llm_base_url = "http://localhost:11434"
            mock_config.llm_model = "llama2"
            mock_config.llm_api_key = None
            mock_config.llm_timeout_seconds = 30
            mock_config.llm_max_tokens = 1000
            mock_config.llm_temperature = 0.7
            mock_config.llm_improve_prompt = "Improve this note:"
            mock_config.debug_mode = False
            yield mock_config

    def test_llm_client_initialization(self, mock_config):
        """Test LLM client initializes with correct config values."""
        client = LLMClient()

        assert client.base_url == "http://localhost:11434"
        assert client.model == "llama2"
        assert client.api_key is None
        assert client.timeout == 30
        assert client.max_tokens == 1000
        assert client.temperature == 0.7

    def test_make_request_success(self, mock_config):
        """Test successful HTTP request to LLM API."""
        client = LLMClient()

        mock_response_data = {"choices": [{"message": {"content": "improved text"}}]}
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client._make_request("chat/completions", {"test": "data"})

        assert result == mock_response_data

    def test_make_request_with_api_key(self, mock_config):
        """Test HTTP request includes API key when configured."""
        mock_config.llm_api_key = "test-api-key"
        client = LLMClient()

        mock_response_data = {"choices": [{"message": {"content": "improved text"}}]}
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)

        with (
            patch("urllib.request.urlopen", return_value=mock_response),
            patch("urllib.request.Request") as mock_request,
        ):
            client._make_request("chat/completions", {"test": "data"})

            # Check that request was created with Authorization header
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test-api-key"

    def test_make_request_http_error(self, mock_config):
        """Test HTTP error handling."""
        client = LLMClient()

        http_error = urllib.error.HTTPError(
            url="http://test.com", code=404, msg="Not Found", hdrs={}, fp=Mock()
        )
        http_error.read = Mock(return_value=b"Error details")

        with patch("urllib.request.urlopen", side_effect=http_error):
            with pytest.raises(LLMError, match="HTTP 404: Error details"):
                client._make_request("chat/completions", {"test": "data"})

    def test_make_request_connection_error(self, mock_config):
        """Test connection error handling."""
        client = LLMClient()

        url_error = urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=url_error):
            with pytest.raises(LLMError, match="Connection error: Connection refused"):
                client._make_request("chat/completions", {"test": "data"})

    def test_make_request_json_decode_error(self, mock_config):
        """Test JSON decode error handling."""
        client = LLMClient()

        mock_response = Mock()
        mock_response.read.return_value = b"invalid json"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(LLMError, match="Invalid JSON response"):
                client._make_request("chat/completions", {"test": "data"})

    def test_improve_note_success(self, mock_config):
        """Test successful note improvement."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Improved note text"}}]
            }

            result = client.improve_note("original text")

            assert result == "Improved note text"
            mock_request.assert_called_once_with(
                "chat/completions",
                {
                    "model": "llama2",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that improves text. Return only the improved text without any explanations, quotes, or additional formatting. If curator feedback is provided, use it to guide your improvements.",
                        },
                        {
                            "role": "user",
                            "content": "Improve this note:\n\noriginal text",
                        },
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7,
                },
            )

    def test_improve_note_with_curator_feedback(self, mock_config):
        """Test note improvement with curator feedback."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Improved note text"}}]
            }

            result = client.improve_note("original text", "Make it more formal")

            assert result == "Improved note text"
            # Check that curator feedback was included in the prompt
            call_args = mock_request.call_args[0][1]
            user_message = call_args["messages"][1]["content"]
            assert "Curator feedback that was provided to the user:" in user_message
            assert "Make it more formal" in user_message

    def test_improve_note_disabled(self, mock_config):
        """Test error when LLM is disabled."""
        mock_config.llm_enabled = False
        client = LLMClient()

        with pytest.raises(LLMError, match="LLM functionality is disabled"):
            client.improve_note("some text")

    def test_improve_note_empty_text(self, mock_config):
        """Test that empty text is returned unchanged."""
        client = LLMClient()

        result = client.improve_note("   ")
        assert result == "   "

    def test_improve_note_no_choices_error(self, mock_config):
        """Test error when API returns no choices."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {"choices": []}

            with pytest.raises(LLMError, match="No response choices returned from API"):
                client.improve_note("some text")

    def test_improve_note_malformed_response(self, mock_config):
        """Test error handling for malformed API response."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {"invalid": "response"}

            with pytest.raises(LLMError, match="No response choices returned from API"):
                client.improve_note("some text")

    def test_cleanup_text_success(self, mock_config):
        """Test successful text cleanup."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Clean text"}}]
            }

            result = client.cleanup_text("messy text")

            assert result == "Clean text"
            mock_request.assert_called_once()

    def test_cleanup_text_custom_instruction(self, mock_config):
        """Test text cleanup with custom instruction."""
        client = LLMClient()

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Custom cleaned text"}}]
            }

            result = client.cleanup_text("messy text", "Make it formal")

            assert result == "Custom cleaned text"
            # Check that custom instruction was used
            call_args = mock_request.call_args[0][1]
            user_message = call_args["messages"][1]["content"]
            assert "Make it formal" in user_message

    def test_cleanup_text_disabled(self, mock_config):
        """Test error when LLM is disabled for cleanup."""
        mock_config.llm_enabled = False
        client = LLMClient()

        with pytest.raises(LLMError, match="LLM functionality is disabled"):
            client.cleanup_text("some text")

    def test_cleanup_text_empty_text(self, mock_config):
        """Test that empty text cleanup returns unchanged."""
        client = LLMClient()

        result = client.cleanup_text("   ")
        assert result == "   "

    def test_test_connection_success(self, mock_config):
        """Test successful connection test."""
        client = LLMClient()

        with patch.object(client, "cleanup_text") as mock_cleanup:
            mock_cleanup.return_value = "Hello back"

            result = client.test_connection()

            assert result is True
            mock_cleanup.assert_called_once_with("Hello", "Just say 'Hello' back")

    def test_test_connection_failure(self, mock_config):
        """Test connection test failure."""
        client = LLMClient()

        with patch.object(client, "cleanup_text") as mock_cleanup:
            mock_cleanup.side_effect = LLMError("Connection failed")

            result = client.test_connection()

            assert result is False

    def test_global_llm_client_instance(self, mock_config):
        """Test that global llm_client instance is properly initialized."""
        # The global instance should be created when module is imported
        assert llm_client is not None
        assert isinstance(llm_client, LLMClient)
