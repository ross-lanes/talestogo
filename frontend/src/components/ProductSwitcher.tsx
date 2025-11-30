import React, { useState } from 'react';
import {
  Box,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Divider,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  Apps as ProductIcon,
  Check as CheckIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useProduct } from '../contexts/ProductContext';
import { useAuth } from '../contexts/AuthContext';

const ProductSwitcher: React.FC = () => {
  const { currentProduct, availableProducts, upcomingProducts, switchProduct, isSolsticeHC } = useProduct();
  const { user } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSwitchProduct = (productId: string) => {
    switchProduct(productId as any);
    handleClose();

    // Navigate to product-specific home page
    switch (productId) {
      case 'heads':
        navigate('/heads');
        break;
      case 'canon':
        navigate('/canon');
        break;
      case 'tales':
        navigate('/');
        break;
      // Add other products as they become available
      default:
        navigate('/');
    }
  };

  // Show ProductSwitcher if there are multiple products OR upcoming products
  // Note: We show it even with 1 available + 0 upcoming for Solstice HC users
  // because upcoming products might not load immediately on page load
  const hasMultipleProducts = availableProducts.length > 1 || upcomingProducts.length > 0;
  const isSolsticeUser = isSolsticeHC; // Solstice HC always sees switcher (for upcoming products)
  const isAdmin = user?.is_admin || false; // Admins always see the switcher

  if (!hasMultipleProducts && !isSolsticeUser && !isAdmin) {
    return null;
  }

  return (
    <Box>
      <IconButton
        onClick={handleClick}
        sx={{
          color: 'common.white',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
          },
        }}
      >
        <ProductIcon />
      </IconButton>

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
            minWidth: { xs: 280, sm: 280 },
            maxWidth: { xs: '90vw', sm: 400 },
            maxHeight: { xs: '70vh', sm: 500 },
          },
        }}
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="overline" color="text.secondary" fontWeight={600}>
            Solstice AI Suite
          </Typography>
        </Box>
        <Divider />

        {/* Available Products */}
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            Available Products
          </Typography>
        </Box>
        {availableProducts.map((product) => (
          <MenuItem
            key={product.id}
            onClick={() => handleSwitchProduct(product.id)}
            selected={product.id === currentProduct.id}
            sx={{
              py: 1.5,
              px: 2,
              '&.Mui-selected': {
                backgroundColor: 'rgba(117, 201, 200, 0.12)',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>
              {product.id === currentProduct.id ? (
                <CheckIcon fontSize="small" sx={{ color: '#75C9C8' }} />
              ) : (
                <ProductIcon fontSize="small" />
              )}
            </ListItemIcon>
            <ListItemText
              primary={
                <Typography variant="body2" fontWeight={product.id === currentProduct.id ? 600 : 400}>
                  {product.name}
                </Typography>
              }
              secondary={product.description}
              secondaryTypographyProps={{
                variant: 'caption',
                color: 'text.secondary',
              }}
            />
          </MenuItem>
        ))}

        {/* Upcoming Products */}
        {upcomingProducts.length > 0 && (
          <>
            <Divider sx={{ mt: 1 }} />
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                Coming Soon
              </Typography>
            </Box>
            {upcomingProducts.map((product) => (
              <MenuItem
                key={product.id}
                disabled
                sx={{
                  py: 1.5,
                  px: 2,
                  opacity: 0.6,
                }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <LockIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2">
                      {product.name}
                    </Typography>
                  }
                  secondary={product.description}
                  secondaryTypographyProps={{
                    variant: 'caption',
                    color: 'text.secondary',
                  }}
                />
              </MenuItem>
            ))}
          </>
        )}

        <Divider sx={{ mt: 1 }} />
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            One login, all products. Shared brands across the suite.
          </Typography>
        </Box>
      </Menu>
    </Box>
  );
};

export default ProductSwitcher;
