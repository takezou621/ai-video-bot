"""
Base API client for AI Video Bot.

Provides common functionality for all API clients including:
- Standardized error handling
- Retry logic with exponential backoff
- Request/response logging
- API key rotation support
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from dataclasses import dataclass

import requests

from config.constants import DEFAULT_API_TIMEOUT, DEFAULT_MAX_RETRIES
from api_key_manager import get_api_key, report_api_success, report_api_failure

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standardized API response container."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    is_rate_limit: bool = False


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, is_rate_limit: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.is_rate_limit = is_rate_limit


class RateLimitError(APIError):
    """Exception raised when rate limit is hit."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, is_rate_limit=True)
        self.retry_after = retry_after


class BaseAPIClient(ABC):
    """
    Base class for all API clients.

    Provides common functionality:
    - HTTP request handling with retry logic
    - Error handling and logging
    - Rate limit detection and handling
    - API key rotation (for Gemini, etc.)
    """

    def __init__(
        self,
        service_name: str,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_API_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        api_key_var: Optional[str] = None
    ):
        """
        Initialize base API client.

        Args:
            service_name: Name of the service (for logging, e.g., "GEMINI", "ELEVENLABS")
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            api_key_var: Environment variable name for API key (for rotation support)
        """
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key_var = api_key_var
        self._current_api_key: Optional[str] = None

    @abstractmethod
    def build_request_headers(self) -> Dict[str, str]:
        """
        Build request headers for the API.

        Returns:
            Dictionary of headers
        """
        return {"Content-Type": "application/json"}

    def get_api_key(self) -> Optional[str]:
        """
        Get API key with rotation support.

        Returns:
            API key or None if not configured
        """
        if self.api_key_var:
            return get_api_key(self.service_name)
        return None

    def build_url(self, endpoint: str) -> str:
        """
        Build full URL from base URL and endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Full URL
        """
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        return endpoint

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make POST request with retry logic.

        Args:
            endpoint: API endpoint
            data: Form data to send
            json_data: JSON data to send
            headers: Additional headers
            **kwargs: Additional request arguments

        Returns:
            APIResponse object
        """
        url = self.build_url(endpoint)
        request_headers = self.build_request_headers()
        if headers:
            request_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    timeout=self.timeout,
                    **kwargs
                )
                return self._handle_response(response, attempt)

            except requests.exceptions.Timeout as e:
                logger.warning(f"[{self.service_name}] Timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    return APIResponse(
                        success=False,
                        error_message=f"Request timeout: {str(e)}"
                    )
                time.sleep(2 ** attempt)  # Exponential backoff

            except requests.exceptions.RequestException as e:
                logger.warning(f"[{self.service_name}] Request error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt == self.max_retries - 1:
                    return APIResponse(
                        success=False,
                        error_message=f"Request failed: {str(e)}"
                    )
                time.sleep(2 ** attempt)

        return APIResponse(success=False, error_message="Max retries exceeded")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make GET request with retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional request arguments

        Returns:
            APIResponse object
        """
        url = self.build_url(endpoint)
        request_headers = self.build_request_headers()
        if headers:
            request_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=self.timeout,
                    **kwargs
                )
                return self._handle_response(response, attempt)

            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                logger.warning(f"[{self.service_name}] GET error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt == self.max_retries - 1:
                    return APIResponse(
                        success=False,
                        error_message=f"GET request failed: {str(e)}"
                    )
                time.sleep(2 ** attempt)

        return APIResponse(success=False, error_message="Max retries exceeded")

    def _handle_response(self, response: requests.Response, attempt: int) -> APIResponse:
        """
        Handle API response, checking for errors and rate limits.

        Args:
            response: Response object
            attempt: Current attempt number

        Returns:
            APIResponse object
        """
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            wait_time = int(retry_after) if retry_after else 2 ** attempt

            if self.api_key_var and 'api_key' in locals():
                report_api_failure(self.service_name, self._current_api_key, is_rate_limit=True)

            logger.warning(f"[{self.service_name}] Rate limit hit, waiting {wait_time}s before retry")
            time.sleep(wait_time)

            if attempt < self.max_retries - 1:
                # Try with next API key if available
                if self.api_key_var:
                    self._current_api_key = self.get_api_key()
                return APIResponse(
                    success=False,
                    status_code=response.status_code,
                    error_message="Rate limit hit, retrying...",
                    is_rate_limit=True
                )

            return APIResponse(
                success=False,
                status_code=response.status_code,
                error_message="Rate limit exceeded after all retries",
                is_rate_limit=True
            )

        # Check for other HTTP errors
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            is_rate_limit = "quota" in error_msg.lower() or "rate" in error_msg.lower()

            if self.api_key_var:
                report_api_failure(self.service_name, self._current_api_key, is_rate_limit=is_rate_limit)

            return APIResponse(
                success=False,
                status_code=response.status_code,
                error_message=error_msg,
                is_rate_limit=is_rate_limit
            )

        # Success - report if API key is being tracked
        if self.api_key_var:
            report_api_success(self.service_name, self._current_api_key)

        # Try to parse as JSON first
        try:
            data = response.json()
            return APIResponse(
                success=True,
                data=data,
                status_code=response.status_code
            )
        except ValueError:
            # Return as text if not JSON
            return APIResponse(
                success=True,
                text=response.text,
                status_code=response.status_code
            )


class GeminiAPIClient(BaseAPIClient):
    """Gemini API client with key rotation support."""

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        timeout: int = DEFAULT_API_TIMEOUT
    ):
        super().__init__(
            service_name="GEMINI",
            timeout=timeout,
            api_key_var="GEMINI_API_KEY"
        )
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def build_request_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def build_url(self, endpoint: str) -> str:
        """Add API key to URL for Gemini."""
        api_key = self.get_api_key()
        if api_key:
            return f"{self.base_url}/{endpoint}?key={api_key}"
        return f"{self.base_url}/{endpoint}"

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.9,
        max_output_tokens: int = 8192
    ) -> APIResponse:
        """
        Generate content using Gemini API.

        Args:
            prompt: Text prompt
            temperature: Sampling temperature
            max_output_tokens: Maximum output tokens

        Returns:
            APIResponse with generated text
        """
        self._current_api_key = self.get_api_key()

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens
            }
        }

        response = self.post(f"{self.model}:generateContent", json_data=payload)

        if response.success and response.data:
            # Extract text from Gemini response
            candidates = response.data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    response.text = parts[0].get("text", "")

        return response


class ElevenLabsAPIClient(BaseAPIClient):
    """ElevenLabs API client."""

    def __init__(self, api_key: str, timeout: int = DEFAULT_API_TIMEOUT):
        super().__init__(
            service_name="ELEVENLABS",
            base_url="https://api.elevenlabs.io/v1",
            timeout=timeout
        )
        self._api_key = api_key

    def build_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "xi-api-key": self._api_key
        }

    def transcribe(self, audio_path: str) -> APIResponse:
        """
        Transcribe audio using ElevenLabs STT.

        Args:
            audio_path: Path to audio file

        Returns:
            APIResponse with transcription
        """
        with open(audio_path, 'rb') as audio_file:
            files = {'file': audio_file}
            headers = {'xi-api-key': self._api_key}

            response = requests.post(
                f"{self.base_url}/speech-to-text",
                files=files,
                headers=headers,
                timeout=self.timeout
            )

            return self._handle_response(response, 0)


if __name__ == "__main__":
    # Test API client
    logging.basicConfig(level=logging.INFO)

    client = GeminiAPIClient()
    print(f"Gemini client initialized with model: {client.model}")
