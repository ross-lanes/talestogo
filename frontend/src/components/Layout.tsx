import { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Menu,
  MenuItem,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Tune as CustomizeIcon,
  TextFields as QueryIcon,
  Label as DescriptorIcon,
  Groups as CompetitorIcon,
  TrendingUp as TrendingUpIcon,
  Visibility as VisibilityIcon,
  SentimentSatisfied as SentimentIcon,
  Warning as WarningIcon,
  Flag as FlagIcon,
  Announcement as AnnouncementIcon,
  ChatBubble as ResponseIcon,
  Description as ReportIcon,
  Logout as LogoutIcon,
  AdminPanelSettings as AdminIcon,
  CloudDownload as CollectionIcon,
  MoreVert as MoreVertIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  HelpOutline as HelpIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTenant } from '../contexts/TenantContext';
import { useProduct } from '../contexts/ProductContext';
import BrandSwitcher from './BrandSwitcher';
import TenantSwitcher from './TenantSwitcher';
import ProductSwitcher from './ProductSwitcher';
import talesWhite from './tales_white.png';

const drawerWidth = 240;

// Product taglines
const PRODUCT_TAGLINES: Record<string, string> = {
  tales: 'Shape your AI story.',
  heads: 'Know your audience.',
  vision: 'See the market clearly.',
  pulse: 'Measure what matters.',
  voice: 'Optimize every word.',
  guardian: 'Ensure compliance.',
};

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();
  const { tenant } = useTenant();
  const { currentProduct } = useProduct();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleUserMenuClose();
    navigate('/login');
  };

  const handleSettings = () => {
    navigate('/settings');
    handleUserMenuClose();
  };

  const handleAdminPanel = () => {
    navigate('/admin/users');
    handleUserMenuClose();
  };

  const handleTenantManagement = () => {
    navigate('/admin/tenants');
    handleUserMenuClose();
  };

  const handleSchedulerDashboard = () => {
    navigate('/admin/scheduler');
    handleUserMenuClose();
  };

  const handleHowTalesWorks = () => {
    navigate('/how-tales-works');
    handleUserMenuClose();
  };

  const handleHelp = () => {
    navigate('/help');
    handleUserMenuClose();
  };


  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/', indent: false },
    { text: 'Manage Brands', icon: <CustomizeIcon />, path: '/manage/brands', indent: false },
    { text: 'Collect & Analyze', icon: <CollectionIcon />, path: '/collect-analyze', indent: false },
    { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics/brand-mentions', indent: false },
    { text: 'Brand Mentions', icon: <AnnouncementIcon />, path: '/analytics/brand-mentions', indent: true },
    { text: 'Positioning', icon: <TrendingUpIcon />, path: '/analytics/positioning', indent: true },
    { text: 'Share of Voice', icon: <VisibilityIcon />, path: '/analytics/share-of-voice', indent: true },
    { text: 'Descriptors', icon: <DescriptorIcon />, path: '/analytics/descriptors', indent: true },
    { text: 'Sentiment', icon: <SentimentIcon />, path: '/analytics/sentiment', indent: true },
    { text: 'Threats', icon: <WarningIcon />, path: '/analytics/threats', indent: true },
    { text: 'Recommendations', icon: <FlagIcon />, path: '/analytics/recommendations', indent: false },
    { text: 'Reports', icon: <ReportIcon />, path: '/reports', indent: false },
  ];

  const handleMenuItemClick = (item: any) => {
    if (item.path) {
      navigate(item.path);
    }
  };

  const drawer = (
    <Box sx={{
      height: '100%',
      backgroundColor: tenant?.primary_color || '#003e60',
      display: 'flex',
      flexDirection: 'column',
    }}>
  <Toolbar
  sx={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    px: 2,
    minHeight: { xs: 106, sm: 114 },
    height: { xs: 106, sm: 114 },
    gap: 1,
    cursor: 'pointer',
    backgroundColor: tenant?.primary_color || '#003e60',  // Use tenant primary color
    color: 'common.white',               // make all text inside white
    '&:hover': {
    },
    '& h1': {
      margin: 0,
      color: 'common.white',             // ensure h1 text is white
    },
  }}
  onClick={() => navigate('/')}
>
  <Typography
    variant="body2"
    component="div"
    sx={{
      textAlign: 'center',
      fontSize: '0.875rem',
      fontStyle: 'italic',
      lineHeight: 1.3,
      color: 'common.white',             // ensure secondary text is white
    }}
  >
    <img
      src={talesWhite}
      alt={currentProduct.name}
      style={{
        width: 120,
        maxWidth: '100%',
        display: 'block',
        margin: '0 auto',
      }}
    />
    {PRODUCT_TAGLINES[currentProduct.id] || 'Solstice AI Suite'}
  </Typography>
