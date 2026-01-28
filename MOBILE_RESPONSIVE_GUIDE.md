# Mobile Responsive Implementation Guide

This guide documents the mobile-responsive patterns implemented in Tales and how to apply them to remaining pages.

## Completed Updates

### ✅ Foundation
- **Theme** (`theme.ts`): Responsive typography (h1-h6 scale down on mobile)
- **Layout** (`Layout.tsx`): Reduced AppBar height, responsive spacing, optimized navigation
- **Utilities** (`utils/responsive.ts`): Hooks and helpers for responsive design
- **Components**:
  - `ResponsiveContainer`: Wrapper for responsive content
  - `ResponsiveTable`: Mobile-friendly table with horizontal scroll

### ✅ Core Pages
- **Dashboard** (`Dashboard.tsx`): Fully responsive charts, KPI cards, mobile-optimized buttons
- **BrandMentions** (`analytics/BrandMentions.tsx`): Complete mobile optimization

### ✅ Navigation
- **BrandSwitcher**: Compact mode for mobile
- **ProductSwitcher**: Mobile-optimized menus

## Mobile-Responsive Patterns

### Pattern 1: Responsive Paper/Card Padding
```tsx
// Before:
<Paper sx={{ p: 4 }}>

// After:
<Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
```

### Pattern 2: Responsive Header Sections
```tsx
// Before:
<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
  <Typography variant="h6">Chart Title</Typography>
  <Button startIcon={<Download />}>Image</Button>
</Box>

// After:
<Box sx={{
  display: 'flex',
  flexDirection: { xs: 'column', sm: 'row' },
  justifyContent: 'space-between',
  alignItems: { xs: 'flex-start', sm: 'center' },
  mb: 2,
  gap: { xs: 2, sm: 0 }
}}>
  <Typography variant="h6">Chart Title</Typography>
  <Button
    startIcon={<Download sx={{ display: { xs: 'none', sm: 'inline' } }} />}
    size="small"
    sx={{ minWidth: { xs: 44, sm: 'auto' }, px: { xs: 1, sm: 2 } }}
  >
    <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Image</Box>
    <Download sx={{ display: { xs: 'inline', sm: 'none' } }} />
  </Button>
</Box>
```

### Pattern 3: Responsive Chart Heights
```tsx
// Before:
<ChartContainer width="100%" height={400}>

// After:
<ChartContainer width="100%" height={{ xs: 300, sm: 350, md: 400 }}>
```

### Pattern 4: Responsive Tables with Horizontal Scroll
```tsx
// Before:
<Box sx={{ overflowX: 'auto' }}>
  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
    <thead>
      <tr>
        <th style={{ padding: '12px' }}>Header</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style={{ padding: '12px' }}>Data</td>
      </tr>
    </tbody>
  </table>
</Box>

// After:
<Box sx={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
  <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>
    <thead>
      <tr>
        <th style={{ padding: '8px 12px', fontSize: '0.875rem' }}>Header</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style={{ padding: '8px 12px', fontSize: '0.875rem' }}>Data</td>
      </tr>
    </tbody>
  </table>
</Box>
```

### Pattern 5: Responsive Margins
```tsx
// Before:
<Paper sx={{ mt: 4, mb: 4 }}>

// After:
<Paper sx={{ mt: { xs: 3, sm: 4 }, mb: { xs: 3, sm: 4 } }}>
```

## Applying to Analytics Pages

All analytics pages need these updates:

1. **Update all Paper components** with responsive padding
2. **Update all section headers** to stack on mobile
3. **Make download buttons icon-only** on mobile
4. **Set responsive chart heights**
5. **Add horizontal scroll** to tables with `minWidth`
6. **Reduce table cell padding** and font size on mobile

### Files to Update:
- `/frontend/src/pages/analytics/PositioningAnalysis.tsx`
- `/frontend/src/pages/analytics/DescriptorAnalysis.tsx`
- `/frontend/src/pages/analytics/CompetitorThreats.tsx`
- `/frontend/src/pages/analytics/SentimentAnalysis.tsx`
- `/frontend/src/pages/analytics/Recommendations.tsx`
- `/frontend/src/pages/analytics/ShareOfVoice.tsx`
- `/frontend/src/pages/analytics/StrategicPriorities.tsx`

## Testing Checklist

### Breakpoints to Test:
- **Mobile Portrait**: 375px (iPhone SE)
- **Mobile Landscape**: 667px
- **Tablet**: 768px (iPad)
- **Desktop**: 1200px+

### What to Test:
- [ ] No horizontal scroll on any page (except intentional table scroll)
- [ ] All touch targets ≥44px height
- [ ] Text is readable without zooming
- [ ] Charts render correctly and are touch-friendly
- [ ] Tables scroll horizontally when needed
- [ ] Navigation works smoothly
- [ ] Forms are usable with on-screen keyboard
- [ ] Images scale properly

### Browser Testing:
- [ ] Safari iOS (priority)
- [ ] Chrome Mobile
- [ ] Firefox Mobile
- [ ] Samsung Internet

## Quick Reference

### Material-UI Breakpoints:
- `xs`: 0-600px (mobile)
- `sm`: 600-900px (tablet)
- `md`: 900-1200px (small desktop)
- `lg`: 1200-1536px (desktop)
- `xl`: 1536px+ (large desktop)

### Touch-Friendly Sizes:
- Minimum button/touch target: 44x44px
- Comfortable tap area: 48x48px
- Text links: 44px height minimum

### Responsive Helper Hooks:
```tsx
import { useIsMobile, useIsTablet, useIsDesktop } from '../utils/responsive';

const isMobile = useIsMobile(); // < 600px
const isTablet = useIsTablet(); // 600-900px
const isDesktop = useIsDesktop(); // > 900px
```

## Next Steps

1. Apply patterns to remaining analytics pages
2. Update management pages (forms, brand management, etc.)
3. Test on real devices
4. Optimize performance for mobile networks
5. Run Google Mobile-Friendly Test
