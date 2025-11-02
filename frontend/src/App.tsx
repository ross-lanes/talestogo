import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { theme } from './theme/theme';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Manage from './pages/Manage';
import Queries from './pages/manage/Queries';
import Competitors from './pages/manage/Competitors';
import Descriptors from './pages/manage/Descriptors';
import BrandInfo from './pages/manage/BrandInfo';
import Reports from './pages/Reports';
import DataAnalysis from './pages/DataAnalysis';
import Data from './pages/Data';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import InviteAccept from './pages/auth/InviteAccept';
import Settings from './pages/Settings';
import UserManagement from './pages/admin/UserManagement';
import UserBrandData from './pages/admin/UserBrandData';
import SentimentAnalysis from './pages/analytics/SentimentAnalysis';
import PositioningAnalysis from './pages/analytics/PositioningAnalysis';
import ShareOfVoice from './pages/analytics/ShareOfVoice';
import DescriptorAnalysis from './pages/analytics/DescriptorAnalysis';
import CompetitorThreats from './pages/analytics/CompetitorThreats';
import Recommendations from './pages/analytics/Recommendations';
import HowTalesWorks from './pages/HowTalesWorks';
import { AuthProvider } from './contexts/AuthContext';
import { BrandProvider } from './contexts/BrandContext';
import ProtectedRoute from './components/ProtectedRoute';

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
        <ThemeProvider theme={theme}>
          <Router>
            <AuthProvider>
              <BrandProvider>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/invite/accept" element={<InviteAccept />} />

                  {/* Protected Routes */}
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Dashboard />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Analytics Routes */}
                  <Route
                    path="/analytics/positioning"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <PositioningAnalysis />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/analytics/share-of-voice"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <ShareOfVoice />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/analytics/descriptors"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <DescriptorAnalysis />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/analytics/sentiment"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <SentimentAnalysis />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/analytics/threats"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <CompetitorThreats />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/analytics/recommendations"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Recommendations />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Manage Route - redirect to brand-info */}
                  <Route
                    path="/manage"
                    element={<Navigate to="/manage/brand-info" replace />}
                  />

                  {/* Data Management Routes */}
                  <Route
                    path="/manage/queries"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Queries />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/manage/descriptors"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Descriptors />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/manage/competitors"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Competitors />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/manage/brand-info"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <BrandInfo />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Data Route */}
                  <Route
                    path="/data"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Data />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Data Analysis Route */}
                  <Route
                    path="/data-analysis"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <DataAnalysis />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Settings Route */}
                  <Route
                    path="/settings"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Settings />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* How Tales Works Route */}
                  <Route
                    path="/how-tales-works"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <HowTalesWorks />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Admin Routes */}
                  <Route
                    path="/admin/users"
                    element={
                      <ProtectedRoute requireAdmin>
                        <Layout>
                          <UserManagement />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/users/:userId/brands/:brandId"
                    element={
                      <ProtectedRoute requireAdmin>
                        <Layout>
                          <UserBrandData />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />

                  {/* Catch-all redirect */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </BrandProvider>
            </AuthProvider>
          </Router>
        </ThemeProvider>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
