import { test, expect } from '@playwright/test';

/**
 * E2E-T010: 创建教材项目
 */
test('user can create textbook project', async ({ page }) => {
  await page.goto('/dashboard');

  await page.click('button:has-text("新建项目")');

  await page.fill('input[name="name"]', '人工智能导论');
  await page.fill('textarea[name="description"]', '介绍人工智能基础知识的教材');

  await page.click('button[type="submit"]');

  await expect(page.locator('text=人工智能导论')).toBeVisible();
});

/**
 * E2E-T011: 创建章节
 */
test('user can create chapter', async ({ page }) => {
  await page.goto('/projects/test-project');

  await page.click('button:has-text("添加章节")');

  await page.fill('input[name="title"]', '第一章：人工智能概述');
  await page.fill('input[name="order"]', '1');

  await page.click('button[type="submit"]');

  await expect(page.locator('text=第一章：人工智能概述')).toBeVisible();
});

/**
 * E2E-T012: 章节列表分页
 */
test('chapter list pagination works', async ({ page }) => {
  await page.goto('/projects/test-project');

  const chapters = page.locator('[data-testid="chapter-card"]');
  const count = await chapters.count();

  expect(count).toBeGreaterThan(0);

  if (await page.locator('button:has-text("下一页")').isVisible()) {
    await page.click('button:has-text("下一页")');
    await expect(page.locator('text=第2页')).toBeVisible();
  }
});
