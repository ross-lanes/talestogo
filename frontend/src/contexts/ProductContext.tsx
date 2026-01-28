import React, { createContext, useContext } from 'react';
import type { ReactNode } from 'react';

// Product type - Tales only
export type ProductType = 'tales';

interface ProductInfo {
  id: ProductType;
  name: string;
  description: string;
  logoPath: string;
  enabled: boolean;
  externalUrl?: string;
}

// Tales product definition
const TALES_PRODUCT: ProductInfo = {
  id: 'tales',
  name: 'Tales',
  description: 'AI Reputation Intelligence',
  logoPath: '/tales_white.png',
  enabled: true,
};

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
  userAllowedProducts?: string[];
  isAdmin?: boolean;
}

export const ProductProvider: React.FC<ProductProviderProps> = ({ children }) => {
  // Tales is the only product
  const currentProduct = TALES_PRODUCT;
  const products = [TALES_PRODUCT];
  const availableProducts = [TALES_PRODUCT];
  const upcomingProducts: ProductInfo[] = [];

  // No-op since there's only one product
  const switchProduct = (_productId: ProductType) => {
    // Only Tales is available
  };

  const value: ProductContextType = {
    currentProduct,
    products,
    availableProducts,
    upcomingProducts,
    switchProduct,
    isSolsticeHC: false,
  };

  return <ProductContext.Provider value={value}>{children}</ProductContext.Provider>;
};
