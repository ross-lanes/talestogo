import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  FormControlLabel,
  Switch,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CloudDownload as CollectionIcon,
  Schedule as ScheduleIcon,
  Save as SaveIcon,
  CalendarMonth as CalendarIcon,
  EventRepeat as EventRepeatIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useBrand } from '../contexts/BrandContext';
import TaskProgressIndicator from '../components/TaskProgressIndicator';
import { formatDateEST } from '../utils/dateUtils';

interface ScheduleData {
  id: number;
  user_id: number;
  brand_id: number;
  collection_frequency: string;
  schedule_type: string | null;  // Legacy, deprecated
  is_enabled: boolean;
  timezone: string;
  // New collection tracking fields
  last_collection_at: string | null;
  next_collection_at: string | null;
  // Analysis tracking fields
  last_monthly_analysis_at: string | null;
  last_quarterly_analysis_at: string | null;
  last_annual_analysis_at: string | null;
  // Legacy fields
  last_run_at: string | null;
  next_run_at: string | null;
  last_batch_id: number | null;
  send_email_notification: boolean;
  notification_email: string | null;
  created_at: string;
  updated_at: string;
}

interface HistoryEntry {
  id: number;
  scheduled_task_id: number;
  started_at: string;
  completed_at: string | null;
  status: string;
  batch_id: number | null;
  collection_responses: number;
  analysis_responses: number;
  error_message: string | null;
}

interface SystemSchedule {
  collection: {
    frequency: string;
    day: string;
    time_utc: string;
  };
  analysis: {
    monthly: { day: number; time_utc: string };
    quarterly: { months: number[]; day: number; time_utc: string };
    annual: { month: number; day: number; time_utc: string };
  };
  next_collection: string;
  next_monthly_analysis: string;
  next_quarterly_analysis: string;
  next_annual_analysis: string;
}

interface Response {
  id: number;
  query_id: string;
  platform: string;
  response_text: string;
  timestamp: string;
  analyzed_at: string | null;
  brand_mentioned: string | null;
  sentiment: string | null;
}

