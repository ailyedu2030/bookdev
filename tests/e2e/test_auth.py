"""
E2E tests for authentication pages: login, register, logout.
"""
from playwright.sync_api import Page, expect


class TestLoginPage:
    """Tests for the login page."""

    def test_login_page_loads(self, page: Page):
        """Test that the login page loads correctly with all elements."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        expect(page.locator("text=AI教材开发系统")).toBeVisible()
        expect(page.locator("text=登录到您的账户")).toBeVisible()
        expect(page.locator('input[type="email"]')).toBeVisible()
        expect(page.locator('input[type="password"]')).toBeVisible()
        expect(page.locator('button[type="submit"]')).toBeVisible()
        expect(page.locator("text=注册")).toBeVisible()

    def test_login_page_redirects_authenticated_user(self, authenticated_page: Page):
        """Test that authenticated users are redirected away from login page."""
        authenticated_page.goto("http://localhost:3000/login")
        authenticated_page.wait_for_url("**/dashboard", timeout=5000)

    def test_register_link_works(self, page: Page):
        """Test that the register link navigates to register page."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.click("text=注册")
        page.wait_for_url("**/register", timeout=5000)

        expect(page.locator("text=创建账户")).toBeVisible()


class TestLoginFunctionality:
    """Tests for login functionality."""

    def test_login_success(self, page: Page):
        """Test successful login with valid credentials."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[type="email"]', "admin@example.com")
        page.fill('input[type="password"]', "password123")
        page.click('button[type="submit"]')

        page.wait_for_url("**/dashboard", timeout=10000)

        expect(page.locator("text=仪表盘")).toBeVisible()

    def test_login_failure_with_invalid_credentials(self, page: Page):
        """Test login failure with invalid credentials shows error message."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[type="email"]', "invalid@example.com")
        page.fill('input[type="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        page.wait_for_selector(".ant-message-error", timeout=5000)
        expect(page.locator(".ant-message-error")).toBeVisible()

    def test_login_failure_with_empty_fields(self, page: Page):
        """Test that empty fields show validation errors."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.click('button[type="submit"]')

        expect(page.locator("text=请输入邮箱")).toBeVisible()


class TestLogout:
    """Tests for logout functionality."""

    def test_logout(self, authenticated_page: Page):
        """Test that user can logout successfully."""
        authenticated_page.wait_for_selector('[class*="ant-dropdown-trigger"]', timeout=5000)
        authenticated_page.click('[class*="ant-dropdown-trigger"]')
        authenticated_page.wait_for_selector(".ant-dropdown-menu", timeout=5000)
        authenticated_page.click("text=退出登录")

        authenticated_page.wait_for_url("**/login", timeout=5000)
        expect(authenticated_page.locator("text=AI教材开发系统")).toBeVisible()


class TestRegisterPage:
    """Tests for the register page."""

    def test_register_page_loads(self, page: Page):
        """Test that the register page loads correctly."""
        page.goto("http://localhost:3000/register")
        page.wait_for_load_state("networkidle")

        expect(page.locator("text=创建账户")).toBeVisible()
        expect(page.locator("text=注册AI教材开发系统")).toBeVisible()
        expect(page.locator('input[placeholder="姓名"]')).toBeVisible()
        expect(page.locator('input[placeholder="邮箱地址"]')).toBeVisible()
        expect(page.locator('input[placeholder="密码"]')).toBeVisible()
        expect(page.locator('input[placeholder="确认密码"]')).toBeVisible()
        expect(page.locator('button[type="submit"]')).toBeVisible()

    def test_register_link_redirects_authenticated_user(self, authenticated_page: Page):
        """Test that authenticated users are redirected away from register page."""
        authenticated_page.goto("http://localhost:3000/register")
        authenticated_page.wait_for_url("**/dashboard", timeout=5000)

    def test_login_link_works(self, page: Page):
        """Test that the login link navigates to login page."""
        page.goto("http://localhost:3000/register")
        page.wait_for_load_state("networkidle")

        page.click("text=登录")
        page.wait_for_url("**/login", timeout=5000)

        expect(page.locator("text=登录到您的账户")).toBeVisible()
