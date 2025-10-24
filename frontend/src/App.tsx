import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme/theme';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Queries from './pages/manage/Queries';
import Competitors from './pages/manage/Competitors';
import Descriptors from './pages/manage/Descriptors';
import Responses from './pages/data/Responses';

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Placeholder components for other pages
const PlaceholderPage = ({ title }: { title: string }) => (
  <div>
    <h2>{title}</h2>
    <p>This page will be built in the next phase.</p>
  </div>
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />

              {/* Analytics Routes */}
              <Route path="/analytics/positioning" element={<PlaceholderPage title="Positioning Analysis" />} />
              <Route path="/analytics/share-of-voice" element={<PlaceholderPage title="Share of Voice" />} />
              <Route path="/analytics/descriptors" element={<PlaceholderPage title="Descriptor Analysis" />} />
              <Route path="/analytics/sentiment" element={<PlaceholderPage title="Sentiment Analysis" />} />
              <Route path="/analytics/threats" element={<PlaceholderPage title="Competitor Threats" />} />
              <Route path="/analytics/priorities" element={<PlaceholderPage title="Strategic Priorities" />} />

              {/* Data Management Routes */}
              <Route path="/manage/queries" element={<Queries />} />
              <Route path="/manage/descriptors" element={<Descriptors />} />
              <Route path="/manage/competitors" element={<Competitors />} />

              {/* Data Viewing Routes */}
              <Route path="/data/responses" element={<Responses />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
