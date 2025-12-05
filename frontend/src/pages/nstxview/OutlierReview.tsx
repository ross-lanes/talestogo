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
  TablePagination,
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
  Card,
  CardContent,
  Grid,
  Divider,
  Link,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  CheckCircle as ApproveIcon,
  Cancel as DismissIcon,
  Delete as DeleteIcon,
  OpenInNew as OpenIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface OutlierSummary {
  id: number;
  parameter_name: string;
  parameter_category: string | null;
  value: number | null;
  unit: string | null;
  paper_id: number;
  paper_title: string | null;
  paper_doi: string | null;
  page_number: number | null;
  outlier_reason: string | null;
  flagged_at: string | null;
  reviewed: boolean;
  review_action: string | null;
}

interface OutlierDetail {
  id: number;
  parameter_name: string;
  parameter_category: string | null;
  value: number | null;
  value_min: number | null;
  value_max: number | null;
  unit: string | null;
  paper_id: number;
  paper_title: string | null;
  paper_doi: string | null;
  paper_authors: string[] | null;
  page_number: number | null;
  context: string | null;
  outlier_reason: string | null;
  flagged_at: string | null;
  flagged_by_threshold_id: number | null;
  threshold_min: number | null;
  threshold_max: number | null;
  threshold_unit: string | null;
  reviewed: boolean;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_action: string | null;
  review_notes: string | null;
  corrected_value: number | null;
  corrected_unit: string | null;
}

interface OutlierStatistics {
  total_outliers: number;
  unreviewed_outliers: number;
  reviewed_outliers: number;
  by_parameter: Array<{ parameter_name: string; count: number }>;
  by_action: Record<string, number>;
  flagged_today: number;
  flagged_this_week: number;
}

