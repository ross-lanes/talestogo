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

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AuthProvider>
            <BrandProvider>
              <TaskStatusProvider>
                <AppContent />
              </TaskStatusProvider>
            </BrandProvider>
          </AuthProvider>
        </Router>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