</Toolbar>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.12)' }} />
      <Box sx={{ px: 2, py: 2 }}>
        <TenantSwitcher />
      </Box>
      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.12)' }} />
      <List sx={{ flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleMenuItemClick(item)}
              sx={{
                pl: item.indent ? 5.75 : 2,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                },
                '&.Mui-selected': {
                  backgroundColor: 'rgba(255, 255, 255, 0.16)',
                  borderLeft: '4px solid',
                  borderLeftColor: 'common.white',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'common.white', minWidth: 36 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 600 : 400,
                  color: 'common.white'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* RobotRachel Logo at Bottom */}
      <Box
        sx={{
          mt: 'auto',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: 'common.white',
            display: 'block',
            mb: 0.5,
            fontSize: '0.75rem',
          }}
        >
          Made by
        </Typography>
        <Box
          component="a"
          href="http://www.robotrachel.com"
          target="_blank"
          rel="noopener noreferrer"
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            px: 2,
            pb: 2,
            textDecoration: 'none',
            transition: 'opacity 0.2s',
            '&:hover': {
              opacity: 0.8,
            },
          }}
        >
          <img
            src="/logos/robotrachel2-white-logo.png"
            alt="RobotRachel"
            style={{
              width: '132px',
              maxWidth: '100%',
              height: 'auto',
            }}
          />
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', backgroundColor: 'white', minHeight: '100vh', width: '100%' }}>
      <CssBaseline />

      {/* Sidebar Navigation */}
      <Box
        component="nav"
        sx={{
          width: { sm: drawerWidth },
          flexShrink: { sm: 0 },
          backgroundColor: { sm: tenant?.primary_color || '#003e60' }
        }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
              height: '100vh',
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              position: 'static',
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
              backgroundColor: 'transparent',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: '100%',
          minWidth: 0, // Allow flex item to shrink below content size
          minHeight: '100vh',
          backgroundColor: 'white',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Top AppBar */}
        <AppBar
          position="static"
          sx={{
            backgroundColor: 'primary.main',
            width: '100%',
          }}
        >
          <Toolbar
            sx={{
              minHeight: { xs: 106, sm: 114 },
              height: { xs: 106, sm: 114 },
              width: '100%',
              pr: '10px !important', // Right padding 10px from edge
            }}
          >
            {/* Left: hamburger (mobile only) */}
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>

            {/* Tenant Logo (if available) */}
            {tenant?.logo_url && (
              <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                <img
                  src={tenant.logo_url}
                  alt={tenant.tenant_name}
                  style={{
                    height: '40px',
                    maxWidth: '150px',
                    objectFit: 'contain',
                  }}
                />
              </Box>
            )}

            {/* Right: group pushed to the far right with ml: 'auto' */}
            {user && (
              <Box
                sx={{
                  ml: 'auto',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  color: 'common.white',
                  '& .MuiTypography-root': { color: 'common.white' },
                  '& .MuiSvgIcon-root': { color: 'common.white' },
                  '& *': { color: 'common.white' },
                }}
              >
                <BrandSwitcher />
                <ProductSwitcher />
                <IconButton onClick={handleUserMenuOpen} color="inherit" sx={{ p: 0.5 }}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', color: 'common.white' }}>
                    {user.email.charAt(0).toUpperCase()}
                  </Avatar>
                </IconButton>
              </Box>
            )}
          </Toolbar>
        </AppBar>

        {/* User Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Signed in as
            </Typography>
            <Typography variant="body1" fontWeight={600}>
              {user?.email}
            </Typography>
          </Box>
          <Divider />
          <MenuItem onClick={handleSettings}>
            <ListItemIcon>
              <SettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>
          {isAdmin && (
            <>
              <MenuItem onClick={handleAdminPanel}>
                <ListItemIcon>
                  <AdminIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>User Management</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleTenantManagement}>
                <ListItemIcon>
                  <BusinessIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Tenant Management</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleSchedulerDashboard}>
                <ListItemIcon>
                  <ScheduleIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Scheduler Dashboard</ListItemText>
              </MenuItem>
            </>
          )}
          <MenuItem onClick={handleHelp}>
            <ListItemIcon>
              <HelpIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Help & Support</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleHowTalesWorks}>
            <ListItemIcon>
              <InfoIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>How Tales Works</ListItemText>
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Logout</ListItemText>
          </MenuItem>
        </Menu>

        {/* Page Content */}
        <Box sx={{ p: 3, flexGrow: 1, backgroundColor: 'white' }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
