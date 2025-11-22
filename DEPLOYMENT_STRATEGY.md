# Solstice AI Suite - Multi-Tenant Deployment Strategy

**Date Created:** November 21, 2025
**Status:** Ready for Implementation
**Version:** 1.0

---

## Overview

This document outlines the strategy for deploying the Solstice AI Suite as a multi-tenant platform while maintaining a clean, single-codebase architecture.

## Problem Statement

### Problem 1: Multiple Tenant Deployments
- **Solstice HC Tenant**: Needs access to full Solstice AI Suite (Tales + Heads + Vision + Pulse + Voice + Guardian)
- **Princeton University / RobotRachel Tenant**: Needs access to Tales ONLY

### Problem 2: Continuous Development
- Tales must remain stable in production for all tenants
- New products (Heads, Vision, etc.) need active development
- Shared database/brands across products
- Zero-downtime deployments
- Princeton users should never see or access products under development

---

## Solution: Tenant-Based Product Access Control

### Core Principle
**Single codebase, single deployment, tenant-based feature filtering**

Instead of maintaining separate codebases or deployments, use tenant configuration to control which products each tenant can access.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   SINGLE DEPLOYMENT                          │
│                   tales.robotrachel.com                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              TENANT: Solstice HC                      │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │  │
│  │  │Tales │  │Heads │  │Vision│  │Pulse │  │Voice │  │  │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  │  │
│  │  All products visible and accessible                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         TENANT: Princeton University                  │  │
│  │  ┌──────┐                                            │  │
│  │  │Tales │  Only Tales visible                        │  │
│  │  └──────┘  No Product Switcher shown                │  │
│  │  Other products: 403 Forbidden                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Shared Database with tenant isolation via tenant_id        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Configuration

#### 1.1 Create Tenant Configuration System

**File: `app/config.py`**

```python
from typing import List, Dict

class TenantConfig:
    """Configuration for tenant-specific product access"""

    # Map tenant names to allowed products
    TENANT_PRODUCTS: Dict[str, List[str]] = {
        "Solstice HC": ["tales", "heads", "vision", "pulse", "voice", "guardian"],
        "Princeton University": ["tales"],  # Tales only
        # Default for any other tenant
        "default": ["tales"]
    }

    @staticmethod
    def get_tenant_products(tenant_name: str) -> List[str]:
        """Get list of products enabled for a tenant"""
        return TenantConfig.TENANT_PRODUCTS.get(
            tenant_name,
            TenantConfig.TENANT_PRODUCTS["default"]
        )

    @staticmethod
    def is_product_enabled_for_tenant(tenant_name: str, product: str) -> bool:
        """Check if a product is enabled for a specific tenant"""
        allowed_products = TenantConfig.get_tenant_products(tenant_name)
        return product in allowed_products
```

#### 1.2 Create Product Access Middleware

**File: `app/dependencies.py`**

```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.models import User, Tenant
from app.config import TenantConfig
from app.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_product_access(product: str):
    """Dependency to verify user's tenant has access to a product"""
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Get user's tenant name
        tenant_name = None
        if current_user.tenant_id:
            tenant = db.query(Tenant).filter(
                Tenant.id == current_user.tenant_id
            ).first()
            tenant_name = tenant.name if tenant else None

        # Check if product is allowed for this tenant
        if not TenantConfig.is_product_enabled_for_tenant(
            tenant_name or "default",
            product
        ):
            raise HTTPException(
                status_code=403,
                detail=f"Product '{product}' is not available for your organization"
            )

        return current_user

    return _check
```

#### 1.3 Protect Product-Specific Routes

**Update: `app/routers/personas.py` (Heads)**

```python
from app.dependencies import check_product_access

router = APIRouter(
    prefix="/personas",
    tags=["Heads - Personas"],
    dependencies=[Depends(check_product_access("heads"))]  # Blocks non-Solstice tenants
)

# All routes in this router now require "heads" product access
@router.get("/generations")
def get_generations(...):
    # Only accessible to Solstice HC users
    pass
```

**Tales routes remain unchanged** - No dependency needed since Tales is available to all tenants.

---

### Phase 2: Frontend Configuration

#### 2.1 Update Product Type Definitions

**File: `frontend/src/contexts/ProductContext.tsx`**

```typescript
interface ProductInfo {
  id: ProductType;
  name: string;
  description: string;
  logoPath: string;
  enabled: boolean;
  requiredTenants?: string[];  // NEW: Optional list of tenants that can access
}
```

#### 2.2 Update Product Catalog

