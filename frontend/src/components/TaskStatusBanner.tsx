import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  IconButton,
  Collapse,
  Chip,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Autorenew as AutorenewIcon,
} from '@mui/icons-material';
import { useTaskStatus, type Task } from '../contexts/TaskStatusContext';
import { formatDateEST } from '../utils/dateUtils';

const TASK_TYPE_LABELS: Record<string, string> = {
  collection: 'Collection',
  analysis: 'Analysis',
  report_generation: 'Report Generation',
};

const TASK_TYPE_COLORS: Record<string, string> = {
  collection: '#75c9c8',  // Teal
  analysis: '#003e60',    // Purple
  report_generation: '#80a1d4',  // Blue
};

interface TaskItemProps {
  task: Task;
  onDismiss: (taskId: number) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onDismiss }) => {
  const [expanded, setExpanded] = useState(false);

  const taskLabel = TASK_TYPE_LABELS[task.task_type] || task.task_type;
  const taskColor = TASK_TYPE_COLORS[task.task_type] || '#003e60';

  // Auto-dismiss completed tasks after 30 seconds
  useEffect(() => {
    if (task.status === 'completed') {
      const timer = setTimeout(() => {
        onDismiss(task.id);
      }, 30000); // 30 seconds

      return () => clearTimeout(timer);
    }

    // Also auto-dismiss tasks that have been "running" for more than 2 hours (likely stale)
    if (task.status === 'running') {
      const startedAt = new Date(task.started_at).getTime();
      const now = Date.now();
      const twoHoursInMs = 2 * 60 * 60 * 1000;

      if (now - startedAt > twoHoursInMs) {
        console.warn(`Auto-dismissing stale task ${task.id} that has been running for >2 hours`);
        onDismiss(task.id);
      }
    }
  }, [task.status, task.id, task.started_at, onDismiss]);

  // Determine status icon and color
  const getStatusIcon = () => {
    switch (task.status) {
      case 'running':
        return <AutorenewIcon sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />;
      case 'completed':
        return <CheckCircleIcon sx={{ color: '#58A13B' }} />;
      case 'failed':
        return <ErrorIcon sx={{ color: '#EA4A4A' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (task.status) {
      case 'running':
        return taskColor;
      case 'completed':
        return '#58A13B';
      case 'failed':
        return '#EA4A4A';
      default:
        return '#666';
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        mb: 1,
        borderLeft: `4px solid ${getStatusColor()}`,
        overflow: 'hidden',
      }}
    >
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
            {getStatusIcon()}
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              {taskLabel}
            </Typography>
            <Chip
              label={task.status.toUpperCase()}
              size="small"
              sx={{
                backgroundColor: getStatusColor(),
                color: 'white',
                fontWeight: 600,
                fontSize: '0.75rem',
              }}
            />
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {task.status !== 'running' && (
              <IconButton
                size="small"
                onClick={() => setExpanded(!expanded)}
                title={expanded ? 'Collapse' : 'Expand'}
                sx={{ color: 'text.secondary' }}
              >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            )}
            {/* Always show close button so users can dismiss notifications */}
            <IconButton
              size="small"
              onClick={() => onDismiss(task.id)}
              title="Close notification"
              sx={{
                color: 'text.secondary',
                '&:hover': {
                  color: 'error.main',
                  backgroundColor: 'rgba(234, 74, 74, 0.1)'
                }
              }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Progress bar for running tasks */}
        {task.status === 'running' && (
          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                {task.message || 'Processing...'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {task.progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={task.progress}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: 'rgba(0,0,0,0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: taskColor,
                },
              }}
            />
            {task.total_items > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                {task.processed_items} of {task.total_items} items processed
              </Typography>
            )}
          </Box>
        )}

        {/* Completion message */}
        {task.status === 'completed' && !expanded && (
          <Typography variant="body2" color="text.secondary">
            Task completed successfully
          </Typography>
        )}

        {/* Error message preview */}
        {task.status === 'failed' && !expanded && (
          <Typography variant="body2" color="error">
            Task failed - click to see details
          </Typography>
        )}

        {/* Expanded details */}
        <Collapse in={expanded}>
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
            {task.status === 'completed' && (
              <Alert severity="success" sx={{ mb: 1 }}>
                Task completed successfully!
                {task.total_items > 0 && ` Processed ${task.total_items} items.`}
              </Alert>
            )}
            {task.status === 'failed' && task.error_message && (
              <Alert severity="error" sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Error Details:
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                  {task.error_message}
                </Typography>
              </Alert>
            )}
            <Typography variant="caption" color="text.secondary" display="block">
              Started: {formatDateEST(task.started_at, 'full')}
            </Typography>
            {task.completed_at && (
              <Typography variant="caption" color="text.secondary" display="block">
                Completed: {formatDateEST(task.completed_at, 'full')}
              </Typography>
            )}
          </Box>
        </Collapse>
      </Box>
    </Paper>
  );
};

export const TaskStatusBanner: React.FC = () => {
  const { tasks, dismissTask } = useTaskStatus();

  // Don't render anything if there are no active tasks
  if (tasks.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 64, // Below app bar
        right: 16,
        width: 400,
        maxWidth: 'calc(100vw - 32px)',
        maxHeight: 'calc(100vh - 96px)',
        overflowY: 'auto',
        zIndex: 1200,
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'transparent',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
        },
      }}
    >
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} onDismiss={dismissTask} />
      ))}
    </Box>
  );
};
