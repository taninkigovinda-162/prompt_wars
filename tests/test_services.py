"""Tests for AI and Database services."""
import asyncio
from unittest.mock import patch, MagicMock
import pytest
from app.services.ai_service import AIService
from app.services.db_service import DBService


def test_ai_service_rejects_missing_key():
    """AIService starts in test mode (model=None) when key is placeholder."""
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "your_api_key_here"):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "your_api_key_here"}):
            service = AIService()
            assert service.model is None


def test_ai_service_rejects_empty_key():
    """AIService starts in test mode (model=None) when key is empty."""
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", ""):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            service = AIService()
            assert service.model is None


@patch("app.services.ai_service.genai.GenerativeModel")
def test_ai_service_initializes_with_valid_key(mock_model_class):
    """AIService should initialize successfully with a valid key."""
    mock_model_class.return_value = MagicMock()
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key_123"):
        service = AIService()
        assert service.model is not None
        mock_model_class.assert_called_once_with('gemini-2.0-flash')


@patch("app.services.ai_service.genai.GenerativeModel")
def test_ai_service_generates_response(mock_model_class):
    """AI service should return Gemini's response text."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "You must be 18+ to vote in India."
    mock_response.prompt_feedback = None
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key_123"):
        service = AIService()
        answer = asyncio.run(service.generate_response("Am I eligible?"))
        assert answer == "You must be 18+ to vote in India."
        mock_model_instance.generate_content.assert_called_once()


@patch("app.services.ai_service.genai.GenerativeModel")
def test_ai_service_caches_response(mock_model_class):
    """Repeated identical questions should return cached result without extra API calls."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Cached answer."
    mock_response.prompt_feedback = None
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key_123"):
        service = AIService()
        answer1 = asyncio.run(service.generate_response("Test question"))
        answer2 = asyncio.run(service.generate_response("Test question"))
        assert answer1 == answer2 == "Cached answer."
        # generate_content should only be called ONCE due to cache
        assert mock_model_instance.generate_content.call_count == 1


@patch("app.services.db_service.firestore.client")
def test_db_service_log_chat(mock_firestore_client):
    """DB service should log chat to Firestore collection."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()

    mock_firestore_client.return_value = mock_db
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document

    service = DBService()
    service.log_chat("user1", "question", "answer")

    mock_db.collection.assert_called_with("chat_history")
    mock_collection.document.assert_called_once()
    mock_document.set.assert_called_once()
