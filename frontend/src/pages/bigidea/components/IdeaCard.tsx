import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Collapse,
  TextField,
  Button,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import BookmarkAddIcon from '@mui/icons-material/BookmarkAdd';
import type { Idea } from '../../../types/bigidea';
import { IdeaScale } from '../../../types/bigidea';

interface IdeaCardProps {
  idea: Idea;
  onUpdate: (updatedIdea: Idea) => void;
  onExpand: () => Promise<void>;
  onSave: () => void;
  isExpanding: boolean;
}

const SCALE_COLORS: Record<string, { bg: string; text: string }> = {
  [IdeaScale.SAFE]: { bg: '#e8f5e9', text: '#2e7d32' },
  [IdeaScale.AMBITIOUS]: { bg: '#e3f2fd', text: '#1565c0' },
  [IdeaScale.VERY_AMBITIOUS]: { bg: '#fff3e0', text: '#e65100' },
  [IdeaScale.INCREDIBLY_AMBITIOUS]: { bg: '#ffebee', text: '#c62828' },
};

export default function IdeaCard({
  idea,
  onUpdate,
  onExpand,
  onSave,
  isExpanding,
}: IdeaCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedIdea, setEditedIdea] = useState(idea);
  const [copied, setCopied] = useState(false);

  const scaleColor = SCALE_COLORS[idea.scale] || { bg: '#f5f5f5', text: '#616161' };

  const handleCopy = async () => {
    const text = `${idea.title}\n\n${idea.description}\n\nArea: ${idea.area}\nScale: ${idea.scale}\n\nRationale:\n${idea.rationale}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    onUpdate(editedIdea);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedIdea(idea);
    setIsEditing(false);
  };

  return (
    <Card
      elevation={0}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
        transition: 'all 0.2s',
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            {isEditing ? (
              <TextField
                fullWidth
                value={editedIdea.title}
                onChange={(e) => setEditedIdea({ ...editedIdea, title: e.target.value })}
                variant="outlined"
                size="small"
                sx={{ mb: 1 }}
              />
            ) : (
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {idea.title}
              </Typography>
            )}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={idea.area}
                size="small"
                variant="outlined"
              />
              <Chip
                label={idea.scale}
                size="small"
                sx={{
                  bgcolor: scaleColor.bg,
                  color: scaleColor.text,
                  fontWeight: 500,
                }}
              />
            </Box>
          </Box>

          {/* Action buttons */}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {isEditing ? (
              <>
                <Tooltip title="Save changes">
                  <IconButton size="small" onClick={handleSaveEdit} color="primary">
                    <SaveIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Cancel">
                  <IconButton size="small" onClick={handleCancelEdit}>
                    <CancelIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            ) : (
              <>
                <Tooltip title="Edit idea">
                  <IconButton size="small" onClick={() => setIsEditing(true)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
                  <IconButton size="small" onClick={handleCopy}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Expand with AI">
                  <IconButton
                    size="small"
                    onClick={onExpand}
                    disabled={isExpanding}
                    color="secondary"
                  >
                    {isExpanding ? (
                      <CircularProgress size={18} />
                    ) : (
                      <AutoFixHighIcon fontSize="small" />
                    )}
                  </IconButton>
                </Tooltip>
                <Tooltip title="Save to library">
                  <IconButton size="small" onClick={onSave} color="primary">
                    <BookmarkAddIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>
        </Box>

        {/* Description */}
        {isEditing ? (
          <TextField
            fullWidth
            multiline
            rows={4}
            value={editedIdea.description}
            onChange={(e) => setEditedIdea({ ...editedIdea, description: e.target.value })}
            variant="outlined"
            size="small"
            sx={{ mb: 2 }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
            {idea.description}
          </Typography>
        )}

        {/* Expand/Collapse Rationale */}
        <Button
          size="small"
          onClick={() => setExpanded(!expanded)}
          endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{ textTransform: 'none' }}
        >
          {expanded ? 'Hide Rationale' : 'Show Rationale'}
        </Button>

        <Collapse in={expanded}>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Rationale
            </Typography>
            {isEditing ? (
              <TextField
                fullWidth
                multiline
                rows={3}
                value={editedIdea.rationale}
                onChange={(e) => setEditedIdea({ ...editedIdea, rationale: e.target.value })}
                variant="outlined"
                size="small"
              />
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                {idea.rationale}
              </Typography>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}
