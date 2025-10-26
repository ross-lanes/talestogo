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
        }}
      >
        <img
          src="/airologopurple.png"
          alt="AIRO Logo"
          style={{ height: '40px', width: 'auto' }}
        />
        <Typography
          variant="body2"
          component="div"
          color="text.secondary"
          sx={{
            textAlign: 'center',
            fontSize: '0.875rem',
            fontStyle: 'italic',
            lineHeight: 1.3,
          }}
        >
          See your brand through<br />the eyes of AIs
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleMenuItemClick(item)}
              sx={{
                pl: item.indent ? 5.75 : 2,
                '&:hover': {
                  backgroundColor: 'rgba(128, 161, 212, 0.08)',
                },
                '&.Mui-selected': {
                  backgroundColor: 'rgba(128, 161, 212, 0.12)',
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
    <Box sx={{ display: 'flex' }}>
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
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h4" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            AI Reputation Optimizer
          </Typography>

          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2" color="inherit" sx={{ display: { xs: 'none', md: 'block' } }}>
                {user.organization || user.email}
              </Typography>
              {isAdmin && (
                <Chip
                  label="Admin"
                  size="small"
                  color="secondary"
                  sx={{ display: { xs: 'none', sm: 'flex' } }}
                />
              )}

              <IconButton
                onClick={handleUserMenuOpen}
                color="inherit"
                sx={{ p: 0.5 }}
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
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
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar
          sx={{
            minHeight: { xs: 106, sm: 114 },
            height: { xs: 106, sm: 114 },
          }}
        />
        {children}
      </Box>
    </Box>
  );
}
