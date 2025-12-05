import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Card,
  CardContent,
  Tooltip,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  History as HistoryIcon,
  PlayArrow as RunIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface ThresholdSummary {
  id: number;
  parameter_name: string;
  parameter_pattern: string | null;
  min_value: number | null;
  max_value: number | null;
  expected_unit: string | null;
  category: string | null;
  active: boolean;
  source: string | null;
  notes: string | null;
}

interface ThresholdDetail {
  id: number;
  parameter_name: string;
  parameter_pattern: string | null;
  min_value: number | null;
  max_value: number | null;
  expected_unit: string | null;
  category: string | null;
  reason_below: string | null;
  reason_above: string | null;
  flag_all: boolean;
  special_case: string | null;
  source: string | null;
  active: boolean;
  created_at: string;
  created_by: number | null;
  notes: string | null;
}

interface ThresholdHistoryRecord {
  id: number;
  parameter_name: string;
  old_min: number | null;
  old_max: number | null;
  new_min: number | null;
  new_max: number | null;
  changed_by: number;
  changed_by_email: string | null;
  changed_at: string;
  reason: string | null;
  reprocessing_triggered: boolean;
}

const ThresholdManagement: React.FC = () => {
  const [thresholds, setThresholds] = useState<ThresholdSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedThreshold, setSelectedThreshold] = useState<ThresholdDetail | null>(null);
  const [historyRecords, setHistoryRecords] = useState<ThresholdHistoryRecord[]>([]);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [reprocessDialogOpen, setReprocessDialogOpen] = useState(false);

  // Edit form state
  const [editMinValue, setEditMinValue] = useState('');
  const [editMaxValue, setEditMaxValue] = useState('');
  const [editReason, setEditReason] = useState('');
  const [triggerReprocessing, setTriggerReprocessing] = useState(false);

  useEffect(() => {
    fetchThresholds();
  }, [categoryFilter]);

  const fetchThresholds = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();
      params.append('active_only', 'true');

      if (categoryFilter !== 'all') {
        params.append('category', categoryFilter);
      }

      const response = await fetch(`${API_BASE}/nstxview/thresholds/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch thresholds');
      }

      const data = await response.json();
      setThresholds(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const viewThresholdDetail = async (thresholdId: number) => {
    try {
      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/thresholds/${thresholdId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch threshold details');
      }

      const data = await response.json();
      setSelectedThreshold(data);
      setDetailDialogOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const openEditDialog = () => {
    if (!selectedThreshold) return;

    setEditMinValue(selectedThreshold.min_value?.toString() || '');
    setEditMaxValue(selectedThreshold.max_value?.toString() || '');
    setEditReason('');
    setTriggerReprocessing(false);
    setDetailDialogOpen(false);
    setEditDialogOpen(true);
  };

  const submitEdit = async () => {
    if (!selectedThreshold) return;

    if (!editReason.trim()) {
      setError('Please provide a reason for changing the threshold');
      return;
    }

    try {
      const token = localStorage.getItem('tales_access_token');
      const payload: any = {
        reason: editReason,
        trigger_reprocessing: triggerReprocessing,
      };

      if (editMinValue) {
        payload.min_value = parseFloat(editMinValue);
      }
      if (editMaxValue) {
        payload.max_value = parseFloat(editMaxValue);
      }

      const response = await fetch(`${API_BASE}/nstxview/thresholds/${selectedThreshold.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update threshold');
      }

      setSuccess('Threshold updated successfully' + (triggerReprocessing ? '. Reprocessing initiated.' : ''));
      setEditDialogOpen(false);
      setSelectedThreshold(null);
      fetchThresholds();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const viewHistory = async (thresholdId: number) => {
    try {
      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/thresholds/${thresholdId}/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch threshold history');
      }

      const data = await response.json();
      setHistoryRecords(data);
      setHistoryDialogOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const triggerManualReprocessing = async () => {
    try {
      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/thresholds/reprocess`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to trigger reprocessing');
      }

      setSuccess('Reprocessing initiated successfully');
      setReprocessDialogOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const filteredThresholds = thresholds.filter(t =>
    t.parameter_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Parameter Threshold Management
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Configure acceptable ranges for NSTX/NSTX-U parameters based on machine specifications
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Paper sx={{ mb: 3, p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              placeholder="Search parameter name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="Category"
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="operational">Operational</MenuItem>
                <MenuItem value="plasma">Plasma</MenuItem>
                <MenuItem value="performance">Performance</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={12} md={5} sx={{ textAlign: 'right' }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchThresholds}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<RunIcon />}
              onClick={() => setReprocessDialogOpen(true)}
            >
              Reprocess All
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Parameter</TableCell>
              <TableCell>Min Value</TableCell>
              <TableCell>Max Value</TableCell>
              <TableCell>Unit</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Source</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : filteredThresholds.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No thresholds found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredThresholds.map((threshold) => (
                <TableRow key={threshold.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {threshold.parameter_name}
                    </Typography>
                    {threshold.parameter_pattern && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Pattern: {threshold.parameter_pattern}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {threshold.min_value !== null ? threshold.min_value : '—'}
                  </TableCell>
                  <TableCell>
                    {threshold.max_value !== null ? threshold.max_value : '—'}
                  </TableCell>
                  <TableCell>{threshold.expected_unit}</TableCell>
                  <TableCell>
                    <Chip
                      label={threshold.category}
                      size="small"
                      color={
                        threshold.category === 'operational' ? 'primary' :
                        threshold.category === 'plasma' ? 'secondary' : 'default'
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title={threshold.source || 'No source'}>
                      <Typography variant="caption" noWrap sx={{ maxWidth: 200, display: 'block' }}>
                        {threshold.source || '—'}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => viewThresholdDetail(threshold.id)}
                      title="View Details"
                    >
                      <InfoIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => viewHistory(threshold.id)}
                      title="View History"
                    >
                      <HistoryIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedThreshold && (
          <>
            <DialogTitle>
              {selectedThreshold.parameter_name}
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Acceptable Range
                      </Typography>
                      <Typography variant="h6">
                        {selectedThreshold.min_value} - {selectedThreshold.max_value} {selectedThreshold.expected_unit}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Category
                      </Typography>
                      <Chip label={selectedThreshold.category} />
                    </CardContent>
                  </Card>
                </Grid>

                {selectedThreshold.parameter_pattern && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Matching Pattern
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {selectedThreshold.parameter_pattern}
                    </Typography>
                  </Grid>
                )}

                <Grid item xs={12}>
                  <Divider />
                </Grid>

                {selectedThreshold.reason_below && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Reason Below Minimum
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50' }}>
                      <Typography variant="body2">
                        {selectedThreshold.reason_below}
                      </Typography>
                    </Paper>
                  </Grid>
                )}

                {selectedThreshold.reason_above && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Reason Above Maximum
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50' }}>
                      <Typography variant="body2">
                        {selectedThreshold.reason_above}
                      </Typography>
                    </Paper>
                  </Grid>
                )}

                {selectedThreshold.source && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Source
                    </Typography>
                    <Typography variant="body2">
                      {selectedThreshold.source}
                    </Typography>
                  </Grid>
                )}

                {selectedThreshold.notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Notes
                    </Typography>
                    <Typography variant="body2">
                      {selectedThreshold.notes}
                    </Typography>
                  </Grid>
                )}

                {(selectedThreshold.flag_all || selectedThreshold.special_case) && (
                  <>
                    <Grid item xs={12}>
                      <Divider />
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Special Handling
                      </Typography>
                      {selectedThreshold.flag_all && (
                        <Chip label="Flag All Instances" color="warning" sx={{ mt: 1, mr: 1 }} />
                      )}
                      {selectedThreshold.special_case && (
                        <Chip label={selectedThreshold.special_case} color="info" sx={{ mt: 1 }} />
                      )}
                    </Grid>
                  </>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button
                variant="contained"
                onClick={openEditDialog}
                startIcon={<EditIcon />}
              >
                Edit Threshold
              </Button>
              <Button
                onClick={() => viewHistory(selectedThreshold.id)}
                startIcon={<HistoryIcon />}
              >
                View History
              </Button>
              <Button onClick={() => setDetailDialogOpen(false)}>
                Close
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Edit Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Edit Threshold: {selectedThreshold?.parameter_name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Minimum Value"
                  type="number"
                  value={editMinValue}
                  onChange={(e) => setEditMinValue(e.target.value)}
                  helperText={`Current: ${selectedThreshold?.min_value || 'none'}`}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Maximum Value"
                  type="number"
                  value={editMaxValue}
                  onChange={(e) => setEditMaxValue(e.target.value)}
                  helperText={`Current: ${selectedThreshold?.max_value || 'none'}`}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Reason for Change"
                  multiline
                  rows={3}
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  required
                  placeholder="Explain why this threshold is being changed..."
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={triggerReprocessing}
                      onChange={(e) => setTriggerReprocessing(e.target.checked)}
                    />
                  }
                  label="Reprocess all measurements with new threshold (may take several minutes)"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={submitEdit}
            disabled={!editReason.trim()}
          >
            Update Threshold
          </Button>
        </DialogActions>
      </Dialog>

      {/* History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Threshold Change History
        </DialogTitle>
        <DialogContent dividers>
          {historyRecords.length === 0 ? (
            <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
              No change history found
            </Typography>
          ) : (
            <List>
              {historyRecords.map((record, index) => (
                <React.Fragment key={record.id}>
                  {index > 0 && <Divider />}
                  <ListItem alignItems="flex-start">
                    <ListItemText
                      primary={
                        <>
                          <Typography variant="body2" component="span">
                            Changed from {record.old_min} - {record.old_max} to{' '}
                            <strong>{record.new_min} - {record.new_max}</strong>
                          </Typography>
                          {record.reprocessing_triggered && (
                            <Chip label="Reprocessing Triggered" size="small" color="warning" sx={{ ml: 1 }} />
                          )}
                        </>
                      }
                      secondary={
                        <>
                          <Typography variant="caption" display="block" color="text.secondary">
                            {new Date(record.changed_at).toLocaleString()} by {record.changed_by_email || 'Unknown'}
                          </Typography>
                          {record.reason && (
                            <Typography variant="body2" sx={{ mt: 0.5 }}>
                              Reason: {record.reason}
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Reprocess Confirmation Dialog */}
      <Dialog
        open={reprocessDialogOpen}
        onClose={() => setReprocessDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Reprocess All Measurements?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will re-evaluate all parameter measurements against current thresholds.
            This may take several minutes.
          </Alert>
          <Typography variant="body2">
            Use this when you want to apply current thresholds to all measurements,
            not just new ones. This is useful after making threshold changes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReprocessDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={triggerManualReprocessing}
            color="warning"
          >
            Start Reprocessing
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ThresholdManagement;
