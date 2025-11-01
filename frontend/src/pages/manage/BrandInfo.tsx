import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import { Download, Share } from '@mui/icons-material';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';
import ShareBrandDialog from '../../components/ShareBrandDialog';

interface BrandInfo {
  id: number;
  user_id: number;
  brand_name: string;
  website_url: string | null;
  industry: string | null;
  description: string | null;
  strategic_messages: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const BrandInfo: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const isNewBrand = searchParams.get('new') === 'true';

  // Form state
  const [brandId, setBrandId] = useState<number | null>(null);
  const [brandName, setBrandName] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [industry, setIndustry] = useState('');
  const [description, setDescription] = useState('');
  const [strategicMessages, setStrategicMessages] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [brandExists, setBrandExists] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  // Fetch existing brand info on mount (unless creating new brand)
  // Re-run when location changes (including query params)
  useEffect(() => {
    if (!isNewBrand) {
      fetchBrandInfo();
    } else {
      // For new brand, clear form and skip fetching
      setBrandId(null);
      setBrandName('');
      setWebsiteUrl('');
      setIndustry('');
      setDescription('');
      setStrategicMessages('');
      setFetching(false);
      setBrandExists(false);
      setError('');
      setSuccess('');
    }
  }, [location.search]);

  const fetchBrandInfo = async () => {
    setFetching(true);
    setError('');
    try {
      const response = await api.get<BrandInfo>('/brand-info/');
      const data = response.data;
      setBrandId(data.id);
      setBrandName(data.brand_name || '');
      setWebsiteUrl(data.website_url || '');
      setIndustry(data.industry || '');
      setDescription(data.description || '');
      setStrategicMessages(data.strategic_messages || '');
      setBrandExists(true);
    } catch (err: any) {
      // 404 is expected if brand info doesn't exist yet
      if (err.response?.status === 404) {
        setBrandExists(false);
        setBrandId(null);
      } else {
        console.error('Error fetching brand info:', err);
        setError(err.response?.data?.detail || 'Failed to load brand info');
      }
    } finally {
      setFetching(false);
    }
  };

  const handleDownloadCSV = () => {
    if (!brandExists) return;

    const csvHeaders = ['Field', 'Value'];
    const csvRows = [
      ['Brand Name', `"${brandName.replace(/"/g, '""')}"`],
      ['Website URL', `"${websiteUrl.replace(/"/g, '""')}"`],
      ['Industry', `"${industry.replace(/"/g, '""')}"`],
      ['Description', `"${description.replace(/"/g, '""')}"`],
      ['Strategic Messages', `"${strategicMessages.replace(/"/g, '""')}"`]
    ];

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}_${day}_${year}`;

    link.download = `BrandInfo_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    // Validation
    if (!brandName.trim()) {
      setError('Brand name is required');
      setLoading(false);
      return;
    }
    if (!websiteUrl.trim()) {
      setError('Website URL is required');
      setLoading(false);
      return;
    }
    if (!industry.trim()) {
      setError('Industry is required');
      setLoading(false);
      return;
    }
    if (!description.trim()) {
      setError('Brand description is required');
      setLoading(false);
      return;
    }

