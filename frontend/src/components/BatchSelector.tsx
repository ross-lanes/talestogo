import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Typography,
  Chip,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { CalendarMonth } from '@mui/icons-material';

interface CollectionBatch {
  id: number;
  batch_name: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  total_queries: number;
  total_responses: number;
  platforms: string | null;
  description: string | null;
}

interface BatchSelectorProps {
  selectedBatchId: number | null;
  onBatchChange: (batchId: number | null) => void;
  showAllOption?: boolean;
  label?: string;
}

const BatchSelector: React.FC<BatchSelectorProps> = ({
  selectedBatchId,
  onBatchChange,
  showAllOption = true,
  label = 'Collection Batch',
}) => {
  const { data: batches, isLoading, error } = useQuery<CollectionBatch[]>({
    queryKey: ['collection-batches'],
    queryFn: async () => {
      const response = await api.get('/batches/');
      return response.data;
    },
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          Loading batches...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Typography variant="body2" color="error">
        Error loading batches
      </Typography>
    );
  }

  if (!batches || batches.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No collection batches available
      </Typography>
    );
  }

  return (
    <FormControl fullWidth size="small">
      <InputLabel id="batch-selector-label">{label}</InputLabel>
      <Select
        labelId="batch-selector-label"
        id="batch-selector"
        value={selectedBatchId ?? ''}
        label={label}
        onChange={(e) => {
          const value = e.target.value;
          onBatchChange(value === '' ? null : Number(value));
        }}
        startAdornment={
          <CalendarMonth sx={{ ml: 1, mr: 0.5, color: 'text.secondary', fontSize: 20 }} />
        }
      >
        {showAllOption && (
          <MenuItem value="">
            <Typography variant="body2" fontWeight={600}>
              All Data
            </Typography>
          </MenuItem>
        )}
        {batches.map((batch) => (
          <MenuItem key={batch.id} value={batch.id}>
            <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%', py: 0.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2" fontWeight={500}>
                  {batch.batch_name}
                </Typography>
                <Chip
                  label={batch.status}
                  size="small"
                  color={getStatusColor(batch.status)}
                  sx={{ height: 20, fontSize: '0.7rem', textTransform: 'capitalize' }}
                />
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                <Typography variant="caption" color="text.secondary">
                  {formatDate(batch.started_at)}
                  {batch.completed_at && ` - ${formatDate(batch.completed_at)}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {batch.total_responses} responses • {batch.total_queries} queries
                </Typography>
                {batch.platforms && (
                  <Typography variant="caption" color="text.secondary">
                    {batch.platforms}
                  </Typography>
                )}
              </Box>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default BatchSelector;
