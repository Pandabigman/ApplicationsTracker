/**
 * Clerk mock for E2E tests.
 *
 * This file is aliased in place of @clerk/clerk-react by vite.config.e2e.js.
 * Every hook returns a fully-signed-in user so ProtectedRoute always renders
 * the page content and the real Clerk SDK (and its JWKS/session calls) is
 * never loaded.
 */

// Pass-through provider — ignores publishableKey
export function ClerkProvider({ children }) {
  return children;
}

// Always signed in: render children
export function SignedIn({ children }) {
  return children;
}

// Never signed out: render nothing
export function SignedOut() {
  return null;
}

// These won't render (SignedOut is null), but must be exported
export function SignIn() {
  return null;
}

export function SignUp() {
  return null;
}

// Minimal user button placeholder
export function UserButton() {
  return null;
}

// auth hook — always signed in, returns a fake token that the stubbed API accepts
export function useAuth() {
  return {
    getToken: async () => 'e2e-mock-jwt-token',
    isSignedIn: true,
    userId: 'user_e2e_test_aaaa',
  };
}

// clerk instance hook — stub the listener used in AuthSetup
export function useClerk() {
  return {
    addListener: () => () => {},
  };
}
