import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { CalendarMonth } from '@mui/icons-material';
import { useBrand } from '../contexts/BrandContext';

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
  const { activeBrand } = useBrand();

  const { data: batches, isLoading, error } = useQuery<CollectionBatch[]>({
    queryKey: ['collection-batches', activeBrand?.id],
    queryFn: async () => {
      const params = activeBrand?.id ? { brand_id: activeBrand.id } : {};
      const response = await api.get('/batches/', { params });
      return response.data;
    },
    enabled: !!activeBrand, // Only fetch when there's an active brand
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    // Display collection start date and time in EST for clear identification
    // This helps distinguish between multiple collections on the same day
    const dateStr = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      timeZone: 'America/New_York'
    });
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: 'America/New_York'
    });
    return `${dateStr} at ${timeStr}`;
  };

  // Sort batches by started_at descending (most recent first)
  const sortedBatches = batches ? [...batches].sort((a, b) =>
    new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  ) : [];

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

  // Get the display value for the selected batch
  const getDisplayValue = () => {
    if (selectedBatchId === null || selectedBatchId === undefined) {
      return 'All Data';
    }
    const selectedBatch = sortedBatches.find(b => b.id === selectedBatchId);
    return selectedBatch ? formatDate(selectedBatch.started_at) : '';
  };

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
        renderValue={() => (
          <Typography variant="body2" fontWeight={500}>
            {getDisplayValue()}
          </Typography>
        )}
      >
        {sortedBatches.map((batch) => (
          <MenuItem key={batch.id} value={batch.id}>
            <Typography variant="body2">
              {formatDate(batch.started_at)}
            </Typography>
          </MenuItem>
        ))}
        {showAllOption && (
          <MenuItem value="">
            <Typography variant="body2" fontWeight={600}>
              All Data
            </Typography>
          </MenuItem>
        )}
      </Select>
    </FormControl>
  );
};

export default BatchSelector;
