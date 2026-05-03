"""Tests to ensure 100% coverage across edge cases and error handling."""
import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.ai_service import AIService
from app.services.db_service import DBService
from app.utils.auth import verify_token


# ---------------------------------------------------------
# Test Main App Edge Cases
# ---------------------------------------------------------
def test_create_app_no_frontend_dir(caplog):
    """Test create_app when frontend directory is missing."""
    with patch("os.path.exists", return_value=False):
        create_app()
        assert "Frontend directory not found" in caplog.text


def test_google_cloud_logging_success():
    """Test successful Google Cloud Logging setup."""
    import importlib
    import app.main

    with patch.dict(os.environ, {"K_SERVICE": "mock_service"}):
        with patch("google.cloud.logging.Client") as MockClient:
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance
            importlib.reload(app.main)
            mock_client_instance.setup_logging.assert_called_once()

    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(app.main)


def test_google_cloud_logging_fallback(caplog):
    """Test logging fallback when K_SERVICE is set but client fails."""
    # We simulate the fallback by reloading the main module with mocked env
    import importlib
    import app.main

    with patch.dict(os.environ, {"K_SERVICE": "mock_service"}):
        with patch("google.cloud.logging.Client") as MockClient:
            MockClient.side_effect = Exception("Mock logging error")
            # Force reload to trigger the module-level K_SERVICE check
            importlib.reload(app.main)
            assert "Google Cloud Logging not available: Mock logging error" in caplog.text

    # Reload again to restore normal state for other tests
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(app.main)


# ---------------------------------------------------------
# Test AI Service Edge Cases
# ---------------------------------------------------------
@patch("app.services.ai_service.genai.configure")
def test_ai_service_init_exception(mock_configure, caplog):
    """Test AI service logs error and sets model=None when genai.configure throws."""
    mock_configure.side_effect = Exception("Mock config error")
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key"):
        service = AIService()
        assert service.model is None
        assert "Failed to initialize Gemini model: Mock config error" in caplog.text


@patch("app.services.ai_service.genai.GenerativeModel")
@patch("app.services.ai_service.genai.configure")
def test_ai_service_lazy_init(mock_configure, mock_model_class):
    """Test _try_lazy_init successfully initializes model if key becomes available."""
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", ""):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            service = AIService()
            assert service.model is None

    # Now make the key available and try lazy init
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "new_valid_key"):
        service._try_lazy_init()
        assert service.model is not None
        mock_configure.assert_called_once_with(api_key="new_valid_key")


@pytest.mark.asyncio
@patch("app.services.ai_service.genai.GenerativeModel")
async def test_ai_service_uninitialized_model(mock_model_class):
    """Test AI service response generation when model is uninitialized."""
    from app.services.ai_service import ai_cache
    ai_cache.clear()
    
    with patch("app.services.ai_service.settings.GEMINI_API_KEY", ""):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            service = AIService()
            # Force model to None to simulate uninitialized state
            service.model = None
            with pytest.raises(HTTPException) as exc_info:
                await service.generate_response("Question")
            assert exc_info.value.status_code == 503
            assert "AI service is not initialized" in exc_info.value.detail


@pytest.mark.asyncio
@patch("app.services.ai_service.genai.GenerativeModel")
async def test_ai_service_blocked_response(mock_model_class):
    """Test AI service response when blocked by safety filters."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.prompt_feedback.block_reason = "SAFETY"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key"):
        service = AIService()
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_response("Bad question")
        assert exc_info.value.status_code == 400
        assert "blocked by safety filters" in exc_info.value.detail


@pytest.mark.asyncio
@patch("app.services.ai_service.genai.GenerativeModel")
async def test_ai_service_empty_response(mock_model_class):
    """Test AI service response when API returns empty text."""
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""
    mock_response.prompt_feedback = None
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key"):
        service = AIService()
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_response("Empty question")
        assert exc_info.value.status_code == 500
        assert "AI response failed" in exc_info.value.detail


@pytest.mark.asyncio
@patch("app.services.ai_service.genai.GenerativeModel")
async def test_ai_service_generic_exception(mock_model_class, caplog):
    """Test AI service response when a generic exception occurs during generation."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("Mock generation error")
    mock_model_class.return_value = mock_model_instance

    with patch("app.services.ai_service.settings.GEMINI_API_KEY", "valid_key"):
        service = AIService()
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_response("Question")
        assert exc_info.value.status_code == 500
        assert "Gemini API error: Mock generation error" in caplog.text


# ---------------------------------------------------------
# Test Database Service Edge Cases
# ---------------------------------------------------------
@patch("app.services.db_service.firestore.client")
def test_db_service_log_chat_exception(mock_client, caplog):
    """Test database logging failure handling."""
    mock_db = MagicMock()
    mock_client.return_value = mock_db
    mock_db.collection.side_effect = Exception("Mock DB error")
    
    service = DBService()
    service.log_chat("uid", "question", "answer")
    assert "Failed to log chat to Firestore: Mock DB error" in caplog.text


def test_db_service_init_exception(caplog):
    """Test database service init fallback."""
    with patch("app.services.db_service.firestore.client", side_effect=Exception("Mock DB init error")):
        service = DBService()
        assert service.db is None
        assert "Firestore not available" in caplog.text


# ---------------------------------------------------------
# Test Auth Middleware Edge Cases
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_verify_token_valid():
    """Test verify_token with a valid simulated token."""
    from fastapi.security import HTTPAuthorizationCredentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock_token")
    with patch("app.utils.auth.auth.verify_id_token", return_value={"uid": "test_uid"}):
        token_data = await verify_token(credentials)
        assert token_data == {"uid": "test_uid"}


@pytest.mark.asyncio
async def test_verify_token_empty():
    """Test verify_token with empty credentials."""
    token_data = await verify_token(None)
    assert token_data == {"uid": "anonymous", "email": "anonymous@demo.local"}


def test_firebase_admin_init_exception(caplog):
    """Test Firebase Admin init exception handling."""
    import importlib
    import app.utils.auth
    with patch("app.utils.auth.firebase_admin.get_app", side_effect=ValueError):
        with patch("app.utils.auth.firebase_admin.initialize_app", side_effect=Exception("Mock firebase init error")):
            importlib.reload(app.utils.auth)
            assert "Failed to initialize Firebase Admin: Mock firebase init error" in caplog.text
            
    # Restore
    importlib.reload(app.utils.auth)


@pytest.mark.asyncio
async def test_verify_token_invalid():
    """Test verify_token with an invalid token."""
    from fastapi.security import HTTPAuthorizationCredentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock_token")
    with patch("app.utils.auth.auth.verify_id_token", side_effect=Exception("Mock invalid token")):
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail


# ---------------------------------------------------------
# Test Routes Background Task Error
# ---------------------------------------------------------
@patch("app.routes.routes.ai_service.generate_response", return_value="Mock answer")
@patch("app.routes.routes.db_service.log_chat", side_effect=Exception("Background mock error"))
@patch("app.routes.routes.verify_token", return_value={"uid": "test_uid"})
def test_ask_assistant_background_error(mock_verify, mock_log, mock_ai, caplog):
    """Test background task failure logging in the /ask endpoint."""
    # Temporarily disable rate limiting just for this test client
    from app.main import app
    app.dependency_overrides[verify_token] = lambda: {"uid": "test_uid"}
    client = TestClient(app)
    
    # Run the endpoint
    response = client.post("/ask", json={"question": "Test question"})
    
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock answer"
    assert "Background Firestore log failed: Background mock error" in caplog.text
