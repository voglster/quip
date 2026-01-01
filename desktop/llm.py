"""LLM integration for Quip - Simple wrapper for Ollama API calls"""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from config import config


class LLMError(Exception):
    """Exception for LLM-related errors"""

    pass


class LLMClient:
    """Simple LLM client for Ollama OpenAI-compatible API"""

    def __init__(self):
        self.base_url = config.llm_base_url
        self.model = config.llm_model
        self.api_key = config.llm_api_key
        self.timeout = config.llm_timeout_seconds
        self.max_tokens = config.llm_max_tokens
        self.temperature = config.llm_temperature

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Ollama API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        json_data = json.dumps(data).encode("utf-8")

        try:
            request = urllib.request.Request(
                url, data=json_data, headers=headers, method="POST"
            )

            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            raise LLMError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise LLMError(f"Connection error: {e.reason}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise LLMError(f"Request failed: {e}")

    def improve_note(
        self,
        text: str,
        curator_feedback: str = None,
        vocabulary_hints: list = None,
        use_voice_prompt: bool = False,
    ) -> str:
        """Improve a quick note using configured prompt

        Args:
            text: The note text to improve
            curator_feedback: Optional curator feedback to provide context
            vocabulary_hints: Optional list of commonly-used terms to watch for
            use_voice_prompt: If True, use voice-specific improvement prompt

        Returns:
            Improved note text

        Raises:
            LLMError: If the API call fails
        """
        if not config.llm_enabled:
            raise LLMError("LLM functionality is disabled in configuration")

        if not text.strip():
            return text

        # Choose prompt based on voice or manual improvement
        prompt = (
            config.llm_voice_improve_prompt
            if use_voice_prompt
            else config.llm_improve_prompt
        )

        # Build user content with optional context
        user_content = prompt

        # Add vocabulary hints context if provided
        if vocabulary_hints and use_voice_prompt:
            hints_text = ", ".join(vocabulary_hints)
            user_content += f"\n\nUser's common vocabulary: {hints_text}\nConsider these terms when similar-sounding words appear in context."

        # If curator feedback is provided, include it in the context
        if curator_feedback:
            user_content += f"\n\nCurator feedback that was provided to the user:\n{curator_feedback}"

        user_content += f"\n\nNote to improve:\n{text}"

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that improves text. Return only the improved text without any explanations, quotes, or additional formatting. If curator feedback is provided, use it to guide your improvements.",
            },
            {"role": "user", "content": user_content},
        ]

        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if config.debug_mode:
            print("\n" + "=" * 80)
            print("DEBUG LLM: Improving note")
            print("=" * 80)
            print(f"Input text: '{text}'")
            print(f"\nPrompt: '{prompt}'")
            print("\nFull request:")
            print(json.dumps(request_data, indent=2))

        try:
            response = self._make_request("chat/completions", request_data)

            if config.debug_mode:
                print("\nRaw response:")
                print(json.dumps(response, indent=2))

            if "choices" not in response or not response["choices"]:
                raise LLMError("No response choices returned from API")

            content = response["choices"][0]["message"]["content"]

            if config.debug_mode:
                print(f"\nImproved text: '{content}'")
                print("=" * 80 + "\n")

            return content.strip()

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Failed to process LLM response: {e}")

    def cleanup_text(self, text: str, instruction: Optional[str] = None) -> str:
        """Clean up text using LLM

        Args:
            text: The text to clean up
            instruction: Optional custom instruction, defaults to general cleanup

        Returns:
            Cleaned up text

        Raises:
            LLMError: If the API call fails
        """
        if not config.llm_enabled:
            raise LLMError("LLM functionality is disabled in configuration")

        if not text.strip():
            return text

        if instruction is None:
            instruction = (
                "Clean up and improve this note while preserving its meaning and tone. "
                "Fix grammar, spelling, and make it more concise and clear. "
                "Don't add new information, just improve what's there:"
            )

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that improves text clarity and grammar.",
            },
            {"role": "user", "content": f"{instruction}\n\n{text}"},
        ]

        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            response = self._make_request("chat/completions", request_data)

            if "choices" not in response or not response["choices"]:
                raise LLMError("No response choices returned from API")

            content = response["choices"][0]["message"]["content"]
            return content.strip()

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Failed to process LLM response: {e}")

    def test_connection(self) -> bool:
        """Test if LLM service is available

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.cleanup_text("Hello", "Just say 'Hello' back")
            return "hello" in response.lower()
        except LLMError:
            return False


# Global LLM client instance
llm_client = LLMClient()
