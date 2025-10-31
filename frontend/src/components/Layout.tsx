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
  ChatBubble as ResponseIcon,
  Description as ReportIcon,
  Logout as LogoutIcon,
  AdminPanelSettings as AdminIcon,
  CloudDownload as CollectionIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import BrandSwitcher from './BrandSwitcher';
import talesWhite from './tales_white.png';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

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


  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/', indent: false },
    { text: 'Customize', icon: <CustomizeIcon />, path: '/manage', indent: false },
    { text: 'Data', icon: <CollectionIcon />, path: '/data', indent: false },
    { text: 'Full Analysis', icon: <AnalyticsIcon />, path: '/data-analysis', indent: false },
    { text: 'Positioning', icon: <TrendingUpIcon />, path: '/analytics/positioning', indent: true },
    { text: 'Share of Voice', icon: <VisibilityIcon />, path: '/analytics/share-of-voice', indent: true },
    { text: 'Descriptors', icon: <DescriptorIcon />, path: '/analytics/descriptors', indent: true },
    { text: 'Sentiment', icon: <SentimentIcon />, path: '/analytics/sentiment', indent: true },
    { text: 'Threats', icon: <WarningIcon />, path: '/analytics/threats', indent: true },
    { text: 'Priorities', icon: <FlagIcon />, path: '/analytics/priorities', indent: true },
  ];

  const handleMenuItemClick = (item: any) => {
    if (item.path) {
      navigate(item.path);
    }
  };

  const drawer = (
    <Box>
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
    backgroundColor: '#665775',          // 💜 background color
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
      alt="Tales"
      style={{
        width: 120,
        maxWidth: '100%',
        display: 'block',
        margin: '0 auto',
      }}
    />
    Shape your AI story.
  </Typography>
</Toolbar>

      <Divider />
      <List sx={{ backgroundColor: '#ECE8ED' }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleMenuItemClick(item)}
              sx={{
                pl: item.indent ? 5.75 : 2,
                backgroundColor: '#ECE8ED',
                '&:hover': {
                  backgroundColor: 'rgba(128, 161, 212, 0.2)',
                },
                '&.Mui-selected': {
                  backgroundColor: 'rgba(128, 161, 212, 0.3)',
                  borderLeft: '4px solid',
                  borderLeftColor: 'secondary.main',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'secondary.main', minWidth: 36 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 600 : 400,
                  color: 'text.primary'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', backgroundColor: 'white', minHeight: '100vh' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: 'primary.main',
        }}
      >
<Toolbar
  sx={{
    minHeight: { xs: 106, sm: 114 },
    height: { xs: 106, sm: 114 },
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
  
  {/* Right: group pushed to the far right with ml: 'auto' */}
  {user && (
    <Box
      sx={{
        ml: 'auto',                    // <-- pushes this box to the right
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        color: 'common.white',         // base color for descendants
        // Make sure icons and typography inside are white as well
        '& .MuiTypography-root': { color: 'common.white' },
        '& .MuiSvgIcon-root': { color: 'common.white' },
        // Apply white to any other descendants (BrandSwitcher internals)
        '& *': { color: 'common.white' },
      }}
    >
      {/* BrandSwitcher often renders its own elements — wrapping + descendant selector above forces white */}
      <BrandSwitcher />
      {/* Avatar: keep bg as secondary, but force the letter to be white */}
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
          <MenuItem onClick={handleAdminPanel}>
            <ListItemIcon>
              <AdminIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>User Management</ListItemText>
          </MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
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
              backgroundColor: 'white',
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
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
              backgroundColor: 'white',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 0,
          width: { xs: '100%', sm: `calc(100% - ${drawerWidth}px)` },
          maxWidth: '100vw',
          minHeight: '100vh',
          backgroundColor: 'white',
          boxSizing: 'border-box',
          overflowX: 'hidden',
        }}
      >
        <Toolbar
          sx={{
            minHeight: { xs: 106, sm: 114 },
            height: { xs: 106, sm: 114 },
          }}
        />
        <Box sx={{ p: 3, minHeight: 'calc(100vh - 114px)', backgroundColor: 'white' }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
