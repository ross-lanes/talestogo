import { test, expect } from '@playwright/test';

/**
 * Authentication Tests
 *
 * These tests verify the login/logout flow.
 * Note: OAuth testing requires either:
 * 1. A test Google account with credentials in env vars
 * 2. Mocking the OAuth flow
 * 3. Manual login before tests (auth state storage)
 */

// These tests should run WITHOUT auth state to test login flow
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Login Page', () => {
  test('should display login page when not authenticated', async ({ page }) => {
    // Navigate to the app without auth
    await page.goto('/');

    // Should be redirected to login or see login UI
    await expect(page).toHaveURL(/.*login.*/i);

    // Verify Google login button is present (rendered as iframe by @react-oauth/google)
    const googleLoginIframe = page.frameLocator('iframe[src*="accounts.google.com"]');
    const googleButton = googleLoginIframe.locator('button, div[role="button"]').first();
    await expect(googleButton).toBeVisible({ timeout: 10000 });
  });

  test('should show login UI elements', async ({ page }) => {
    await page.goto('/login');

    // Verify page title contains expected text
    await expect(page).toHaveTitle(/RobotRachel Apps Suite/i);

    // Verify branding/logo is present
    const logo = page.locator('img').first();
    await expect(logo).toBeVisible();
  });
});

test.describe('Protected Routes', () => {
  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Try to access a protected route (dashboard, analytics, etc.)
    await page.goto('/dashboard');

    // Should be redirected to login
    await expect(page).toHaveURL(/.*login.*/i);
  });

  test('should redirect to login when accessing analytics without auth', async ({ page }) => {
    await page.goto('/analytics/brand-mentions');

    // Should be redirected to login
    await expect(page).toHaveURL(/.*login.*/i);
  });
});

/**
 * Note: To test actual login flow, you'll need to either:
 *
 * 1. Use Playwright's auth storage:
 *    - Login manually once
 *    - Store auth state: await page.context().storageState({ path: 'auth.json' })
 *    - Reuse in tests: { storageState: 'auth.json' }
 *
 * 2. Use environment variables for test account:
 *    - Set PLAYWRIGHT_TEST_EMAIL and PLAYWRIGHT_TEST_PASSWORD
 *    - Automate Google OAuth flow
 *
 * 3. Mock the OAuth response:
 *    - Intercept API calls
 *    - Return mock JWT tokens
 *
 * Example auth fixture (for future use):
 *
 * test.use({
 *   storageState: 'e2e/fixtures/auth.json'
 * });
 */
