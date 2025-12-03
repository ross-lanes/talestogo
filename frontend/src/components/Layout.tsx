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
  Search as SearchIcon,
  CompareArrows as CompareIcon,
  Bookmark as BookmarkIcon,
  AutoAwesome as AutoAwesomeIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTenant } from '../contexts/TenantContext';
import { useProduct } from '../contexts/ProductContext';
import BrandSwitcher from './BrandSwitcher';
import TenantSwitcher from './TenantSwitcher';
import ProductSwitcher from './ProductSwitcher';
import talesWhite from './tales_white.png';

// Product logos map - using imported assets for bundled products
const PRODUCT_LOGOS: Record<string, string> = {
  tales: talesWhite,
  // Other products use logoPath from ProductContext (public folder)
};

const drawerWidth = 240;

// Product taglines
const PRODUCT_TAGLINES: Record<string, string> = {
  tales: 'Shape your AI story.',
  heads: 'Know your audience.',
  canon: 'Research FDA data.',
  nstxview: 'Call the shots.',
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
    navigate('/settings/users');
    handleUserMenuClose();
  };

  const handleTenantManagement = () => {
    navigate('/settings/tenants');
    handleUserMenuClose();
  };

  const handleSchedulerDashboard = () => {
    navigate('/settings/scheduler');
    handleUserMenuClose();
  };

  const handleDataBatches = () => {
    navigate('/settings/batches');
    handleUserMenuClose();
  };

  const handleHelp = () => {
    navigate('/help');
    handleUserMenuClose();
  };


  // Tales navigation menu items
  const talesMenuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/', indent: false },
    { text: 'Manage Brand', icon: <CustomizeIcon />, path: '/manage/brands', indent: false },
    { text: 'Collect & Analyze', icon: <CollectionIcon />, path: '/collect-analyze', indent: false },
    { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics/brand-mentions', indent: false },
    { text: 'Brand Mentions', icon: <AnnouncementIcon />, path: '/analytics/brand-mentions', indent: true },
    { text: 'Positioning', icon: <TrendingUpIcon />, path: '/analytics/positioning', indent: true },
    { text: 'Share of Voice', icon: <VisibilityIcon />, path: '/analytics/share-of-voice', indent: true },
    { text: 'Descriptors', icon: <DescriptorIcon />, path: '/analytics/descriptors', indent: true },
    { text: 'Sentiment', icon: <SentimentIcon />, path: '/analytics/sentiment', indent: true },
    { text: 'Threats', icon: <WarningIcon />, path: '/analytics/threats', indent: true },
    { text: 'Reports', icon: <ReportIcon />, path: '/reports', indent: false },
    { text: 'How Tales Works', icon: <InfoIcon />, path: '/how-tales-works', indent: false },
  ];

  // Canon navigation menu items
  const canonMenuItems = [
    { text: 'Look Up', icon: <SearchIcon />, path: '/canon', indent: false },
    { text: 'Ask a Question', icon: <ResponseIcon />, path: '/canon/ask', indent: false },
    { text: 'Check a Document', icon: <ReportIcon />, path: '/canon/documents', indent: false },
    { text: 'Compare Drugs', icon: <CompareIcon />, path: '/canon/compare', indent: false },
    { text: 'How Canon Works', icon: <InfoIcon />, path: '/how-canon-works', indent: false },
  ];

  // Heads navigation menu items
  const headsMenuItems = [
    { text: 'Generate Personas', icon: <AutoAwesomeIcon />, path: '/heads', indent: false },
    { text: 'How Heads Works', icon: <InfoIcon />, path: '/how-heads-works', indent: false },
  ];

  // NSTXView navigation menu items
  const nstxviewMenuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/nstxview', indent: false },
    { text: 'Browse Papers', icon: <ReportIcon />, path: '/nstxview/papers', indent: false },
    { text: 'Explore Shots', icon: <TrendingUpIcon />, path: '/nstxview/shots', indent: false },
    { text: 'Analyze Parameters', icon: <AnalyticsIcon />, path: '/nstxview/parameters', indent: false },
    { text: 'Phenomena', icon: <AutoAwesomeIcon />, path: '/nstxview/phenomena', indent: false },
    // Processing Status is admin-only
    ...(isAdmin ? [{ text: 'Processing Status', icon: <SettingsIcon />, path: '/nstxview/processing', indent: false }] : []),
    { text: 'Saved Conversations', icon: <BookmarkIcon />, path: '/nstxview/conversations', indent: false },
    { text: 'How NSTXView Works', icon: <InfoIcon />, path: '/how-nstxview-works', indent: false },
  ];

  // Select menu items based on current product
  const getMenuItems = () => {
    switch (currentProduct.id) {
      case 'canon':
        return canonMenuItems;
      case 'heads':
        return headsMenuItems;
      case 'nstxview':
        return nstxviewMenuItems;
      default:
        return talesMenuItems;
    }
  };
  const menuItems = getMenuItems();

  const handleMenuItemClick = (item: any) => {
    if (item.path) {
      navigate(item.path);
    }
  };

  const drawer = (
    <Box sx={{
      height: '100%',
      backgroundColor: '#000000',
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
    minHeight: { xs: 90, sm: 114 }, // Reduced mobile height
    height: { xs: 90, sm: 114 },
    gap: 0.5,
    cursor: 'pointer',
    backgroundColor: '#000000',  // Black background
    color: 'common.white',               // make all text inside white
    '&:hover': {
    },
    '& h1': {
      margin: 0,
      color: 'common.white',             // ensure h1 text is white
    },
  }}
  onClick={() => {
    if (currentProduct.id === 'canon') navigate('/canon');
    else if (currentProduct.id === 'heads') navigate('/heads');
    else navigate('/');
  }}
>
  <Typography
    variant="body2"
    component="div"
    sx={{
      textAlign: 'center',
      fontSize: { xs: '0.75rem', sm: '0.875rem' }, // Smaller on mobile
      fontStyle: 'italic',
      lineHeight: 1.3,
      color: 'common.white',             // ensure secondary text is white
    }}
  >
    {currentProduct.id === 'nstxview' ? (
      <Typography
        variant="h4"
        component="div"
        sx={{
          fontWeight: 900,
          letterSpacing: '-0.5px',
          color: 'common.white',
          textAlign: 'center',
          fontSize: { xs: '1.5rem', sm: '2rem' },
        }}
      >
        NSTXView
      </Typography>
    ) : (
      <Box
        component="img"
        src={PRODUCT_LOGOS[currentProduct.id] || currentProduct.logoPath}
        alt={currentProduct.name}
        sx={{
          width: { xs: 100, sm: 120 }, // Smaller logo on mobile
          maxWidth: '100%',
          display: 'block',
          margin: '0 auto',
        }}
      />
    )}
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
              width: '182px',
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
          backgroundColor: { sm: '#000000' }
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
            backgroundColor: '#000000',
            width: '100%',
          }}
        >
          <Toolbar
            sx={{
              minHeight: { xs: 90, sm: 114 }, // Reduced mobile height
              height: { xs: 90, sm: 114 },
              width: '100%',
              pr: { xs: 1, sm: '10px' }, // Less padding on mobile
              pl: { xs: 1, sm: 2 },
            }}
          >
            {/* Left: hamburger (mobile only) */}
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: { xs: 0.5, sm: 2 }, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>

            {/* Tenant Logo (if available) */}
            {tenant?.logo_url && (
              <Box sx={{
                display: { xs: 'none', sm: 'flex' }, // Hide logo on mobile to save space
                alignItems: 'center',
                mr: 2
              }}>
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
                  gap: { xs: 0.5, sm: 2 }, // Reduced gap on mobile
                  color: 'common.white',
                  '& .MuiTypography-root': { color: 'common.white' },
                  '& .MuiSvgIcon-root': { color: 'common.white' },
                  '& *': { color: 'common.white' },
                }}
              >
                {/* Hide BrandSwitcher for non-Tales products */}
                {currentProduct.id === 'tales' && <BrandSwitcher />}
                <ProductSwitcher />
                <IconButton onClick={handleUserMenuOpen} color="inherit" sx={{ p: 0.5 }}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', color: 'common.white' }}>
                    {user?.email?.charAt(0)?.toUpperCase() || '?'}
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
              <MenuItem onClick={handleDataBatches}>
                <ListItemIcon>
                  <StorageIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Data Batches</ListItemText>
              </MenuItem>
            </>
          )}
          <MenuItem onClick={handleHelp}>
            <ListItemIcon>
              <HelpIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Help & Support</ListItemText>
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
        <Box sx={{
          p: { xs: 2, sm: 3 }, // Less padding on mobile
          flexGrow: 1,
          backgroundColor: 'white',
          width: '100%',
          maxWidth: '100%', // Prevent overflow
          overflowX: 'hidden', // Prevent horizontal scroll
        }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
