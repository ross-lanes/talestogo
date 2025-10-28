import { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper, Alert } from '@mui/material';
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

  const fetchTaskStatus = async () => {
    try {
      const response = await api.get<TaskStatus>('/tasks/status/');
      const data = response.data;

      setTaskStatus(data);

      // If task is completed or failed, stop polling and call onComplete
      if (data && (data.status === 'completed' || data.status === 'failed')) {
        setIsPolling(false);
        if (onComplete) {
          onComplete();
        }
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

  // Don't render anything if no task or task is completed
  if (!taskStatus || taskStatus.status === 'completed') {
    return null;
  }

  const getTaskTypeLabel = (taskType: string) => {
    switch (taskType) {
      case 'collection':
        return 'Data Collection';
      case 'analysis_and_report':
        return 'Analysis & Report Generation';
      default:
        return taskType;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        mb: 3,
        borderLeft: `4px solid`,
        borderColor: taskStatus.status === 'failed' ? 'error.main' : 'primary.main',
      }}
    >
      <Box>
        <Typography variant="h6" gutterBottom>
          {getTaskTypeLabel(taskStatus.task_type)} in Progress
        </Typography>

        {taskStatus.status === 'failed' && taskStatus.error_message && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {taskStatus.error_message}
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
  );
}
