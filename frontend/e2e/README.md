# E2E Testing with Playwright

End-to-end tests for the Tales application using Playwright.

## Running Tests

### Run all tests (headless)
```bash
npm run test:e2e
```

### Run with UI (interactive mode)
```bash
npm run test:e2e:ui
```

### Run in headed mode (see browser)
```bash
npm run test:e2e:headed
```

### Debug mode (step through tests)
```bash
npm run test:e2e:debug
```

### Run specific test file
```bash
npx playwright test e2e/auth/login.spec.ts
```

### Run tests matching a pattern
```bash
npx playwright test --grep "login"
```

## Test Structure

```
e2e/
├── auth/              # Authentication tests
├── analytics/         # Analytics page tests
├── admin/             # Admin functionality tests
├── fixtures/          # Shared test data and helpers
└── README.md         # This file
```

## Authentication Setup

Since Tales uses Google OAuth, you have a few options for testing authenticated flows:

### Option 1: Manual Auth State (Recommended for hobby projects)

1. Start the dev server: `npm run dev`
2. Login manually through the UI
3. Run this in browser console to save auth state:
   ```javascript
   // Navigate to http://localhost:5173 first
   // Then run in console:
   JSON.stringify({
     cookies: document.cookie.split(';').map(c => c.trim()),
     localStorage: Object.entries(localStorage)
   })
   ```
4. Save the output to `e2e/fixtures/auth.json`
5. Use in tests:
   ```typescript
   test.use({ storageState: 'e2e/fixtures/auth.json' });
   ```

### Option 2: Environment Variables

Set test account credentials:
```bash
export PLAYWRIGHT_TEST_EMAIL="your-test@gmail.com"
export PLAYWRIGHT_TEST_PASSWORD="your-password"
```

Then create an auth fixture that automates login.

### Option 3: Mock OAuth (For CI/CD)

Intercept OAuth requests and return mock tokens. See `fixtures/` for examples.

## Testing Against Different Environments

### Local Development
```bash
npm run test:e2e
```
(Uses `http://localhost:5173` by default)

### Railway Development
```bash
PLAYWRIGHT_BASE_URL=https://tales-frontend-development.up.railway.app npm run test:e2e
```

### Production (Read-only tests)
```bash
PLAYWRIGHT_BASE_URL=https://apps.robotrachel.com npm run test:e2e
```

## Viewing Test Reports

After tests run, open the HTML report:
```bash
npx playwright show-report
```

## Tips

- **Selectors**: Use `data-testid` attributes for stable selectors
- **Waiting**: Playwright auto-waits for elements; avoid manual waits
- **Screenshots**: Taken automatically on failure
- **Videos**: Recorded only on failure to save space
- **Traces**: Available on retry to debug failures

## CI/CD Integration

Tests can run on GitHub Actions (see `.github/workflows/e2e.yml` when set up).

Weekly scheduled tests run every Monday at 9am UTC.

## Writing New Tests

1. Create a new file in the appropriate directory
2. Follow the naming convention: `*.spec.ts`
3. Use descriptive test names
4. Keep tests independent and isolated
5. Clean up test data after tests

Example:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something specific', async ({ page }) => {
    await page.goto('/path');
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

## Troubleshooting

**Tests timing out?**
- Increase timeout in `playwright.config.ts`
- Check if dev server is running

**Elements not found?**
- Use Playwright Inspector: `npm run test:e2e:debug`
- Check selectors with `page.locator('selector').highlight()`

**Auth issues?**
- Verify auth state is valid
- Check token expiration
- Re-generate auth.json if needed
