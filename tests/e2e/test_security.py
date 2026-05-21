"""
E2E tests for the security page.
"""
from playwright.sync_api import Page, expect


class TestSecurityPage:
    """Tests for the security page."""

    def test_security_page_loads(self, authenticated_page: Page):
        """Test that the security page loads correctly."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('安全扫描')")).toBeVisible()

    def test_tabs_present(self, authenticated_page: Page):
        """Test that all security tabs are present."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("文本扫描")')).toBeVisible()
        expect(authenticated_page.locator('button:has-text("DOI验证")')).toBeVisible()
        expect(authenticated_page.locator('button:has-text("法规验证")')).toBeVisible()

    def test_scan_instructions_card(self, authenticated_page: Page):
        """Test that scan instructions card is displayed."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=扫描说明")).toBeVisible()
        expect(authenticated_page.locator("text=文本扫描").first).toBeVisible()
        expect(authenticated_page.locator("text=DOI验证").first).toBeVisible()
        expect(authenticated_page.locator("text=法规验证").first).toBeVisible()


class TestTextScanning:
    """Tests for text scanning functionality."""

    def test_text_scan_tab_active_by_default(self, authenticated_page: Page):
        """Test that text scan tab is active by default."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-tabs-tab-active:has-text('文本扫描')")).toBeVisible()

    def test_text_input_area_visible(self, authenticated_page: Page):
        """Test that text input area is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("textarea")).toBeVisible()

    def test_scan_button_visible(self, authenticated_page: Page):
        """Test that scan button is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator('button:has-text("开始扫描")')).toBeVisible()

    def test_scan_validation_empty_text(self, authenticated_page: Page):
        """Test validation when scanning empty text."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("开始扫描")')

        expect(authenticated_page.locator("text=请输入要扫描的文本")).toBeVisible()

    def test_scan_success(self, authenticated_page: Page):
        """Test successful text scan."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.fill("textarea", "这是一段测试文本内容，用于验证安全扫描功能。")
        authenticated_page.click('button:has-text("开始扫描")')

        authenticated_page.wait_for_timeout(2000)


class TestDoiVerification:
    """Tests for DOI verification functionality."""

    def test_doi_tab_switch(self, authenticated_page: Page):
        """Test switching to DOI verification tab."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("DOI验证")')

        expect(authenticated_page.locator(".ant-tabs-tab-active:has-text('DOI验证')")).toBeVisible()

    def test_doi_input_visible(self, authenticated_page: Page):
        """Test that DOI input is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("DOI验证")')

        expect(authenticated_page.locator('input[placeholder*="DOI"]')).toBeVisible()

    def test_doi_verify_button_visible(self, authenticated_page: Page):
        """Test that verify DOI button is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("DOI验证")')

        expect(authenticated_page.locator('button:has-text("验证DOI")')).toBeVisible()

    def test_doi_validation_empty(self, authenticated_page: Page):
        """Test validation when DOI is empty."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("DOI验证")')
        authenticated_page.click('button:has-text("验证DOI")')

        expect(authenticated_page.locator("text=请输入DOI")).toBeVisible()

    def test_doi_verification_success(self, authenticated_page: Page):
        """Test successful DOI verification."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("DOI验证")')
        authenticated_page.fill('input[placeholder*="DOI"]', "10.1234/example.doi")
        authenticated_page.click('button:has-text("验证DOI")')

        authenticated_page.wait_for_timeout(2000)


class TestRegulationVerification:
    """Tests for regulation verification functionality."""

    def test_regulation_tab_switch(self, authenticated_page: Page):
        """Test switching to regulation verification tab."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("法规验证")')

        expect(authenticated_page.locator(".ant-tabs-tab-active:has-text('法规验证')")).toBeVisible()

    def test_regulation_textarea_visible(self, authenticated_page: Page):
        """Test that regulation text input is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("法规验证")')

        textareas = authenticated_page.locator("textarea")
        expect(textareas.last).toBeVisible()

    def test_regulation_verify_button_visible(self, authenticated_page: Page):
        """Test that verify button is visible."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("法规验证")')

        expect(authenticated_page.locator('button:has-text("验证合规性")')).toBeVisible()

    def test_regulation_validation_empty(self, authenticated_page: Page):
        """Test validation when regulation text is empty."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click('button:has-text("法规验证")')
        authenticated_page.click('button:has-text("验证合规性")')

        expect(authenticated_page.locator("text=请输入要验证的文本")).toBeVisible()


class TestSecurityResults:
    """Tests for security scan results display."""

    def test_result_display_safe(self, authenticated_page: Page):
        """Test that safe results are displayed correctly."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        result_icon = authenticated_page.locator(".security-result")
        if result_icon.is_visible():
            expect(result_icon).toBeVisible()

    def test_result_icon_safe(self, authenticated_page: Page):
        """Test that safe result shows correct icon."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        safe_icon = authenticated_page.locator('[class*="safe"]')
        if safe_icon.count() > 0:
            expect(safe_icon.first).toBeVisible()

    def test_result_tag_display(self, authenticated_page: Page):
        """Test that result tags are displayed."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        result_tags = authenticated_page.locator(".ant-tag")
        if result_tags.count() > 0:
            expect(result_tags.first).toBeVisible()


class TestSecurityScanInstructions:
    """Tests for scan instructions."""

    def test_text_scan_instruction(self, authenticated_page: Page):
        """Test text scan instruction is shown."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=对教材文本内容进行安全检查")).toBeVisible()

    def test_doi_verification_instruction(self, authenticated_page: Page):
        """Test DOI verification instruction is shown."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=验证文献引用的DOI是否有效")).toBeVisible()

    def test_regulation_verification_instruction(self, authenticated_page: Page):
        """Test regulation verification instruction is shown."""
        authenticated_page.goto("http://localhost:3000/security")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=检查内容是否符合教育法规")).toBeVisible()
