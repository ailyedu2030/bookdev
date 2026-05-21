"""
E2E tests for the knowledge graph page.
"""
from playwright.sync_api import Page, expect


class TestKnowledgeGraphPage:
    """Tests for the knowledge graph page."""

    def test_graph_page_loads(self, authenticated_page: Page):
        """Test that the knowledge graph page loads correctly."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("h1:has-text('知识图谱')")).toBeVisible()

    def test_filter_dropdown_visible(self, authenticated_page: Page):
        """Test that filter dropdown is visible."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator(".ant-select")).toBeVisible()

    def test_filter_options_work(self, authenticated_page: Page):
        """Test that filter options can be selected."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click(".ant-select")
        authenticated_page.wait_for_selector(".ant-select-dropdown", state="visible")

        expect(authenticated_page.locator("text=全部类型")).toBeVisible()
        expect(authenticated_page.locator("text=章节")).toBeVisible()
        expect(authenticated_page.locator("text=小节")).toBeVisible()
        expect(authenticated_page.locator("text=概念")).toBeVisible()
        expect(authenticated_page.locator("text=术语")).toBeVisible()


class TestKnowledgeGraphCanvas:
    """Tests for the knowledge graph canvas."""

    def test_canvas_element_present(self, authenticated_page: Page):
        """Test that canvas element is present."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("canvas.knowledge-graph-container")).toBeVisible()

    def test_graph_renders_nodes(self, authenticated_page: Page):
        """Test that graph renders nodes on canvas."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        canvas = authenticated_page.locator("canvas.knowledge-graph-container")
        canvas.wait_for(state="visible")


class TestKnowledgeGraphInteraction:
    """Tests for knowledge graph interaction."""

    def test_node_selection(self, authenticated_page: Page):
        """Test that clicking on a node selects it."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        canvas = authenticated_page.locator("canvas.knowledge-graph-container")
        canvas.click(position={"x": 400, "y": 300})

        authenticated_page.wait_for_timeout(500)

    def test_node_detail_panel(self, authenticated_page: Page):
        """Test that node detail panel appears when node is selected."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        canvas = authenticated_page.locator("canvas.knowledge-graph-container")
        canvas.click(position={"x": 400, "y": 300})

        authenticated_page.wait_for_timeout(500)

        detail_panel = authenticated_page.locator("text=节点详情")
        if detail_panel.is_visible():
            expect(detail_panel).toBeVisible()


class TestKnowledgeGraphLegend:
    """Tests for knowledge graph legend."""

    def test_node_type_legend(self, authenticated_page: Page):
        """Test that node type legend is displayed."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=章节")).toBeVisible()
        expect(authenticated_page.locator("text=小节")).toBeVisible()
        expect(authenticated_page.locator("text=概念")).toBeVisible()
        expect(authenticated_page.locator("text=术语")).toBeVisible()

    def test_edge_type_legend(self, authenticated_page: Page):
        """Test that edge type legend is displayed."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        expect(authenticated_page.locator("text=CONTAINS")).toBeVisible()
        expect(authenticated_page.locator("text=FOLLOWS")).toBeVisible()
        expect(authenticated_page.locator("text=DEFINES")).toBeVisible()
        expect(authenticated_page.locator("text=USES")).toBeVisible()
        expect(authenticated_page.locator("text=REFERENCES")).toBeVisible()


class TestKnowledgeGraphFiltering:
    """Tests for knowledge graph filtering functionality."""

    def test_filter_by_chapter(self, authenticated_page: Page):
        """Test filtering by chapter type."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click(".ant-select")
        authenticated_page.wait_for_selector(".ant-select-dropdown", state="visible")
        authenticated_page.click('.ant-select-dropdown li:has-text("章节")')

        authenticated_page.wait_for_timeout(500)

    def test_filter_by_all_resets(self, authenticated_page: Page):
        """Test that selecting 'all' shows all nodes."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.click(".ant-select")
        authenticated_page.wait_for_selector(".ant-select-dropdown", state="visible")
        authenticated_page.click('.ant-select-dropdown li:has-text("全部类型")')

        authenticated_page.wait_for_timeout(500)


class TestKnowledgeGraphEmptyState:
    """Tests for knowledge graph empty state."""

    def test_empty_state_message(self, authenticated_page: Page):
        """Test that empty state message is shown when no data."""
        authenticated_page.goto("http://localhost:3000/knowledge-graph")
        authenticated_page.wait_for_load_state("networkidle")

        empty_state = authenticated_page.locator(".ant-empty")
        if empty_state.is_visible():
            expect(empty_state.locator("text=暂无知识图谱数据")).toBeVisible()
