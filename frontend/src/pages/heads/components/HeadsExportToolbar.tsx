import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PrintIcon from '@mui/icons-material/Print';
import SlideshowIcon from '@mui/icons-material/Slideshow';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DataObjectIcon from '@mui/icons-material/DataObject';
import DescriptionIcon from '@mui/icons-material/Description';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import PptxGenJS from 'pptxgenjs';
import type { Persona, HeadsFormData } from '../../../types/heads';

interface HeadsExportToolbarProps {
  personas: Persona[];
  formData: HeadsFormData;
  onBack: () => void;
  onExportJson: () => void;
  onExportText: () => void;
  onPrint: () => void;
}

const HeadsExportToolbar: React.FC<HeadsExportToolbarProps> = ({
  personas,
  formData,
  onBack,
  onExportJson,
  onExportText,
  onPrint,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExportSlides = () => {
    try {
      const pres = new PptxGenJS();
      pres.layout = 'LAYOUT_16x9';

      const colors = {
        headerBg: 'F8FAFC',
        headerBorder: 'E2E8F0',
        badgeBg: 'E0E7FF',
        badgeText: '4338CA',
        textPrimary: '0F172A',
        textSecondary: '64748B',
        textLight: '94A3B8',
        boxBg: 'F8FAFC',
        boxBorder: 'E2E8F0',
        indigoBg: 'EEF2FF',
        indigoBorder: 'C7D2FE',
        indigoText: '312E81',
        emerald: '10B981',
        rose: 'F43F5E',
        blue: '3B82F6',
        indigo: '4F46E5',
      };

      // Title Slide
      const titleSlide = pres.addSlide();
      titleSlide.background = { color: '003e60' };

      titleSlide.addShape(pres.ShapeType.ellipse, {
        x: 4.5,
        y: 1.5,
        w: 1,
        h: 1,
        fill: { color: '80a1d4' },
      });

      titleSlide.addText('Persona Report', {
        x: 0,
        y: 2.6,
        w: '100%',
        fontSize: 44,
        color: 'FFFFFF',
        align: 'center',
        bold: true,
        fontFace: 'Arial',
      });
      titleSlide.addText(`Brand: ${formData.brand}`, {
        x: 0,
        y: 3.5,
        w: '100%',
        fontSize: 24,
        color: '80a1d4',
        align: 'center',
        fontFace: 'Arial',
      });
      titleSlide.addText(`Generated on ${new Date().toLocaleDateString()}`, {
        x: 0,
        y: 5,
        w: '100%',
        fontSize: 12,
        color: 'CCCCCC',
        align: 'center',
        fontFace: 'Arial',
      });

      // Persona Slides
      personas.forEach((p) => {
        const slide = pres.addSlide();
        slide.background = { color: 'FFFFFF' };

        // Header Section
        slide.addShape(pres.ShapeType.rect, {
          x: 0,
          y: 0,
          w: '100%',
          h: 1.5,
          fill: { color: colors.headerBg },
          line: { color: colors.headerBorder, width: 1 },
        });

        // Badge Pill
        slide.addShape(pres.ShapeType.roundRect, {
          x: 0.4,
          y: 0.25,
          w: 2.5,
          h: 0.35,
          fill: { color: colors.badgeBg },
          rectRadius: 0.5,
          line: { color: colors.badgeBg },
        });
        slide.addText(p.generalizationTitle.toUpperCase(), {
          x: 0.4,
          y: 0.25,
          w: 2.5,
          h: 0.35,
          fontSize: 10,
          color: colors.badgeText,
          align: 'center',
          bold: true,
          fontFace: 'Arial',
        });

        // Name
        slide.addText(p.name, {
          x: 0.4,
          y: 0.65,
          w: 6,
          h: 0.5,
          fontSize: 28,
          color: colors.textPrimary,
          bold: true,
          fontFace: 'Arial',
        });

        // Demographics Row
        const demoText = `${p.age}  |  ${p.occupation}  |  ${p.location || ''}  |  ${p.workplace || ''}`;
        slide.addText(demoText, {
          x: 0.4,
          y: 1.1,
          w: 7.5,
          h: 0.3,
          fontSize: 12,
          color: colors.textSecondary,
          fontFace: 'Arial',
        });

        // Avatar
        const avatarSize = 1.2;
        const avatarX = 8.4;
        const avatarY = 0.15;

        slide.addShape(pres.ShapeType.ellipse, {
          x: avatarX,
          y: avatarY,
          w: avatarSize,
          h: avatarSize,
          fill: { color: colors.headerBorder },
        });

        if (p.avatarBase64) {
          slide.addImage({
            data: p.avatarBase64,
            x: avatarX,
            y: avatarY,
            w: avatarSize,
            h: avatarSize,
            sizing: { type: 'contain', w: avatarSize, h: avatarSize },
          });
        } else {
          slide.addText('No Image', {
            x: avatarX,
            y: avatarY,
            w: avatarSize,
            h: avatarSize,
            fontSize: 8,
            align: 'center',
            color: colors.textLight,
          });
        }

        // Profile Quote
        slide.addText(`"${p.profile}"`, {
          x: 0.4,
          y: 1.6,
          w: 9.2,
          h: 0.6,
          fontSize: 11,
          color: '475569',
          italic: true,
          fontFace: 'Arial',
          valign: 'top',
        });

        // Technology Profile
        const techY = 2.2;
        const techH = 0.65;
        const techBoxW = 4.4;
        const techGap = 0.4;

        slide.addShape(pres.ShapeType.roundRect, {
          x: 0.4,
          y: techY,
          w: techBoxW,
          h: techH,
          fill: { color: colors.boxBg },
          line: { color: colors.boxBorder },
          rectRadius: 0.1,
        });
        slide.addText('TECHNOLOGY ABILITY', {
          x: 0.5,
          y: techY + 0.05,
          w: 4,
          h: 0.2,
          fontSize: 8,
          color: colors.textSecondary,
          bold: true,
        });
        slide.addText(p.technologyAbility || 'N/A', {
          x: 0.5,
          y: techY + 0.25,
          w: 4,
          h: 0.3,
          fontSize: 10,
          color: colors.textPrimary,
        });

        slide.addShape(pres.ShapeType.roundRect, {
          x: 0.4 + techBoxW + techGap,
          y: techY,
          w: techBoxW,
          h: techH,
          fill: { color: colors.boxBg },
          line: { color: colors.boxBorder },
          rectRadius: 0.1,
        });
        slide.addText('TECHNOLOGY COMFORTABILITY', {
          x: 0.5 + techBoxW + techGap,
          y: techY + 0.05,
          w: 4,
          h: 0.2,
          fontSize: 8,
          color: colors.textSecondary,
          bold: true,
        });
        slide.addText(p.technologyComfortability || 'N/A', {
          x: 0.5 + techBoxW + techGap,
          y: techY + 0.25,
          w: 4,
          h: 0.3,
          fontSize: 10,
          color: colors.textPrimary,
        });

        // Goals & Frustrations
        const listY = 3.05;
        const listH = 1.3;

        slide.addText('GOALS & MOTIVATIONS', {
          x: 0.4,
          y: listY,
          w: 4.4,
          h: 0.3,
          fontSize: 10,
          color: colors.emerald,
          bold: true,
        });
        slide.addText(p.goals.join('\n'), {
          x: 0.4,
          y: listY + 0.25,
          w: 4.4,
          h: listH,
          fontSize: 9,
          color: '334155',
          bullet: { type: 'bullet' },
          valign: 'top',
        });

        slide.addText('FRUSTRATIONS & PAIN POINTS', {
          x: 0.4 + techBoxW + techGap,
          y: listY,
          w: 4.4,
          h: 0.3,
          fontSize: 10,
          color: colors.rose,
          bold: true,
        });
        slide.addText(p.frustrations.join('\n'), {
          x: 0.4 + techBoxW + techGap,
          y: listY + 0.25,
          w: 4.4,
          h: listH,
          fontSize: 9,
          color: '334155',
          bullet: { type: 'bullet' },
          valign: 'top',
        });

        // Bottom Section
        const botY = 4.5;
        const botH = 0.9;

        slide.addText('BRAND PERCEPTION', {
          x: 0.4,
          y: botY,
          fontSize: 9,
          color: colors.blue,
          bold: true,
        });
        slide.addShape(pres.ShapeType.roundRect, {
          x: 0.4,
          y: botY + 0.2,
          w: 4.4,
          h: botH,
          fill: { color: colors.boxBg },
          line: { color: colors.boxBorder },
          rectRadius: 0.1,
        });
        slide.addText(p.brandView, {
          x: 0.5,
          y: botY + 0.2,
          w: 4.2,
          h: botH,
          fontSize: 9,
          color: '475569',
          valign: 'middle',
        });

        slide.addText('MARKETING STRATEGY', {
          x: 0.4 + techBoxW + techGap,
          y: botY,
          fontSize: 9,
          color: colors.indigo,
          bold: true,
        });
        slide.addShape(pres.ShapeType.roundRect, {
          x: 0.4 + techBoxW + techGap,
          y: botY + 0.2,
          w: 4.4,
          h: botH,
          fill: { color: colors.indigoBg },
          line: { color: colors.indigoBorder },
          rectRadius: 0.1,
        });
        slide.addText(p.marketingStrategy, {
          x: 0.5 + techBoxW + techGap,
          y: botY + 0.2,
          w: 4.2,
          h: botH,
          fontSize: 9,
          color: colors.indigoText,
          valign: 'middle',
        });
      });

      const fileName = `${formData.brand.replace(/\s+/g, '_')}_Personas.pptx`;
      pres.writeFile({ fileName });
    } catch (e) {
      console.error('Failed to generate slides', e);
      alert('Could not generate slides. Please check console for details.');
    }
  };

  const handleSavePDF = () => {
    window.print();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        alignItems: { xs: 'flex-start', md: 'center' },
        justifyContent: 'space-between',
        gap: 2,
        mb: 4,
        pb: 3,
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
      className="no-print"
    >
      {/* Left Side */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={onBack} sx={{ bgcolor: 'action.hover' }}>
          <ArrowBackIcon />
        </IconButton>
        <Box>
          <Typography variant="h5" fontWeight={700}>
            Generated Personas
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Showing {personas.length} results for <strong>{formData.brand}</strong>
          </Typography>
        </Box>
      </Box>

      {/* Right Side - Export Buttons */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<PictureAsPdfIcon />}
          onClick={handleSavePDF}
        >
          PDF
        </Button>
        <Button
          variant="outlined"
          size="small"
          startIcon={<SlideshowIcon />}
          onClick={handleExportSlides}
        >
          Slides
        </Button>
        <Box ref={exportMenuRef}>
          <Button
            variant="contained"
            size="small"
            endIcon={<KeyboardArrowDownIcon />}
            onClick={handleMenuOpen}
            startIcon={<FileDownloadIcon />}
          >
            Export
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem
              onClick={() => {
                onExportJson();
                handleMenuClose();
              }}
            >
              <ListItemIcon>
                <DataObjectIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Export as JSON</ListItemText>
            </MenuItem>
            <MenuItem
              onClick={() => {
                onExportText();
                handleMenuClose();
              }}
            >
              <ListItemIcon>
                <DescriptionIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Export as Text</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
        <Button variant="outlined" size="small" startIcon={<PrintIcon />} onClick={onPrint}>
          Print
        </Button>
      </Box>
    </Box>
  );
};

export default HeadsExportToolbar;
