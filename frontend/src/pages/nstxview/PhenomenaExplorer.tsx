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
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Star as PrimaryIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface PhenomenonType {
  type: string;
  category: string | null;
  count: number;
}

interface PhenomenonSummary {
  id: number;
  phenomenon_type: string;
  phenomenon_category: string | null;
  description: string | null;
  is_primary_focus: boolean;
  paper_id: number;
  paper_title: string | null;
  shot_number: number | null;
}

const categoryColors: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  instability: 'error',
  confinement: 'success',
  heating: 'warning',
  transport: 'info',
  mhd: 'primary',
  disruption: 'error',
  divertor: 'secondary',
};

const PhenomenaExplorer: React.FC = () => {
  const [phenomenaTypes, setPhenomenaTypes] = useState<PhenomenonType[]>([]);
  const [phenomena, setPhenomena] = useState<PhenomenonSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [primaryOnly, setPrimaryOnly] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [viewMode, setViewMode] = useState<'types' | 'all'>('types');

  const fetchPhenomenaTypes = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/phenomena/types`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch phenomena types');
      }

      const data = await response.json();
      setPhenomenaTypes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchPhenomena = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();
      if (searchQuery) params.append('type', searchQuery);
      if (categoryFilter) params.append('category', categoryFilter);
      if (primaryOnly) params.append('primary_only', 'true');
      params.append('limit', '200');

      const response = await fetch(`${API_BASE}/nstxview/phenomena?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch phenomena');
      }

      const data = await response.json();
      setPhenomena(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'types') {
      fetchPhenomenaTypes();
    } else {
      fetchPhenomena();
    }
  }, [viewMode, categoryFilter, primaryOnly]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    if (viewMode === 'all') {
      fetchPhenomena();
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
  const categories = [...new Set(phenomenaTypes.map(p => p.category).filter(Boolean))];

  const filteredTypes = phenomenaTypes.filter(p => {
    if (categoryFilter && p.category !== categoryFilter) return false;
    if (searchQuery && !p.type.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const paginatedTypes = filteredTypes.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  const paginatedPhenomena = phenomena.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Phenomena
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {viewMode === 'types'
              ? `${phenomenaTypes.length} phenomenon types observed`
              : `${phenomena.length} phenomenon occurrences`}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>View</InputLabel>
            <Select
              value={viewMode}
              label="View"
              onChange={(e) => setViewMode(e.target.value as 'types' | 'all')}
            >
              <MenuItem value="types">By Type</MenuItem>
              <MenuItem value="all">All Occurrences</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={viewMode === 'types' ? fetchPhenomenaTypes : fetchPhenomena}
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
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <form onSubmit={handleSearch} style={{ flex: 1, minWidth: 200 }}>
            <TextField
              fullWidth
              placeholder="Search by phenomenon type..."
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
          {viewMode === 'all' && (
            <FormControlLabel
              control={
                <Switch
                  checked={primaryOnly}
                  onChange={(e) => setPrimaryOnly(e.target.checked)}
                />
              }
              label="Primary Focus Only"
            />
          )}
        </Box>
      </Paper>

      {/* Content */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : viewMode === 'types' ? (
        /* Phenomena Types View */
        <Grid container spacing={2}>
          {paginatedTypes.map((phenom) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={phenom.type}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {phenom.type.replace(/_/g, ' ')}
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={`${phenom.count} occurrences`}
                      size="small"
                      variant="outlined"
                    />
                    {phenom.category && (
                      <Chip
                        label={phenom.category}
                        size="small"
                        color={categoryColors[phenom.category] || 'default'}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
          {paginatedTypes.length === 0 && (
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 4 }}>
                No phenomena found
              </Typography>
            </Grid>
          )}
        </Grid>
      ) : (
        /* All Phenomena Table */
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Phenomenon</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="center">Primary</TableCell>
                <TableCell>Shot</TableCell>
                <TableCell>Paper</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedPhenomena.map((phenom) => (
                <TableRow key={phenom.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {phenom.phenomenon_type.replace(/_/g, ' ')}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {phenom.phenomenon_category && (
                      <Chip
                        label={phenom.phenomenon_category}
                        size="small"
                        color={categoryColors[phenom.phenomenon_category] || 'default'}
                      />
                    )}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 250 }}>
                    <Typography variant="body2" noWrap title={phenom.description || ''}>
                      {phenom.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    {phenom.is_primary_focus && (
                      <PrimaryIcon color="primary" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    {phenom.shot_number && (
                      <Chip
                        label={phenom.shot_number}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace' }}
                      />
                    )}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 200 }}>
                    <Typography variant="body2" noWrap>
                      {phenom.paper_title || '-'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
              {paginatedPhenomena.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="textSecondary" sx={{ py: 4 }}>
                      No phenomena found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={phenomena.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      )}
    </Box>
  );
};

export default PhenomenaExplorer;
