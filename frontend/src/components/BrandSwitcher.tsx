import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Divider,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Business as BrandIcon,
  KeyboardArrowDown,
  Add as AddIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useBrand } from '../contexts/BrandContext';
import { useNavigate } from 'react-router-dom';

const BrandSwitcher: React.FC = () => {
  const { activeBrand, brands, loading, switchBrand } = useBrand();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [switching, setSwitching] = useState(false);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSwitchBrand = async (brandId: number) => {
    setSwitching(true);
    try {
      await switchBrand(brandId);
      handleClose();
      setSwitching(false);
      // Navigate to Dashboard when brand is switched
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to switch brand:', error);
      setSwitching(false);
    }
  };

  const handleAddBrand = () => {
    handleClose();
    navigate('/manage/brand-info?new=true');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          Loading brands...
        </Typography>
      </Box>
    );
  }

  // If no brands exist, show "Add Brand" button
  if (brands.length === 0) {
    return (
      <Button
        variant="outlined"
        startIcon={<AddIcon />}
        onClick={handleAddBrand}
        size="small"
        sx={{
          borderColor: '#75C9C8',
          color: '#75C9C8',
          '&:hover': {
            borderColor: '#5FB3B2',
            backgroundColor: 'rgba(117, 201, 200, 0.08)',
          },
        }}
      >
        Add Brand
      </Button>
    );
  }

  return (
    <Box>
      <Button
        onClick={handleClick}
        disabled={switching}
        startIcon={<BrandIcon sx={{ display: { xs: 'none', sm: 'inline' } }} />}
        endIcon={<KeyboardArrowDown />}
        sx={{
          color: 'text.primary',
          textTransform: 'none',
          px: { xs: 1, sm: 2 },
          py: 1,
          borderRadius: 1,
          minWidth: { xs: 'auto', sm: 'auto' },
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', ml: { xs: 0, sm: 1 } }}>
          <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.2, display: { xs: 'none', sm: 'block' } }}>
            Brand
          </Typography>
          <Typography variant="body2" fontWeight={600} sx={{ lineHeight: 1.2, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
            {switching ? 'Switching...' : activeBrand?.brand_name || 'Select Brand'}
          </Typography>
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: { xs: 280, sm: 250 },
            maxWidth: { xs: '90vw', sm: 400 },
            maxHeight: { xs: '70vh', sm: 400 },
          },
        }}
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="overline" color="text.secondary" fontWeight={600}>
            Your Brands ({brands.length}/20)
          </Typography>
        </Box>
        <Divider />

        {brands.map((brand) => {
          const isActive = activeBrand?.id === brand.id;
          return (
            <MenuItem
              key={brand.id}
              onClick={() => handleSwitchBrand(brand.id)}
              selected={isActive}
              sx={{
                py: 1.5,
                px: 2,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(117, 201, 200, 0.12)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {isActive ? (
                  <CheckIcon fontSize="small" sx={{ color: '#75C9C8' }} />
                ) : (
                  <BrandIcon fontSize="small" />
                )}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" fontWeight={isActive ? 600 : 400}>
                      {brand.brand_name}
                    </Typography>
                    {isActive && (
                      <Chip label="Active" size="small" sx={{ height: 20, fontSize: '0.7rem' }} />
                    )}
                  </Box>
                }
                secondary={brand.industry || 'No industry set'}
                secondaryTypographyProps={{
                  variant: 'caption',
                  color: 'text.secondary',
                }}
              />
            </MenuItem>
          );
        })}

        {brands.length < 20 && (
          <>
            <Divider />
            <MenuItem
              onClick={handleAddBrand}
              sx={{
                py: 1.5,
                px: 2,
                color: '#75C9C8',
                '&:hover': {
                  backgroundColor: 'rgba(117, 201, 200, 0.08)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <AddIcon fontSize="small" sx={{ color: '#75C9C8' }} />
              </ListItemIcon>
              <ListItemText
                primary="Add New Brand"
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: 600,
                }}
              />
            </MenuItem>
          </>
        )}
      </Menu>
    </Box>
  );
};

export default BrandSwitcher;
