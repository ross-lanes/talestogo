import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export interface Task {
  id: number;
  task_type: 'collection' | 'analysis' | 'report_generation';
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total_items: number;
  processed_items: number;
  message: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  updated_at: string;
}

interface TaskStatusContextType {
  tasks: Task[];
  isLoading: boolean;
  refreshTasks: () => Promise<void>;
  dismissTask: (taskId: number) => void;
}

const TaskStatusContext = createContext<TaskStatusContextType | undefined>(undefined);

export const useTaskStatus = () => {
  const context = useContext(TaskStatusContext);
  if (!context) {
    throw new Error('useTaskStatus must be used within a TaskStatusProvider');
  }
  return context;
};

interface TaskStatusProviderProps {
  children: React.ReactNode;
}

export const TaskStatusProvider: React.FC<TaskStatusProviderProps> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dismissedTaskIds, setDismissedTaskIds] = useState<Set<number>>(new Set());

  const refreshTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.get<Task[]>('/tasks/status');
      // Filter out dismissed tasks
      const filteredTasks = response.data.filter(task => !dismissedTaskIds.has(task.id));
      setTasks(filteredTasks);
    } catch (error: any) {
      console.error('Failed to fetch task status:', error);
      // Don't show error to user - just fail silently for background polling
    } finally {
      setIsLoading(false);
    }
  }, [dismissedTaskIds]);

  const dismissTask = useCallback(async (taskId: number) => {
    try {
      await api.post(`/tasks/${taskId}/dismiss`);
      // Add to dismissed set
      setDismissedTaskIds(prev => new Set(prev).add(taskId));
      // Remove from current tasks
      setTasks(prev => prev.filter(task => task.id !== taskId));
    } catch (error: any) {
      console.error('Failed to dismiss task:', error);
    }
  }, []);

  // Poll for task updates every 5 seconds
  useEffect(() => {
    // Initial fetch
    refreshTasks();

    // Set up polling interval
    const interval = setInterval(() => {
      refreshTasks();
    }, 5000); // Poll every 5 seconds

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, [refreshTasks]);

  return (
    <TaskStatusContext.Provider value={{ tasks, isLoading, refreshTasks, dismissTask }}>
      {children}
    </TaskStatusContext.Provider>
  );
};
