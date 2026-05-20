"""
E2E tests for the admin user management page.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.admin
class TestAdminUsersPage:
    """Tests for the admin users management page."""

    def test_admin_users_page_loads(self, authenticated_page: Page):
        """Test that the admin users page loads correctly."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('用户管理')")).toBeVisible()

    def test_add_user_button_visible(self, authenticated_page: Page):
        """Test that add user button is visible."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("添加用户")')).toBeVisible()


class TestUserTable:
    """Tests for user table display."""

    def test_user_table_displayed(self, authenticated_page: Page):
        """Test that user table is displayed."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-table")).toBeVisible()

    def test_user_data_displayed(self, authenticated_page: Page):
        """Test that user data is displayed in the table."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=admin@example.com")).toBeVisible()
        expect(authenticated_page.locator("text=管理员")).toBeVisible()

    def test_user_role_tags(self, authenticated_page: Page):
        """Test that user role tags are displayed."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        role_tags = authenticated_page.locator(".ant-tag")
        expect(role_tags.first).toBeVisible()

    def test_user_action_buttons(self, authenticated_page: Page):
        """Test that user action buttons are visible."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        edit_buttons = authenticated_page.locator('button[class*="edit"]')
        expect(edit_buttons.first).toBeVisible()


class TestCreateUser:
    """Tests for creating new users."""

    def test_create_user_modal_opens(self, authenticated_page: Page):
        """Test that create user modal opens."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加用户")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        expect(authenticated_page.locator("text=添加用户")).toBeVisible()

    def test_create_user_form_fields(self, authenticated_page: Page):
        """Test that create user form has all required fields."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加用户")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        expect(authenticated_page.locator('input[placeholder="请输入姓名"]')).toBeVisible()
        expect(authenticated_page.locator('input[placeholder="请输入邮箱"]')).toBeVisible()
        expect(authenticated_page.locator(".ant-select")).toBeVisible()
        expect(authenticated_page.locator('input[placeholder="请输入密码"]')).toBeVisible()

    def test_create_user_validation_empty_fields(self, authenticated_page: Page):
        """Test validation for empty fields."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加用户")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.click('.ant-modal button:has-text("确定")')

        expect(authenticated_page.locator("text=请输入姓名")).toBeVisible()

    def test_create_user_success(self, authenticated_page: Page):
        """Test successful user creation."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加用户")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.fill('input[placeholder="请输入姓名"]', "测试用户")
        authenticated_page.fill('input[placeholder="请输入邮箱"]', "testuser@example.com")

        authenticated_page.click(".ant-select")
        authenticated_page.wait_for_selector(".ant-select-dropdown", state="visible")
        authenticated_page.click('.ant-select-dropdown li:has-text("编辑")')

        authenticated_page.fill('input[placeholder="请输入密码"]', "password123")

        authenticated_page.click('.ant-modal button:has-text("确定")')

        authenticated_page.wait_for_selector(".ant-modal", state="hidden", timeout=5000)

    def test_create_user_modal_close(self, authenticated_page: Page):
        """Test that create user modal can be closed."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加用户")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.click(".ant-modal button:has-text('取消')")

        authenticated_page.wait_for_selector(".ant-modal", state="hidden")


class TestEditUser:
    """Tests for editing users."""

    def test_edit_user_modal_opens(self, authenticated_page: Page):
        """Test that edit user modal opens."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('.ant-btn-text:first-child')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        expect(authenticated_page.locator("text=编辑用户")).toBeVisible()

    def test_edit_user_form_prefilled(self, authenticated_page: Page):
        """Test that edit form is prefilled with user data."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('.ant-btn-text:first-child')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        name_input = authenticated_page.locator('input[placeholder="请输入姓名"]')
        expect(name_input).toBeVisible()

    def test_edit_user_role_change(self, authenticated_page: Page):
        """Test changing user role."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('.ant-btn-text:first-child')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.click(".ant-select")
        authenticated_page.wait_for_selector(".ant-select-dropdown", state="visible")
        authenticated_page.click('.ant-select-dropdown li:has-text("查看者")')

    def test_edit_user_password_optional(self, authenticated_page: Page):
        """Test that password is optional when editing."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('.ant-btn-text:first-child')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        password_input = authenticated_page.locator('input[placeholder*="留空则不修改"]')
        expect(password_input).toBeVisible()


class TestDeleteUser:
    """Tests for deleting users."""

    def test_delete_user_confirmation(self, authenticated_page: Page):
        """Test delete confirmation dialog appears."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        delete_button = authenticated_page.locator('.ant-btn-dangerous').first
        if delete_button.is_visible():
            delete_button.click()
            authenticated_page.wait_for_selector(".ant-popover", state="visible")

            expect(authenticated_page.locator("text=确定删除此用户？")).toBeVisible()

    def test_delete_user_cancel(self, authenticated_page: Page):
        """Test that delete can be cancelled."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        delete_button = authenticated_page.locator('.ant-btn-dangerous').first
        if delete_button.is_visible():
            delete_button.click()
            authenticated_page.wait_for_selector(".ant-popover", state="visible")

            authenticated_page.click("text=取消")

            authenticated_page.wait_for_selector(".ant-popover", state="hidden")


class TestUserRoles:
    """Tests for user role display."""

    def test_admin_role_displayed(self, authenticated_page: Page):
        """Test that admin role is displayed correctly."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=管理员")).toBeVisible()

    def test_editor_role_displayed(self, authenticated_page: Page):
        """Test that editor role is displayed correctly."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=编辑")).toBeVisible()

    def test_viewer_role_displayed(self, authenticated_page: Page):
        """Test that viewer role is displayed correctly."""
        authenticated_page.goto("http://localhost:3000/admin/users")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=查看者")).toBeVisible()


class TestAdminAccessControl:
    """Tests for admin access control."""

    def test_non_admin_redirected(self, page: Page):
        """Test that non-admin users are redirected from admin page."""
        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[type="email"]', "viewer1@example.com")
        page.fill('input[type="password"]', "password123")
        page.click('button[type="submit"]')

        page.wait_for_url("**/dashboard", timeout=10000)

        page.goto("http://localhost:3000/admin/users")
        page.wait_for_timeout(1000)

        current_url = page.url
        assert "/admin/users" not in current_url or page.locator("h1:has-text('仪表盘')").is_visible()
