import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

// Product types in the Solstice AI Suite
export type ProductType = 'tales' | 'heads' | 'canon' | 'nstxview' | 'vision' | 'pulse' | 'voice' | 'guardian';

interface ProductInfo {
  id: ProductType;
  name: string;
  description: string;
  logoPath: string;
  enabled: boolean;
  requiredTenants?: string[]; // Optional list of tenants that can access this product
  requiresUserAccess?: boolean; // If true, only available via user's allowed_products (no tenant fallback)
  externalUrl?: string; // If set, product opens in external URL instead of internal route
}

// Product catalog - will expand as we add more products
const PRODUCTS: ProductInfo[] = [
  {
    id: 'tales',
    name: 'Tales',
    description: 'Brand Reputation Monitor',
    logoPath: '/tales_white.png',
    enabled: true,
    // No requiredTenants = available to all tenants
  },
  {
    id: 'heads',
    name: 'Heads',
    description: 'AI-Powered Persona Generator',
    logoPath: '/heads_white.png',
    enabled: true,
    // No requiredTenants = available to all tenants
  },
  {
    id: 'canon',
    name: 'Canon',
    description: 'FDA Drug Data Research',
    logoPath: '/canon_logo_white.png',
    enabled: true,
    // No requiredTenants = available to all tenants
  },
  {
    id: 'nstxview',
    name: 'NSTXView',
    description: 'NSTX-U Research Database',
    logoPath: '/nstxview_white.png',
    enabled: true,
    requiresUserAccess: true, // Only show to users with explicit access
    externalUrl: 'https://nstxview.robotrachel.com',
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

interface ProductContextType {
  currentProduct: ProductInfo;
  products: ProductInfo[];
  availableProducts: ProductInfo[];
  upcomingProducts: ProductInfo[];
  switchProduct: (productId: ProductType) => void;
  isSolsticeHC: boolean;
}

const ProductContext = createContext<ProductContextType | undefined>(undefined);

export const useProduct = () => {
  const context = useContext(ProductContext);
  if (!context) {
    throw new Error('useProduct must be used within a ProductProvider');
  }
  return context;
};

interface ProductProviderProps {
  children: ReactNode;
  tenantName?: string;
  userAllowedProducts?: string[];  // User-specific product access list
}

export const ProductProvider: React.FC<ProductProviderProps> = ({ children, tenantName, userAllowedProducts }) => {
  // Check if user is in Solstice HC tenant
  const isSolsticeHC = tenantName === 'Solstice HC';

  // Helper function to check if a product is accessible to the current user
  const isProductAccessible = (product: ProductInfo): boolean => {
    // If product requires explicit user access, only check allowed_products
    if (product.requiresUserAccess) {
      return userAllowedProducts?.includes(product.id) ?? false;
    }

    // If we have user-specific allowed products, use that
    if (userAllowedProducts && userAllowedProducts.length > 0) {
      return userAllowedProducts.includes(product.id);
    }

    // Fallback to tenant-based access (for backwards compatibility)
    // If product has no tenant requirements, it's available to all
    if (!product.requiredTenants || product.requiredTenants.length === 0) {
      return true;
    }
    // Check if current tenant is in the required list
    return product.requiredTenants.includes(tenantName || 'default');
  };

  // Filter products based on user access AND enabled status
  const availableProducts = PRODUCTS.filter(p => {
    // Must be enabled
    if (!p.enabled) return false;
    // Must be accessible to this user
    return isProductAccessible(p);
  });

  // Upcoming products (disabled but would be visible to user when enabled)
  const upcomingProducts = PRODUCTS.filter(p => {
    // Skip enabled products
    if (p.enabled) return false;
    // Show only if user would have access when enabled
    return isProductAccessible(p);
  });

  // Initialize from localStorage or default to first available
  const [currentProduct, setCurrentProduct] = useState<ProductInfo>(() => {
    const savedProductId = localStorage.getItem('sas_active_product') as ProductType;
    const savedProduct = availableProducts.find(p => p.id === savedProductId);
    return savedProduct || availableProducts[0];
  });

  // Persist product selection to localStorage
  useEffect(() => {
    localStorage.setItem('sas_active_product', currentProduct.id);
  }, [currentProduct]);

  // If saved product becomes unavailable, switch to first available
  useEffect(() => {
    if (!availableProducts.find(p => p.id === currentProduct.id)) {
      setCurrentProduct(availableProducts[0]);
    }
  }, [availableProducts, currentProduct]);

  // Auto-detect product based on URL path
  const location = useLocation();
  useEffect(() => {
    const path = location.pathname;
    let detectedProductId: ProductType | null = null;

    if (path.startsWith('/canon')) {
      detectedProductId = 'canon';
    } else if (path.startsWith('/heads')) {
      detectedProductId = 'heads';
    } else if (path === '/' || path.startsWith('/manage') || path.startsWith('/analytics') || path.startsWith('/collect') || path.startsWith('/reports') || path.startsWith('/settings')) {
      detectedProductId = 'tales';
    }

    // Switch product if detected and different from current
    if (detectedProductId && detectedProductId !== currentProduct.id) {
      const product = availableProducts.find(p => p.id === detectedProductId);
      if (product) {
        setCurrentProduct(product);
      }
    }
  }, [location.pathname, availableProducts, currentProduct.id]);

  const switchProduct = (productId: ProductType) => {
    const product = availableProducts.find(p => p.id === productId);
    if (product) {
      setCurrentProduct(product);
    } else {
      console.warn(`Product ${productId} is not available`);
    }
  };

  const value: ProductContextType = {
    currentProduct,
    products: PRODUCTS, // All products (for reference)
    availableProducts, // Enabled products accessible to this tenant
    upcomingProducts, // Disabled products that tenant would have access to
    switchProduct,
    isSolsticeHC,
  };

  return <ProductContext.Provider value={value}>{children}</ProductContext.Provider>;
};
