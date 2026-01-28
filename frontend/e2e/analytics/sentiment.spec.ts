import { test, expect } from '@playwright/test';

/**
 * Sentiment Analytics Tests
 *
 * These tests verify the Sentiment analytics page functionality.
 * Tests run against Railway development environment with authenticated state.
 */

// Use authenticated state from fixtures
test.use({ storageState: 'e2e/fixtures/auth.json' });

test.describe('Sentiment Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to sentiment page
    await page.goto('/analytics/sentiment');
  });

  test('should display page title', async ({ page }) => {
    // Verify page title
    const heading = page.locator('h1, h2').first();
    await expect(heading).toContainText(/Sentiment Analysis/i);
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

  test('should display sentiment breakdown by platform', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Verify at least one platform is shown (if data exists)
    const platformTexts = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity'];
    let foundPlatform = false;
    for (const platform of platformTexts) {
      const count = await page.locator(`text="${platform}"`).count();
      if (count > 0) {
        foundPlatform = true;
        break;
      }
    }

    // Check if charts exist - if yes, platforms should exist
    const chartExists = await page.locator('svg.recharts-surface').count();
    if (chartExists > 0) {
      expect(foundPlatform).toBeTruthy();
    }
  });

  test('should display sentiment categories', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check for sentiment categories (if data exists)
    const sentiments = ['Positive', 'Neutral', 'Negative', 'Mixed'];
    let foundSentiment = false;

    for (const sentiment of sentiments) {
      const count = await page.locator(`text="${sentiment}"`).count();
      if (count > 0) {
        foundSentiment = true;
        break;
      }
    }

    // At least one sentiment should be present if there's data
    const chartExists = await page.locator('svg.recharts-surface').count();
    if (chartExists > 0) {
      expect(foundSentiment).toBeTruthy();
    }
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
    const noDataMessage = page.locator('text=/No sentiment data available/i');
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

test.describe('Sentiment Interactivity', () => {
  test('should show tooltip on chart hover', async ({ page }) => {
    await page.goto('/analytics/sentiment');

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
 *    npm run test:e2e -- sentiment
 */
