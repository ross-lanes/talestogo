import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { api } from '../services/api';

interface Tenant {
  id: number;
  tenant_name: string;
  subdomain: string | null;
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  custom_domain: string | null;
  created_at: string;
  updated_at: string;
}

interface TenantContextType {
  tenant: Tenant | null;
  allTenants: Tenant[];
  isAdmin: boolean;
  overrideTenant: (tenantId: number | null) => void;
  refreshTenant: () => Promise<void>;
  loading: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

interface TenantProviderProps {
  children: ReactNode;
  isAdmin: boolean;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children, isAdmin }) => {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [allTenants, setAllTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [overrideId, setOverrideId] = useState<number | null>(null);

  const fetchMyTenant = async () => {
    try {
      const response = await api.get('/tenants/me');
      return response.data;
    } catch (error) {
      console.error('Error fetching tenant:', error);
      return null;
    }
  };

  const fetchAllTenants = async () => {
    if (!isAdmin) return [];

    try {
      const response = await api.get('/tenants/');
      return response.data;
    } catch (error) {
      console.error('Error fetching all tenants:', error);
      return [];
    }
  };

  const refreshTenant = async () => {
    setLoading(true);
    try {
      // Fetch user's actual tenant
      const myTenant = await fetchMyTenant();

      // If admin, fetch all tenants
      const tenants = await fetchAllTenants();
      setAllTenants(tenants);

      // If there's an override, use that tenant
      if (overrideId !== null && tenants.length > 0) {
        const overrideTenant = tenants.find((t: Tenant) => t.id === overrideId);
        setTenant(overrideTenant || myTenant);
      } else {
        setTenant(myTenant);
      }
    } catch (error) {
      console.error('Error refreshing tenant:', error);
    } finally {
      setLoading(false);
    }
  };

  const overrideTenant = (tenantId: number | null) => {
    if (!isAdmin) return;

    setOverrideId(tenantId);

    // Update tenant immediately
    if (tenantId === null) {
      // Reset to user's actual tenant
      fetchMyTenant().then(setTenant);
    } else {
      // Use override tenant
      const overrideTenant = allTenants.find(t => t.id === tenantId);
      if (overrideTenant) {
        setTenant(overrideTenant);
      }
    }

    // Store in localStorage for persistence
    if (tenantId === null) {
      localStorage.removeItem('admin_tenant_override');
    } else {
      localStorage.setItem('admin_tenant_override', tenantId.toString());
    }
  };

  useEffect(() => {
    // Check for stored override on mount
    const stored = localStorage.getItem('admin_tenant_override');
    if (stored && isAdmin) {
      setOverrideId(parseInt(stored, 10));
    }

    refreshTenant();
  }, [isAdmin]);

  return (
    <TenantContext.Provider
      value={{
        tenant,
        allTenants,
        isAdmin,
        overrideTenant,
        refreshTenant,
        loading,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};
