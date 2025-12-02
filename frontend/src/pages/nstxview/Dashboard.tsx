import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Description as PaperIcon,
  Bolt as ShotIcon,
  Analytics as ParameterIcon,
  Science as PhenomenonIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

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
  const [searchQuery, setSearchQuery] = useState('');
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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/nstxview/papers?search=${encodeURIComponent(searchQuery)}`);
    }
  };

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

      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <form onSubmit={handleSearch}>
          <TextField
            fullWidth
            placeholder="Search papers, shots, parameters, or phenomena..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </form>
      </Paper>

      {/* Processing Status Banner */}
      {processingStatus?.active_task && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Processing in progress:</strong> {processingStatus.active_task.message}
            ({processingStatus.active_task.processed_items}/{processingStatus.active_task.total_items})
          </Typography>
        </Alert>
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

      {/* Top Lists */}
      {stats && (
        <Grid container spacing={3}>
          {/* Top Parameters */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Top Parameters
              </Typography>
              <List>
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

          {/* Top Phenomena */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Top Phenomena
              </Typography>
              <List>
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

      {/* Quick Actions */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            onClick={() => navigate('/nstxview/papers')}
          >
            Browse Papers
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/nstxview/shots')}
          >
            Explore Shots
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/nstxview/parameters')}
          >
            Analyze Parameters
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/nstxview/processing')}
          >
            Processing Status
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default NSTXViewDashboard;
