"""
Monitoring API Integration Tests

Tests for monitoring endpoints with proper admin authentication:
- GET /api/monitor/health - Health check
- GET /api/monitor/logs - Audit logs
"""


class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check(self, test_client):
        """Test health check returns status"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "version" in data

    def test_health_check_components(
        self,
        test_client,
    ):
        """Test health check includes component statuses"""
        response = test_client.get("/api/monitor/health")

        assert response.status_code == 200
        data = response.json()
        assert "components" in data
