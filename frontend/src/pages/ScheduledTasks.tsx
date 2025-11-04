import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Switch,
  TextField,
  Alert,
  Snackbar,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
} from '@mui/material';
import { Schedule as ScheduleIcon, Save as SaveIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useBrand } from '../contexts/BrandContext';
import { format } from 'date-fns';

interface ScheduleData {
  id: number;
  user_id: number;
  brand_id: number;
  schedule_type: string;
  is_enabled: boolean;
  timezone: string;
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

export default function ScheduledTasks() {
  const { activeBrand } = useBrand();
  const queryClient = useQueryClient();

  const [scheduleType, setScheduleType] = useState('middle');
  const [isEnabled, setIsEnabled] = useState(true);
  const [sendEmail, setSendEmail] = useState(true);
  const [notificationEmail, setNotificationEmail] = useState('');

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info' as 'success' | 'error' | 'info',
  });

  // Fetch existing schedule
  const { data: schedule, isLoading, refetch } = useQuery<ScheduleData | null>({
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
      setScheduleType(schedule.schedule_type);
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

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data = {
        brand_id: activeBrand!.id,
        schedule_type: scheduleType,
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
      refetch();
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

  const getScheduleLabel = (type: string) => {
    switch (type) {
      case 'first_day':
        return 'First day of month (1st)';
      case 'middle':
        return 'Middle of month (15th)';
      case 'last_day':
        return 'Last day of month';
      default:
        return type;
    }
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

  if (!activeBrand) {
    return (
      <Box>
        <Typography variant="h2" component="h1" gutterBottom>
          Scheduled Data Collection
        </Typography>
        <Alert severity="info">
          Please select a brand to configure scheduled data collection.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Scheduled Data Collection
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Set up automated monthly data collection and analysis. Your data will be collected and analyzed automatically on the day you choose each month.
      </Typography>

      {/* Configuration */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <ScheduleIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5">Schedule Configuration</Typography>
        </Box>

        {isLoading ? (
          <CircularProgress />
        ) : (
          <>
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">Collection Day</FormLabel>
              <RadioGroup
                value={scheduleType}
                onChange={(e) => setScheduleType(e.target.value)}
              >
                <FormControlLabel
                  value="first_day"
                  control={<Radio />}
                  label="First day of month (1st) - Start of month reporting"
                />
                <FormControlLabel
                  value="middle"
                  control={<Radio />}
                  label="Middle of month (15th) - Mid-month checkpoint"
                />
                <FormControlLabel
                  value="last_day"
                  control={<Radio />}
                  label="Last day of month - End of month summary"
                />
              </RadioGroup>
            </FormControl>

            {schedule && (
              <FormControlLabel
                control={
                  <Switch
                    checked={isEnabled}
                    onChange={(e) => setIsEnabled(e.target.checked)}
                  />
                }
                label="Enable automatic collection"
                sx={{ mb: 3 }}
              />
            )}

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Email Notifications
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={sendEmail}
                    onChange={(e) => setSendEmail(e.target.checked)}
                  />
                }
                label="Send email when collection completes"
                sx={{ mb: 2 }}
              />

              {sendEmail && (
                <TextField
                  fullWidth
                  label="Notification Email (optional)"
                  placeholder="Leave blank to use your account email"
                  value={notificationEmail}
                  onChange={(e) => setNotificationEmail(e.target.value)}
                  helperText="Override the default email address for notifications"
                />
              )}
            </Box>

            {schedule && schedule.next_run_at && (
              <Alert severity="info" sx={{ mb: 3 }}>
                Next scheduled run: {format(new Date(schedule.next_run_at), 'MMMM dd, yyyy \'at\' h:mm a')}
              </Alert>
            )}

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
              {saveMutation.isPending ? 'Saving...' : 'Save Schedule'}
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
                      {format(new Date(run.started_at), 'MMM dd, yyyy h:mm a')}
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
