import { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper, Alert, Dialog, DialogTitle, DialogContent, DialogActions, Button, IconButton } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import { api } from '../services/api';

interface TaskStatus {
  id: number;
  task_type: string;
  status: string;
  progress: number;
  total_items: number;
  processed_items: number;
  message: string | null;
  error_message: string | null;
}

interface TaskProgressIndicatorProps {
  onComplete?: () => void;
  autoRefresh?: boolean;
}

export default function TaskProgressIndicator({ onComplete, autoRefresh = true }: TaskProgressIndicatorProps) {
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const fetchTaskStatus = async () => {
    try {
      const response = await api.get<TaskStatus>('/tasks/status/');
      const data = response.data;

      const previousStatus = taskStatus?.status;
      setTaskStatus(data);

      // If task just completed (transition from running to completed), show success dialog
      if (data && data.status === 'completed' && previousStatus === 'running') {
        setIsPolling(false);
        setShowSuccessDialog(true);
        if (onComplete) {
          onComplete();
        }
      }

      // If task failed or cancelled, stop polling
      if (data && (data.status === 'failed' || data.status === 'cancelled')) {
        setIsPolling(false);
      }
    } catch (error) {
      console.error('Error fetching task status:', error);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchTaskStatus();

    // Set up polling if autoRefresh is enabled
    if (autoRefresh) {
      setIsPolling(true);
    }
  }, [autoRefresh]);

  useEffect(() => {
    if (!isPolling) return;

    const interval = setInterval(() => {
      fetchTaskStatus();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [isPolling]);

  const getTaskTypeLabel = (taskType: string) => {
    switch (taskType) {
      case 'collection':
        return 'Collection';
      case 'analysis':
        return 'Analysis';
      case 'analysis_and_report':
        return 'Analysis & Report Generation';
      default:
        return taskType;
    }
  };

  const handleCloseSuccessDialog = () => {
    setShowSuccessDialog(false);
  };

  const handleCancelTask = async () => {
    if (!taskStatus || taskStatus.status !== 'running') return;

    setIsCancelling(true);
    try {
      await api.post(`/tasks/cancel/${taskStatus.id}`);
      setIsPolling(false);
      // Refresh task status to show cancelled state
      await fetchTaskStatus();
    } catch (error: any) {
      console.error('Error cancelling task:', error);
      alert(error.response?.data?.detail || 'Failed to cancel task');
    } finally {
      setIsCancelling(false);
    }
  };

  // Don't render progress bar if no task or task is completed (but show failed and cancelled tasks)
  if (!taskStatus || (taskStatus.status === 'completed' && !showSuccessDialog)) {
    return (
      <>
        {/* Success Dialog */}
        <Dialog
          open={showSuccessDialog}
          onClose={handleCloseSuccessDialog}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle sx={{ textAlign: 'center', pt: 4 }}>
            <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" component="div">
              Success!
            </Typography>
          </DialogTitle>
          <DialogContent sx={{ textAlign: 'center', pb: 2 }}>
            <Typography variant="body1" color="text.secondary">
              Your data has been analyzed and your report is ready!
            </Typography>
          </DialogContent>
          <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
            <Button
              onClick={handleCloseSuccessDialog}
              variant="contained"
              sx={{ bgcolor: '#003e60', '&:hover': { bgcolor: '#80a1d4' } }}
            >
              Got it!
            </Button>
          </DialogActions>
        </Dialog>
      </>
    );
  }

  return (
    <>
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 3,
          borderLeft: `4px solid`,
          borderColor: taskStatus.status === 'failed' ? 'error.main' : taskStatus.status === 'cancelled' ? 'warning.main' : 'primary.main',
        }}
      >
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              {getTaskTypeLabel(taskStatus.task_type)} {taskStatus.status === 'cancelled' ? 'Cancelled' : 'in Progress'}
            </Typography>
            {taskStatus.status === 'running' && (
              <Button
                variant="outlined"
                color="error"
                size="small"
                startIcon={<StopCircleIcon />}
                onClick={handleCancelTask}
                disabled={isCancelling}
                sx={{ minWidth: 100 }}
              >
                {isCancelling ? 'Stopping...' : 'Stop'}
              </Button>
            )}
          </Box>

          {taskStatus.status === 'failed' && taskStatus.error_message && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {taskStatus.error_message}
            </Alert>
          )}

          {taskStatus.status === 'cancelled' && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {taskStatus.message || 'Task was cancelled'}
            </Alert>
          )}

          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {taskStatus.message || 'Processing...'}
              </Typography>
              <Typography variant="body2" color="text.secondary" fontWeight="bold">
                {taskStatus.progress}%
              </Typography>
            </Box>

            <LinearProgress
              variant="determinate"
              value={taskStatus.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                },
              }}
            />

            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {taskStatus.processed_items} of {taskStatus.total_items} items processed
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Success Dialog */}
      <Dialog
        open={showSuccessDialog}
        onClose={handleCloseSuccessDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ textAlign: 'center', pt: 4 }}>
          <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
          <Typography variant="h5" component="div">
            Success!
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ textAlign: 'center', pb: 2 }}>
          <Typography variant="body1" color="text.secondary">
            Your data has been analyzed and your report is ready!
          </Typography>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
          <Button
            onClick={handleCloseSuccessDialog}
            variant="contained"
            sx={{ bgcolor: '#003e60', '&:hover': { bgcolor: '#80a1d4' } }}
          >
            Got it!
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