export default function CollectAndAnalyze() {
  const { activeBrand } = useBrand();
  const queryClient = useQueryClient();
  const [currentTab, setCurrentTab] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info' as 'success' | 'error' | 'info',
  });

  // Scheduling state (frequency is now fixed, no longer user-configurable)
  const [isEnabled, setIsEnabled] = useState(true);
  const [sendEmail, setSendEmail] = useState(true);
  const [notificationEmail, setNotificationEmail] = useState('');

  // Fetch responses
  const { data: responses, isLoading: responsesLoading } = useQuery<Response[]>({
    queryKey: ['responses'],
    queryFn: async () => {
      const response = await api.get('/responses/');
      return response.data;
    },
    retry: false,
  });

  // Fetch system schedule (fixed for all brands)
  const { data: systemSchedule } = useQuery<SystemSchedule>({
    queryKey: ['system-schedule'],
    queryFn: async () => {
      const response = await api.get('/scheduled-tasks/system-schedule');
      return response.data;
    },
  });

  // Fetch existing schedule
  const { data: schedule, isLoading: scheduleLoading, refetch: refetchSchedule } = useQuery<ScheduleData | null>({
    queryKey: ['schedule', activeBrand?.id],
    queryFn: async () => {
      if (!activeBrand) return null;
      const response = await api.get('/scheduled-tasks/', {
        params: { brand_id: activeBrand.id },
      });
      return response.data;
    },
    enabled: !!activeBrand,
  });

  // Update form when schedule data loads
  useEffect(() => {
    if (schedule) {
      setIsEnabled(schedule.is_enabled);
      setSendEmail(schedule.send_email_notification);
      setNotificationEmail(schedule.notification_email || '');
    }
  }, [schedule]);

  // Fetch history
  const { data: history } = useQuery<HistoryEntry[]>({
    queryKey: ['schedule-history', schedule?.id],
    queryFn: async () => {
      if (!schedule) return [];
      const response = await api.get(`/scheduled-tasks/${schedule.id}/history`);
      return response.data;
    },
    enabled: !!schedule,
  });


  // Collection mutation
  const collectionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tasks/run-collection/');
      return response.data;
    },
    onSuccess: (data) => {
      setShowProgress(true);
      setSnackbar({
        open: true,
        message: data.message + ' ' + (data.note || ''),
        severity: 'success',
      });
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start collection',
        severity: 'error',
      });
    },
  });

  // Save schedule mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = {
        brand_id: activeBrand!.id,
        collection_frequency: 'weekly',  // Legacy field - actual schedule is 1st/7th/14th/21st of each month
        send_email_notification: sendEmail,
        notification_email: notificationEmail || null,
      };

      if (schedule) {
        return api.patch(`/scheduled-tasks/${schedule.id}`, {
          ...data,
          is_enabled: isEnabled,
        });
      } else {
        return api.post('/scheduled-tasks/', data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
      refetchSchedule();
      setSnackbar({
        open: true,
        message: 'Schedule saved successfully!',
        severity: 'success',
      });
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to save schedule',
        severity: 'error',
      });
    },
  });

  const handleRunPipeline = () => {
    collectionMutation.mutate();
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'warning';
    }
  };

  const formatDate = (isoString: string) => {
    return formatDateEST(isoString, 'full');
  };

  if (!activeBrand) {
    return (
      <Box>
        <Typography variant="h2" component="h1" gutterBottom>
          Collect & Analyze
        </Typography>
        <Alert severity="info">
          Please select a brand to collect and analyze data.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Collect & Analyze
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Your brand data is automatically collected and analyzed multiple times per month.
        Reports are generated monthly, quarterly, and annually.
        Run manual collection for immediate results, or configure notifications below.
      </Typography>

      <Tabs
        value={currentTab}
        onChange={(_, newValue) => setCurrentTab(newValue)}
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Automated Schedule" />
        <Tab label="Manual Run" />
      </Tabs>

      {/* Manual Reports Tab */}
      {currentTab === 1 && (
        <Box>
          {/* Action Buttons */}
          <Paper sx={{ p: 4, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Manually Run Collection & Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Click the button below to gather responses from AI platforms and automatically analyze them to populate insights across all analytics pages. This process will take some time. You will receive an email when the process is complete.
            </Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Note:</strong> By default, this will analyze only the latest collected data. For longer-term analysis (quarterly, annual, or custom date ranges), please contact <a href="mailto:admin@robotrachel.com" style={{ color: 'inherit' }}>admin@robotrachel.com</a>.
              </Typography>
            </Alert>

            <Button
              variant="contained"
              size="large"
              startIcon={<CollectionIcon />}
              onClick={handleRunPipeline}
              disabled={collectionMutation.isPending}
              sx={{
                backgroundColor: '#80A1D4',
                '&:hover': {
                  backgroundColor: '#6B8BC0',
                },
              }}
            >
              {collectionMutation.isPending ? 'Running...' : 'Run Collection & Analysis'}
            </Button>
          </Paper>

          {/* Progress Indicator */}
          {showProgress && (
            <TaskProgressIndicator
              onComplete={() => {
                setShowProgress(false);
                queryClient.invalidateQueries({ queryKey: ['responses'] });
                queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
                queryClient.invalidateQueries({ queryKey: ['reports'] });
              }}
            />
          )}

          {/* Quick Stats */}
          <Paper sx={{ p: 4 }}>
            <Typography variant="h5" gutterBottom>
              Data Overview
            </Typography>
            {responsesLoading ? (
              <CircularProgress />
            ) : (
              <Box>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  Total Responses Collected: <strong>{responses?.length || 0}</strong>
                </Typography>
                <Typography variant="body1">
                  Responses Analyzed: <strong>{responses?.filter(r => r.analyzed_at).length || 0}</strong>
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      )}

      {/* Automated Schedule Tab */}
      {currentTab === 0 && (
        <Box>
          {/* System Schedule Info */}
          <Paper sx={{ p: 3, mb: 4, bgcolor: 'primary.50' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <CalendarIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Automated Schedule</Typography>
            </Box>

            <List dense>
              <ListItem>
                <ListItemIcon>
                  <EventRepeatIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Data Collection + Analysis"
                  secondary="On the 1st, 7th, 14th, and 21st of each month at 6:30 AM UTC (runs silently, no email)"
                />
              </ListItem>
              <Divider component="li" />
              <ListItem>
                <ListItemIcon>
                  <AssessmentIcon color="secondary" />
                </ListItemIcon>
                <ListItemText
                  primary="Monthly Reports"
                  secondary="Generated on the 1st of each month at 6:00 AM UTC (email sent)"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <AssessmentIcon color="secondary" />
                </ListItemIcon>
                <ListItemText
                  primary="Quarterly Reports"
                  secondary="Generated on Apr 1, Jul 1, Oct 1, Jan 1 at 7:00 AM UTC (email sent)"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <AssessmentIcon color="secondary" />
                </ListItemIcon>
                <ListItemText
                  primary="Annual Report"
                  secondary="Generated on January 1 at 8:00 AM UTC (email sent)"
                />
              </ListItem>
            </List>

            {systemSchedule && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Next collection:</strong>{' '}
                  {formatDateEST(systemSchedule.next_collection, 'full')}
                </Typography>
                <Typography variant="body2">
                  <strong>Next monthly report:</strong>{' '}
                  {formatDateEST(systemSchedule.next_monthly_analysis, 'full')}
                </Typography>
              </Alert>
            )}
          </Paper>

          {/* Brand Settings */}
          <Paper sx={{ p: 4, mb: 4 }}>
            <Box display="flex" alignItems="center" mb={3}>
              <ScheduleIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h5">Brand Settings</Typography>
            </Box>

            {scheduleLoading ? (
              <CircularProgress />
            ) : (
              <>
                <FormControlLabel
                  control={
                    <Switch
                      checked={isEnabled}
                      onChange={(e) => setIsEnabled(e.target.checked)}
                    />
                  }
                  label="Enable automated data collection for this brand"
                  sx={{ mb: 3, display: 'block' }}
                />

                {!isEnabled && (
                  <Alert severity="warning" sx={{ mb: 3 }}>
                    Automated collection is disabled. Your brand will not be included
                    in scheduled data collection or receive automated reports.
                  </Alert>
                )}

                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Report Notifications
                  </Typography>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={sendEmail}
                        onChange={(e) => setSendEmail(e.target.checked)}
                      />
                    }
                    label="Send email when reports are ready"
                    sx={{ mb: 2 }}
                  />

                  {sendEmail && (
                    <TextField
                      fullWidth
                      label="Notification Email (optional)"
                      placeholder="Leave blank to use your account email"
                      value={notificationEmail}
                      onChange={(e) => setNotificationEmail(e.target.value)}
                      helperText="Override the default email address for report notifications"
                    />
                  )}
                </Box>

                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending}
                  sx={{
                    backgroundColor: '#80A1D4',
                    '&:hover': {
                      backgroundColor: '#6B8BC0',
                    },
                  }}
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Settings'}
                </Button>
              </>
            )}
          </Paper>

          {/* Execution History */}
          {history && history.length > 0 && (
            <Paper sx={{ p: 4 }}>
              <Typography variant="h5" gutterBottom>
                Execution History
              </Typography>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Responses Collected</TableCell>
                      <TableCell align="right">Responses Analyzed</TableCell>
                      <TableCell>Duration</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {history.map((run) => (
                      <TableRow key={run.id}>
                        <TableCell>
                          {formatDateEST(run.started_at, 'full')}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={run.status}
                            color={getStatusColor(run.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{run.collection_responses}</TableCell>
                        <TableCell align="right">{run.analysis_responses}</TableCell>
                        <TableCell>
                          {run.completed_at
                            ? `${Math.round(
                                (new Date(run.completed_at).getTime() -
                                  new Date(run.started_at).getTime()) /
                                  60000
                              )} min`
                            : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}
        </Box>
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
}
