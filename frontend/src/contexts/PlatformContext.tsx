import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { api } from '../services/api';
import { useAuth } from './AuthContext';

// Default platform colors (fallback when API not available)
const DEFAULT_PLATFORM_COLORS: Record<string, string> = {
  'ChatGPT': '#10a37f',
  'Claude': '#d97706',
  'Gemini': '#4285f4',
  'Perplexity': '#20808d',
};

interface PlatformInfo {
  key: string;
  name: string;
  color: string;
}

interface PlatformContextType {
  platforms: PlatformInfo[];
  platformColors: Record<string, string>;
  loading: boolean;
  error: string | null;
  refreshPlatforms: () => Promise<void>;
  getPlatformColor: (platformName: string) => string;
}

const PlatformContext = createContext<PlatformContextType | undefined>(undefined);

export const usePlatformConfig = () => {
  const context = useContext(PlatformContext);
  if (!context) {
    throw new Error('usePlatformConfig must be used within a PlatformProvider');
  }
  return context;
};

interface PlatformProviderProps {
  children: ReactNode;
}

export const PlatformProvider: React.FC<PlatformProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [platformColors, setPlatformColors] = useState<Record<string, string>>(DEFAULT_PLATFORM_COLORS);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshPlatforms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<{ platforms: PlatformInfo[] }>('/analytics/platform-config');
      const platformList = response.data.platforms || [];
      setPlatforms(platformList);

      // Build color map from platforms
      const colors: Record<string, string> = {};
      platformList.forEach((p) => {
        colors[p.name] = p.color;
      });

      // Merge with defaults (in case some platforms are missing colors)
      setPlatformColors({ ...DEFAULT_PLATFORM_COLORS, ...colors });
    } catch (err: any) {
      console.error('Error fetching platform config:', err);
      // If 401 or 403, user is not authenticated - use defaults silently
      if (err.response?.status === 401 || err.response?.status === 403) {
        setPlatformColors(DEFAULT_PLATFORM_COLORS);
      } else {
        setError(err.response?.data?.detail || 'Failed to load platform configuration');
        // Still use defaults on error
        setPlatformColors(DEFAULT_PLATFORM_COLORS);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch platform config when user is authenticated
  useEffect(() => {
    if (isAuthenticated) {
      refreshPlatforms();
    } else {
      // Use defaults when not authenticated
      setPlatformColors(DEFAULT_PLATFORM_COLORS);
      setLoading(false);
    }
  }, [isAuthenticated, refreshPlatforms]);

  // Helper function to get color for a platform name
  const getPlatformColor = useCallback((platformName: string): string => {
    return platformColors[platformName] || '#666666';
  }, [platformColors]);

  const value: PlatformContextType = {
    platforms,
    platformColors,
    loading,
    error,
    refreshPlatforms,
    getPlatformColor,
  };

  return <PlatformContext.Provider value={value}>{children}</PlatformContext.Provider>;
};
