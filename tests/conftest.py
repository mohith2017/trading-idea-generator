import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_vector_store(monkeypatch):
    def mock_query(*args, **kwargs):
        return "Mock trading idea: LONG AAPL based on strong technical indicators"
    
    monkeypatch.setattr(
        "llama_index.core.query_engine.router_query_engine.RouterQueryEngine.query",
        mock_query
    )
