import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useAuthStore } from '../../../store/authStore';

// Mock the auth store
jest.mock('../../../store/authStore');

// Create a mock Login component that doesn't require router dependencies
const MockedLogin = React.lazy(() => import('../Login'));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

// Test wrapper with theme only
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <React.Suspense fallback={<div>Loading...</div>}>
        {children}
      </React.Suspense>
    </ThemeProvider>
  );
};

describe('Login Component', () => {
  const mockLogin = jest.fn();
  const mockClearError = jest.fn();
  
  const defaultAuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: mockLogin,
    register: jest.fn(),
    logout: jest.fn(),
    clearError: mockClearError,
    checkAuth: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthStore.mockReturnValue(defaultAuthState);
  });

  describe('Rendering', () => {
    test('should render login form with all elements', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByText('Food Planning App')).toBeInTheDocument();
      expect(screen.getByText('Sign In')).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByText(/don't have an account\? sign up/i)).toBeInTheDocument();
    });

    test('should render link to register page', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const registerLink = screen.getByText(/don't have an account\? sign up/i);
      expect(registerLink.closest('a')).toHaveAttribute('href', '/register');
    });

    test('should focus email field on load', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      expect(emailField).toHaveFocus();
    });
  });

  describe('Form Validation', () => {
    test('should show email required error when email is empty', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
      });
    });

    test('should show password length error when password is too short', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, '123'); // Too short
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
      });
    });

    test('should not show validation errors for valid input', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
        expect(screen.queryByText('Password must be at least 6 characters')).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    test('should call login with correct credentials on valid form submission', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailField, 'user@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'user@example.com',
          password: 'password123',
        });
      });
    });

    test('should clear errors before login attempt', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailField, 'user@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockClearError).toHaveBeenCalled();
      });
    });

    test('should not submit form with invalid data', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      // Should show validation errors but not call login
      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
      });
      
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    test('should show loading state during login', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        isLoading: true,
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /signing in\.\.\./i });
      expect(submitButton).toBeDisabled();
    });

    test('should disable form fields during loading', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        isLoading: true,
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button');
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent('Signing In...');
    });
  });

  describe('Error Display', () => {
    test('should display authentication error', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Invalid credentials',
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError');
    });

    test('should display network error', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Network connection failed',
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    });

    test('should not display error alert when no error', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('should have proper form labels and structure', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      
      expect(emailField).toHaveAttribute('type', 'email');
      expect(emailField).toHaveAttribute('autocomplete', 'email');
      expect(emailField).toBeRequired();
      
      expect(passwordField).toHaveAttribute('type', 'password');
      expect(passwordField).toHaveAttribute('autocomplete', 'current-password');
      expect(passwordField).toBeRequired();
    });

    test('should associate error messages with form fields', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        const emailField = screen.getByLabelText(/email address/i);
        expect(emailField).toHaveAttribute('aria-invalid', 'true');
        expect(emailField).toHaveAccessibleDescription();
      });
    });

    test('should have proper heading hierarchy', () => {
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const mainHeading = screen.getByRole('heading', { level: 1 });
      const subHeading = screen.getByRole('heading', { level: 2 });
      
      expect(mainHeading).toHaveTextContent('Food Planning App');
      expect(subHeading).toHaveTextContent('Sign In');
    });
  });

  describe('Keyboard Navigation', () => {
    test('should support tab navigation through form elements', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Should start with email focused
      expect(emailField).toHaveFocus();
      
      // Tab to password field
      await user.tab();
      expect(passwordField).toHaveFocus();
      
      // Tab to submit button
      await user.tab();
      expect(submitButton).toHaveFocus();
    });

    test('should submit form on Enter key press', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      
      // Press Enter in password field
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });
  });

  describe('Integration with Auth Store', () => {
    test('should react to auth store state changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Initially no error
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();

      // Update mock to return error state
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Login failed',
      });

      rerender(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });

    test('should handle rapid state changes gracefully', async () => {
      const user = userEvent.setup();
      
      // Start with normal state
      const { rerender } = render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      
      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');

      // Switch to loading state
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        isLoading: true,
      });

      rerender(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByRole('button')).toBeDisabled();

      // Switch to error state
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Authentication failed',
      });

      rerender(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      expect(screen.getByText('Authentication failed')).toBeInTheDocument();
      expect(screen.getByRole('button')).not.toBeDisabled();
    });
  });
});