import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { api } from '../services/api';

interface BrandInfo {
  id: number;
  brand_name: string;
  website_url: string | null;
  industry: string | null;
  description: string | null;
  strategic_messages: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface BrandContextType {
  activeBrand: BrandInfo | null;
  brands: BrandInfo[];
  loading: boolean;
  error: string | null;
  switchBrand: (brandId: number) => Promise<void>;
  addBrand: (brandData: Partial<BrandInfo>) => Promise<BrandInfo>;
  updateBrand: (brandId: number, brandData: Partial<BrandInfo>) => Promise<void>;
  deleteBrand: (brandId: number) => Promise<void>;
  refreshBrands: () => Promise<void>;
}

const BrandContext = createContext<BrandContextType | undefined>(undefined);

export const useBrand = () => {
  const context = useContext(BrandContext);
  if (!context) {
    throw new Error('useBrand must be used within a BrandProvider');
  }
  return context;
};

interface BrandProviderProps {
  children: ReactNode;
}

export const BrandProvider: React.FC<BrandProviderProps> = ({ children }) => {
  const [activeBrand, setActiveBrand] = useState<BrandInfo | null>(null);
  const [brands, setBrands] = useState<BrandInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all brands and active brand on mount
  useEffect(() => {
    refreshBrands();
  }, []);

  const refreshBrands = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all brands
      const brandsResponse = await api.get<BrandInfo[]>('/brands/');
      setBrands(brandsResponse.data);

      // Find and set the active brand
      const active = brandsResponse.data.find(brand => brand.is_active);
      setActiveBrand(active || null);
    } catch (err: any) {
      console.error('Error fetching brands:', err);
      // If 401, user is not authenticated - don't set error
      if (err.response?.status !== 401) {
        setError(err.response?.data?.detail || 'Failed to load brands');
      }
      setBrands([]);
      setActiveBrand(null);
    } finally {
      setLoading(false);
    }
  };

  const switchBrand = async (brandId: number) => {
    setError(null);
    try {
      const response = await api.post<BrandInfo>(`/brands/${brandId}/activate`);
      setActiveBrand(response.data);

      // Update brands list to reflect active status change
      setBrands(prevBrands =>
        prevBrands.map(brand => ({
          ...brand,
          is_active: brand.id === brandId
        }))
      );
    } catch (err: any) {
      console.error('Error switching brand:', err);
      setError(err.response?.data?.detail || 'Failed to switch brand');
      throw err;
    }
  };

  const addBrand = async (brandData: Partial<BrandInfo>): Promise<BrandInfo> => {
    setError(null);
    try {
      const response = await api.post<BrandInfo>('/brands/', brandData);
      const newBrand = response.data;

      // Add to brands list
      setBrands(prevBrands => [...prevBrands, newBrand]);

      // If this is the first brand, it will be active
      if (newBrand.is_active) {
        setActiveBrand(newBrand);
      }

      return newBrand;
    } catch (err: any) {
      console.error('Error adding brand:', err);
      setError(err.response?.data?.detail || 'Failed to add brand');
      throw err;
    }
  };

  const updateBrand = async (brandId: number, brandData: Partial<BrandInfo>) => {
    setError(null);
    try {
      const response = await api.put<BrandInfo>(`/brands/${brandId}`, brandData);
      const updatedBrand = response.data;

      // Update brands list
      setBrands(prevBrands =>
        prevBrands.map(brand =>
          brand.id === brandId ? updatedBrand : brand
        )
      );

      // Update active brand if it's the one being updated
      if (activeBrand?.id === brandId) {
        setActiveBrand(updatedBrand);
      }
    } catch (err: any) {
      console.error('Error updating brand:', err);
      setError(err.response?.data?.detail || 'Failed to update brand');
      throw err;
    }
  };

  const deleteBrand = async (brandId: number) => {
    setError(null);
    try {
      await api.delete(`/brands/${brandId}`);

      // Remove from brands list
      setBrands(prevBrands => prevBrands.filter(brand => brand.id !== brandId));

      // If deleted brand was active, clear active brand and refresh
      if (activeBrand?.id === brandId) {
        setActiveBrand(null);
        // Refresh to get new active brand (backend should auto-activate another)
        await refreshBrands();
      }
    } catch (err: any) {
      console.error('Error deleting brand:', err);
      setError(err.response?.data?.detail || 'Failed to delete brand');
      throw err;
    }
  };

  const value: BrandContextType = {
    activeBrand,
    brands,
    loading,
    error,
    switchBrand,
    addBrand,
    updateBrand,
    deleteBrand,
    refreshBrands,
  };

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>;
};
