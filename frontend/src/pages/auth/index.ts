/**
 * Barrel export for all auth pages.
 *
 * This allows imports like:
 *   import { Login, Register, InviteAccept } from '@/pages/auth'
 *
 * Instead of:
 *   import Login from '@/pages/auth/Login'
 *   import Register from '@/pages/auth/Register'
 *   import InviteAccept from '@/pages/auth/InviteAccept'
 */

export { default as InviteAccept } from './InviteAccept';
export { default as Login } from './Login';
export { default as Register } from './Register';
