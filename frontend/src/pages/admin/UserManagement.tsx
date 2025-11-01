import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material';
import { adminAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface User {
  id: number;
  email: string;
  full_name?: string;
  organization?: string;
  is_admin: boolean;
  is_active: boolean;
  is_invited: boolean;
  invitation_expires_at?: string;
  created_at: string;
}

const UserManagement: React.FC = () => {
  const { isAdmin } = useAuth();

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Invite dialog
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteFullName, setInviteFullName] = useState('');
  const [inviteOrganization, setInviteOrganization] = useState('');

  // Invitation link dialog
  const [inviteLinkDialogOpen, setInviteLinkDialogOpen] = useState(false);
  const [invitationLink, setInvitationLink] = useState('');
  const [invitedUserEmail, setInvitedUserEmail] = useState('');
  const [invitedUserName, setInvitedUserName] = useState('');
  const [linkCopied, setLinkCopied] = useState(false);

  // Edit dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editIsActive, setEditIsActive] = useState(false);
  const [editIsAdmin, setEditIsAdmin] = useState(false);


  useEffect(() => {
    if (isAdmin) {
      loadUsers();
    }
  }, [isAdmin]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.listUsers();
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async () => {
    setError('');
    setSuccess('');

    if (!inviteEmail || !inviteFullName) {
      setError('Email and full name are required');
      return;
    }

    try {
      const response = await adminAPI.createInvitation(inviteEmail, inviteFullName);

      // Show the invitation link dialog
      setInvitationLink(response.invitation_url);
      setInvitedUserEmail(inviteEmail);
      setInvitedUserName(inviteFullName);
      setInviteDialogOpen(false);
      setInviteLinkDialogOpen(true);

      // Reset form
      setInviteEmail('');
      setInviteFullName('');
      setInviteOrganization('');

      loadUsers();
    } catch (err: any) {
      console.error('Failed to create invitation:', err);
      setError(err.response?.data?.detail || 'Failed to create invitation');
    }
  };

  const handleCopyLink = () => {
    const emailMessage = `Hi ${invitedUserName},

You've been invited to join TALES - a platform for tracking and analyzing how AI language models depict your brand.

To get started, simply visit:
${invitationLink}

And sign in with your Google account (${invitedUserEmail}).

Best,
The RobotRachel Team`;

    navigator.clipboard.writeText(emailMessage);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 3000);
  };

  const handleCloseLinkDialog = () => {
    setInviteLinkDialogOpen(false);
    setInvitationLink('');
    setLinkCopied(false);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setEditIsActive(user.is_active);
    setEditIsAdmin(user.is_admin);
    setEditDialogOpen(true);
  };

  const handleSaveUserChanges = async () => {
    if (!editingUser) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.updateUserStatus(editingUser.id, {
        is_active: editIsActive,
        is_admin: editIsAdmin,
      });

      setSuccess(`User ${editingUser.email} updated successfully`);
      setEditDialogOpen(false);
      setEditingUser(null);
      loadUsers();
    } catch (err: any) {
      console.error('Failed to update user:', err);
      setError(err.response?.data?.detail || 'Failed to update user');
    }
  };


  const columns: GridColDef[] = [
    {
      field: 'email',
      headerName: 'Email',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'full_name',
      headerName: 'Full Name',
      flex: 0.8,
      minWidth: 150,
    },
    {
      field: 'organization',
      headerName: 'Organization',
      flex: 0.8,
      minWidth: 150,
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const user = params.row as User;
        if (!user.is_active && user.is_invited) {
          return <Chip label="Pending" color="warning" size="small" />;
        }
        return (
          <Chip
            label={user.is_active ? 'Active' : 'Inactive'}
            color={user.is_active ? 'success' : 'default'}
            size="small"
          />
        );
      },
    },
    {
      field: 'is_admin',
      headerName: 'Admin',
      width: 100,
      renderCell: (params) =>
        params.value ? <Chip label="Admin" color="primary" size="small" /> : null,
    },
    {
      field: 'is_invited',
      headerName: 'Invited',
      width: 100,
      renderCell: (params) =>
        params.value ? <Chip label="Invited" color="info" size="small" /> : null,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <IconButton onClick={() => handleEditUser(params.row as User)} size="small" color="primary">
          <EditIcon />
        </IconButton>
      ),
    },
  ];

  if (!isAdmin) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
        <Alert severity="error">You do not have permission to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setInviteDialogOpen(true)}
        >
          Invite User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Paper elevation={2}>
        <DataGrid
          rows={users}
          columns={columns}
          loading={loading}
          autoHeight
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 10 } },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite New User</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Add a user's email address to the approved list. They can then sign in with their Google account.
          </Typography>

          <TextField
            fullWidth
            label="Email (must be a Gmail address)"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            required
            sx={{ mb: 2, mt: 1 }}
          />

          <TextField
            fullWidth
            label="Full Name"
            value={inviteFullName}
            onChange={(e) => setInviteFullName(e.target.value)}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Organization"
            value={inviteOrganization}
            onChange={(e) => setInviteOrganization(e.target.value)}
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleInviteUser} variant="contained" disabled={!inviteEmail}>
            Add User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User: {editingUser?.email}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={editIsActive}
                  onChange={(e) => setEditIsActive(e.target.checked)}
                />
              }
              label="Active"
            />
            <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Inactive users cannot log in
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={editIsAdmin}
                  onChange={(e) => setEditIsAdmin(e.target.checked)}
                />
              }
              label="Admin"
            />
            <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4 }}>
              Admins can manage users and view all data
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveUserChanges} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invitation Link Dialog */}
      <Dialog open={inviteLinkDialogOpen} onClose={handleCloseLinkDialog} maxWidth="md" fullWidth>
        <DialogTitle>User Added Successfully!</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {invitedUserEmail} has been added to the approved users list. Copy the email message below and send it to them:
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
            <Button
              variant="contained"
              onClick={handleCopyLink}
              fullWidth
              size="large"
            >
              {linkCopied ? 'Copied!' : 'Copy Email Message'}
            </Button>
          </Box>

          <Alert severity="info">
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              Email Template:
            </Typography>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem' }}>
{`Hi ${invitedUserName},

You've been invited to join TALES - a platform for tracking and analyzing how AI language models depict your brand.

To get started, simply visit:
${invitationLink}

And sign in with your Google account (${invitedUserEmail}).

Best,
The RobotRachel Team`}
            </Typography>
          </Alert>

          {linkCopied && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Link copied to clipboard! You can now paste it into your email.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseLinkDialog} variant="contained">
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserManagement;
