import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DownloadIcon from '@mui/icons-material/Download';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import { saveAs } from 'file-saver';
import type { ClientProject, SavedIdea, BigIdeaFormData } from '../../types/bigidea';
import { IdeaScale } from '../../types/bigidea';
import { getProjects, saveProjects } from '../../services/bigideaService';

const SCALE_COLORS: Record<string, { bg: string; text: string }> = {
  [IdeaScale.SAFE]: { bg: '#e8f5e9', text: '#2e7d32' },
  [IdeaScale.AMBITIOUS]: { bg: '#e3f2fd', text: '#1565c0' },
  [IdeaScale.VERY_AMBITIOUS]: { bg: '#fff3e0', text: '#e65100' },
  [IdeaScale.INCREDIBLY_AMBITIOUS]: { bg: '#ffebee', text: '#c62828' },
};

export default function IdeasLibrary() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ClientProject[]>([]);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // View Dialog
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedIdea, setSelectedIdea] = useState<SavedIdea | null>(null);

  // Delete Confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ideaToDelete, setIdeaToDelete] = useState<{ projectId: string; ideaId: string } | null>(null);

  useEffect(() => {
    setProjects(getProjects());
  }, []);

  const totalIdeas = projects.reduce((sum, p) => sum + p.ideas.length, 0);

  const handleViewIdea = (idea: SavedIdea) => {
    setSelectedIdea(idea);
    setViewDialogOpen(true);
  };

  const handleDownloadIdea = async (idea: SavedIdea) => {
    const children: Paragraph[] = [];

    // Title
    children.push(
      new Paragraph({
        text: idea.title,
        heading: HeadingLevel.TITLE,
        spacing: { after: 400 },
      })
    );

    // Saved date
    children.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `Saved: ${new Date(idea.savedAt).toLocaleDateString()}`,
            italics: true,
            color: '666666',
          }),
        ],
        spacing: { after: 400 },
      })
    );

    // Area and Scale
    children.push(
      new Paragraph({
        children: [
          new TextRun({ text: 'Area: ', bold: true }),
          new TextRun({ text: idea.area }),
          new TextRun({ text: '  |  ' }),
          new TextRun({ text: 'Scale: ', bold: true }),
          new TextRun({ text: idea.scale }),
        ],
        spacing: { after: 200 },
      })
    );

    // Description
    children.push(
      new Paragraph({
        text: 'Description',
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 300, after: 100 },
      })
    );
    children.push(
      new Paragraph({
        text: idea.description,
        spacing: { after: 200 },
      })
    );

    // Rationale
    children.push(
      new Paragraph({
        text: 'Rationale',
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 300, after: 100 },
      })
    );
    children.push(
      new Paragraph({
        text: idea.rationale,
        spacing: { after: 200 },
      })
    );

    // Notes (if any)
    if (idea.notes) {
      children.push(
        new Paragraph({
          text: 'Notes',
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 300, after: 100 },
        })
      );
      children.push(
        new Paragraph({
          text: idea.notes,
          spacing: { after: 200 },
        })
      );
    }

    // Tags (if any)
    if (idea.tags && idea.tags.length > 0) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: 'Tags: ', bold: true }),
            new TextRun({ text: idea.tags.join(', ') }),
          ],
          spacing: { before: 200, after: 200 },
        })
      );
    }

    const doc = new Document({
      sections: [
        {
          properties: {},
          children,
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `${idea.title.replace(/\s+/g, '_')}_idea.docx`);
  };

  const handleEditIdea = (idea: SavedIdea) => {
    if (idea.formData) {
      // Store the form data in session storage for the Dashboard to pick up
      sessionStorage.setItem('bigidea_edit_formdata', JSON.stringify(idea.formData));
      navigate('/bigidea');
    } else {
      setErrorMessage('This idea does not have saved form data for editing.');
      setTimeout(() => setErrorMessage(null), 3000);
    }
  };

  const handleConfirmDelete = (projectId: string, ideaId: string) => {
    setIdeaToDelete({ projectId, ideaId });
    setDeleteDialogOpen(true);
  };

  const handleDeleteIdea = () => {
    if (!ideaToDelete) return;

    const updatedProjects = projects
      .map((project) => {
        if (project.id === ideaToDelete.projectId) {
          return {
            ...project,
            ideas: project.ideas.filter((idea) => idea.id !== ideaToDelete.ideaId),
          };
        }
        return project;
      })
      .filter((project) => project.ideas.length > 0); // Remove empty projects

    setProjects(updatedProjects);
    saveProjects(updatedProjects);
    setSuccessMessage('Idea deleted successfully');
    setTimeout(() => setSuccessMessage(null), 3000);
    setDeleteDialogOpen(false);
    setIdeaToDelete(null);
  };

  const formatFormData = (formData: BigIdeaFormData): string => {
    const parts: string[] = [];
    if (formData.clientName) parts.push(`Client: ${formData.clientName}`);
    if (formData.targetAudience) parts.push(`Audience: ${formData.targetAudience}`);
    if (formData.campaignGoal) parts.push(`Goal: ${formData.campaignGoal}`);
    if (formData.budget) parts.push(`Budget: ${formData.budget}`);
    return parts.join(' | ');
  };

  // Empty state
  if (totalIdeas === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Ideas Library
          </Typography>
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 10,
            px: 4,
            bgcolor: 'grey.50',
            borderRadius: 2,
            border: '1px dashed',
            borderColor: 'grey.300',
          }}
        >
          <FolderOpenIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            The library is currently empty.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            When you save an idea, it will appear here.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => navigate('/bigidea')}
          >
            Generate Ideas
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Ideas Library
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {totalIdeas} saved idea{totalIdeas !== 1 ? 's' : ''} across {projects.length} project{projects.length !== 1 ? 's' : ''}
        </Typography>
      </Box>

      {/* Messages */}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setErrorMessage(null)}>
          {errorMessage}
        </Alert>
      )}

      {/* Projects */}
      {projects.map((project) => (
        <Accordion key={project.id} defaultExpanded sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" fontWeight={600}>
              {project.name}
            </Typography>
            <Chip
              label={`${project.ideas.length} idea${project.ideas.length !== 1 ? 's' : ''}`}
              size="small"
              sx={{ ml: 2 }}
            />
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {project.ideas.map((idea) => {
                const scaleColor = SCALE_COLORS[idea.scale] || { bg: '#f5f5f5', text: '#616161' };
                return (
                  <Card
                    key={idea.id}
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
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" fontWeight={600} gutterBottom>
                            {idea.title}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                            <Chip label={idea.area} size="small" variant="outlined" />
                            <Chip
                              label={idea.scale}
                              size="small"
                              sx={{
                                bgcolor: scaleColor.bg,
                                color: scaleColor.text,
                                fontWeight: 500,
                              }}
                            />
                            {idea.tags?.map((tag) => (
                              <Chip key={tag} label={tag} size="small" color="primary" variant="outlined" />
                            ))}
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {idea.description.length > 150
                              ? `${idea.description.substring(0, 150)}...`
                              : idea.description}
                          </Typography>
                          {idea.formData && (
                            <Typography variant="caption" color="text.secondary">
                              {formatFormData(idea.formData)}
                            </Typography>
                          )}
                        </Box>

                        {/* Actions */}
                        <Box sx={{ display: 'flex', gap: 0.5, ml: 2 }}>
                          <Tooltip title="View full idea">
                            <IconButton size="small" onClick={() => handleViewIdea(idea)}>
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download as Word">
                            <IconButton size="small" onClick={() => handleDownloadIdea(idea)}>
                              <DownloadIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {idea.formData && (
                            <Tooltip title="Edit & regenerate">
                              <IconButton size="small" onClick={() => handleEditIdea(idea)} color="primary">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete idea">
                            <IconButton
                              size="small"
                              onClick={() => handleConfirmDelete(project.id, idea.id)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}

      {/* View Idea Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        {selectedIdea && (
          <>
            <DialogTitle>
              <Typography variant="h5" fontWeight={600}>
                {selectedIdea.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip label={selectedIdea.area} size="small" variant="outlined" />
                <Chip
                  label={selectedIdea.scale}
                  size="small"
                  sx={{
                    bgcolor: SCALE_COLORS[selectedIdea.scale]?.bg || '#f5f5f5',
                    color: SCALE_COLORS[selectedIdea.scale]?.text || '#616161',
                    fontWeight: 500,
                  }}
                />
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Description
              </Typography>
              <Typography variant="body2" sx={{ mb: 3, whiteSpace: 'pre-wrap' }}>
                {selectedIdea.description}
              </Typography>

              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Rationale
              </Typography>
              <Typography variant="body2" sx={{ mb: 3, whiteSpace: 'pre-wrap' }}>
                {selectedIdea.rationale}
              </Typography>

              {selectedIdea.notes && (
                <>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Notes
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 3, whiteSpace: 'pre-wrap' }}>
                    {selectedIdea.notes}
                  </Typography>
                </>
              )}

              {selectedIdea.tags && selectedIdea.tags.length > 0 && (
                <>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Tags
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
                    {selectedIdea.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" color="primary" variant="outlined" />
                    ))}
                  </Box>
                </>
              )}

              {selectedIdea.formData && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Original Inputs
                  </Typography>
                  <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                    <Typography variant="body2">
                      <strong>Client:</strong> {selectedIdea.formData.clientName}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Target Audience:</strong> {selectedIdea.formData.targetAudience}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Campaign Goal:</strong> {selectedIdea.formData.campaignGoal}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Budget:</strong> {selectedIdea.formData.budget}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Idea Scale:</strong> {selectedIdea.formData.ideaScale}
                    </Typography>
                    {selectedIdea.formData.ideaAreas && (
                      <Typography variant="body2">
                        <strong>Idea Areas:</strong> {selectedIdea.formData.ideaAreas}
                      </Typography>
                    )}
                    {selectedIdea.formData.competitors && (
                      <Typography variant="body2">
                        <strong>Competitors:</strong> {selectedIdea.formData.competitors}
                      </Typography>
                    )}
                  </Box>
                </>
              )}

              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                Saved on {new Date(selectedIdea.savedAt).toLocaleString()}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => handleDownloadIdea(selectedIdea)} startIcon={<DownloadIcon />}>
                Download
              </Button>
              {selectedIdea.formData && (
                <Button onClick={() => handleEditIdea(selectedIdea)} startIcon={<EditIcon />} color="primary">
                  Edit & Regenerate
                </Button>
              )}
              <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Idea</DialogTitle>
        <DialogContent>
          <Typography>Are you sure you want to delete this idea? This action cannot be undone.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteIdea} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
