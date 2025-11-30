import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

// Product types in the Solstice AI Suite
export type ProductType = 'tales' | 'heads' | 'canon' | 'vision' | 'pulse' | 'voice' | 'guardian';

interface ProductInfo {
  id: ProductType;
  name: string;
  description: string;
  logoPath: string;
  enabled: boolean;
  requiredTenants?: string[]; // Optional list of tenants that can access this product
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
    description: 'Persona Intelligence Platform',
    logoPath: '/heads_white.png',
    enabled: false, // Coming soon - still in development
    requiredTenants: ['Solstice HC'], // Only Solstice HC can access
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
}

export const ProductProvider: React.FC<ProductProviderProps> = ({ children, tenantName }) => {
  // Check if user is in Solstice HC tenant
  const isSolsticeHC = tenantName === 'Solstice HC';

  // Helper function to check if a product is accessible to the current tenant
  const isProductAccessible = (product: ProductInfo): boolean => {
    // If product has no tenant requirements, it's available to all
    if (!product.requiredTenants || product.requiredTenants.length === 0) {
      return true;
    }
    // Check if current tenant is in the required list
    return product.requiredTenants.includes(tenantName || 'default');
  };

  // Filter products based on tenant AND enabled status
  const availableProducts = PRODUCTS.filter(p => {
    // Must be enabled
    if (!p.enabled) return false;
    // Must be accessible to this tenant
    return isProductAccessible(p);
  });

  // Upcoming products (disabled but would be visible to tenant when enabled)
  const upcomingProducts = PRODUCTS.filter(p => {
    // Skip enabled products
    if (p.enabled) return false;
    // Show only if tenant would have access when enabled
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
