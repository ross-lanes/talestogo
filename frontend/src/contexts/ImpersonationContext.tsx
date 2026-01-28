import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface ImpersonatedUser {
  id: number;
  email: string;
  full_name?: string;
}

interface ImpersonationContextType {
  impersonatedUser: ImpersonatedUser | null;
  setImpersonatedUser: (user: ImpersonatedUser | null) => void;
  isImpersonating: boolean;
  exitImpersonation: () => void;
}

const ImpersonationContext = createContext<ImpersonationContextType | undefined>(undefined);

const IMPERSONATION_KEY = 'tales_impersonation';

export const ImpersonationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [impersonatedUser, setImpersonatedUserState] = useState<ImpersonatedUser | null>(null);

  // Load impersonation state from sessionStorage on mount
  useEffect(() => {
    const storedImpersonation = sessionStorage.getItem(IMPERSONATION_KEY);
    if (storedImpersonation) {
      try {
        const parsed = JSON.parse(storedImpersonation);
        setImpersonatedUserState(parsed);
      } catch (error) {
        console.error('Failed to parse impersonation data:', error);
        sessionStorage.removeItem(IMPERSONATION_KEY);
      }
    }
  }, []);

  const setImpersonatedUser = (user: ImpersonatedUser | null) => {
    setImpersonatedUserState(user);
    if (user) {
      sessionStorage.setItem(IMPERSONATION_KEY, JSON.stringify(user));
    } else {
      sessionStorage.removeItem(IMPERSONATION_KEY);
    }
  };

  const exitImpersonation = () => {
    setImpersonatedUser(null);
    // Optionally reload the page to refresh all data
    window.location.reload();
  };

  const value: ImpersonationContextType = {
    impersonatedUser,
    setImpersonatedUser,
    isImpersonating: !!impersonatedUser,
    exitImpersonation,
  };

  return <ImpersonationContext.Provider value={value}>{children}</ImpersonationContext.Provider>;
};

export const useImpersonation = () => {
  const context = useContext(ImpersonationContext);
  if (context === undefined) {
    throw new Error('useImpersonation must be used within an ImpersonationProvider');
  }
  return context;
};
