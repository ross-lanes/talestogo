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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Science as ShotIcon,
  Analytics as ParamIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface PaperSummary {
  id: number;
  title: string | null;
  authors: string[] | null;
  journal: string | null;
  publication_date: string | null;
  doi: string | null;
  status: string;
  shot_count: number;
  parameter_count: number;
  phenomenon_count: number;
}

interface PaperDetail {
  id: number;
  drive_file_id: string;
  original_filename: string;
  subfolder: string | null;
  title: string | null;
  authors: string[] | null;
  journal: string | null;
  publication_date: string | null;
  doi: string | null;
  abstract: string | null;
  key_findings: string[] | null;
  experiment_type: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

const statusColors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  downloading: 'primary',
  extracting_text: 'primary',
  extracting_data: 'primary',
  generating_embeddings: 'primary',
  completed: 'success',
  error: 'error',
};

const PaperBrowser: React.FC = () => {
  const [papers, setPapers] = useState<PaperSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Detail dialog
  const [selectedPaper, setSelectedPaper] = useState<PaperDetail | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchPapers = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      params.append('status', 'completed');
      params.append('limit', '200');

      const response = await fetch(`${API_BASE}/nstxview/papers?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch papers');
      }

      const data = await response.json();
      setPapers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPapers();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchPapers();
  };

  const handleViewPaper = async (paperId: number) => {
    try {
      setDetailLoading(true);
      setDetailOpen(true);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/papers/${paperId}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch paper details');
      }

      const data = await response.json();
      setSelectedPaper(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load paper details');
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

  const paginatedPapers = papers.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Browse Papers
          </Typography>
          <Typography variant="body1" color="textSecondary">
            {papers.length} papers in database
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPapers}
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

      {/* Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <form onSubmit={handleSearch}>
          <TextField
            fullWidth
            placeholder="Search by title, authors, or abstract..."
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
      </Paper>

      {/* Papers Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ width: '100%' }}>
          <Table sx={{ width: '100%', tableLayout: 'fixed' }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: '40%' }}>Summary</TableCell>
                <TableCell sx={{ width: '20%' }}>Authors</TableCell>
                <TableCell sx={{ width: '15%' }}>Journal</TableCell>
                <TableCell align="center" sx={{ width: '12.5%' }}>Shots</TableCell>
                <TableCell align="center" sx={{ width: '12.5%' }}>Parameters</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedPapers.map((paper) => (
                <TableRow key={paper.id} hover>
                  <TableCell sx={{ maxWidth: 350 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleViewPaper(paper.id)}
                        title="View Summary"
                        sx={{ flexShrink: 0 }}
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                      {paper.doi ? (
                        <Typography
                          variant="body2"
                          component="a"
                          href={paper.doi.startsWith('http') ? paper.doi : `https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            color: 'primary.main',
                            textDecoration: 'none',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            '&:hover': { textDecoration: 'underline' },
                          }}
                          title={paper.title || 'Untitled'}
                        >
                          {paper.title || 'Untitled'}
                        </Typography>
                      ) : (
                        <Typography variant="body2" noWrap title={paper.title || 'Untitled'}>
                          {paper.title || 'Untitled'}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ maxWidth: 200 }}>
                    <Typography variant="body2" noWrap>
                      {paper.authors?.slice(0, 2).join(', ')}
                      {paper.authors && paper.authors.length > 2 && ' et al.'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap>
                      {paper.journal || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      icon={<ShotIcon />}
                      label={paper.shot_count}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      icon={<ParamIcon />}
                      label={paper.parameter_count}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                </TableRow>
              ))}
              {paginatedPapers.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography variant="body2" color="textSecondary" sx={{ py: 4 }}>
                      No papers found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={papers.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      )}

      {/* Paper Detail Dialog */}
      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {detailLoading ? (
            'Loading...'
          ) : selectedPaper?.doi ? (
            <Typography
              component="a"
              href={selectedPaper.doi.startsWith('http') ? selectedPaper.doi : `https://doi.org/${selectedPaper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                color: 'primary.main',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
                fontSize: 'inherit',
                fontWeight: 'inherit',
              }}
            >
              {selectedPaper?.title || 'Paper Details'}
              <OpenInNewIcon sx={{ fontSize: 16, ml: 0.5, verticalAlign: 'middle' }} />
            </Typography>
          ) : (
            selectedPaper?.title || 'Paper Details'
          )}
        </DialogTitle>
        <DialogContent>
          {detailLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : selectedPaper ? (
            <Box sx={{ mt: 1 }}>
              {/* Authors */}
              {selectedPaper.authors && selectedPaper.authors.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Authors
                  </Typography>
                  <Typography variant="body2">
                    {selectedPaper.authors.join(', ')}
                  </Typography>
                </Box>
              )}

              {/* Journal & Date */}
              <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
                {selectedPaper.journal && (
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">
                      Journal
                    </Typography>
                    <Typography variant="body2">{selectedPaper.journal}</Typography>
                  </Box>
                )}
                {selectedPaper.publication_date && (
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">
                      Published
                    </Typography>
                    <Typography variant="body2">{selectedPaper.publication_date}</Typography>
                  </Box>
                )}
                {selectedPaper.doi && (
                  <Box>
                    <Typography variant="subtitle2" color="textSecondary">
                      DOI
                    </Typography>
                    <Typography variant="body2">{selectedPaper.doi}</Typography>
                  </Box>
                )}
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Abstract */}
              {selectedPaper.abstract && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Abstract
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {selectedPaper.abstract}
                  </Typography>
                </Box>
              )}

              {/* Key Findings */}
              {selectedPaper.key_findings && selectedPaper.key_findings.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Key Findings
                  </Typography>
                  <List dense>
                    {selectedPaper.key_findings.map((finding, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={finding} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Status & Metadata */}
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Chip
                  label={`Status: ${selectedPaper.status}`}
                  color={statusColors[selectedPaper.status] || 'default'}
                  size="small"
                />
                {selectedPaper.experiment_type && (
                  <Chip
                    label={`Type: ${selectedPaper.experiment_type}`}
                    variant="outlined"
                    size="small"
                  />
                )}
              </Box>

              {selectedPaper.error_message && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {selectedPaper.error_message}
                </Alert>
              )}
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PaperBrowser;
