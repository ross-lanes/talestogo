import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Description as PaperIcon,
  Bolt as ShotIcon,
  Analytics as ParameterIcon,
  Science as PhenomenonIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import NSTXViewChat from './NSTXViewChat';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const CHART_COLORS = ['#2196f3', '#ff9800', '#4caf50', '#9c27b0', '#f44336', '#00bcd4'];

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || '';

interface DashboardStats {
  papers: {
    total: number;
    completed: number;
    processing: number;
  };
  shots: {
    total: number;
    unique: number;
  };
  parameters: {
    total: number;
    top: Array<{ name: string; count: number }>;
  };
  phenomena: {
    total: number;
    top: Array<{ type: string; count: number }>;
  };
}

interface ProcessingStatus {
  total_papers: number;
  pending: number;
  processing: number;
  completed: number;
  error: number;
  active_task: {
    id: number;
    type: string;
    total_items: number;
    processed_items: number;
    message: string;
    started_at: string;
  } | null;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
}> = ({ title, value, subtitle, icon, color, onClick }) => (
  <Card
    sx={{
      height: '100%',
      cursor: onClick ? 'pointer' : 'default',
      transition: 'transform 0.2s',
      '&:hover': onClick ? { transform: 'translateY(-2px)' } : {},
    }}
    onClick={onClick}
  >
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography color="textSecondary" variant="overline">
            {title}
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, opacity: 0.7 }}>{icon}</Box>
      </Box>
    </CardContent>
  </Card>
);

const NSTXViewDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      // Fetch stats and processing status in parallel
      const [statsRes, processingRes] = await Promise.all([
        fetch(`${API_BASE}/nstxview/stats`, { headers }),
        fetch(`${API_BASE}/nstxview/processing/status`, { headers }),
      ]);

      if (!statsRes.ok || !processingRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const [statsData, processingData] = await Promise.all([
        statsRes.json(),
        processingRes.json(),
      ]);

      setStats(statsData);
      setProcessingStatus(processingData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            NSTXView Dashboard
          </Typography>
          <Typography variant="body1" color="textSecondary">
            NSTX/NSTX-U Plasma Physics Research Analysis
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* AI Chat Interface */}
      <Box sx={{ mb: 3 }}>
        <NSTXViewChat />
      </Box>

      {/* Processing Status Banner */}
      {processingStatus && (processingStatus.processing > 0 || processingStatus.pending > 0) && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2">
              <strong>Processing Progress:</strong> {processingStatus.completed} of {processingStatus.total_papers} papers completed
            </Typography>
            <Chip
              label={processingStatus.processing > 0 ? 'Processing...' : `${processingStatus.pending} pending`}
              color={processingStatus.processing > 0 ? 'primary' : 'default'}
              size="small"
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={(processingStatus.completed / processingStatus.total_papers) * 100}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
            <Typography variant="caption" color="textSecondary">
              Completed: {processingStatus.completed}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Processing: {processingStatus.processing}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Pending: {processingStatus.pending}
            </Typography>
            {processingStatus.error > 0 && (
              <Typography variant="caption" color="error">
                Errors: {processingStatus.error}
              </Typography>
            )}
          </Box>
        </Paper>
      )}

      {/* Stats Grid */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Papers"
              value={stats.papers.completed}
              subtitle={`${stats.papers.processing} processing`}
              icon={<PaperIcon sx={{ fontSize: 40 }} />}
              color="#2196f3"
              onClick={() => navigate('/nstxview/papers')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Unique Shots"
              value={stats.shots.unique}
              subtitle={`${stats.shots.total} total mentions`}
              icon={<ShotIcon sx={{ fontSize: 40 }} />}
              color="#ff9800"
              onClick={() => navigate('/nstxview/shots')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Parameters"
              value={stats.parameters.total}
              icon={<ParameterIcon sx={{ fontSize: 40 }} />}
              color="#4caf50"
              onClick={() => navigate('/nstxview/parameters')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Phenomena"
              value={stats.phenomena.total}
              icon={<PhenomenonIcon sx={{ fontSize: 40 }} />}
              color="#9c27b0"
              onClick={() => navigate('/nstxview/phenomena')}
            />
          </Grid>
        </Grid>
      )}

      {/* Charts Section */}
      {stats && (stats.parameters.top.length > 0 || stats.phenomena.top.length > 0) && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Top Parameters Chart */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Top Parameters
              </Typography>
              {stats.parameters.top.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart
                    data={stats.parameters.top.map(p => ({
                      name: p.name.replace(/_/g, ' ').substring(0, 15) + (p.name.length > 15 ? '...' : ''),
                      count: p.count,
                    }))}
                    layout="vertical"
                    margin={{ left: 80, right: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={75} />
                    <Tooltip formatter={(value: number) => [`${value} values`, 'Count']} />
                    <Bar dataKey="count" fill="#2196f3" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="textSecondary" sx={{ py: 4, textAlign: 'center' }}>
                  No parameters extracted yet
                </Typography>
              )}
            </Paper>
          </Grid>

          {/* Top Phenomena Chart */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Top Phenomena
              </Typography>
              {stats.phenomena.top.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={stats.phenomena.top.map(p => ({
                        name: p.type.replace(/_/g, ' '),
                        value: p.count,
                      }))}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} (${((percent as number) * 100).toFixed(0)}%)`}
                      labelLine={false}
                    >
                      {stats.phenomena.top.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [`${value} occurrences`, 'Count']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="textSecondary" sx={{ py: 4, textAlign: 'center' }}>
                  No phenomena extracted yet
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Top Lists - Text version for details */}
      {stats && (
        <Grid container spacing={3}>
          {/* Top Parameters List */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Parameter Details
              </Typography>
              <List dense>
                {stats.parameters.top.length > 0 ? (
                  stats.parameters.top.map((param, index) => (
                    <React.Fragment key={param.name}>
                      <ListItem>
                        <ListItemText
                          primary={param.name.replace(/_/g, ' ')}
                          secondary={`${param.count} occurrences`}
                        />
                        <Chip
                          label={param.count}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </ListItem>
                      {index < stats.parameters.top.length - 1 && <Divider />}
                    </React.Fragment>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText primary="No parameters extracted yet" />
                  </ListItem>
                )}
              </List>
            </Paper>
          </Grid>

          {/* Top Phenomena List */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Phenomena Details
              </Typography>
              <List dense>
                {stats.phenomena.top.length > 0 ? (
                  stats.phenomena.top.map((phenom, index) => (
                    <React.Fragment key={phenom.type}>
                      <ListItem>
                        <ListItemText
                          primary={phenom.type.replace(/_/g, ' ')}
                          secondary={`${phenom.count} occurrences`}
                        />
                        <Chip
                          label={phenom.count}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      </ListItem>
                      {index < stats.phenomena.top.length - 1 && <Divider />}
                    </React.Fragment>
                  ))
                ) : (
                  <ListItem>
                    <ListItemText primary="No phenomena extracted yet" />
                  </ListItem>
                )}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}

    </Box>
  );
};

export default NSTXViewDashboard;
