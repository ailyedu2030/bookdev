import { test, expect } from '@playwright/test';

/**
 * E2E-T020: 知识图谱页面加载
 */
test('knowledge graph page loads', async ({ page }) => {
  await page.goto('/knowledge-graph');

  await expect(page.locator('h1:has-text("知识图谱")')).toBeVisible();
});

/**
 * E2E-T021: 知识图谱节点搜索
 */
test('knowledge graph node search works', async ({ page }) => {
  await page.goto('/knowledge-graph');

  await page.fill('input[placeholder="搜索节点"]', '人工智能');

  await page.waitForTimeout(500);

  await expect(page.locator('[data-testid="node-card"]').first()).toBeVisible();
});

/**
 * E2E-T022: 术语表页面加载
 */
test('term glossary page loads', async ({ page }) => {
  await page.goto('/terms');

  await expect(page.locator('h1:has-text("术语表")')).toBeVisible();
});

/**
 * E2E-T023: 添加新术语
 */
test('user can add new term', async ({ page }) => {
  await page.goto('/terms');

  await page.click('button:has-text("添加术语")');

  await page.fill('input[name="term"]', '人工智能');
  await page.fill('input[name="definition"]', 'Artificial Intelligence，使机器具有人类智能的技术');

  await page.click('button[type="submit"]');

  await expect(page.locator('text=人工智能')).toBeVisible();
});
