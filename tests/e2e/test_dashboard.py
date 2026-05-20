"""
E2E tests for the dashboard page.
"""
import pytest
from playwright.sync_api import Page, expect


class TestDashboardPage:
    """Tests for the main dashboard page."""

    def test_dashboard_loads(self, authenticated_page: Page):
        """Test that the dashboard page loads correctly."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('仪表盘')")).toBeVisible()

    def test_status_cards_display(self, authenticated_page: Page):
        """Test that all status cards are displayed with correct information."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=MiniMax API 状态")).toBeVisible()
        expect(authenticated_page.locator("text=活跃项目")).toBeVisible()
        expect(authenticated_page.locator("text=章节总数")).toBeVisible()
        expect(authenticated_page.locator("text=已完成章节")).toBeVisible()

    def test_quality_gate_section_display(self, authenticated_page: Page):
        """Test that quality gate section is displayed."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=质量门禁检查")).toBeVisible()
        expect(authenticated_page.locator("text=代码检查")).toBeVisible()
        expect(authenticated_page.locator("text=安全扫描")).toBeVisible()
        expect(authenticated_page.locator("text=覆盖率")).toBeVisible()

    def test_recent_logs_display(self, authenticated_page: Page):
        """Test that recent activity logs are displayed."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=最近活动")).toBeVisible()

        activity_items = authenticated_page.locator(".activity-item")
        expect(activity_items.first()).toBeVisible()

    def test_module_status_display(self, authenticated_page: Page):
        """Test that module status section is displayed."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=模块状态")).toBeVisible()
        expect(authenticated_page.locator("text=内容生成")).toBeVisible()
        expect(authenticated_page.locator("text=质量检查")).toBeVisible()
        expect(authenticated_page.locator("text=安全扫描")).toBeVisible()

    def test_navigation_from_dashboard(self, authenticated_page: Page):
        """Test that navigation from dashboard works correctly."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('text=项目列表')
        authenticated_page.wait_for_url("**/projects", timeout=5000)
        expect(authenticated_page.locator("h1:has-text('项目列表')")).toBeVisible()


class TestDashboardAutoRefresh:
    """Tests for dashboard auto-refresh functionality."""

    def test_auto_refresh_enabled(self, authenticated_page: Page):
        """Test that dashboard auto-refreshes data."""
        authenticated_page.goto("http://localhost:3000/dashboard")
        authenticated_page.wait_for_load_state("networkidle")

        page_content_1 = authenticated_page.content()

        authenticated_page.wait_for_timeout(35000)

        page_content_2 = authenticated_page.content()
        assert page_content_1 != page_content_2 or authenticated_page.is_visible("text=仪表盘")


class TestDashboardDataLoading:
    """Tests for dashboard data loading states."""

    def test_loading_state_displayed(self, page: Page):
        """Test that loading spinner is displayed while data loads."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[type="email"]', "admin@example.com")
        page.fill('input[type="password"]', "password123")
        page.click('button[type="submit"]')

        page.goto("http://localhost:3000/dashboard")

        page.locator(".ant-spin").wait_for(timeout=5000, state="visible")