const OutlierReview: React.FC = () => {
  const [outliers, setOutliers] = useState<OutlierSummary[]>([]);
  const [statistics, setStatistics] = useState<OutlierStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [reviewStatusFilter, setReviewStatusFilter] = useState<string>('unreviewed');
  const [selectedOutlier, setSelectedOutlier] = useState<OutlierDetail | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'correct' | 'dismiss' | 'delete'>('dismiss');
  const [reviewNotes, setReviewNotes] = useState('');
  const [correctedValue, setCorrectedValue] = useState('');
  const [correctedUnit, setCorrectedUnit] = useState('');

  useEffect(() => {
    fetchOutliers();
    fetchStatistics();
  }, [reviewStatusFilter]);

  const fetchOutliers = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();

      if (reviewStatusFilter === 'reviewed') {
        params.append('reviewed', 'true');
      } else if (reviewStatusFilter === 'unreviewed') {
        params.append('reviewed', 'false');
      }

      if (searchTerm) {
        params.append('parameter_name', searchTerm);
      }

      params.append('limit', '1000');

      const response = await fetch(`${API_BASE}/nstxview/outliers?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch outliers');
      }

      const data = await response.json();
      setOutliers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/outliers/statistics/summary`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const viewOutlierDetail = async (outlierId: number) => {
    try {
      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/outliers/${outlierId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch outlier details');
      }

      const data = await response.json();
      setSelectedOutlier(data);
      setDetailDialogOpen(true);

      // Pre-fill review form
      setCorrectedValue(data.value?.toString() || '');
      setCorrectedUnit(data.unit || '');
      setReviewNotes('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const submitReview = async () => {
    if (!selectedOutlier) return;

    try {
      const token = localStorage.getItem('tales_access_token');
      const payload: any = {
        action: reviewAction,
        notes: reviewNotes,
      };

      if (reviewAction === 'correct') {
        payload.corrected_value = parseFloat(correctedValue);
        payload.corrected_unit = correctedUnit;
      }

      const response = await fetch(`${API_BASE}/nstxview/outliers/${selectedOutlier.id}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to submit review');
      }

      // Refresh data
      fetchOutliers();
      fetchStatistics();
      setReviewDialogOpen(false);
      setDetailDialogOpen(false);
      setReviewNotes('');

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const formatDOI = (doi: string | null) => {
    if (!doi) return null;
    return doi.startsWith('http') ? doi : `https://doi.org/${doi}`;
  };

  const getReviewActionColor = (action: string | null) => {
    switch (action) {
      case 'correct': return 'success';
      case 'dismiss': return 'default';
      case 'delete': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Outlier Detection & Review
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Review parameter measurements flagged as outside normal NSTX/NSTX-U operating ranges
        </Typography>
      </Box>

      {statistics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h3" color="primary">{statistics.total_outliers}</Typography>
                <Typography variant="body2" color="text.secondary">Total Outliers</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h3" color="warning.main">{statistics.unreviewed_outliers}</Typography>
                <Typography variant="body2" color="text.secondary">Needs Review</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h3" color="success.main">{statistics.reviewed_outliers}</Typography>
                <Typography variant="body2" color="text.secondary">Reviewed</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h3">{statistics.flagged_this_week}</Typography>
                <Typography variant="body2" color="text.secondary">Flagged This Week</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
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
              <InputLabel>Review Status</InputLabel>
              <Select
                value={reviewStatusFilter}
                onChange={(e) => setReviewStatusFilter(e.target.value)}
                label="Review Status"
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="unreviewed">Needs Review</MenuItem>
                <MenuItem value="reviewed">Reviewed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={12} md={5} sx={{ textAlign: 'right' }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchOutliers}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Parameter</TableCell>
              <TableCell>Value</TableCell>
              <TableCell>Paper</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Flagged</TableCell>
              <TableCell>Status</TableCell>
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
            ) : outliers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No outliers found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              outliers
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((outlier) => (
                  <TableRow key={outlier.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {outlier.parameter_name}
                      </Typography>
                      {outlier.parameter_category && (
                        <Typography variant="caption" color="text.secondary">
                          {outlier.parameter_category}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="error">
                        {outlier.value} {outlier.unit}
                      </Typography>
                      {outlier.page_number && (
                        <Typography variant="caption" color="text.secondary">
                          Page {outlier.page_number}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell sx={{ maxWidth: 300 }}>
                      <Typography variant="body2" noWrap>
                        {outlier.paper_title || 'Unknown'}
                      </Typography>
                      {outlier.paper_doi && (
                        <Link
                          href={formatDOI(outlier.paper_doi) || '#'}
                          target="_blank"
                          rel="noopener"
                          variant="caption"
                          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                        >
                          View Paper <OpenIcon sx={{ fontSize: 12 }} />
                        </Link>
                      )}
                    </TableCell>
                    <TableCell sx={{ maxWidth: 350 }}>
                      <Typography variant="caption" color="text.secondary">
                        {outlier.outlier_reason || 'No reason provided'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {outlier.flagged_at && (
                        <Typography variant="caption">
                          {new Date(outlier.flagged_at).toLocaleDateString()}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {outlier.reviewed ? (
                        <Chip
                          label={outlier.review_action || 'reviewed'}
                          color={getReviewActionColor(outlier.review_action)}
                          size="small"
                        />
                      ) : (
                        <Chip
                          icon={<WarningIcon />}
                          label="Needs Review"
                          color="warning"
                          size="small"
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => viewOutlierDetail(outlier.id)}
                        title="View Details"
                      >
                        <ViewIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={outliers.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[25, 50, 100]}
        />
      </TableContainer>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedOutlier && (
          <>
            <DialogTitle>
              Outlier Details: {selectedOutlier.parameter_name}
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Reported Value
                  </Typography>
                  <Typography variant="h6" color="error" gutterBottom>
                    {selectedOutlier.value} {selectedOutlier.unit}
                  </Typography>
                  {(selectedOutlier.value_min || selectedOutlier.value_max) && (
                    <Typography variant="caption" color="text.secondary">
                      Range: {selectedOutlier.value_min} - {selectedOutlier.value_max}
                    </Typography>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Normal Range
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    {selectedOutlier.threshold_min} - {selectedOutlier.threshold_max} {selectedOutlier.threshold_unit}
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Divider />
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Paper
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    {selectedOutlier.paper_title}
                  </Typography>
                  {selectedOutlier.paper_authors && (
                    <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                      Authors: {selectedOutlier.paper_authors.join(', ')}
                    </Typography>
                  )}
                  {selectedOutlier.paper_doi && (
                    <Link
                      href={formatDOI(selectedOutlier.paper_doi) || '#'}
                      target="_blank"
                      rel="noopener"
                      variant="body2"
                    >
                      View Paper (DOI) <OpenIcon sx={{ fontSize: 14 }} />
                    </Link>
                  )}
                  {selectedOutlier.page_number && (
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                      Page {selectedOutlier.page_number}
                    </Typography>
                  )}
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Outlier Reason
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'error.50' }}>
                    <Typography variant="body2">
                      {selectedOutlier.outlier_reason}
                    </Typography>
                  </Paper>
                </Grid>

                {selectedOutlier.context && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Context from Paper
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                        "{selectedOutlier.context}"
                      </Typography>
                    </Paper>
                  </Grid>
                )}

                {selectedOutlier.reviewed && (
                  <>
                    <Grid item xs={12}>
                      <Divider />
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Review Information
                      </Typography>
                      <Chip
                        label={selectedOutlier.review_action || 'reviewed'}
                        color={getReviewActionColor(selectedOutlier.review_action)}
                        sx={{ mt: 1 }}
                      />
                      {selectedOutlier.review_notes && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {selectedOutlier.review_notes}
                        </Typography>
                      )}
                      {selectedOutlier.corrected_value && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Corrected to: {selectedOutlier.corrected_value} {selectedOutlier.corrected_unit}
                        </Typography>
                      )}
                    </Grid>
                  </>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              {!selectedOutlier.reviewed && (
                <Button
                  variant="contained"
                  onClick={() => setReviewDialogOpen(true)}
                  startIcon={<ApproveIcon />}
                >
                  Review Outlier
                </Button>
              )}
              <Button onClick={() => setDetailDialogOpen(false)}>
                Close
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Review Dialog */}
      <Dialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Review Outlier</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Action</InputLabel>
              <Select
                value={reviewAction}
                onChange={(e) => setReviewAction(e.target.value as any)}
                label="Action"
              >
                <MenuItem value="correct">Correct - Update with correct value</MenuItem>
                <MenuItem value="dismiss">Dismiss - False positive, value is correct</MenuItem>
                <MenuItem value="delete">Delete - Mark for removal (admin approval required)</MenuItem>
              </Select>
            </FormControl>

            {reviewAction === 'correct' && (
              <Box sx={{ mb: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Corrected Value"
                      type="number"
                      value={correctedValue}
                      onChange={(e) => setCorrectedValue(e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Corrected Unit"
                      value={correctedUnit}
                      onChange={(e) => setCorrectedUnit(e.target.value)}
                    />
                  </Grid>
                </Grid>
              </Box>
            )}

            <TextField
              fullWidth
              label="Review Notes"
              multiline
              rows={4}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Explain your decision (optional)..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={submitReview}
            disabled={reviewAction === 'correct' && !correctedValue}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OutlierReview;
