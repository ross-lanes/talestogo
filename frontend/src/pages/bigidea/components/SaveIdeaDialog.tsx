import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Chip,
  Box,
  Typography,
} from '@mui/material';
import type { Idea } from '../../../types/bigidea';

interface SaveIdeaDialogProps {
  open: boolean;
  idea: Idea | null;
  onClose: () => void;
  onSave: (idea: Idea, projectName: string, notes: string, tags: string[]) => void;
  defaultProjectName?: string;
}

export default function SaveIdeaDialog({
  open,
  idea,
  onClose,
  onSave,
  defaultProjectName = '',
}: SaveIdeaDialogProps) {
  const [projectName, setProjectName] = useState(defaultProjectName);
  const [notes, setNotes] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleSave = () => {
    if (!projectName.trim() || !idea) {
      return;
    }
    onSave(idea, projectName.trim(), notes.trim(), tags);
    // Reset form
    setProjectName(defaultProjectName);
    setNotes('');
    setTags([]);
    setTagInput('');
    onClose();
  };

  const handleClose = () => {
    setProjectName(defaultProjectName);
    setNotes('');
    setTags([]);
    setTagInput('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Save Idea to Library</DialogTitle>
      <DialogContent>
        {idea && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              {idea.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {idea.description.substring(0, 100)}...
            </Typography>
          </Box>
        )}

        <TextField
          fullWidth
          label="Project Name"
          required
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="e.g., 'Q3 Marketing Plan'"
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Notes"
          multiline
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add any additional thoughts or context..."
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Add Tags"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a tag and press Enter"
          helperText="Press Enter to add a tag"
          sx={{ mb: 1 }}
        />

        {tags.length > 0 && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {tags.map((tag) => (
              <Chip
                key={tag}
                label={tag}
                size="small"
                onDelete={() => handleRemoveTag(tag)}
              />
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={!projectName.trim()}
        >
          Save Idea
        </Button>
      </DialogActions>
    </Dialog>
  );
}
