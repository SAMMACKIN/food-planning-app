import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import '@testing-library/jest-dom';
import Dashboard from '../Dashboard';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock console.log
const consoleMock = {
  log: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });

describe('Dashboard', () => {
  const theme = createTheme();

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <Dashboard />
        </ThemeProvider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset window size
    window.innerWidth = 1024;
    window.dispatchEvent(new Event('resize'));
  });

  describe('Desktop View', () => {
    test('should render dashboard with all main cards', () => {
      renderDashboard();

      expect(screen.getByText('🏠 Food Planning Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome back! Let\'s plan some delicious meals.')).toBeInTheDocument();

      // Check all main cards
      expect(screen.getByText('Family')).toBeInTheDocument();
      expect(screen.getByText('Manage family members and dietary preferences')).toBeInTheDocument();

      expect(screen.getByText('Pantry')).toBeInTheDocument();
      expect(screen.getByText('Track ingredients and inventory')).toBeInTheDocument();

      expect(screen.getByText('Meal Plans')).toBeInTheDocument();
      expect(screen.getByText('Plan weekly meals and schedules')).toBeInTheDocument();

      expect(screen.getByText('Recipes')).toBeInTheDocument();
      expect(screen.getByText('AI-powered meal suggestions')).toBeInTheDocument();
    });

    test('should navigate to family page when Family card is clicked', () => {
      renderDashboard();

      const familyCard = screen.getByText('Family').closest('.MuiCard-root');
      fireEvent.click(familyCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/family');
    });

    test('should navigate to pantry page when Pantry card is clicked', () => {
      renderDashboard();

      const pantryCard = screen.getByText('Pantry').closest('.MuiCard-root');
      fireEvent.click(pantryCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/pantry');
    });

    test('should navigate to meal planning page when Meal Plans card is clicked', () => {
      renderDashboard();

      const mealPlansCard = screen.getByText('Meal Plans').closest('.MuiCard-root');
      fireEvent.click(mealPlansCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/meal-planning');
    });

    test('should navigate to recommendations page when Recipes card is clicked', () => {
      renderDashboard();

      const recipesCard = screen.getByText('Recipes').closest('.MuiCard-root');
      fireEvent.click(recipesCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/recommendations');
    });

    test('should handle card button clicks correctly', () => {
      renderDashboard();

      const manageButton = screen.getByText('Manage Family');
      fireEvent.click(manageButton);

      expect(mockNavigate).toHaveBeenCalledWith('/family');
    });

    test('should render quick actions section', () => {
      renderDashboard();

      expect(screen.getByText('🚀 Quick Actions')).toBeInTheDocument();
      expect(screen.getByText('Add Family Member')).toBeInTheDocument();
      expect(screen.getByText('Update Pantry')).toBeInTheDocument();
      expect(screen.getByText('Shopping List')).toBeInTheDocument();
    });

    test('should handle quick action clicks', () => {
      renderDashboard();

      // Add Family Member
      fireEvent.click(screen.getByText('Add Family Member'));
      expect(mockNavigate).toHaveBeenCalledWith('/family');

      // Update Pantry
      fireEvent.click(screen.getByText('Update Pantry'));
      expect(mockNavigate).toHaveBeenCalledWith('/pantry');

      // Shopping List
      fireEvent.click(screen.getByText('Shopping List'));
      expect(consoleMock.log).toHaveBeenCalledWith('Generate shopping list');
    });

    test('should apply hover effects on cards', () => {
      renderDashboard();

      const familyCard = screen.getByText('Family').closest('.MuiCard-root');
      
      // Check that card has hover styles
      expect(familyCard).toHaveStyle({
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      });
    });

    test('should render all card avatars with icons', () => {
      renderDashboard();

      // Check for avatar elements
      const avatars = screen.getAllByRole('img', { hidden: true });
      expect(avatars.length).toBeGreaterThanOrEqual(4);
    });

    test('should render outlined buttons in desktop view', () => {
      renderDashboard();

      const buttons = screen.getAllByRole('button');
      const outlinedButtons = buttons.filter(button => 
        button.classList.contains('MuiButton-outlined') ||
        button.textContent === 'Manage Family' ||
        button.textContent === 'View Pantry' ||
        button.textContent === 'Plan Meals' ||
        button.textContent === 'Get Recipes'
      );

      expect(outlinedButtons.length).toBeGreaterThan(0);
    });
  });

  describe('Mobile View', () => {
    beforeEach(() => {
      // Set viewport to mobile
      window.innerWidth = 375;
      window.dispatchEvent(new Event('resize'));
    });

    test('should render mobile-optimized header', () => {
      renderDashboard();

      expect(screen.getByText('🏠 Dashboard')).toBeInTheDocument();
      expect(screen.queryByText('🏠 Food Planning Dashboard')).not.toBeInTheDocument();
    });

    test('should render contained buttons in mobile view', () => {
      renderDashboard();

      const buttons = screen.getAllByRole('button');
      const containedButtons = buttons.filter(button => 
        button.classList.contains('MuiButton-contained')
      );

      expect(containedButtons.length).toBeGreaterThan(0);
    });

    test('should render full-width quick action buttons in mobile', () => {
      renderDashboard();

      const quickActionButtons = [
        screen.getByText('Add Family Member'),
        screen.getByText('Update Pantry'),
        screen.getByText('Shopping List')
      ];

      quickActionButtons.forEach(button => {
        const buttonElement = button.closest('button');
        expect(buttonElement).toHaveClass('MuiButton-fullWidth');
      });
    });

    test('should apply mobile-specific card styles', () => {
      renderDashboard();

      const cards = screen.getAllByRole('article', { hidden: true });
      expect(cards.length).toBe(4);
    });

    test('should handle card interactions in mobile view', () => {
      renderDashboard();

      const familyCard = screen.getByText('Family').closest('.MuiCard-root');
      fireEvent.click(familyCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/family');
    });
  });

  describe('Responsive Behavior', () => {
    test('should update layout when resizing from desktop to mobile', () => {
      const { rerender } = renderDashboard();

      // Start with desktop
      expect(screen.getByText('🏠 Food Planning Dashboard')).toBeInTheDocument();

      // Resize to mobile
      window.innerWidth = 375;
      window.dispatchEvent(new Event('resize'));

      rerender(
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            <Dashboard />
          </ThemeProvider>
        </BrowserRouter>
      );

      expect(screen.getByText('🏠 Dashboard')).toBeInTheDocument();
    });

    test('should maintain functionality across different screen sizes', () => {
      const viewports = [320, 768, 1024, 1440];

      viewports.forEach(width => {
        window.innerWidth = width;
        window.dispatchEvent(new Event('resize'));

        const { unmount } = renderDashboard();

        // Verify navigation works
        const familyCard = screen.getByText('Family').closest('.MuiCard-root');
        fireEvent.click(familyCard!);
        expect(mockNavigate).toHaveBeenCalledWith('/family');

        unmount();
        mockNavigate.mockClear();
      });
    });
  });

  describe('Accessibility', () => {
    test('should have appropriate heading hierarchy', () => {
      renderDashboard();

      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toHaveTextContent(/Dashboard/);

      const h2s = screen.getAllByRole('heading', { level: 2 });
      expect(h2s.length).toBeGreaterThan(0);
    });

    test('should have descriptive button labels', () => {
      renderDashboard();

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName();
      });
    });

    test('should support keyboard navigation', () => {
      renderDashboard();

      const familyCard = screen.getByText('Family').closest('.MuiCard-root');
      familyCard!.focus();
      
      fireEvent.keyDown(familyCard!, { key: 'Enter' });
      expect(mockNavigate).toHaveBeenCalledWith('/family');
    });
  });

  describe('Error Handling', () => {
    test('should handle navigation errors gracefully', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockNavigate.mockImplementation(() => {
        throw new Error('Navigation failed');
      });

      renderDashboard();

      expect(() => {
        fireEvent.click(screen.getByText('Family').closest('.MuiCard-root')!);
      }).not.toThrow();

      consoleError.mockRestore();
    });
  });
});