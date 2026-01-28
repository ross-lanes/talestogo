import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { formatDateEST } from '../utils/dateUtils';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Alert,
  AlertTitle,
  Select,
  MenuItem,
  Button,
  FormControl,
  InputLabel,
  Stack,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface SchedulerDashboardData {
  summary: {
    [key: string]: number;
    success: number;
    failed: number;
    partial: number;
    running: number;
    success_rate: number;
    total_active_schedules: number;
    total_schedules: number;
  };
  recent_activity: TaskHistoryItem[];
  active_schedules: ScheduleItem[];
  all_schedules: ScheduleItem[];
  health: {
    failed_tasks: TaskHistoryItem[];
    overdue_tasks: ScheduleItem[];
    stalled_tasks: TaskHistoryItem[];
    has_issues: boolean;
  };
}

interface TaskHistoryItem {
  id: number;
  scheduled_task_id: number;
  status: string;
  user_email: string | null;
  user_name: string | null;
  brand_name: string | null;
  brand_id: number;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  collection_responses: number | null;
  analysis_responses: number | null;
  error_message: string | null;
  schedule_type: string | null;
}

interface ScheduleItem {
  id: number;
  user_email: string | null;
  user_name: string | null;
  user_id: number;
  brand_name: string | null;
  brand_id: number;
  schedule_type: string;
  is_enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  last_status: string | null;
  send_email_notification: boolean;
  notification_email: string | null;
  timezone: string;
  is_overdue: boolean;
}

