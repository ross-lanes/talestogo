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
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Description as PaperIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface ShotSummary {
  id: number;
  shot_number: number;
  role: string;
  paper_id: number;
  paper_title: string | null;
  context: string | null;
  parameter_count: number;
  phenomenon_count: number;
}

interface ShotDetail {
  id: number;
  shot_number: number;
  role: string;
  context: string | null;
  characteristics: Record<string, any> | null;
  paper_id: number;
  paper_title: string | null;
  parameters: Array<{
    name: string;
    category: string | null;
    value: number | null;
    value_min: number | null;
    value_max: number | null;
    unit: string | null;
    uncertainty: number | null;
    context: string | null;
  }>;
  phenomena: Array<{
    type: string;
    category: string | null;
    description: string | null;
    is_primary_focus: boolean;
  }>;
}

const roleColors: Record<string, 'primary' | 'secondary' | 'default'> = {
  primary: 'primary',
  comparison: 'secondary',
  reference: 'default',
};

const ShotExplorer: React.FC = () => {
  const navigate = useNavigate();
  const [shots, setShots] = useState<ShotSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Detail dialog
  const [selectedShot, setSelectedShot] = useState<ShotDetail[] | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchShots = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();
      if (searchQuery) params.append('shot_number', searchQuery);
      if (roleFilter) params.append('role', roleFilter);
      params.append('limit', '200');

      const response = await fetch(`${API_BASE}/nstxview/shots?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch shots');
      }

      const data = await response.json();
      setShots(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShots();
  }, [roleFilter]);

  const isValidShotNumber = (value: string): boolean => {
    if (!value.trim()) return true; // Empty is valid (shows all)
    const num = parseInt(value, 10);
    return !isNaN(num) && num >= 100000 && num <= 199999;
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidShotNumber(searchQuery)) {
      setError('Shot numbers must be 6 digits starting with 1 (e.g., 141234). Use the NSTXView chat on the dashboard for natural language questions.');
      return;
    }
    setPage(0);
    fetchShots();
  };

  const handleViewShot = async (shotNumber: number) => {
    try {
      setDetailLoading(true);
      setDetailOpen(true);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/shots/${shotNumber}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch shot details');
      }

      const data = await response.json();
      setSelectedShot(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load shot details');
      setDetailOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get unique shot numbers for summary stats
  const uniqueShots = new Set(shots.map(s => s.shot_number)).size;
  const paginatedShots = shots.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Explore Shots
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {uniqueShots} unique shots across {shots.length} mentions
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchShots}
        >
          Refresh
        </Button>
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
              placeholder="Search by shot number (e.g., 141234)..."
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
            <InputLabel>Role</InputLabel>
            <Select
              value={roleFilter}
              label="Role"
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="primary">Primary</MenuItem>
              <MenuItem value="comparison">Comparison</MenuItem>
              <MenuItem value="reference">Reference</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Shots Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Shot Number</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Paper</TableCell>
                <TableCell>Context</TableCell>
                <TableCell align="center">Parameters</TableCell>
                <TableCell align="center">Phenomena</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedShots.map((shot) => (
                <TableRow key={shot.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', fontFamily: 'monospace' }}>
                      {shot.shot_number}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={shot.role}
                      size="small"
                      color={roleColors[shot.role] || 'default'}
                    />
                  </TableCell>
                  <TableCell sx={{ maxWidth: 250 }}>
                    <Typography variant="body2" noWrap title={shot.paper_title || ''}>
                      {shot.paper_title || 'Unknown'}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ maxWidth: 300 }}>
                    <Typography variant="body2" noWrap title={shot.context || ''}>
                      {shot.context || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip label={shot.parameter_count} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell align="center">
                    <Chip label={shot.phenomenon_count} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => handleViewShot(shot.shot_number)}
                      title="View All Data for This Shot"
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedShots.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="textSecondary" sx={{ py: 4 }}>
                      No shots found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={shots.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      )}

      {/* Shot Detail Dialog */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          {detailLoading
            ? 'Loading...'
            : selectedShot && selectedShot.length > 0
            ? `Shot ${selectedShot[0].shot_number} - ${selectedShot.length} paper${selectedShot.length > 1 ? 's' : ''}`
            : 'Shot Details'}
        </DialogTitle>
        <DialogContent>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedShot && selectedShot.length > 0 ? (
            <Box sx={{ mt: 1 }}>
              {selectedShot.map((shot, idx) => (
                <Card key={shot.id} sx={{ mb: 2 }}>
                  <CardContent>
                    {/* Paper Reference */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <PaperIcon color="action" />
                      <Typography variant="subtitle1">
                        {shot.paper_title || 'Unknown Paper'}
                      </Typography>
                      <Chip
                        label={shot.role}
                        size="small"
                        color={roleColors[shot.role] || 'default'}
                      />
                    </Box>

                    {/* Context */}
                    {shot.context && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Context
                        </Typography>
                        <Typography variant="body2">{shot.context}</Typography>
                      </Box>
                    )}

                    {/* Parameters */}
                    {shot.parameters.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 1 }}>
                          Parameters ({shot.parameters.length})
                        </Typography>
                        <Grid container spacing={1}>
                          {shot.parameters.map((param, i) => (
                            <Grid item xs={12} sm={6} md={4} key={i}>
                              <Paper variant="outlined" sx={{ p: 1 }}>
                                <Typography variant="caption" color="textSecondary">
                                  {param.name}
                                </Typography>
                                <Typography variant="body2">
                                  {param.value !== null
                                    ? `${param.value}${param.unit ? ` ${param.unit}` : ''}`
                                    : param.value_min !== null && param.value_max !== null
                                    ? `${param.value_min} - ${param.value_max}${param.unit ? ` ${param.unit}` : ''}`
                                    : '-'}
                                  {param.uncertainty && ` ± ${param.uncertainty}`}
                                </Typography>
                              </Paper>
                            </Grid>
                          ))}
                        </Grid>
                      </Box>
                    )}

                    {/* Phenomena */}
                    {shot.phenomena.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 1 }}>
                          Phenomena ({shot.phenomena.length})
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {shot.phenomena.map((phenom, i) => (
                            <Chip
                              key={i}
                              label={phenom.type}
                              size="small"
                              color={phenom.is_primary_focus ? 'primary' : 'default'}
                              title={phenom.description || ''}
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          ) : (
            <Typography color="textSecondary">No data available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ShotExplorer;
