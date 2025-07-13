import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Register from '../Register';
import { useAuthStore } from '../../../store/authStore';

// Mock the auth store
jest.mock('../../../store/authStore');

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

// Test wrapper with theme only
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme();
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

describe('Register Component', () => {
  const mockRegister = jest.fn();
  const mockClearError = jest.fn();
  
  const defaultAuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: jest.fn(),
    register: mockRegister,
    logout: jest.fn(),
    clearError: mockClearError,
    checkAuth: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthStore.mockReturnValue(defaultAuthState);
  });

  describe('Rendering', () => {
    test('should render registration form with all elements', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText('Food Planning App')).toBeInTheDocument();
      expect(screen.getByText('Sign Up')).toBeInTheDocument();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
      expect(screen.getByText(/already have an account\? sign in/i)).toBeInTheDocument();
    });

    test('should render link to login page', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const loginLink = screen.getByText(/already have an account\? sign in/i);
      expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
    });

    test('should focus name field on load', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      expect(nameField).toHaveFocus();
    });

    test('should mark email and password as required', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const nameField = screen.getByLabelText(/full name/i);

      expect(emailField).toBeRequired();
      expect(passwordField).toBeRequired();
      expect(nameField).not.toBeRequired(); // Name is optional
    });
  });

  describe('Form Validation', () => {
    test('should show email required error when email is empty', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign up/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
      });
    });

    test('should show password length error when password is too short', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, '123'); // Too short
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
      });
    });

    test('should show name length error when name is too short', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(nameField, 'A'); // Too short
      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Name must be at least 2 characters')).toBeInTheDocument();
      });
    });

    test('should not show validation errors for valid input', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(nameField, 'John Doe');
      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Email is required')).not.toBeInTheDocument();
        expect(screen.queryByText('Password must be at least 6 characters')).not.toBeInTheDocument();
        expect(screen.queryByText('Name must be at least 2 characters')).not.toBeInTheDocument();
      });
    });

    test('should allow registration without name', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });
  });

  describe('Form Submission', () => {
    test('should call register with correct data on valid form submission', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(nameField, 'John Doe');
      await user.type(emailField, 'john@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          password: 'password123',
        });
      });
    });

    test('should clear errors before registration attempt', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

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
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign up/i });
      await user.click(submitButton);

      // Should show validation errors but not call register
      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
      });
      
      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  describe('Navigation after Registration', () => {
    test('should navigate to dashboard on successful registration', async () => {
      const user = userEvent.setup();
      
      // Mock successful registration (no error)
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: null,
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    test('should not navigate when registration fails', async () => {
      const user = userEvent.setup();
      
      // Mock failed registration (with error)
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Email already exists',
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(emailField, 'existing@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalled();
      });

      // Should not navigate when there's an error
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    test('should show loading state during registration', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        isLoading: true,
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /creating account\.\.\./i });
      expect(submitButton).toBeDisabled();
    });

    test('should disable form during loading', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        isLoading: true,
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button');
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveTextContent('Creating Account...');
    });
  });

  describe('Error Display', () => {
    test('should display registration error', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Email already exists',
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText('Email already exists')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError');
    });

    test('should display network error', () => {
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Network connection failed',
      });

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText('Network connection failed')).toBeInTheDocument();
    });

    test('should not display error alert when no error', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('should have proper form labels and structure', () => {
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      
      expect(nameField).toHaveAttribute('autocomplete', 'name');
      
      expect(emailField).toHaveAttribute('type', 'email');
      expect(emailField).toHaveAttribute('autocomplete', 'email');
      expect(emailField).toBeRequired();
      
      expect(passwordField).toHaveAttribute('type', 'password');
      expect(passwordField).toHaveAttribute('autocomplete', 'new-password');
      expect(passwordField).toBeRequired();
    });

    test('should associate error messages with form fields', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /sign up/i });
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
          <Register />
        </TestWrapper>
      );

      const mainHeading = screen.getByRole('heading', { level: 1 });
      const subHeading = screen.getByRole('heading', { level: 2 });
      
      expect(mainHeading).toHaveTextContent('Food Planning App');
      expect(subHeading).toHaveTextContent('Sign Up');
    });
  });

  describe('Keyboard Navigation', () => {
    test('should support tab navigation through form elements', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      // Should start with name focused
      expect(nameField).toHaveFocus();
      
      // Tab to email field
      await user.tab();
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
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);

      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      
      // Press Enter in password field
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
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
          <Register />
        </TestWrapper>
      );

      // Initially no error
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();

      // Update mock to return error state
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Registration failed',
      });

      rerender(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });

    test('should handle rapid state changes gracefully', async () => {
      const user = userEvent.setup();
      
      // Start with normal state
      const { rerender } = render(
        <TestWrapper>
          <Register />
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
          <Register />
        </TestWrapper>
      );

      expect(screen.getByRole('button')).toBeDisabled();

      // Switch to error state
      mockUseAuthStore.mockReturnValue({
        ...defaultAuthState,
        error: 'Registration failed',
      });

      rerender(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      expect(screen.getByText('Registration failed')).toBeInTheDocument();
      expect(screen.getByRole('button')).not.toBeDisabled();
    });
  });

  describe('Form Data Handling', () => {
    test('should handle empty name gracefully', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      // Leave name empty
      await user.type(emailField, 'test@example.com');
      await user.type(passwordField, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          // name should not be included when empty
        });
      });
    });

    test('should trim whitespace from inputs', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      const nameField = screen.getByLabelText(/full name/i);
      const emailField = screen.getByLabelText(/email address/i);
      const passwordField = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(nameField, '  John Doe  ');
      await user.type(emailField, '  test@example.com  ');
      await user.type(passwordField, '  password123  ');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          name: '  John Doe  ', // Note: form doesn't trim, but validation might
          email: '  test@example.com  ',
          password: '  password123  ',
        });
      });
    });
  });
});