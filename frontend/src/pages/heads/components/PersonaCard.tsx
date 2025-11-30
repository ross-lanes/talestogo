import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  TextField,
  Button,
  Divider,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PrintIcon from '@mui/icons-material/Print';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import ImageIcon from '@mui/icons-material/Image';
import PersonIcon from '@mui/icons-material/Person';
import WorkIcon from '@mui/icons-material/Work';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import BusinessIcon from '@mui/icons-material/Business';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import CampaignIcon from '@mui/icons-material/Campaign';
import type { Persona } from '../../../types/heads';
import { ExportFormat } from '../../../types/heads';

interface PersonaCardProps {
  persona: Persona;
  onExport: (persona: Persona, format: ExportFormat) => void;
  onUpdate: (persona: Persona) => void;
  onGenerateImage?: (persona: Persona, styleKeywords?: string) => Promise<void>;
  isGeneratingImage?: boolean;
}

const PersonaCard: React.FC<PersonaCardProps> = ({
  persona,
  onExport,
  onUpdate,
  onGenerateImage,
  isGeneratingImage,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isEditingGoals, setIsEditingGoals] = useState(false);
  const [editedGoals, setEditedGoals] = useState<string[]>(persona.goals);
  const [showImageDialog, setShowImageDialog] = useState(false);
  const [imageStyleKeywords, setImageStyleKeywords] = useState('');

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExport = (format: ExportFormat) => {
    onExport(persona, format);
    handleMenuClose();
  };

  const handlePrint = () => {
    window.print();
    handleMenuClose();
  };

  const handleSaveGoals = () => {
    onUpdate({ ...persona, goals: editedGoals });
    setIsEditingGoals(false);
  };

  const handleCancelEdit = () => {
    setEditedGoals(persona.goals);
    setIsEditingGoals(false);
  };

  const handleGenerateImage = async () => {
    if (onGenerateImage) {
      await onGenerateImage(persona, imageStyleKeywords);
      setShowImageDialog(false);
      setImageStyleKeywords('');
    }
  };

  return (
    <Card
      elevation={0}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        overflow: 'visible',
        '@media print': {
          breakInside: 'avoid',
          pageBreakInside: 'avoid',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          bgcolor: 'grey.50',
          borderBottom: '1px solid',
          borderColor: 'divider',
          p: 3,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'flex', gap: 3, flex: 1 }}>
            {/* Avatar */}
            <Box sx={{ position: 'relative' }}>
              <Avatar
                src={persona.avatarBase64}
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                }}
              >
                {persona.name.charAt(0)}
              </Avatar>
              {onGenerateImage && (
                <Tooltip title="Generate AI Avatar">
                  <IconButton
                    size="small"
                    onClick={() => setShowImageDialog(true)}
                    disabled={isGeneratingImage}
                    sx={{
                      position: 'absolute',
                      bottom: -4,
                      right: -4,
                      bgcolor: 'background.paper',
                      border: '1px solid',
                      borderColor: 'divider',
                      '&:hover': { bgcolor: 'grey.100' },
                    }}
                  >
                    {isGeneratingImage ? (
                      <CircularProgress size={16} />
                    ) : (
                      <ImageIcon fontSize="small" />
                    )}
                  </IconButton>
                </Tooltip>
              )}
            </Box>

            {/* Name & Details */}
            <Box sx={{ flex: 1 }}>
              <Chip
                label={persona.generalizationTitle}
                size="small"
                sx={{
                  bgcolor: 'primary.50',
                  color: 'primary.main',
                  fontWeight: 600,
                  mb: 1,
                }}
              />
              <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
                {persona.name}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, color: 'text.secondary' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <PersonIcon fontSize="small" />
                  <Typography variant="body2">{persona.age}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <WorkIcon fontSize="small" />
                  <Typography variant="body2">{persona.occupation}</Typography>
                </Box>
                {persona.location && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <LocationOnIcon fontSize="small" />
                    <Typography variant="body2">{persona.location}</Typography>
                  </Box>
                )}
                {persona.workplace && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <BusinessIcon fontSize="small" />
                    <Typography variant="body2">{persona.workplace}</Typography>
                  </Box>
                )}
              </Box>
            </Box>
          </Box>

          {/* Menu Button */}
          <IconButton onClick={handleMenuOpen} className="no-print">
            <MoreVertIcon />
          </IconButton>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
            <MenuItem onClick={() => handleExport(ExportFormat.JSON)}>
              <ListItemIcon>
                <FileDownloadIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Export as JSON</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport(ExportFormat.TXT)}>
              <ListItemIcon>
                <FileDownloadIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Export as Text</ListItemText>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handlePrint}>
              <ListItemIcon>
                <PrintIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Print</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      <CardContent sx={{ p: 3 }}>
        {/* Profile Quote */}
        <Typography
          variant="body1"
          sx={{
            fontStyle: 'italic',
            color: 'text.secondary',
            mb: 3,
            pl: 2,
            borderLeft: '3px solid',
            borderColor: 'primary.light',
          }}
        >
          "{persona.profile}"
        </Typography>

        {/* Technology Profile */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                p: 2,
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                TECHNOLOGY ABILITY
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {persona.technologyAbility || 'N/A'}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                p: 2,
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                TECHNOLOGY COMFORTABILITY
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {persona.technologyComfortability || 'N/A'}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Goals & Frustrations */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Goals */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                <Typography variant="subtitle2" color="success.main" fontWeight={600}>
                  GOALS & MOTIVATIONS
                </Typography>
              </Box>
              {!isEditingGoals && (
                <IconButton
                  size="small"
                  onClick={() => setIsEditingGoals(true)}
                  className="no-print"
                >
                  <EditIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
            {isEditingGoals ? (
              <Box>
                {editedGoals.map((goal, idx) => (
                  <TextField
                    key={idx}
                    fullWidth
                    size="small"
                    value={goal}
                    onChange={(e) => {
                      const newGoals = [...editedGoals];
                      newGoals[idx] = e.target.value;
                      setEditedGoals(newGoals);
                    }}
                    sx={{ mb: 1 }}
                  />
                ))}
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveGoals}
                  >
                    Save
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={handleCancelEdit}
                  >
                    Cancel
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {persona.goals.map((goal, idx) => (
                  <Typography component="li" variant="body2" key={idx} sx={{ mb: 0.5 }}>
                    {goal}
                  </Typography>
                ))}
              </Box>
            )}
          </Grid>

          {/* Frustrations */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <ErrorIcon sx={{ color: 'error.main', fontSize: 20 }} />
              <Typography variant="subtitle2" color="error.main" fontWeight={600}>
                FRUSTRATIONS & PAIN POINTS
              </Typography>
            </Box>
            <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
              {persona.frustrations.map((frustration, idx) => (
                <Typography component="li" variant="body2" key={idx} sx={{ mb: 0.5 }}>
                  {frustration}
                </Typography>
              ))}
            </Box>
          </Grid>
        </Grid>

        {/* Brand View & Marketing Strategy */}
        <Grid container spacing={3}>
          {/* Brand Perception */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <LightbulbIcon sx={{ color: 'info.main', fontSize: 20 }} />
              <Typography variant="subtitle2" color="info.main" fontWeight={600}>
                BRAND PERCEPTION
              </Typography>
            </Box>
            <Box
              sx={{
                p: 2,
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="body2">{persona.brandView}</Typography>
            </Box>
          </Grid>

          {/* Marketing Strategy */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CampaignIcon sx={{ color: 'secondary.main', fontSize: 20 }} />
              <Typography variant="subtitle2" color="secondary.main" fontWeight={600}>
                MARKETING STRATEGY
              </Typography>
            </Box>
            <Box
              sx={{
                p: 2,
                bgcolor: 'secondary.50',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'secondary.200',
              }}
            >
              <Typography variant="body2">{persona.marketingStrategy}</Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>

      {/* Image Generation Dialog */}
      {showImageDialog && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1300,
          }}
          onClick={() => setShowImageDialog(false)}
        >
          <Card
            sx={{ p: 3, maxWidth: 400, width: '100%', mx: 2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Generate AI Avatar
            </Typography>
            <TextField
              fullWidth
              label="Style Keywords"
              placeholder="e.g. Photorealistic, professional lighting"
              value={imageStyleKeywords}
              onChange={(e) => setImageStyleKeywords(e.target.value)}
              helperText="Optional - describe the visual style"
              sx={{ mb: 3 }}
            />
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={() => setShowImageDialog(false)}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleGenerateImage}
                disabled={isGeneratingImage}
                startIcon={isGeneratingImage ? <CircularProgress size={16} /> : <ImageIcon />}
              >
                Generate
              </Button>
            </Box>
          </Card>
        </Box>
      )}
    </Card>
  );
};

export default PersonaCard;
