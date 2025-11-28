import { test, expect } from '@playwright/test';

/**
 * Brand Mentions Analytics Tests
 *
 * These tests verify the Brand Mentions analytics page functionality.
 * Tests run against Railway development environment with authenticated state.
 */

// Use authenticated state from fixtures
test.use({ storageState: 'e2e/fixtures/auth.json' });

test.describe('Brand Mentions Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to brand mentions page
    await page.goto('/analytics/brand-mentions');
  });

  test('should display page title', async ({ page }) => {
    // Verify page title
    const heading = page.locator('h1, h2').first();
    await expect(heading).toContainText(/brand mentions/i);
  });

  test('should display explanation text', async ({ page }) => {
    // Verify explanatory text is present
    const explanation = page.locator('text=/Brand Mentions.*tracks/i');
    await expect(explanation).toBeVisible();
  });

  test('should display Brand Mentions over time chart', async ({ page }) => {
    // Wait for chart to load
    await page.waitForSelector('[role="img"]', { timeout: 10000 });

    // Verify chart title
    const chartTitle = page.locator('text=/Brand Mention Rate Over Time/i');
    await expect(chartTitle).toBeVisible();

    // Verify chart container exists
    const chartContainer = page.locator('.recharts-responsive-container').first();
    await expect(chartContainer).toBeVisible();
  });

  test('should display platform breakdown chart', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Verify platform breakdown section
    const platformSection = page.locator('text=/Brand Mention Rate by LLM Platform/i');
    await expect(platformSection).toBeVisible();

    // Verify all platforms are shown
    await expect(page.locator('text=ChatGPT')).toBeVisible();
    await expect(page.locator('text=Claude')).toBeVisible();
    await expect(page.locator('text=Gemini')).toBeVisible();
    await expect(page.locator('text=Perplexity')).toBeVisible();
  });

  test('should allow downloading chart as image', async ({ page }) => {
    // Find download button
    const downloadButton = page.locator('button:has-text("Image")').first();
    await expect(downloadButton).toBeVisible();

    // Click download (in real test, verify download happens)
    // For now, just verify button is clickable
    await expect(downloadButton).toBeEnabled();
  });

  test('should display collection history table', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Verify table exists (if data available)
    const table = page.locator('table');
    const tableVisible = await table.isVisible();

    if (tableVisible) {
      // Verify table headers
      await expect(page.locator('th:has-text("Date")')).toBeVisible();
      await expect(page.locator('th:has-text("Mention Rate")')).toBeVisible();
      await expect(page.locator('th:has-text("Mentions")')).toBeVisible();
      await expect(page.locator('th:has-text("Total Responses")')).toBeVisible();
    }
  });

  test('should handle no data state gracefully', async ({ page }) => {
    // If no data, should show info message
    const noDataMessage = page.locator('text=/No brand mention data available/i');
    const chartExists = await page.locator('.recharts-responsive-container').count();

    // Either chart exists OR no data message shown
    if (chartExists === 0) {
      await expect(noDataMessage).toBeVisible();
    }
  });
});

test.describe('Brand Mentions Interactivity', () => {
  test('should show tooltip on chart hover', async ({ page }) => {
    await page.goto('/analytics/brand-mentions');

    // Wait for chart to render
    await page.waitForSelector('.recharts-responsive-container');

    // Hover over a data point (if exists)
    const dataPoint = page.locator('.recharts-line-dot').first();
    const pointExists = await dataPoint.count();

    if (pointExists > 0) {
      await dataPoint.hover();

      // Tooltip should appear
      const tooltip = page.locator('.recharts-tooltip-wrapper');
      await expect(tooltip).toBeVisible();
    }
  });
});

/**
 * To run these tests:
 *    npm run test:e2e -- brand-mentions
 *
 * Or run all E2E tests:
 *    npm run test:e2e
 *
 * Note: Auth state expires after the JWT token expires.
 * If tests fail with auth errors, regenerate auth.json by logging in
 * to Railway and running the localStorage extraction script again.
 */
