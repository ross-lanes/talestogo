# Theme Flash Fix - Optimistic Loading Implementation

## Problem
When a Solstice tenant user loads the page, there's a brief flash where the UI shows the default purple theme before switching to the navy theme. This creates a jarring user experience.

## Root Cause
The theme loading flow was:
1. Page loads → TenantContext initializes with `tenant = null`
2. TenantThemeProvider sees no tenant → applies default purple theme
3. API call completes → tenant data arrives
4. Theme updates to correct navy color → **visible flash**

## Solution: Optimistic Loading with localStorage Cache

We implemented "optimistic loading" by caching the tenant data in localStorage and loading it immediately on page load, before the API call completes.

### How It Works

1. **On First Visit/Login:**
   - User logs in → API fetches tenant data
   - Tenant data saved to state AND localStorage (`cached_tenant`)
   - Theme applied correctly

2. **On Subsequent Page Loads:**
   - Page loads → TenantContext reads from localStorage IMMEDIATELY
   - Cached tenant (with correct colors) applied from first render
   - API call happens in background
   - If API returns same data → no change, no flash ✓
   - If API returns different data (rare) → theme updates smoothly

## Files Changed

### 1. `frontend/src/contexts/TenantContext.tsx`

#### Added Cache Helper Function
```typescript
const getCachedTenant = (): Tenant | null => {
  try {
    const cached = localStorage.getItem('cached_tenant');
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (error) {
    console.error('Failed to parse cached tenant:', error);
  }
  return null;
};
```

#### Initialize State with Cached Tenant
```typescript
// BEFORE
const [tenant, setTenant] = useState<Tenant | null>(null);

// AFTER
const [tenant, setTenant] = useState<Tenant | null>(getCachedTenant());
```

#### Update Cache When Tenant Changes
```typescript
// In refreshTenant()
if (selectedTenant) {
  localStorage.setItem('cached_tenant', JSON.stringify(selectedTenant));
}

// In overrideTenant()
if (myTenant) {
  localStorage.setItem('cached_tenant', JSON.stringify(myTenant));
}
```

### 2. `frontend/src/components/TenantThemeProvider.tsx`

#### Updated Theme Logic
```typescript
// BEFORE - only applied tenant theme after loading finished
if (loading || !tenant) {
  return baseTheme;
}
return createTheme({ /* tenant colors */ });

// AFTER - apply tenant theme immediately if available (from cache or API)
if (tenant) {
  return createTheme({ /* tenant colors */ });
}
return baseTheme;
```

## Benefits

1. **No Flash:** Users see correct theme colors from first paint
2. **Fast:** No API wait time for theme application
3. **Resilient:** Falls back to default purple only if no cache exists
4. **Transparent:** Works seamlessly with existing auth and tenant switching
5. **User-Specific:** Each browser caches that user's theme

## Edge Cases Handled

1. **First-time user:** No cache → shows default purple → API loads → updates and caches
2. **Returning user:** Cache exists → shows cached theme immediately → API confirms
3. **Tenant switch (admin):** Updates both state and cache → no flash on reload
4. **Cache corruption:** Try-catch prevents errors, falls back to no cache
5. **Tenant theme changed:** API returns new colors → updates smoothly → cache updated

## Testing Checklist

- [ ] Load page as Solstice user → Should show navy immediately, no purple flash
- [ ] Load page as PPPL user → Should show purple immediately (their actual color)
- [ ] Clear localStorage → Should show default purple → Login → Shows correct theme
- [ ] Admin override tenant → Should update immediately and persist on reload
- [ ] Hard refresh (Cmd+Shift+R) → Should still show correct cached theme

## Deployment Notes

**DO NOT DEPLOY during active data collection.** Wait for current collection to complete.

When ready to deploy:
```bash
cd frontend
npm run build
# Deploy built files to production
```

## Future Enhancements (Optional)

1. Add cache expiration (e.g., clear after 7 days)
2. Clear cache on logout for security
3. Add version check to invalidate cache if tenant schema changes

## Technical Details

- **localStorage key:** `cached_tenant`
- **Data format:** JSON-stringified Tenant object
- **Size:** ~200-300 bytes per cached tenant
- **Persistence:** Until browser cache cleared or user logs out

---

**Implementation Date:** November 9, 2024
**Strategy Used:** Optimistic Loading (Strategy 2)
