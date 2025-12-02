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
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  BarChart as ChartIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface ParameterName {
  name: string;
  category: string | null;
  count: number;
}

interface ParameterValue {
  id: number;
  parameter_name: string;
  parameter_category: string | null;
  value: number | null;
  value_min: number | null;
  value_max: number | null;
  unit: string | null;
  uncertainty: number | null;
  shot_number: number | null;
  paper_id: number;
  paper_title: string | null;
}

interface ParameterStatistics {
  parameter_name: string;
  count: number;
  min_value: number | null;
  max_value: number | null;
  avg_value: number | null;
  unit: string | null;
  paper_count: number;
  shot_count: number;
}

const categoryColors: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'info' | 'default'> = {
  plasma: 'primary',
  operational: 'secondary',
  performance: 'success',
  heating: 'warning',
  confinement: 'info',
};

const ParameterAnalysis: React.FC = () => {
  const [parameterNames, setParameterNames] = useState<ParameterName[]>([]);
  const [parameters, setParameters] = useState<ParameterValue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [viewMode, setViewMode] = useState<'names' | 'values'>('names');

  // Statistics dialog
  const [statsOpen, setStatsOpen] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [selectedStats, setSelectedStats] = useState<ParameterStatistics | null>(null);

  const fetchParameterNames = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/parameters/names`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch parameter names');
      }

      const data = await response.json();
      setParameterNames(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchParameters = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();
      if (searchQuery) params.append('name', searchQuery);
      if (categoryFilter) params.append('category', categoryFilter);
      params.append('limit', '200');

      const response = await fetch(`${API_BASE}/nstxview/parameters?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch parameters');
      }

      const data = await response.json();
      setParameters(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'names') {
      fetchParameterNames();
    } else {
      fetchParameters();
    }
  }, [viewMode, categoryFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    if (viewMode === 'values') {
      fetchParameters();
    }
  };

  const handleViewStats = async (parameterName: string) => {
    try {
      setStatsLoading(true);
      setStatsOpen(true);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(
        `${API_BASE}/nstxview/parameters/statistics/${encodeURIComponent(parameterName)}`,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const data = await response.json();
      setSelectedStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
      setStatsOpen(false);
    } finally {
      setStatsLoading(false);
    }
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get unique categories
  const categories = [...new Set(parameterNames.map(p => p.category).filter(Boolean))];

  const filteredNames = parameterNames.filter(p => {
    if (categoryFilter && p.category !== categoryFilter) return false;
    if (searchQuery && !p.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedNames = filteredNames.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const paginatedValues = parameters.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Analyze Parameters
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {viewMode === 'names'
              ? `${parameterNames.length} unique parameter types`
              : `${parameters.length} parameter values`}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>View</InputLabel>
            <Select
              value={viewMode}
              label="View"
              onChange={(e) => setViewMode(e.target.value as 'names' | 'values')}
            >
              <MenuItem value="names">Parameter Types</MenuItem>
              <MenuItem value="values">All Values</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={viewMode === 'names' ? fetchParameterNames : fetchParameters}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <form onSubmit={handleSearch} style={{ flex: 1, minWidth: 200 }}>
            <TextField
              fullWidth
              placeholder="Search by parameter name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              size="small"
            />
          </form>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              label="Category"
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat!}>
                  {cat}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Content */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : viewMode === 'names' ? (
        /* Parameter Names View */
        <Grid container spacing={2}>
          {paginatedNames.map((param) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={param.name}>
              <Card
                sx={{
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 4 },
                }}
                onClick={() => handleViewStats(param.name)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      {param.name.replace(/_/g, ' ')}
                    </Typography>
                    <ChartIcon color="action" fontSize="small" />
                  </Box>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={`${param.count} values`}
                      size="small"
                      variant="outlined"
                    />
                    {param.category && (
                      <Chip
                        label={param.category}
                        size="small"
                        color={categoryColors[param.category] || 'default'}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
          {paginatedNames.length === 0 && (
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                No parameters found
              </Typography>
            </Grid>
          )}
        </Grid>
      ) : (
        /* Parameter Values Table */
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Parameter</TableCell>
                <TableCell>Category</TableCell>
                <TableCell align="right">Value</TableCell>
                <TableCell>Unit</TableCell>
                <TableCell>Shot</TableCell>
                <TableCell>Paper</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedValues.map((param) => (
                <TableRow key={param.id} hover>
                  <TableCell>
                    <Typography variant="body2">
                      {param.parameter_name.replace(/_/g, ' ')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {param.parameter_category && (
                      <Chip
                        label={param.parameter_category}
                        size="small"
                        color={categoryColors[param.parameter_category] || 'default'}
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {param.value !== null
                        ? param.value.toFixed(3)
                        : param.value_min !== null && param.value_max !== null
                        ? `${param.value_min} - ${param.value_max}`
                        : '-'}
                      {param.uncertainty && ` ± ${param.uncertainty}`}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{param.unit || '-'}</Typography>
                  </TableCell>
                  <TableCell>
                    {param.shot_number && (
                      <Chip
                        label={param.shot_number}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace' }}
                      />
                    )}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 200 }}>
                    <Typography variant="body2" noWrap>
                      {param.paper_title || '-'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedValues.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="textSecondary" sx={{ py: 4 }}>
                      No parameter values found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={parameters.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      )}

      {/* Statistics Dialog */}
      <Dialog open={statsOpen} onClose={() => setStatsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {statsLoading
            ? 'Loading...'
            : selectedStats
            ? selectedStats.parameter_name.replace(/_/g, ' ')
            : 'Parameter Statistics'}
        </DialogTitle>
        <DialogContent>
          {statsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedStats ? (
            <Box sx={{ mt: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="caption" color="textSecondary">
                      Total Values
                    </Typography>
                    <Typography variant="h5">{selectedStats.count}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="caption" color="textSecondary">
                      Papers
                    </Typography>
                    <Typography variant="h5">{selectedStats.paper_count}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="caption" color="textSecondary">
                      Shots
                    </Typography>
                    <Typography variant="h5">{selectedStats.shot_count}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="caption" color="textSecondary">
                      Unit
                    </Typography>
                    <Typography variant="h5">{selectedStats.unit || '-'}</Typography>
                  </Paper>
                </Grid>
                {selectedStats.min_value !== null && (
                  <>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          Min
                        </Typography>
                        <Typography variant="h6">
                          {selectedStats.min_value.toFixed(3)}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          Avg
                        </Typography>
                        <Typography variant="h6">
                          {selectedStats.avg_value?.toFixed(3) || '-'}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          Max
                        </Typography>
                        <Typography variant="h6">
                          {selectedStats.max_value?.toFixed(3) || '-'}
                        </Typography>
                      </Paper>
                    </Grid>
                  </>
                )}
              </Grid>
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ParameterAnalysis;