```typescript
const PRODUCTS: ProductInfo[] = [
  {
    id: 'tales',
    name: 'Tales',
    description: 'Brand Reputation Monitor',
    logoPath: '/tales_white.png',
    enabled: true,
    // No requiredTenants = available to all
  },
  {
    id: 'heads',
    name: 'Heads',
    description: 'Persona Intelligence Platform',
    logoPath: '/heads_white.png',
    enabled: true,  // Change from false to true
    requiredTenants: ['Solstice HC'],  // Only Solstice HC
  },
  {
    id: 'vision',
    name: 'Vision',
    description: 'Market Research',
    logoPath: '/vision_white.png',
    enabled: false, // Still in development
    requiredTenants: ['Solstice HC'],
  },
  {
    id: 'pulse',
    name: 'Pulse',
    description: 'Campaign Analytics Engine',
    logoPath: '/pulse_white.png',
    enabled: false,
    requiredTenants: ['Solstice HC'],
  },
  {
    id: 'voice',
    name: 'Voice',
    description: 'Content Optimization Studio',
    logoPath: '/voice_white.png',
    enabled: false,
    requiredTenants: ['Solstice HC'],
  },
  {
    id: 'guardian',
    name: 'Guardian',
    description: 'Compliance & Accuracy',
    logoPath: '/guardian_white.png',
    enabled: false,
    requiredTenants: ['Solstice HC'],
  },
];
```

#### 2.3 Update ProductProvider with Tenant Filtering

```typescript
export const ProductProvider: React.FC<ProductProviderProps> = ({
  children,
  tenantName
}) => {
  const isSolsticeHC = tenantName === 'Solstice HC';

  // Filter products based on tenant AND enabled status
  const availableProducts = PRODUCTS.filter(p => {
    // Check if product is enabled
    if (!p.enabled) return false;

    // Check if product has tenant restrictions
    if (p.requiredTenants && p.requiredTenants.length > 0) {
      // Only show if user's tenant is in the required list
      return p.requiredTenants.includes(tenantName || 'default');
    }

    // No restrictions = available to all
    return true;
  });

  // Upcoming products (disabled but would be visible to tenant when enabled)
  const upcomingProducts = PRODUCTS.filter(p => {
    if (p.enabled) return false;  // Skip enabled products

    // Show upcoming products only if tenant would have access when enabled
    if (p.requiredTenants && p.requiredTenants.length > 0) {
      return p.requiredTenants.includes(tenantName || 'default');
    }

    return true;
  });

  // Initialize from localStorage or default to first available
  const [currentProduct, setCurrentProduct] = useState<ProductInfo>(() => {
    const savedProductId = localStorage.getItem('sas_active_product') as ProductType;
    const savedProduct = availableProducts.find(p => p.id === savedProductId);
    return savedProduct || availableProducts[0];
  });

  // ... rest of context implementation
};
```

---

## User Experience by Tenant

### Solstice HC Users

**Product Switcher:**
- ✓ Visible (Apps icon in top nav)
- Shows "Solstice AI Suite" title
- **Available Products:** Tales (Active), Heads (if enabled)
- **Coming Soon:** Vision, Pulse, Voice, Guardian (if enabled=false)

**API Access:**
- Full access to `/queries/*`, `/responses/*`, `/brands/*` (Tales)
- Full access to `/personas/*` (Heads)
- Future: Access to all other product endpoints

**Branding:**
- "Solstice AI Suite" branding
- Product Switcher prominently displayed

---

### Princeton University Users

**Product Switcher:**
- ✗ Hidden (only 1 product available)
- No suite branding

**API Access:**
- Full access to `/queries/*`, `/responses/*`, `/brands/*` (Tales)
- **403 Forbidden** for `/personas/*` (Heads)
- **403 Forbidden** for all other product endpoints

**Branding:**
- Standard "Tales" branding
- Single-product experience

---

## Development Workflow

### Working on Tales (Stable Product)

1. Develop locally
2. Test thoroughly
3. Deploy to production
4. **Impact:** Both Solstice HC and Princeton users get updates
5. **Risk:** Low (shared stable product)

### Working on Heads (New Product - Solstice Only)

1. Set `enabled: true` in ProductContext
2. Add `requiredTenants: ['Solstice HC']` to Heads product
3. Add `dependencies=[Depends(check_product_access("heads"))]` to Heads router
4. Develop and test locally
5. Deploy to production
6. **Impact:** Only Solstice HC users can see/access
7. **Princeton Impact:** Zero - they never see it, API returns 403
8. **Risk:** Zero for Princeton users (completely isolated)

### Working on Vision (Future Product)

1. Add to PRODUCTS array with `enabled: false`
2. Add `requiredTenants: ['Solstice HC']`
3. Appears in "Coming Soon" for Solstice HC only
4. Princeton users don't see it at all
5. When ready: Set `enabled: true`, deploy
6. Instantly available to Solstice HC users

