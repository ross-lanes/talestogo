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
  Chip,
} from '@mui/material';
import {
  Apps as ProductIcon,
  KeyboardArrowDown,
  Check as CheckIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useProduct } from '../contexts/ProductContext';

const ProductSwitcher: React.FC = () => {
  const { currentProduct, availableProducts, switchProduct, isSolsticeHC } = useProduct();
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
      case 'tales':
        navigate('/');
        break;
      // Add other products as they become available
      default:
        navigate('/');
    }
  };

  // Filter available products
  const enabledProducts = availableProducts.filter(p => p.enabled);
  const upcomingProducts = availableProducts.filter(p => !p.enabled);

  // Don't show ProductSwitcher if only one product is available
  if (enabledProducts.length <= 1 && upcomingProducts.length === 0) {
    return null;
  }

  return (
    <Box>
      <Button
        onClick={handleClick}
        startIcon={<ProductIcon />}
        endIcon={<KeyboardArrowDown />}
        sx={{
          color: 'text.primary',
          textTransform: 'none',
          px: 2,
          py: 1,
          borderRadius: 1,
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', ml: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.2 }}>
            Product
          </Typography>
          <Typography variant="body2" fontWeight={600} sx={{ lineHeight: 1.2 }}>
            {currentProduct.name}
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
            minWidth: 280,
            maxHeight: 500,
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
        {enabledProducts.map((product) => (
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
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" fontWeight={product.id === currentProduct.id ? 600 : 400}>
                    {product.name}
                  </Typography>
                  {product.id === currentProduct.id && (
                    <Chip label="Active" size="small" sx={{ height: 20, fontSize: '0.7rem' }} />
                  )}
                </Box>
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
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2">
                        {product.name}
                      </Typography>
                      <Chip
                        label="Soon"
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.7rem',
                          backgroundColor: 'rgba(0, 0, 0, 0.1)',
                        }}
                      />
                    </Box>
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