    try {
      const brandData = {
        brand_name: brandName,
        website_url: websiteUrl || null,
        industry: industry || null,
        description: description || null,
        strategic_messages: strategicMessages || null,
      };

      if (brandExists && brandId) {
        // Update existing brand using new endpoint
        const response = await api.put<BrandInfo>(`/brands/${brandId}`, brandData);
        setBrandId(response.data.id);
        setSuccess('Brand info updated successfully!');
      } else {
        // Create new brand using new endpoint
        const response = await api.post<BrandInfo>('/brands/', brandData);
        setBrandId(response.data.id);
        setBrandExists(true);
        setSuccess('Brand info created successfully!');
      }

      // Show the dialog after successful save
      setShowDialog(true);
    } catch (err: any) {
      console.error('Brand info save error:', err);
      setError(err.response?.data?.detail || 'Failed to save brand info');
    } finally {
      setLoading(false);
    }
  };

  const handleAiGenerate = async () => {
    setAiGenerating(true);
    setShowDialog(false);

    try {
      // Call the backend API to generate queries, descriptors, and competitors
      await api.post('/brand-info/generate');

      // Navigate to queries page
      navigate('/manage/queries');
    } catch (err: any) {
      console.error('AI generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate content. Please try again.');
      setAiGenerating(false);
    }
  };

  const handleManualEntry = () => {
    setShowDialog(false);
    navigate('/manage/queries');
  };


  if (fetching || aiGenerating) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
          {aiGenerating && (
            <Typography variant="h6" sx={{ mt: 2 }}>
              Generating queries, descriptors, and competitors...
            </Typography>
          )}
          {aiGenerating && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              This may take a few minutes. Please wait...
            </Typography>
          )}
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1} mb={2}>
        <Typography
          variant="body1"
          sx={{
            color: '#80A1D4',
            fontWeight: 'bold',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
        >
          Brand Info
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#75C9C8',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/queries')}
        >
          Queries
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#44809C',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/descriptors')}
        >
          Descriptors
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#9FA8DA',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/competitors')}
        >
          Competitors
        </Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h2">
          {isNewBrand ? 'Add New Brand' : 'Customize Branding'}
        </Typography>
        {brandExists && !isNewBrand && (
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<Share />}
              onClick={() => setShareDialogOpen(true)}
              size="small"
            >
              Share Brand
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadCSV}
              size="small"
            >
              Download as CSV
            </Button>
          </Box>
        )}
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        {isNewBrand
          ? 'Enter information about your new brand. This information will be used to customize analysis and query generation.'
          : 'Configure information about your brand to customize analysis and query generation. This information will be used to tailor AI prompts for your specific brand.'
        }
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Brand Information
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Brand Name"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="e.g., Princeton Plasma Physics Laboratory"
              helperText="The name of your brand or organization"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Website URL"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="e.g., https://www.pppl.gov"
              helperText="Your brand's website"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Industry"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="e.g., Fusion Energy Research, Technology, Healthcare"
              helperText="The industry or sector your brand operates in"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              multiline
              rows={6}
              label="Brand Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide a detailed description of your brand, its mission, key achievements, and unique characteristics..."
              helperText="A comprehensive description that will help AI understand your brand context for analysis and query generation"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Strategic Messages"
              value={strategicMessages}
              onChange={(e) => setStrategicMessages(e.target.value)}
              placeholder="List key messages and narratives you want people to say about your brand..."
              helperText="Things you would like people to say about your brand (e.g., 'Leading innovator in clean energy', 'Pioneering breakthrough research')"
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={loading}
              size="large"
            >
              {loading ? <CircularProgress size={24} /> : brandExists ? 'Update Brand Info' : 'Save Brand Info'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ mt: 3 }}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>How is this used?</strong> Your brand information is used to:
          </Typography>
          <ul style={{ marginTop: '8px', marginBottom: 0 }}>
            <li>Customize AI analysis prompts to look for your brand specifically</li>
            <li>Generate relevant queries tailored to your brand and industry</li>
            <li>Provide context for better sentiment analysis and competitive positioning</li>
          </ul>
        </Alert>
      </Box>

      <Dialog open={showDialog} onClose={() => setShowDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Next Steps</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Would you like to send the information you've just provided to an AI to generate the questions (queries),
            ideal language (descriptors), and competitor information for you?
          </DialogContentText>
          <DialogContentText sx={{ mt: 2, fontStyle: 'italic', color: 'text.secondary' }}>
            (You can always change this information later.)
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={handleManualEntry}
            variant="outlined"
            size="large"
          >
            I'll Write My Own
          </Button>
          <Button
            onClick={handleAiGenerate}
            variant="contained"
            autoFocus
            size="large"
          >
            Generate with AI
          </Button>
        </DialogActions>
      </Dialog>

      {brandId && brandName && (
        <ShareBrandDialog
          open={shareDialogOpen}
          onClose={() => setShareDialogOpen(false)}
          brandId={brandId}
          brandName={brandName}
        />
      )}
    </Container>
  );
};

export default BrandInfo;