---

## Deployment Process

### Current State (Before Implementation)
- Single deployment
- Heads is visible to all but disabled (`enabled: false`)
- No tenant-based access control

### After Implementation
- Single deployment
- Tenant-based product filtering on frontend
- API enforces tenant access via middleware
- Zero configuration changes needed for deployments

### Deployment Steps

1. **Deploy Backend Changes:**
   ```bash
   git push origin main
   # Render auto-deploys
   # Old instances continue serving traffic
   # New instances boot with new code
   # Traffic switches over (zero downtime)
   ```

2. **Deploy Frontend Changes:**
   ```bash
   npm run build
   git push origin main
   # Render auto-deploys frontend
   # CloudFlare CDN updates
   ```

3. **Verification:**
   - Login as Solstice HC user → See Tales + Heads
   - Login as Princeton user → See Tales only
   - Try accessing `/personas/*` as Princeton user → 403 Forbidden

---

## Database Strategy

### Current State (Correct)
✅ Single shared database
✅ `tenant_id` on users table
✅ `user_id` on brands table
✅ `brand_id` on all product data tables

### No Changes Needed
The existing multi-tenant database structure already supports this strategy perfectly.

**Data Isolation:**
- Users belong to tenants (`tenant_id`)
- Brands belong to users (`user_id`)
- All product data belongs to brands (`brand_id`)
- Natural isolation through foreign key relationships

**Shared Brands:**
- Solstice HC users can create brands
- Those brands can be used across Tales, Heads, Vision, etc.
- Princeton users create brands only usable in Tales
- No cross-contamination possible

---

## Benefits

### ✅ Single Codebase
- One repository to maintain
- Shared bug fixes across all tenants
- Easier testing and CI/CD

### ✅ Zero Downtime Deployments
- Rolling deployments on Render
- Old code continues running during deployment
- Traffic switches when new instances are healthy

### ✅ Product Isolation
- Heads development doesn't affect Tales stability
- Princeton users completely isolated from experimental features
- Each product can be developed independently

### ✅ Flexible Product Rollout
- Enable products per tenant instantly
- Test with Solstice HC before wider release
- Easy to add new tenants with custom product access

### ✅ Cost Effective
- Single deployment reduces infrastructure costs
- Shared database reduces complexity
- No duplication of code or resources

### ✅ Future Proof
- Easy to add Vision, Pulse, Voice, Guardian
- Easy to add new tenants with custom access
- Scales naturally as product suite grows

---

## Risks and Mitigations

### Risk: Backend Bug Affects All Tenants
**Mitigation:**
- Comprehensive testing before deployment
- Feature flags for risky changes
- Quick rollback capability (Render deployments)
- Monitor error rates per tenant

### Risk: Product-Specific Code Breaks Tales
**Mitigation:**
- Keep product routers isolated
- Don't modify shared dependencies without testing
- Use router-level dependencies to isolate products
- Integration tests for cross-product scenarios

### Risk: Tenant Configuration Error
**Mitigation:**
- Tenant config is code-based (version controlled)
- Simple, declarative structure
- Easy to audit who has access to what
- Add integration tests for tenant access control

---

## Testing Strategy

### Backend Testing

**Unit Tests:**
```python
def test_solstice_can_access_heads():
    """Solstice HC users can access Heads endpoints"""
    assert TenantConfig.is_product_enabled_for_tenant("Solstice HC", "heads") == True

def test_princeton_cannot_access_heads():
    """Princeton users cannot access Heads endpoints"""
    assert TenantConfig.is_product_enabled_for_tenant("Princeton University", "heads") == False

def test_all_tenants_can_access_tales():
    """All tenants can access Tales endpoints"""
    assert TenantConfig.is_product_enabled_for_tenant("Solstice HC", "tales") == True
    assert TenantConfig.is_product_enabled_for_tenant("Princeton University", "tales") == True
```

**Integration Tests:**
```python
def test_princeton_user_gets_403_on_heads_endpoint(client, princeton_user_token):
    """Princeton user gets 403 when accessing /personas/*"""
    response = client.get("/personas/generations", headers={"Authorization": f"Bearer {princeton_user_token}"})
    assert response.status_code == 403

def test_solstice_user_can_access_heads_endpoint(client, solstice_user_token):
    """Solstice user can access /personas/*"""
    response = client.get("/personas/generations", headers={"Authorization": f"Bearer {solstice_user_token}"})
    assert response.status_code == 200
```

### Frontend Testing

