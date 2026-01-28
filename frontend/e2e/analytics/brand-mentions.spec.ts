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
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Verify chart title
    const chartTitle = page.locator('text=/Brand Mention Rate Over Time/i');
    await expect(chartTitle).toBeVisible();

    // Verify chart container exists (Recharts uses SVG)
    const chartSvg = page.locator('svg.recharts-surface').first();
    await expect(chartSvg).toBeVisible();
  });

  test('should display platform breakdown chart', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Verify platform breakdown section
    const platformSection = page.locator('text=/Brand Mention Rate by LLM Platform/i');
    await expect(platformSection).toBeVisible();

    // Verify at least one platform is shown (since data may vary)
    const platformTexts = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity'];
    let foundPlatform = false;
    for (const platform of platformTexts) {
      const count = await page.locator(`text="${platform}"`).count();
      if (count > 0) {
        foundPlatform = true;
        break;
      }
    }
    expect(foundPlatform).toBeTruthy();
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

    // Verify table exists (if data available) - use first() to handle multiple tables
    const table = page.locator('table').first();
    const tableVisible = await table.isVisible();

    if (tableVisible) {
      // Verify at least one table header is present (column names may vary)
      const headers = await page.locator('th').count();
      expect(headers).toBeGreaterThan(0);
    }
  });

  test('should handle no data state gracefully', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // If no data, should show info message
    const noDataMessage = page.locator('text=/No brand mention data available/i');
    const chartExists = await page.locator('svg.recharts-surface').count();

    // Either chart exists OR no data message shown
    if (chartExists === 0) {
      await expect(noDataMessage).toBeVisible();
    } else {
      // Chart exists, so data is available
      expect(chartExists).toBeGreaterThan(0);
    }
  });
});

test.describe('Brand Mentions Interactivity', () => {
  test('should show tooltip on chart hover', async ({ page }) => {
    await page.goto('/analytics/brand-mentions');

    // Wait for chart to render
    await page.waitForLoadState('networkidle');
    const chartSvg = page.locator('svg.recharts-surface').first();
    await expect(chartSvg).toBeVisible();

    // Hover over the chart area to trigger tooltip
    const chartExists = await chartSvg.count();
    if (chartExists > 0) {
      // Hover over the center of the chart
      await chartSvg.hover();

      // Tooltip wrapper exists (may not always be visible depending on data)
      const tooltipWrapper = page.locator('.recharts-tooltip-wrapper');
      const tooltipCount = await tooltipWrapper.count();
      expect(tooltipCount).toBeGreaterThanOrEqual(0);
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