export default function AdminSchedulerDashboard() {
  const [dashboardData, setDashboardData] = useState<SchedulerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);
  const [activeTab, setActiveTab] = useState(0);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/admin/scheduler/dashboard?days=${days}`);
      setDashboardData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [days]);

  const getStatusChip = (status: string) => {
    const statusConfig: { [key: string]: { color: any; icon: React.ReactElement } } = {
      success: { color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
      failed: { color: 'error', icon: <ErrorIcon fontSize="small" /> },
      partial: { color: 'warning', icon: <WarningIcon fontSize="small" /> },
      running: { color: 'info', icon: <ScheduleIcon fontSize="small" /> },
    };
    const config = statusConfig[status] || { color: 'default', icon: null };
    return <Chip label={status} color={config.color} size="small" icon={config.icon} />;
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return formatDateEST(dateString, 'full');
  };

  const handleRunNow = async (userId: number, brandId: number, userEmail: string | null, brandName: string | null) => {
    if (!window.confirm(`Run collection & analysis now for ${userEmail} - ${brandName}?`)) {
      return;
    }

    try {
      const response = await api.post(`/admin/run-collection-for-user?user_id=${userId}&brand_id=${brandId}`);
      alert(response.data.message);
      // Refresh dashboard to show the new task
      fetchDashboard();
    } catch (err: any) {
      alert(`Error: ${err.response?.data?.detail || 'Failed to start collection'}`);
    }
  };

  const handleClearOverdue = async (scheduleId: number, brandName: string | null) => {
    if (!window.confirm(`Clear overdue schedule for ${brandName || 'Unknown'}? This will reschedule it for the next regular run time.`)) {
      return;
    }

    try {
      const response = await api.post(`/admin/scheduler/clear-overdue/${scheduleId}`);
      alert(`${response.data.message}\nNew scheduled time: ${formatDateTime(response.data.new_next_run)}`);
      // Refresh dashboard
      fetchDashboard();
    } catch (err: any) {
      alert(`Error: ${err.response?.data?.detail || 'Failed to clear overdue schedule'}`);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return formatDateEST(dateString, 'full');
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography color="text.secondary">Loading dashboard...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!dashboardData) return null;

  const summaryKeys = Object.keys(dashboardData.summary);
  const totalRunsKey = summaryKeys.find(k => k.startsWith('total_runs_last')) || 'total_runs';

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Scheduler Dashboard
        </Typography>
        <Stack direction="row" spacing={2}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={days}
              label="Time Range"
              onChange={(e) => setDays(Number(e.target.value))}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={14}>Last 14 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={fetchDashboard}
          >
            Refresh
          </Button>
        </Stack>
      </Box>

      {/* Health Alert */}
      {dashboardData.health.has_issues && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Issues Detected</AlertTitle>
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            {dashboardData.health.failed_tasks.length > 0 && (
              <li>{dashboardData.health.failed_tasks.length} failed/partial task(s)</li>
            )}
            {dashboardData.health.overdue_tasks.length > 0 && (
              <li>
                {dashboardData.health.overdue_tasks.length} overdue schedule(s):
                <Box component="ul" sx={{ mt: 0.5, mb: 0 }}>
                  {dashboardData.health.overdue_tasks.map((task) => (
                    <li key={task.id}>
                      <Typography variant="body2" component="span">
                        {task.brand_name} ({task.schedule_type})
                      </Typography>
                      <Button
                        size="small"
                        color="warning"
                        sx={{ ml: 1, py: 0, minHeight: 'auto' }}
                        onClick={() => handleClearOverdue(task.id, task.brand_name)}
                      >
                        Clear
                      </Button>
                    </li>
                  ))}
                </Box>
              </li>
            )}
            {dashboardData.health.stalled_tasks.length > 0 && (
              <li>{dashboardData.health.stalled_tasks.length} stalled task(s) (running &gt; 2 hours)</li>
            )}
          </Box>
          <Typography variant="body2" sx={{ mt: 1 }}>
            <Button size="small" onClick={() => setActiveTab(3)}>View Health tab for details</Button>
          </Typography>
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Total Runs
              </Typography>
              <Typography variant="h3" component="div" fontWeight="bold">
                {dashboardData.summary[totalRunsKey]}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Success Rate
              </Typography>
              <Typography variant="h3" component="div" fontWeight="bold" color="success.main">
                {dashboardData.summary.success_rate}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {dashboardData.summary.success} successful
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Active Schedules
              </Typography>
              <Typography variant="h3" component="div" fontWeight="bold" color="primary.main">
                {dashboardData.summary.total_active_schedules}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                of {dashboardData.summary.total_schedules} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Failed/Issues
              </Typography>
              <Typography variant="h3" component="div" fontWeight="bold" color="error.main">
                {dashboardData.summary.failed + dashboardData.summary.partial}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {dashboardData.summary.failed} failed, {dashboardData.summary.partial} partial
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, val) => setActiveTab(val)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Overview" />
          <Tab label="Recent Activity" />
          <Tab label="Schedules" />
          <Tab label="Health" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {/* Overview Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom fontWeight="medium">
                  Status Breakdown
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Success</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color="success.main">
                            {dashboardData.summary.success}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Failed</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color="error.main">
                            {dashboardData.summary.failed}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Partial</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color="warning.main">
                            {dashboardData.summary.partial}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Running</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold" color="info.main">
                            {dashboardData.summary.running}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom fontWeight="medium">
                  Active Schedules
                </Typography>
                {dashboardData.active_schedules.length === 0 ? (
                  <Typography color="text.secondary">No active schedules</Typography>
                ) : (
                  <Box component="ul" sx={{ m: 0, pl: 2 }}>
                    {dashboardData.active_schedules.slice(0, 5).map((schedule) => (
                      <li key={schedule.id}>
                        <Typography variant="body2">
                          {schedule.user_email} - {schedule.brand_name}
                        </Typography>
                      </li>
                    ))}
                    {dashboardData.active_schedules.length > 5 && (
                      <li>
                        <Typography variant="body2" color="text.secondary">
                          ... and {dashboardData.active_schedules.length - 5} more
                        </Typography>
                      </li>
                    )}
                  </Box>
                )}
              </Grid>
            </Grid>
          )}

          {/* Activity Tab */}
          {activeTab === 1 && (
            <>
              <Typography variant="h6" gutterBottom fontWeight="medium">
                Recent Activity
              </Typography>
              {dashboardData.recent_activity.length === 0 ? (
                <Typography color="text.secondary">No recent activity</Typography>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Status</TableCell>
                        <TableCell>User</TableCell>
                        <TableCell>Brand</TableCell>
                        <TableCell>Started</TableCell>
                        <TableCell>Duration</TableCell>
                        <TableCell align="right">Collected</TableCell>
                        <TableCell align="right">Analyzed</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {dashboardData.recent_activity.map((item) => (
                        <TableRow key={item.id} hover>
                          <TableCell>{getStatusChip(item.status)}</TableCell>
                          <TableCell>{item.user_email || 'Unknown'}</TableCell>
                          <TableCell>{item.brand_name || 'Unknown'}</TableCell>
                          <TableCell>{formatDate(item.started_at)}</TableCell>
                          <TableCell>{formatDuration(item.duration_seconds)}</TableCell>
                          <TableCell align="right">{item.collection_responses || 0}</TableCell>
                          <TableCell align="right">{item.analysis_responses || 0}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </>
          )}

          {/* Schedules Tab */}
          {activeTab === 2 && (
            <>
              <Typography variant="h6" gutterBottom fontWeight="medium">
                All Scheduled Tasks
              </Typography>
              {dashboardData.all_schedules.length === 0 ? (
                <Typography color="text.secondary">No schedules found</Typography>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Status</TableCell>
                        <TableCell>User</TableCell>
                        <TableCell>Brand</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Next Run</TableCell>
                        <TableCell>Last Run</TableCell>
                        <TableCell>Last Status</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {dashboardData.all_schedules.map((schedule) => (
                        <TableRow
                          key={schedule.id}
                          hover
                          sx={{
                            backgroundColor: schedule.is_overdue ? 'error.50' : 'inherit'
                          }}
                        >
                          <TableCell>
                            <Chip
                              label={schedule.is_enabled ? 'Enabled' : 'Disabled'}
                              color={schedule.is_enabled ? 'success' : 'default'}
                              size="small"
                            />
                            {schedule.is_overdue && (
                              <Chip label="Overdue" color="error" size="small" sx={{ ml: 1 }} />
                            )}
                          </TableCell>
                          <TableCell>{schedule.user_email || 'Unknown'}</TableCell>
                          <TableCell>{schedule.brand_name || 'Unknown'}</TableCell>
                          <TableCell>{schedule.schedule_type}</TableCell>
                          <TableCell>{formatDate(schedule.next_run_at)}</TableCell>
                          <TableCell>{formatDate(schedule.last_run_at)}</TableCell>
                          <TableCell>
                            {schedule.last_status ? getStatusChip(schedule.last_status) : <Typography variant="body2" color="text.secondary">Never run</Typography>}
                          </TableCell>
                          <TableCell align="center">
                            <Button
                              variant="outlined"
                              size="small"
                              onClick={() => handleRunNow(schedule.user_id, schedule.brand_id, schedule.user_email, schedule.brand_name)}
                            >
                              Run Now
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </>
          )}

          {/* Health Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom fontWeight="medium">
                System Health
              </Typography>

              {!dashboardData.health.has_issues ? (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <AlertTitle>All Systems Healthy</AlertTitle>
                  No issues detected with scheduled tasks.
                </Alert>
              ) : (
                <Stack spacing={3} sx={{ mt: 2 }}>
                  {/* Stalled Tasks */}
                  {dashboardData.health.stalled_tasks.length > 0 && (
                    <Box>
                      <Alert severity="error" sx={{ mb: 2 }}>
                        <AlertTitle>Stalled Tasks (Running &gt; 2 hours)</AlertTitle>
                        {dashboardData.health.stalled_tasks.length} task(s) appear to be stuck
                      </Alert>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>User</TableCell>
                              <TableCell>Brand</TableCell>
                              <TableCell>Started</TableCell>
                              <TableCell>Collected</TableCell>
                              <TableCell>Analyzed</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {dashboardData.health.stalled_tasks.map((task) => (
                              <TableRow key={task.id}>
                                <TableCell>{task.user_email}</TableCell>
                                <TableCell>{task.brand_name}</TableCell>
                                <TableCell>{formatDate(task.started_at)}</TableCell>
                                <TableCell>{task.collection_responses || 0}</TableCell>
                                <TableCell>{task.analysis_responses || 0}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}

                  {/* Failed Tasks */}
                  {dashboardData.health.failed_tasks.length > 0 && (
                    <Box>
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        <AlertTitle>Failed/Partial Tasks</AlertTitle>
                        {dashboardData.health.failed_tasks.length} task(s) did not complete successfully
                      </Alert>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Status</TableCell>
                              <TableCell>User</TableCell>
                              <TableCell>Brand</TableCell>
                              <TableCell>Started</TableCell>
                              <TableCell>Error</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {dashboardData.health.failed_tasks.map((task) => (
                              <TableRow key={task.id}>
                                <TableCell>{getStatusChip(task.status)}</TableCell>
                                <TableCell>{task.user_email}</TableCell>
                                <TableCell>{task.brand_name}</TableCell>
                                <TableCell>{formatDate(task.started_at)}</TableCell>
                                <TableCell>{task.error_message || 'No error message'}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}

                  {/* Overdue Schedules */}
                  {dashboardData.health.overdue_tasks.length > 0 && (
                    <Box>
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        <AlertTitle>Overdue Schedules</AlertTitle>
                        {dashboardData.health.overdue_tasks.length} schedule(s) missed their run time
                      </Alert>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>User</TableCell>
                              <TableCell>Brand</TableCell>
                              <TableCell>Type</TableCell>
                              <TableCell>Next Run (Missed)</TableCell>
                              <TableCell align="center">Actions</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {dashboardData.health.overdue_tasks.map((schedule) => (
                              <TableRow key={schedule.id}>
                                <TableCell>{schedule.user_email}</TableCell>
                                <TableCell>{schedule.brand_name}</TableCell>
                                <TableCell>{schedule.schedule_type}</TableCell>
                                <TableCell>{formatDate(schedule.next_run_at)}</TableCell>
                                <TableCell align="center">
                                  <Stack direction="row" spacing={1} justifyContent="center">
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color="primary"
                                      onClick={() => handleRunNow(schedule.user_id, schedule.brand_id, schedule.user_email, schedule.brand_name)}
                                    >
                                      Run Now
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color="warning"
                                      onClick={() => handleClearOverdue(schedule.id, schedule.brand_name)}
                                    >
                                      Clear
                                    </Button>
                                  </Stack>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}
                </Stack>
              )}
            </Box>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
