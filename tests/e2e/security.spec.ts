import { test, expect } from '@playwright/test';

/**
 * E2E-T030: 安全扫描页面加载
 */
test('security scan page loads', async ({ page }) => {
  await page.goto('/security');

  await expect(page.locator('h1:has-text("安全扫描")')).toBeVisible();
});

/**
 * E2E-T031: DOI验证功能
 */
test('DOI verification works', async ({ page }) => {
  await page.goto('/security');

  await page.fill('input[name="doi"]', '10.1234/test.2024');

  await page.click('button:has-text("验证")');

  await page.waitForTimeout(1000);

  await expect(page.locator('text=验证结果')).toBeVisible();
});

/**
 * E2E-T032: 法规验证功能
 */
test('regulation verification works', async ({ page }) => {
  await page.goto('/security');

  await page.fill('textarea[name="content"]', '根据《网络安全法》第47条...');

  await page.click('button:has-text("检查合规性")');

  await page.waitForTimeout(1000);

  await expect(page.locator('text=合规')).toBeVisible();
});

/**
 * E2E-T033: 监控仪表盘加载
 */
test('monitoring dashboard loads', async ({ page }) => {
  await page.goto('/monitor');

  await expect(page.locator('h1:has-text("监控")')).toBeVisible();
  await expect(page.locator('text=系统状态')).toBeVisible();
});

/**
 * E2E-T034: 监控指标显示
 */
test('monitoring metrics are displayed', async ({ page }) => {
  await page.goto('/monitor');

  await page.waitForTimeout(1000);

  await expect(page.locator('text=API调用')).toBeVisible();
  await expect(page.locator('text=Token消耗')).toBeVisible();
});
