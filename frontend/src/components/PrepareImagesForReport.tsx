import { useState } from 'react';
import { Button, Alert, CircularProgress, Box, Typography } from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';
import { api } from '../services/api';
import { captureAndUploadCharts } from '../utils/chartCapture';

/**
 * Component to capture and upload ALL analytics charts to the backend.
 * This prepares images for report/slideshow generation.
 */
export default function PrepareImagesForReport() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleUploadAllCharts = async () => {
    setUploading(true);
    setResult(null);

    try {
      // Define ALL chart container IDs from all analytics pages
      const chartContainerIds = {
        // Brand Mentions page
        'mention_rate': 'mention-rate-chart',
        'brand_mentions_trend': 'brand-mentions-trend-chart',
        'platform_comparison': 'platform-comparison-chart',

        // Positioning Analysis page
        'positioning': 'positioning-chart',
        'positioning_trend': 'positioning-trend-chart',

        // Sentiment Analysis page
        'sentiment': 'sentiment-chart',
        'sentiment_trend': 'sentiment-trend-chart',

        // Share of Voice page
        'share_of_voice': 'share-of-voice-chart',
        'share_of_voice_trend': 'share-of-voice-trend-chart',

        // Descriptor Analysis page
        'descriptor_performance': 'descriptor-performance-chart',

        // Competitor Threats page
        'competitor_threats': 'competitor-threats-chart',
      };

      const result = await captureAndUploadCharts(chartContainerIds, api);
      setResult(result);
    } catch (error: any) {
      setResult({
        success: false,
        message: error.message || 'Failed to upload charts'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ mb: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Prepare Images for Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Click the button below to capture screenshots of all analytics charts and upload them to the server.
        These images will be used in your Word documents and PowerPoint slideshows.
      </Typography>

      <Button
        variant="contained"
        color="primary"
        startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
        onClick={handleUploadAllCharts}
        disabled={uploading}
      >
        {uploading ? 'Uploading Charts...' : 'Upload All Analytics Charts'}
      </Button>

      {result && (
        <Alert severity={result.success ? 'success' : 'error'} sx={{ mt: 2 }}>
          {result.message}
        </Alert>
      )}
    </Box>
  );
}
