from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from analytics.api.analysis_router import analysis_router

# Create a test client instance
app = FastAPI()
app.include_router(analysis_router)
client = TestClient(app)


@pytest.mark.api
def test_analyse_endpoint(request_data, mock_analyse_all_response):
    # Mock the analyse_all function of the AnalysisService instance
    with patch(
        "analytics.service.analysis_service.AnalysisService.analyse_all",
        return_value=mock_analyse_all_response,
    ):
        response = client.post("/analyse", json=request_data)
        assert response.status_code == 200
