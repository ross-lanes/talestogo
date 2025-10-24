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
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  TextFields as QueryIcon,
  Label as DescriptorIcon,
  Groups as CompetitorIcon,
  TrendingUp as TrendingUpIcon,
  Visibility as VisibilityIcon,
  SentimentSatisfied as SentimentIcon,
  Warning as WarningIcon,
  Flag as FlagIcon,
  Storage as DataIcon,
  ChatBubble as ResponseIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 280;

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    {
      text: 'Analytics',
      icon: <AnalyticsIcon />,
      children: [
        { text: 'Positioning', icon: <TrendingUpIcon />, path: '/analytics/positioning' },
        { text: 'Share of Voice', icon: <VisibilityIcon />, path: '/analytics/share-of-voice' },
        { text: 'Descriptors', icon: <DescriptorIcon />, path: '/analytics/descriptors' },
        { text: 'Sentiment', icon: <SentimentIcon />, path: '/analytics/sentiment' },
        { text: 'Threats', icon: <WarningIcon />, path: '/analytics/threats' },
        { text: 'Priorities', icon: <FlagIcon />, path: '/analytics/priorities' },
      ],
    },
    {
      text: 'Data',
      icon: <DataIcon />,
      children: [
        { text: 'Responses', icon: <ResponseIcon />, path: '/data/responses' },
      ],
    },
    {
      text: 'Management',
      icon: <SettingsIcon />,
      children: [
        { text: 'Queries', icon: <QueryIcon />, path: '/manage/queries' },
        { text: 'Descriptors', icon: <DescriptorIcon />, path: '/manage/descriptors' },
        { text: 'Competitors', icon: <CompetitorIcon />, path: '/manage/competitors' },
      ],
    },
  ];

  const drawer = (
    <Box>
      <Toolbar
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          px: 2,
          py: 3,
        }}
      >
        <Box
          component="img"
          src="/pppl-logo.png"
          alt="PPPL Logo"
          sx={{ height: 50, mr: 2 }}
        />
        <Typography variant="h6" noWrap component="div" color="primary" fontWeight={700}>
          AIRO
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <Box key={item.text}>
            {!item.children ? (
              <ListItem disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path!)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'rgba(245, 128, 37, 0.08)',
                      borderLeft: '4px solid',
                      borderLeftColor: 'secondary.main',
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: location.pathname === item.path ? 'secondary.main' : 'inherit' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: location.pathname === item.path ? 700 : 400
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ) : (
              <>
                <ListItem disablePadding>
                  <ListItemButton disabled>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{ fontWeight: 600, fontSize: '0.875rem' }}
                    />
                  </ListItemButton>
                </ListItem>
                {item.children.map((child) => (
                  <ListItem key={child.text} disablePadding>
                    <ListItemButton
                      selected={location.pathname === child.path}
                      onClick={() => navigate(child.path!)}
                      sx={{
                        pl: 4,
                        '&.Mui-selected': {
                          backgroundColor: 'rgba(245, 128, 37, 0.08)',
                          borderLeft: '4px solid',
                          borderLeftColor: 'secondary.main',
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 36,
                          color: location.pathname === child.path ? 'secondary.main' : 'inherit'
                        }}
                      >
                        {child.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={child.text}
                        primaryTypographyProps={{
                          fontSize: '0.875rem',
                          fontWeight: location.pathname === child.path ? 700 : 400
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </>
            )}
          </Box>
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
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AI Reputation Optimizer
          </Typography>
          <Typography variant="body2" color="inherit">
            PPPL Analytics Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
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
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
