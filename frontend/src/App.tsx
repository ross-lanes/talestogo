import { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './contexts/AuthContext';
import { BrandProvider } from './contexts/BrandContext';
import { TaskStatusProvider } from './contexts/TaskStatusContext';
import { AppContent } from './components/AppContent';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Component to handle admin impersonation
function ImpersonationHandler({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Check if this is an impersonation request
    const urlParams = new URLSearchParams(window.location.search);
    const impersonateParam = urlParams.get('impersonate');

    if (impersonateParam && window.opener) {
      // This is a new tab opened from "Login As" feature
      try {
        // Get the impersonation data from the opener's sessionStorage
        const impersonationDataStr = window.opener.sessionStorage.getItem('tales_impersonation');

        if (impersonationDataStr) {
          const impersonationData = JSON.parse(impersonationDataStr);

          // Set the token and user in localStorage
          localStorage.setItem('tales_access_token', impersonationData.token);
          localStorage.setItem('tales_user', JSON.stringify(impersonationData.user));

          // Clear the impersonation data from opener
          window.opener.sessionStorage.removeItem('tales_impersonation');

          // Remove the impersonate parameter from URL and reload
          window.history.replaceState({}, document.title, '/');
          window.location.reload();
        }
      } catch (error) {
        console.error('Failed to set up impersonation:', error);
      }
    }
  }, []);

  return <>{children}</>;
}

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <ImpersonationHandler>
            <AuthProvider>
              <BrandProvider>
                <TaskStatusProvider>
                  <AppContent />
                </TaskStatusProvider>
              </BrandProvider>
            </AuthProvider>
          </ImpersonationHandler>
        </Router>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
