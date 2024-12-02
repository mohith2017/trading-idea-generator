import pytest
from conftest import test_client, mock_vector_store

def test_root_endpoint(test_client):
    """
    Test the root endpoint from main.py
    """
    response = test_client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Trading Idea Generator!",
        "status": "healthy"
    }

class TestGenerateEndpoint:
    """
    Tests for the /api/v1/generate endpoint
    """
    
    def test_successful_generation(self, test_client, mock_vector_store):
        """Test successful trading idea generation"""
        response = test_client.post("/api/v1/generate")
        
        assert response.status_code == 200
        assert "generated_output" in response.json()
        assert "Mock trading idea" in response.json()["generated_output"]

    def test_generation_failure(self, test_client, monkeypatch):
        """Test error handling when generation fails"""
        def mock_failed_query(*args, **kwargs):
            raise Exception("Vector store error")

        monkeypatch.setattr(
            "llama_index.core.query_engine.router_query_engine.RouterQueryEngine.query",
            mock_failed_query
        )
        
        response = test_client.post("/api/v1/generate")
        
        assert response.status_code == 500
        assert "Error generating trade idea" in response.json()["detail"]

    def test_vector_store_found(self, test_client, monkeypatch):
        """Test successful case when vector store is found"""
        def mock_load_index(*args, **kwargs):
            return mock_vector_store 
        
        monkeypatch.setattr(
            "llama_index.core.load_index_from_storage",
            mock_load_index
        )
        
        response = test_client.post("/api/v1/generate")
        
        assert response.status_code == 200
        assert "generated_output" in response.json()
