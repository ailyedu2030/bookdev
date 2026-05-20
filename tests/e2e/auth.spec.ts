import { test, expect } from '@playwright/test';

/**
 * E2E-T001: 用户登录流程
 */
test('user can login', async ({ page }) => {
  await page.goto('/login');

  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');

  await page.click('button[type="submit"]');

  await expect(page).toHaveURL(/\/dashboard/);
});

/**
 * E2E-T002: 用户注册流程
 */
test('new user can register', async ({ page }) => {
  await page.goto('/register');

  await page.fill('input[name="username"]', 'newuser');
  await page.fill('input[name="email"]', 'newuser@example.com');
  await page.fill('input[name="password"]', 'SecurePass123!');
  await page.fill('input[name="confirmPassword"]', 'SecurePass123!');

  await page.click('button[type="submit"]');

  await expect(page).toHaveURL(/\/dashboard/);
});

/**
 * E2E-T003: 登录失败处理
 */
test('login fails with invalid credentials', async ({ page }) => {
  await page.goto('/login');

  await page.fill('input[name="email"]', 'wrong@example.com');
  await page.fill('input[name="password"]', 'wrongpassword');

  await page.click('button[type="submit"]');

  await expect(page.locator('text=Invalid credentials')).toBeVisible();
});
