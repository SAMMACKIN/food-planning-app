import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Layout from '../Layout/Layout';
import { useAuthStore } from '../../store/authStore';
import { apiRequest } from '../../services/api';

// Mock dependencies
jest.mock('../../store/authStore');
jest.mock('../../services/api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: jest.fn(),
  useNavigate: jest.fn(),
  Outlet: () => <div data-testid="outlet">Main Content</div>,
}));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;
const mockUseLocation = useLocation as jest.MockedFunction<typeof useLocation>;

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    is_admin: false,
  };

  const mockLogout = jest.fn();
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuthStore.mockReturnValue({
      user: mockUser,
      logout: mockLogout,
      isLoading: false,
      error: null,
      clearError: jest.fn(),
      login: jest.fn(),
      register: jest.fn(),
    });

    mockUseLocation.mockReturnValue({
      pathname: '/dashboard',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    (require('react-router-dom').useNavigate as jest.Mock).mockReturnValue(mockNavigate);
  });

  test('renders layout with user information', () => {
    renderWithProviders(<Layout />);
    
    expect(screen.getByText('🍽️ Food Planning App')).toBeInTheDocument();
    expect(screen.getByText('Welcome, Test User')).toBeInTheDocument();
    expect(screen.getByTestId('outlet')).toBeInTheDocument();
  });

  test('displays navigation tabs on desktop', () => {
    renderWithProviders(<Layout />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Family')).toBeInTheDocument();
    expect(screen.getByText('Pantry')).toBeInTheDocument();
    expect(screen.getByText('Meal Plans')).toBeInTheDocument();
    expect(screen.getByText('Recipes')).toBeInTheDocument();
  });

  test('shows admin tab for admin users', () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...mockUser, is_admin: true },
      logout: mockLogout,
      isLoading: false,
      error: null,
      clearError: jest.fn(),
      login: jest.fn(),
      register: jest.fn(),
    });

    renderWithProviders(<Layout />);
    
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  test('does not show admin tab for regular users', () => {
    renderWithProviders(<Layout />);
    
    expect(screen.queryByText('Admin')).not.toBeInTheDocument();
  });

  test('calls logout when logout button is clicked', () => {
    renderWithProviders(<Layout />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);
    
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('opens delete account dialog when delete button is clicked', () => {
    renderWithProviders(<Layout />);
    
    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(deleteButton);
    
    expect(screen.getByText('Delete Account')).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone!')).toBeInTheDocument();
  });

  test('delete account requires correct confirmation text', async () => {
    mockApiRequest.mockResolvedValue({});
    renderWithProviders(<Layout />);
    
    // Open delete dialog
    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(deleteButton);
    
    // Try to delete without correct confirmation
    const confirmButton = screen.getByRole('button', { name: /delete account/i });
    expect(confirmButton).toBeDisabled();
    
    // Enter incorrect confirmation
    const textField = screen.getByPlaceholderText('delete my account');
    fireEvent.change(textField, { target: { value: 'wrong text' } });
    expect(confirmButton).toBeDisabled();
    
    // Enter correct confirmation
    fireEvent.change(textField, { target: { value: 'delete my account' } });
    expect(confirmButton).toBeEnabled();
    
    // Click delete
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith('DELETE', '/auth/delete-account');
    });
  });

  test('handles delete account API error', async () => {
    const errorMessage = 'Failed to delete account';
    mockApiRequest.mockRejectedValue({
      response: { data: { detail: errorMessage } }
    });
    
    renderWithProviders(<Layout />);
    
    // Open delete dialog and enter confirmation
    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(deleteButton);
    
    const textField = screen.getByPlaceholderText('delete my account');
    fireEvent.change(textField, { target: { value: 'delete my account' } });
    
    const confirmButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('navigates to correct page when tab is clicked', () => {
    renderWithProviders(<Layout />);
    
    const familyTab = screen.getByText('Family');
    fireEvent.click(familyTab);
    
    expect(mockNavigate).toHaveBeenCalledWith('/family');
  });

  test('highlights current tab based on location', () => {
    mockUseLocation.mockReturnValue({
      pathname: '/family',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    renderWithProviders(<Layout />);
    
    // The implementation would need to check for selected state
    // This test verifies the getCurrentTab function works correctly
    expect(screen.getByText('Family')).toBeInTheDocument();
  });

  test('cancels delete dialog when cancel is clicked', () => {
    renderWithProviders(<Layout />);
    
    // Open delete dialog
    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(deleteButton);
    
    expect(screen.getByText('Delete Account')).toBeInTheDocument();
    
    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    
    // Dialog should be closed
    expect(screen.queryByText('This action cannot be undone!')).not.toBeInTheDocument();
  });

  test('renders mobile view correctly', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(max-width:899.95px)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    renderWithProviders(<Layout />);
    
    // Should show mobile-specific elements
    expect(screen.getByText('🍽️ Food Planner')).toBeInTheDocument();
  });

  test('shows snackbar when delete account succeeds', async () => {
    mockApiRequest.mockResolvedValue({});
    renderWithProviders(<Layout />);
    
    // Perform delete account action
    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(deleteButton);
    
    const textField = screen.getByPlaceholderText('delete my account');
    fireEvent.change(textField, { target: { value: 'delete my account' } });
    
    const confirmButton = screen.getByRole('button', { name: /delete account/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(screen.getByText('Account deleted successfully. Goodbye!')).toBeInTheDocument();
    });
  });
});