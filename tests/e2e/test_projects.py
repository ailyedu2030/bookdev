"""
E2E tests for the projects page and project detail page.
"""
from playwright.sync_api import Page, expect


class TestProjectsPage:
    """Tests for the projects list page."""

    def test_projects_page_loads(self, authenticated_page: Page):
        """Test that the projects page loads correctly."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('项目列表')")).toBeVisible()

    def test_create_project_button_visible(self, authenticated_page: Page):
        """Test that create project button is visible."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("创建项目")')).toBeVisible()

    def test_project_list_displays(self, authenticated_page: Page):
        """Test that project list displays projects correctly."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        project_cards = authenticated_page.locator(".ant-card-hoverable")
        expect(project_cards.first()).toBeVisible()

        expect(authenticated_page.locator("text=计算机科学导论")).toBeVisible()
        expect(authenticated_page.locator("text=人工智能基础")).toBeVisible()

    def test_project_card_status_tags(self, authenticated_page: Page):
        """Test that project status tags are displayed correctly."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=进行中")).toBeVisible()
        expect(authenticated_page.locator("text=已完成")).toBeVisible()

    def test_project_progress_displayed(self, authenticated_page: Page):
        """Test that project progress is displayed on cards."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        progress_elements = authenticated_page.locator(".ant-progress")
        expect(progress_elements.first()).toBeVisible()


class TestCreateProject:
    """Tests for creating new projects."""

    def test_create_project_modal_opens(self, authenticated_page: Page):
        """Test that create project modal opens when button is clicked."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("创建项目")')

        modal = authenticated_page.locator(".ant-modal")
        expect(modal).toBeVisible()
        expect(modal.locator("text=创建新项目")).toBeVisible()

    def test_create_project_modal_form_fields(self, authenticated_page: Page):
        """Test that create project modal has all required form fields."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("创建项目")')

        expect(authenticated_page.locator('input[id*="name"]')).toBeVisible()
        expect(authenticated_page.locator("text=项目名称")).toBeVisible()
        expect(authenticated_page.locator("text=项目描述")).toBeVisible()

    def test_create_project_validation(self, authenticated_page: Page):
        """Test that form validation works for empty fields."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("创建项目")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.click('.ant-modal button:has-text("确定")')

        expect(authenticated_page.locator("text=请输入项目名称")).toBeVisible()

    def test_create_project_success(self, authenticated_page: Page):
        """Test successful project creation."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("创建项目")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.fill('input[id*="name"]', "测试项目")
        authenticated_page.fill("textarea", "这是一个测试项目的描述")

        authenticated_page.click('.ant-modal button:has-text("确定")')

        authenticated_page.wait_for_selector(".ant-modal", state="hidden", timeout=5000)
        expect(authenticated_page.locator("text=项目创建成功")).toBeVisible()

    def test_create_project_modal_close(self, authenticated_page: Page):
        """Test that create project modal can be closed."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("创建项目")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        authenticated_page.click(".ant-modal button:has-text('取消')")

        authenticated_page.wait_for_selector(".ant-modal", state="hidden")


class TestProjectDetailPage:
    """Tests for the project detail page."""

    def test_project_detail_page(self, authenticated_page: Page):
        """Test that project detail page loads correctly."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=计算机科学导论")).toBeVisible()
        expect(authenticated_page.locator("text=章节列表")).toBeVisible()

    def test_project_detail_breadcrumb(self, authenticated_page: Page):
        """Test that breadcrumb navigation is correct."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('.ant-breadcrumb a:has-text("项目列表")')).toBeVisible()

    def test_chapter_list_displayed(self, authenticated_page: Page):
        """Test that chapter list is displayed in project detail."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=第一章：计算机基础")).toBeVisible()
        expect(authenticated_page.locator("text=第二章：算法入门")).toBeVisible()

    def test_chapter_status_displayed(self, authenticated_page: Page):
        """Test that chapter status tags are displayed."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=已批准")).toBeVisible()
        expect(authenticated_page.locator("text=审核中")).toBeVisible()
        expect(authenticated_page.locator("text=草稿")).toBeVisible()

    def test_add_chapter_button(self, authenticated_page: Page):
        """Test that add chapter button is visible."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("添加章节")')).toBeVisible()

    def test_add_chapter_modal(self, authenticated_page: Page):
        """Test that add chapter modal works."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("添加章节")')
        authenticated_page.wait_for_selector(".ant-modal", state="visible")

        expect(authenticated_page.locator("text=添加新章节")).toBeVisible()
        expect(authenticated_page.locator('input[id*="title"]')).toBeVisible()

    def test_project_progress_bar(self, authenticated_page: Page):
        """Test that project progress bar is displayed."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-progress")).toBeVisible()


class TestProjectNavigation:
    """Tests for project navigation."""

    def test_navigate_to_project_detail(self, authenticated_page: Page):
        """Test navigating from projects list to project detail."""
        authenticated_page.goto("http://localhost:3000/projects")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click(".ant-card-hoverable:first-child")
        authenticated_page.wait_for_url("**/projects/1", timeout=5000)

        expect(authenticated_page.locator("h1:has-text('计算机科学导论')")).toBeVisible()

    def test_navigate_to_chapter_editor(self, authenticated_page: Page):
        """Test navigating from project detail to chapter editor."""
        authenticated_page.goto("http://localhost:3000/projects/1")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('.ant-list-item:first-child')
        authenticated_page.wait_for_url("**/chapters/**", timeout=5000)

        expect(authenticated_page.locator("h1, .ant-card-head")).toBeVisible()
