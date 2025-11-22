import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

// Product types in the Solstice AI Suite
export type ProductType = 'tales' | 'heads' | 'vision' | 'pulse' | 'voice' | 'guardian';

interface ProductInfo {
  id: ProductType;
  name: string;
  description: string;
  logoPath: string;
  enabled: boolean;
}

// Product catalog - will expand as we add more products
const PRODUCTS: ProductInfo[] = [
  {
    id: 'tales',
    name: 'Tales',
    description: 'Brand Reputation Monitor',
    logoPath: '/tales_white.png',
    enabled: true,
  },
  {
    id: 'heads',
    name: 'Heads',
    description: 'Persona Intelligence Platform',
    logoPath: '/heads_white.png',
    enabled: false, // Coming soon
  },
  {
    id: 'vision',
    name: 'Vision',
    description: 'Market Research',
    logoPath: '/vision_white.png',
    enabled: false, // Not yet available
  },
  {
    id: 'pulse',
    name: 'Pulse',
    description: 'Campaign Analytics Engine',
    logoPath: '/pulse_white.png',
    enabled: false,
  },
  {
    id: 'voice',
    name: 'Voice',
    description: 'Content Optimization Studio',
    logoPath: '/voice_white.png',
    enabled: false,
  },
  {
    id: 'guardian',
    name: 'Guardian',
    description: 'Compliance & Accuracy',
    logoPath: '/guardian_white.png',
    enabled: false,
  },
];

interface ProductContextType {
  currentProduct: ProductInfo;
  products: ProductInfo[];
  availableProducts: ProductInfo[];
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

  // Filter products based on tenant
  const availableProducts = isSolsticeHC
    ? PRODUCTS
    : PRODUCTS.filter(p => p.id === 'tales'); // Only Tales for other tenants

  // Initialize from localStorage or default to 'tales'
  const [currentProduct, setCurrentProduct] = useState<ProductInfo>(() => {
    const savedProductId = localStorage.getItem('sas_active_product') as ProductType;
    const savedProduct = availableProducts.find(p => p.id === savedProductId && p.enabled);
    return savedProduct || availableProducts[0]; // Default to first available (Tales)
  });

  // Persist product selection to localStorage
  useEffect(() => {
    localStorage.setItem('sas_active_product', currentProduct.id);
  }, [currentProduct]);

  const switchProduct = (productId: ProductType) => {
    const product = availableProducts.find(p => p.id === productId);
    if (product && product.enabled) {
      setCurrentProduct(product);
    } else {
      console.warn(`Product ${productId} is not available or not enabled`);
    }
  };

  const value: ProductContextType = {
    currentProduct,
    products: PRODUCTS, // All products (for display purposes)
    availableProducts, // Filtered by tenant
    switchProduct,
    isSolsticeHC,
  };

  return <ProductContext.Provider value={value}>{children}</ProductContext.Provider>;
};
