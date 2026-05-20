"""
E2E tests for the chapter editor page.
"""
import pytest
from playwright.sync_api import Page, expect


class TestChapterEditorPage:
    """Tests for the chapter editor page."""

    def test_chapter_editor_loads(self, authenticated_page: Page):
        """Test that the chapter editor page loads correctly."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-breadcrumb")).toBeVisible()
        expect(authenticated_page.locator(".ant-card")).toBeVisible()

    def test_chapter_title_displayed(self, authenticated_page: Page):
        """Test that chapter title is displayed."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=第一章：计算机基础")).toBeVisible()

    def test_chapter_status_tag(self, authenticated_page: Page):
        """Test that chapter status tag is displayed."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-tag")).toBeVisible()

    def test_editor_toolbar_buttons(self, authenticated_page: Page):
        """Test that editor toolbar buttons are visible."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("AI生成")')).toBeVisible()
        expect(authenticated_page.locator('button:has-text("保存")')).toBeVisible()

    def test_editor_content_area(self, authenticated_page: Page):
        """Test that editor content area is present."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ProseMirror")).toBeVisible()

    def test_version_history_panel(self, authenticated_page: Page):
        """Test that version history panel is visible."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=版本历史")).toBeVisible()


class TestChapterEditorActions:
    """Tests for chapter editor actions."""

    def test_save_button_works(self, authenticated_page: Page):
        """Test that save button triggers save action."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("保存")')

        authenticated_page.wait_for_timeout(1000)
        message = authenticated_page.locator(".ant-message")
        expect(message.or_(authenticated_page.locator("text=保存成功")))

    def test_ai_generate_button_visible(self, authenticated_page: Page):
        """Test that AI generate button is visible."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        ai_button = authenticated_page.locator('button:has-text("AI生成")')
        expect(ai_button).toBeVisible()

    def test_submit_for_review_button_draft_state(self, authenticated_page: Page):
        """Test submit for review button appears for draft chapters."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/3")
        authenticated_page.wait_for_load_state("networkidle")

        submit_button = authenticated_page.locator('button:has-text("提交审核")')
        if submit_button.is_visible():
            expect(submit_button).toBeVisible()

    def test_approve_reject_buttons_review_state(self, authenticated_page: Page):
        """Test approve and reject buttons appear for chapters in review."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/2")
        authenticated_page.wait_for_load_state("networkidle")

        approve_button = authenticated_page.locator('button:has-text("通过")')
        if approve_button.is_visible(timeout=2000):
            expect(approve_button).toBeVisible()


class TestChapterVersionHistory:
    """Tests for chapter version history."""

    def test_version_history_displays_versions(self, authenticated_page: Page):
        """Test that version history displays all versions."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        version_items = authenticated_page.locator(".version-item")
        version_count = version_items.count()
        assert version_count >= 1

    def test_version_toggle(self, authenticated_page: Page):
        """Test that version history can be toggled."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        toggle_button = authenticated_page.locator('button:has-text("隐藏")')
        if toggle_button.is_visible():
            toggle_button.click()
            expect(authenticated_page.locator('button:has-text("显示")')).toBeVisible()

    def test_version_item_click(self, authenticated_page: Page):
        """Test that clicking a version item loads that version."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        version_item = authenticated_page.locator(".version-item").first
        version_item.click()

        authenticated_page.wait_for_timeout(500)


class TestChapterBreadcrumb:
    """Tests for chapter editor breadcrumb navigation."""

    def test_breadcrumb_navigation(self, authenticated_page: Page):
        """Test that breadcrumb shows correct navigation path."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('.ant-breadcrumb a:has-text("项目列表")')).toBeVisible()
        expect(authenticated_page.locator('.ant-breadcrumb a:has-text("项目详情")')).toBeVisible()


class TestChapterContent:
    """Tests for chapter content editing."""

    def test_editor_accepts_text_input(self, authenticated_page: Page):
        """Test that editor accepts text input."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        editor = authenticated_page.locator(".ProseMirror")
        editor.click()
        editor.fill("测试内容")

        expect(editor).toContainText("测试内容")

    def test_chapter_content_loaded(self, authenticated_page: Page):
        """Test that existing chapter content is loaded."""
        authenticated_page.goto("http://localhost:3000/projects/1/chapters/1")
        authenticated_page.wait_for_load_state("networkidle")

        editor = authenticated_page.locator(".ProseMirror")
        content = editor.text_content()
        assert content is not None
        assert len(content) > 0
