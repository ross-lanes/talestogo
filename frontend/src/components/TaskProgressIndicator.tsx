import { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper, Alert, Dialog, DialogTitle, DialogContent, DialogActions, Button, IconButton } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import { api } from '../services/api';
import { useTaskStatus } from '../contexts/TaskStatusContext';

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
  // REMOVED: Local polling - now uses TaskStatusContext for centralized, optimized polling
  // This was polling every 2 seconds and causing database connection pool exhaustion
  const { tasks } = useTaskStatus();
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [previousTaskId, setPreviousTaskId] = useState<number | null>(null);

  // Get the first task (running, completed, failed, or cancelled)
  const taskStatus = tasks.length > 0 ? tasks[0] : null;

  // Watch for task completion
  useEffect(() => {
    if (!taskStatus) return;

    // If task just completed (new task ID and status is completed)
    if (taskStatus.status === 'completed' && taskStatus.id !== previousTaskId) {
      setShowSuccessDialog(true);
      setPreviousTaskId(taskStatus.id);
      if (onComplete) {
        onComplete();
      }
    }

    // Update previous task ID
    if (taskStatus.id !== previousTaskId) {
      setPreviousTaskId(taskStatus.id);
    }
  }, [taskStatus, onComplete, previousTaskId]);

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
      // Task status will be refreshed by TaskStatusContext
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
