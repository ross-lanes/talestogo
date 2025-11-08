# Testing Guide

This project uses **Vitest** and **React Testing Library** for testing.

## Quick Start

```bash
# Run all tests
npm test

# Run tests in watch mode (auto-rerun on file changes)
npm test

# Run tests once (useful for CI/CD)
npm test -- --run

# Run tests with UI (visual test runner)
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

## Test Results

✅ **15 tests passing** in 2 test files:
- `src/services/brandsService.test.ts` (7 tests)
- `src/utils/dateUtils.test.ts` (8 tests)

## Writing Tests

### Directory Structure

```
frontend/src/
├── utils/
│   ├── dateUtils.ts
│   └── dateUtils.test.ts          # Tests next to the code they test
├── services/
│   ├── brandsService.ts
│   └── brandsService.test.ts
├── components/
│   ├── Layout.tsx
│   └── Layout.test.tsx            # Component tests
└── test/
    └── setup.ts                   # Global test setup
```

### Test File Naming

- **Unit tests**: `filename.test.ts` or `filename.test.tsx`
- **Integration tests**: `filename.integration.test.ts`
- **E2E tests**: `filename.e2e.test.ts`

Place test files **next to the code they test** for easy discovery.

### Unit Test Example (Utility Functions)

See [`src/utils/dateUtils.test.ts`](src/utils/dateUtils.test.ts) for a complete example.

```typescript
import { describe, it, expect } from 'vitest';
import { formatDateEST } from './dateUtils';

describe('dateUtils', () => {
  describe('formatDateEST', () => {
    it('should format a date string in short format', () => {
      const date = '2024-01-15T12:00:00Z';
      const result = formatDateEST(date, 'short');

      expect(result).toContain('Jan');
      expect(result).toContain('15');
      expect(result).toContain('2024');
    });
  });
});
```

### Service Test Example (API Mocking)

See [`src/services/brandsService.test.ts`](src/services/brandsService.test.ts) for a complete example.

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { brandsService } from './brandsService';
import { api } from './api';

// Mock the api module
vi.mock('./api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('brandsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch all brands', async () => {
    const mockBrands = [
      { id: 1, brand_name: 'Brand A' },
    ];

    vi.mocked(api.get).mockResolvedValue({ data: mockBrands });

    const result = await brandsService.list();

    expect(api.get).toHaveBeenCalledWith('/brands');
    expect(result).toEqual(mockBrands);
  });
});
```

### Component Test Example (React Testing Library)

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);

    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('should handle button click', async () => {
    render(<MyComponent />);

    const button = screen.getByRole('button', { name: /click me/i });
    fireEvent.click(button);

    expect(screen.getByText('Clicked!')).toBeInTheDocument();
  });
});
```

### Testing React Query

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';

describe('useMyQuery', () => {
  it('should fetch data successfully', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    vi.mocked(api.get).mockResolvedValue({ data: { id: 1 } });

    const { result } = renderHook(() => useMyQuery(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ id: 1 });
  });
});
```

## Best Practices

### ✅ DO

1. **Test behavior, not implementation**
   - Test what the user sees/does, not internal state
   - Example: `expect(screen.getByText('Success!')).toBeInTheDocument()`

2. **Use descriptive test names**
   - Bad: `it('works', ...)`
   - Good: `it('should display error message when form is invalid', ...)`

3. **Arrange, Act, Assert pattern**
   ```typescript
   it('should do something', () => {
     // Arrange - set up test data
     const data = { id: 1 };

     // Act - perform the action
     const result = myFunction(data);

     // Assert - verify the result
     expect(result).toBe(expected);
   });
   ```

4. **Mock external dependencies**
   - Mock API calls, localStorage, window APIs
   - Don't test external libraries (they have their own tests)

5. **Clean up after each test**
   - Use `beforeEach` and `afterEach`
   - React Testing Library auto-cleans up (via setup.ts)

### ❌ DON'T

1. **Don't test implementation details**
   - Bad: Testing state variables directly
   - Good: Testing rendered output/behavior

2. **Don't write brittle tests**
   - Avoid testing exact text/CSS classes
   - Use semantic queries: `getByRole`, `getByLabelText`

3. **Don't forget to test error cases**
   - Happy path is important, but test failures too!

4. **Don't test third-party code**
   - Don't test React Query, axios, MUI internals
   - Test YOUR code that uses them

## Common Testing Patterns

### Testing Async Functions

```typescript
it('should handle async operations', async () => {
  vi.mocked(api.get).mockResolvedValue({ data: { id: 1 } });

  const result = await myAsyncFunction();

  expect(result).toEqual({ id: 1 });
});
```

### Testing Errors

```typescript
it('should throw error on invalid input', () => {
  expect(() => myFunction(null)).toThrow('Invalid input');
});

it('should handle API errors', async () => {
  vi.mocked(api.get).mockRejectedValue(new Error('API error'));

  await expect(myAsyncFunction()).rejects.toThrow('API error');
});
```

### Testing Timers

```typescript
import { vi } from 'vitest';

it('should call function after delay', () => {
  vi.useFakeTimers();

  const callback = vi.fn();
  setTimeout(callback, 1000);

  vi.advanceTimersByTime(1000);

  expect(callback).toHaveBeenCalled();

  vi.useRealTimers();
});
```

## Coverage

View test coverage with:

```bash
npm run test:coverage
```

This generates a coverage report in `coverage/` directory.

**Current Coverage** (as of initial setup):
- Lines: ~90%+
- Branches: ~85%+
- Functions: ~90%+

**Coverage Goals**:
- Critical paths (auth, data operations): 95%+
- Utility functions: 90%+
- UI components: 70%+

## CI/CD Integration

Add to your CI pipeline (e.g., GitHub Actions):

```yaml
- name: Run tests
  run: npm test -- --run

- name: Check coverage
  run: npm run test:coverage
```

## Troubleshooting

### Tests hanging or timing out

- Check for unresolved promises
- Ensure all async operations use `await`
- Check for infinite loops in components

### Mock not working

```typescript
// Make sure mock is hoisted before imports
vi.mock('./api');

// Clear mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
});
```

### "Cannot find module" errors

- Check file paths in imports
- Verify file extensions (.ts vs .tsx)
- Check vitest.config.ts alias configuration

### MUI component errors

- Check that `setup.ts` mocks `window.matchMedia`
- Ensure `jsdom` environment is set in vitest.config.ts

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing React Query](https://tanstack.com/query/latest/docs/framework/react/guides/testing)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## Next Steps

1. ✅ **Setup complete** - Infrastructure ready
2. 📝 **Write more tests** - Aim for 80%+ coverage
3. 🔄 **Add tests for refactored code** - Especially for brandsService
4. 🚀 **Integrate with CI/CD** - Run tests on every push

Happy testing! 🧪