**Component Tests:**
```typescript
describe('ProductSwitcher', () => {
  it('should show only Tales for Princeton users', () => {
    render(<ProductSwitcher tenantName="Princeton University" />);
    expect(screen.queryByText('Heads')).not.toBeInTheDocument();
    expect(screen.queryByText('Product Switcher')).not.toBeInTheDocument();
  });

  it('should show Tales and Heads for Solstice users', () => {
    render(<ProductSwitcher tenantName="Solstice HC" />);
    expect(screen.getByText('Tales')).toBeInTheDocument();
    expect(screen.getByText('Heads')).toBeInTheDocument();
  });
});
```

---

## Rollout Plan

### Phase 1: Implementation (Week 1)
- [ ] Create `app/config.py` with tenant configuration
- [ ] Create `app/dependencies.py` with product access middleware
- [ ] Update `app/routers/personas.py` with access control
- [ ] Update `frontend/src/contexts/ProductContext.tsx` with tenant filtering
- [ ] Add unit tests for tenant configuration
- [ ] Add integration tests for API access control

### Phase 2: Testing (Week 1)
- [ ] Test locally with Solstice HC tenant
- [ ] Test locally with Princeton tenant
- [ ] Verify ProductSwitcher shows/hides correctly
- [ ] Verify API returns 403 for unauthorized products
- [ ] Test zero-downtime deployment process

### Phase 3: Production Deployment (Week 2)
- [ ] Deploy backend changes
- [ ] Deploy frontend changes
- [ ] Verify Solstice HC users see both Tales and Heads
- [ ] Verify Princeton users see only Tales
- [ ] Monitor error logs for access control issues
- [ ] Confirm no impact to existing Tales functionality

### Phase 4: Future Products (Ongoing)
- [ ] Add Vision to PRODUCTS array when ready
- [ ] Set `enabled: true` when Vision is production-ready
- [ ] Repeat for Pulse, Voice, Guardian

---

## Configuration Reference

### Adding a New Tenant

**Backend:** Update `app/config.py`
```python
TENANT_PRODUCTS: Dict[str, List[str]] = {
    "Solstice HC": ["tales", "heads", "vision", "pulse", "voice", "guardian"],
    "Princeton University": ["tales"],
    "New Tenant Name": ["tales", "heads"],  # Add here
    "default": ["tales"]
}
```

**Frontend:** No changes needed - automatically filtered

### Adding a New Product

**Backend:**
1. Create router in `app/routers/new_product.py`
2. Add `dependencies=[Depends(check_product_access("new_product"))]`
3. Register in `app/main.py`

**Frontend:**
1. Add to `ProductType` in `ProductContext.tsx`
2. Add to `PRODUCTS` array with `requiredTenants`
3. Set `enabled: true` when ready for production

### Enabling a Product for a Tenant

**Backend:** Update `app/config.py`
```python
"Tenant Name": ["tales", "new_product"],  # Add product to list
```

**Frontend:** Add to `requiredTenants` array
```typescript
{
  id: 'new_product',
  requiredTenants: ['Solstice HC', 'Tenant Name'],  // Add tenant here
}
```

---

## Success Metrics

### Technical Metrics
- ✅ Zero downtime during deployments
- ✅ No 500 errors from tenant access control
- ✅ 100% test coverage for tenant configuration
- ✅ < 1% error rate across all products

### Business Metrics
- ✅ Princeton users continue using Tales without interruption
- ✅ Solstice HC users can access Heads
- ✅ New products can be deployed without affecting existing users
- ✅ Deployment frequency increases (safe to deploy more often)

---

## Appendix A: File Structure

```
tales_project/
├── app/
│   ├── config.py                    # NEW: Tenant product configuration
│   ├── dependencies.py              # NEW: Product access middleware
│   ├── routers/
│   │   ├── queries.py              # Tales - No access control needed
│   │   ├── responses.py            # Tales - No access control needed
│   │   ├── brands.py               # Tales - No access control needed
│   │   ├── personas.py             # Heads - ADD access control
│   │   ├── vision.py               # Future - Will need access control
│   │   └── ...
│   └── main.py                     # Register all routers
├── frontend/
│   └── src/
│       └── contexts/
│           └── ProductContext.tsx  # UPDATE: Add tenant filtering
└── DEPLOYMENT_STRATEGY.md          # This document
```

---

## Appendix B: Contact and Support

**Strategy Owner:** RobotRachel (robotrachel@gmail.com)
**Implementation Date:** TBD
**Review Date:** After Phase 3 completion

**Questions or Issues:**
- Review this document first
- Check implementation examples in code
- Test locally before deploying
- Monitor logs after deployment

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-21 | Initial strategy document | Claude Code |

---

**END OF DOCUMENT**
