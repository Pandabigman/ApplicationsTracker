/**
 * Global test setup for Vitest.
 *
 * Runs before every test file. Sets up:
 * 1. @testing-library/jest-dom matchers (toBeInTheDocument, etc.)
 * 2. MSW server lifecycle (start / reset / stop)
 * 3. Clerk mock (applied globally so all tests see a signed-in user)
 */
import '@testing-library/jest-dom';
import React from 'react';
import { beforeAll, afterAll, afterEach, vi } from 'vitest';

// ---------------------------------------------------------------------------
// framer-motion mock — render motion.* as plain elements with no animations
// so exit-animated elements are removed from the DOM immediately in tests
// ---------------------------------------------------------------------------
vi.mock('framer-motion', () => {
  const createMotionComponent = (tag) =>
    React.forwardRef(({ children, animate, initial, exit, variants, transition, whileHover, whileTap, whileFocus, layout, layoutId, onAnimationComplete, ...props }, ref) =>
      React.createElement(tag, { ...props, ref }, children)
    );
  return {
    motion: new Proxy({}, { get: (_, tag) => createMotionComponent(tag) }),
    AnimatePresence: ({ children }) => children,
  };
});
import { server } from './integration/setup/msw-handlers.js';

// ---------------------------------------------------------------------------
// MSW server
// ---------------------------------------------------------------------------
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// ---------------------------------------------------------------------------
// Clerk mock — all components see a signed-in user in tests
// ---------------------------------------------------------------------------
vi.mock('@clerk/clerk-react', () => ({
  ClerkProvider: ({ children }) => children,
  SignedIn: ({ children }) => children,
  SignedOut: () => null,
  SignIn: () => null,
  SignUp: () => null,
  UserButton: () => null,
  useAuth: vi.fn(() => ({
    getToken: async () => 'mock-clerk-token',
    isSignedIn: true,
    userId: 'user_test_aaaa',
  })),
  useClerk: vi.fn(() => ({
    addListener: vi.fn(() => () => {}),
  })),
}));

// ---------------------------------------------------------------------------
// Suppress noisy console.error output from React in tests
// (e.g. "Warning: An update to ... was not wrapped in act(...)")
// ---------------------------------------------------------------------------
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('act(') || args[0].includes('Warning:'))
    ) {
      return;
    }
    originalError(...args);
  };
});
afterAll(() => {
  console.error = originalError;
});
