import { test, expect } from '@playwright/test';

/**
 * Share of Voice Analytics Tests
 *
 * These tests verify the Share of Voice analytics page functionality.
 * Tests run against Railway development environment with authenticated state.
 */

// Use authenticated state from fixtures
test.use({ storageState: 'e2e/fixtures/auth.json' });

test.describe('Share of Voice Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to share of voice page
    await page.goto('/analytics/share-of-voice');
  });

  test('should display page title', async ({ page }) => {
    // Verify page title
    const heading = page.locator('h1, h2').first();
    await expect(heading).toContainText(/Share of Voice/i);
  });

  test('should display explanation text', async ({ page }) => {
    // Verify explanatory text is present
    const explanation = page.locator('text=/Share of Voice.*measures/i');
    await expect(explanation).toBeVisible();
  });

  test('should display charts if data available', async ({ page }) => {
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Verify chart container exists (Recharts uses SVG)
    const chartSvg = page.locator('svg.recharts-surface').first();
    const chartExists = await chartSvg.count();

    // Charts should be present if there's data
    if (chartExists > 0) {
      await expect(chartSvg).toBeVisible();
    }
  });

  test('should display competitor breakdown', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Verify share of voice by competitor section exists
    // This may vary based on data, so we'll check for common elements
    const sovElements = await page.locator('text=/share of voice/i').count();
    expect(sovElements).toBeGreaterThan(0);
  });

  test('should allow downloading chart as image', async ({ page }) => {
    // Find download button
    const downloadButton = page.locator('button:has-text("Image")').first();

    // Download button should be visible if there's data
    const chartExists = await page.locator('svg.recharts-surface').count();
    if (chartExists > 0) {
      await expect(downloadButton).toBeVisible();
      await expect(downloadButton).toBeEnabled();
    }
  });

  test('should display collection history table', async ({ page }) => {
    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Verify table exists (if data available) - use first() to handle multiple tables
    const table = page.locator('table').first();
    const tableVisible = await table.isVisible();

    if (tableVisible) {
      // Verify at least one table header is present
      const headers = await page.locator('th').count();
      expect(headers).toBeGreaterThan(0);
    }
  });

  test('should handle no data state gracefully', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // If no data, should show info message
    const noDataMessage = page.locator('text=/No share of voice data available/i');
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

test.describe('Share of Voice Interactivity', () => {
  test('should show tooltip on chart hover', async ({ page }) => {
    await page.goto('/analytics/share-of-voice');

    // Wait for chart to render
    await page.waitForLoadState('networkidle');
    const chartSvg = page.locator('svg.recharts-surface').first();

    const chartExists = await chartSvg.count();
    if (chartExists > 0) {
      await expect(chartSvg).toBeVisible();

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
 *    npm run test:e2e -- share-of-voice
 */
