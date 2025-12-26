import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Component to redirect to external URLs
const ExternalRedirect: React.FC<{ url: string }> = ({ url }) => {
  useEffect(() => {
    window.location.href = url;
  }, [url]);
  return null;
};
import Layout from './Layout';
import Dashboard from '../pages/Dashboard';
import Queries from '../pages/manage/Queries';
import Competitors from '../pages/manage/Competitors';
import Descriptors from '../pages/manage/Descriptors';
import BrandInfo from '../pages/manage/BrandInfo';
import ManageBrands from '../pages/manage/ManageBrands';
import ReportsPage from '../pages/ReportsPage';
import CollectAndAnalyze from '../pages/CollectAndAnalyze';
import Settings from '../pages/Settings';
import UserManagement from '../pages/admin/UserManagement';
import TenantManagement from '../pages/admin/TenantManagement';
import UserBrandData from '../pages/admin/UserBrandData';
import AdminBatches from '../pages/admin/AdminBatches';
import AdminSchedulerDashboard from '../pages/AdminSchedulerDashboard';
import SentimentAnalysis from '../pages/analytics/SentimentAnalysis';
import PositioningAnalysis from '../pages/analytics/PositioningAnalysis';
import ShareOfVoice from '../pages/analytics/ShareOfVoice';
import BrandMentions from '../pages/analytics/BrandMentions';
import DescriptorAnalysis from '../pages/analytics/DescriptorAnalysis';
import CompetitorThreats from '../pages/analytics/CompetitorThreats';
import Recommendations from '../pages/analytics/Recommendations';
import HowTalesWorks from '../pages/HowTalesWorks';
import HowHeadsWorks from '../pages/HowHeadsWorks';
import HowCanonWorks from '../pages/HowCanonWorks';
import Help from '../pages/Help';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import InviteAccept from '../pages/auth/InviteAccept';
// Heads - Persona Intelligence Platform pages
import HeadsDashboard from '../pages/heads/Dashboard';
import GeneratePersonas from '../pages/heads/GeneratePersonas';
import GeneratePatientPersonas from '../pages/heads/GeneratePatientPersonas';
import GenerateHCPPersonas from '../pages/heads/GenerateHCPPersonas';
import Generations from '../pages/heads/Generations';
// Canon - FDA Drug Data Research pages
import {
  CanonLookup,
  CanonQuery,
  CanonAdverseEvents,
  CanonCompare,
  CanonDocuments,
  CanonSavedSearches,
} from '../pages/canon';
// Big Idea Generator - Marketing Idea Generation pages
import { BigIdeaDashboard } from '../pages/bigidea';
import { useAuth } from '../contexts/AuthContext';
import { TenantProvider, useTenant } from '../contexts/TenantContext';
import { ProductProvider } from '../contexts/ProductContext';
import { TenantThemeProvider } from './TenantThemeProvider';
import { TaskStatusBanner } from './TaskStatusBanner';
import { ImpersonationBanner } from './ImpersonationBanner';
import ProtectedRoute from './ProtectedRoute';

// Inner component that has access to TenantContext
const AppRoutes: React.FC = () => {
  const { tenant } = useTenant();
  const { user } = useAuth();

  return (
    <ProductProvider tenantName={tenant?.tenant_name} userAllowedProducts={user?.allowed_products}>
      <TenantThemeProvider>
        <ImpersonationBanner />
        <TaskStatusBanner />
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
            path="/analytics/brand-mentions"
            element={
              <ProtectedRoute>
                <Layout>
                  <BrandMentions />
                </Layout>
              </ProtectedRoute>
            }
          />
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
          <Route path="/manage" element={<Navigate to="/manage/brands" replace />} />

          {/* Data Management Routes */}
          <Route
            path="/manage/brands"
            element={
              <ProtectedRoute>
                <Layout>
                  <ManageBrands />
                </Layout>
              </ProtectedRoute>
            }
          />
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

          {/* Collect & Analyze Route */}
          <Route
            path="/collect-analyze"
            element={
              <ProtectedRoute>
                <Layout>
                  <CollectAndAnalyze />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Legacy routes - redirect to new consolidated page */}
          <Route path="/data" element={<Navigate to="/collect-analyze" replace />} />
          <Route path="/scheduled-tasks" element={<Navigate to="/collect-analyze" replace />} />
          <Route path="/data-analysis" element={<Navigate to="/collect-analyze" replace />} />

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

          {/* How It Works Routes */}
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
          <Route
            path="/how-heads-works"
            element={
              <ProtectedRoute>
                <Layout>
                  <HowHeadsWorks />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/how-canon-works"
            element={
              <ProtectedRoute>
                <Layout>
                  <HowCanonWorks />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Help Route */}
          <Route
            path="/help"
            element={
              <ProtectedRoute>
                <Layout>
                  <Help />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Reports Route */}
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <Layout>
                  <ReportsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Admin Routes - use /settings prefix to avoid conflict with /admin API routes */}
          <Route
            path="/settings/users"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <UserManagement />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/tenants"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <TenantManagement />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/users/:userId/brands/:brandId"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <UserBrandData />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/scheduler"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <AdminSchedulerDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings/batches"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <AdminBatches />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Heads - Persona Intelligence Platform Routes */}
          <Route
            path="/heads"
            element={
              <ProtectedRoute>
                <Layout>
                  <HeadsDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/heads/generate"
            element={
              <ProtectedRoute>
                <Layout>
                  <GeneratePersonas />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/heads/generate/patient"
            element={
              <ProtectedRoute>
                <Layout>
                  <GeneratePatientPersonas />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/heads/generate/hcp"
            element={
              <ProtectedRoute>
                <Layout>
                  <GenerateHCPPersonas />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/heads/generations"
            element={
              <ProtectedRoute>
                <Layout>
                  <Generations />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* NSTXView redirect - external app */}
          <Route
            path="/nstxview"
            element={<ExternalRedirect url="https://nstxview.robotrachel.com" />}
          />
          <Route
            path="/nstxview/*"
            element={<ExternalRedirect url="https://nstxview.robotrachel.com" />}
          />

          {/* Canon - FDA Drug Data Research Routes */}
          <Route
            path="/canon"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonLookup />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/canon/ask"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonQuery />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/canon/adverse-events"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonAdverseEvents />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/canon/compare"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonCompare />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/canon/documents"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonDocuments />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/canon/saved"
            element={
              <ProtectedRoute>
                <Layout>
                  <CanonSavedSearches />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Big Idea Generator - Marketing Idea Generation Routes */}
          <Route
            path="/bigidea"
            element={
              <ProtectedRoute>
                <Layout>
                  <BigIdeaDashboard />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </TenantThemeProvider>
    </ProductProvider>
  );
};

export const AppContent: React.FC = () => {
  const { user } = useAuth();

  return (
    <TenantProvider isAdmin={user?.is_admin || false}>
      <AppRoutes />
    </TenantProvider>
  );
};
