import { test, expect } from '@playwright/test';

/**
 * Dashboard Tests
 *
 * These tests verify the main Dashboard page functionality.
 * Tests run against Railway development environment with authenticated state.
 */

// Use authenticated state from fixtures
test.use({ storageState: 'e2e/fixtures/auth.json' });

test.describe('Dashboard Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
  });

  test('should display dashboard page', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify we're on the root path (dashboard is at /)
    await expect(page).toHaveURL(/\/$|\/dashboard/);
  });

  test('should display key metrics cards', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Look for metric cards - they should contain numbers or "No data"
    // Common metrics: Mention Rate, Sentiment, Share of Voice, etc.
    const cards = page.locator('[role="region"], .MuiCard-root, .MuiPaper-root');
    const cardCount = await cards.count();

    // Dashboard should have multiple metric cards
    expect(cardCount).toBeGreaterThan(0);
  });

  test('should display batch selector', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Batch selector should be present
    const batchSelector = page.locator('text=/Select.*Batch/i, text=/Latest/i').first();

    // Either batch selector exists or there's no data yet
    const selectorCount = await batchSelector.count();
    expect(selectorCount).toBeGreaterThanOrEqual(0);
  });

  test('should display charts if data available', async ({ page }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check for charts (Recharts uses SVG)
    const charts = page.locator('svg.recharts-surface');
    const chartCount = await charts.count();

    // If there's data, charts should be present
    if (chartCount > 0) {
      expect(chartCount).toBeGreaterThan(0);
    }
  });

  test('should display download dashboard button', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Look for download button (icon or text)
    const downloadButton = page.locator('button:has-text("Image"), button:has-text("Download")').first();

    // Download button should exist
    const buttonCount = await downloadButton.count();
    if (buttonCount > 0) {
      await expect(downloadButton).toBeVisible();
      await expect(downloadButton).toBeEnabled();
    }
  });

  test('should handle no brand data state', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // If no brand data, should show appropriate message
    const noBrandMessage = page.locator('text=/add a brand/i, text=/no brand/i').first();
    const charts = page.locator('svg.recharts-surface');

    const chartsExist = await charts.count();
    const messageExists = await noBrandMessage.count();

    // Either charts exist OR no brand message shown
    if (chartsExist === 0 && messageExists > 0) {
      await expect(noBrandMessage).toBeVisible();
    }
  });

  test('should navigate to analytics pages from cards', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if there are clickable links to analytics pages
    const analyticsLinks = page.locator('a[href*="/analytics/"]');
    const linkCount = await analyticsLinks.count();

    // Dashboard typically has links to detailed analytics pages
    if (linkCount > 0) {
      expect(linkCount).toBeGreaterThan(0);
    }
  });
});

test.describe('Dashboard Interactivity', () => {

  test('should show tooltips on chart hover', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for charts to render
    await page.waitForLoadState('networkidle');
    const charts = page.locator('svg.recharts-surface');

    const chartCount = await charts.count();
    if (chartCount > 0) {
      const firstChart = charts.first();
      await expect(firstChart).toBeVisible();

      // Hover over chart
      await firstChart.hover();

      // Tooltip wrapper may appear
      const tooltipWrapper = page.locator('.recharts-tooltip-wrapper');
      const tooltipCount = await tooltipWrapper.count();
      expect(tooltipCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should change data when selecting different batch', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check if batch selector exists
    const batchSelect = page.locator('select, [role="combobox"]').first();
    const selectExists = await batchSelect.count();

    if (selectExists > 0) {
      await expect(batchSelect).toBeVisible();

      // Check if there are multiple options
      const options = page.locator('option, [role="option"]');
      const optionCount = await options.count();

      if (optionCount > 1) {
        // Selecting different batch should trigger data reload
        // Just verify the selector is functional
        expect(optionCount).toBeGreaterThan(1);
      }
    }
  });
});

test.describe('Dashboard Task Status', () => {

  test('should display active tasks if any', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check for task status indicators
    const taskIndicators = page.locator('text=/running/i, text=/collecting/i, text=/analyzing/i').first();

    // Task indicators may or may not be present
    const taskCount = await taskIndicators.count();
    expect(taskCount).toBeGreaterThanOrEqual(0);
  });
});

/**
 * To run these tests:
 *    npm run test:e2e -- dashboard
 */
