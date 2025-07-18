import React from 'react';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import SavedRecipes from '../SavedRecipes';
import { useRecipes } from '../../../hooks/useRecipes';
import { useAuthStore } from '../../../store/authStore';
import { apiRequest } from '../../../services/api';

// Mock dependencies
jest.mock('../../../hooks/useRecipes');
jest.mock('../../../store/authStore');
jest.mock('../../../services/api');

// Mock recipe components
jest.mock('../../../components/Recipe/RecipeInstructions', () => {
  return function MockRecipeInstructions({ instructions, prepTime }: { instructions: string[]; prepTime: number }) {
    return (
      <div data-testid="recipe-instructions">
        <div>Prep time: {prepTime} minutes</div>
        {instructions.map((instruction, index) => (
          <div key={index}>{instruction}</div>
        ))}
      </div>
    );
  };
});

jest.mock('../../../components/Recipe/CreateRecipeForm', () => {
  return function MockCreateRecipeForm({ open, onClose, onSave, initialData, isEdit }: any) {
    if (!open) return null;
    return (
      <div data-testid="create-recipe-form">
        <div>{isEdit ? 'Edit Recipe' : 'Create Recipe'}</div>
        <button onClick={() => onSave({ name: initialData?.name || 'New Recipe' })}>
          Save Recipe
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

jest.mock('../../../components/Recipe/RateRecipeDialog', () => {
  return function MockRateRecipeDialog({ open, onClose, onSubmit }: any) {
    if (!open) return null;
    return (
      <div data-testid="rate-recipe-dialog">
        <button onClick={() => onSubmit({ rating: 5, review_text: 'Great!' })}>
          Submit Rating
        </button>
        <button onClick={onClose}>Close</button>
      </div>
    );
  };
});

const mockUseRecipes = useRecipes as jest.MockedFunction<typeof useRecipes>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

// Mock data
const mockRecipes = [
  {
    id: '1',
    user_id: 'user1',
    name: 'Pasta Carbonara',
    description: 'Classic Italian pasta',
    prep_time: 30,
    difficulty: 'medium',
    servings: 4,
    ingredients_needed: [
      { name: 'pasta', quantity: '400g', unit: 'g', have_in_pantry: true },
      { name: 'eggs', quantity: '4', unit: 'pieces', have_in_pantry: false },
    ],
    instructions: ['Cook pasta', 'Make sauce', 'Combine'],
    tags: ['italian', 'pasta'],
    nutrition_notes: 'High protein',
    pantry_usage_score: 0.8,
    ai_generated: true,
    ai_provider: 'claude',
    source: 'ai',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    user_id: 'user1',
    name: 'Chicken Salad',
    description: 'Fresh and healthy',
    prep_time: 15,
    difficulty: 'easy',
    servings: 2,
    ingredients_needed: [
      { name: 'chicken', quantity: '200g', unit: 'g', have_in_pantry: false },
      { name: 'lettuce', quantity: '1', unit: 'head', have_in_pantry: true },
    ],
    instructions: ['Prepare chicken', 'Mix with vegetables'],
    tags: ['healthy', 'salad'],
    nutrition_notes: 'Low carb',
    pantry_usage_score: 0.5,
    ai_generated: false,
    source: 'manual',
    created_at: '2024-01-14T10:00:00Z',
    updated_at: '2024-01-14T10:00:00Z'
  }
];

const mockRating = {
  id: 'rating1',
  recipe_id: '1',
  user_id: 'user1',
  rating: 5,
  review_text: 'Excellent recipe!',
  would_make_again: true,
  cooking_notes: 'Perfect timing',
  created_at: '2024-01-15T12:00:00Z',
  updated_at: '2024-01-15T12:00:00Z'
};

describe('SavedRecipes', () => {
  const mockRecipeHooks = {
    savedRecipes: mockRecipes,
    loading: false,
    error: null,
    fetchSavedRecipes: jest.fn(),
    deleteRecipe: jest.fn(),
    saveRecipe: jest.fn(),
    updateRecipe: jest.fn(),
    createRecipeRating: jest.fn(),
    getRecipeRatings: jest.fn(),
    updateRecipeRating: jest.fn(),
    clearError: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseRecipes.mockReturnValue(mockRecipeHooks);
    mockUseAuthStore.mockReturnValue({
      user: { id: 'user1', email: 'test@example.com' },
      isAuthenticated: true,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      checkAuth: jest.fn(),
      clearError: jest.fn(),
      loading: false,
      error: null,
    });
    // Mock the health check API call to resolve immediately
    mockApiRequest.mockImplementation((method, endpoint) => {
      if (endpoint === '/recipes/debug/health') {
        return Promise.resolve({ user_recipe_count: 2, status: 'healthy' });
      }
      return Promise.resolve({});
    });
  });

  const renderSavedRecipes = async () => {
    let result;
    await act(async () => {
      result = render(<SavedRecipes />);
    });
    // Wait for the health check to complete
    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/recipes/debug/health');
    });
    return result!;
  };

  describe('Component Rendering', () => {
    test('should render saved recipes page', async () => {
      await renderSavedRecipes();

      expect(screen.getByText('Saved Recipes')).toBeInTheDocument();
      expect(screen.getByText('Pasta Carbonara')).toBeInTheDocument();
      expect(screen.getByText('Chicken Salad')).toBeInTheDocument();
    });

    test('should display loading state', async () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        loading: true,
        savedRecipes: [],
      });

      await renderSavedRecipes();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('should display error state', async () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        error: 'Failed to load recipes',
        savedRecipes: [],
      });

      await renderSavedRecipes();
      expect(screen.getByText('Failed to load recipes')).toBeInTheDocument();
    });

    test('should display empty state when no recipes', async () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        savedRecipes: [],
      });

      await renderSavedRecipes();
      expect(screen.getByText("You haven't saved any recipes yet. Go to Recommendations to find and save some recipes!")).toBeInTheDocument();
    });

    test('should display recipe cards with correct information', async () => {
      await renderSavedRecipes();

      // Check Pasta Carbonara card
      const pastaCard = screen.getByText('Pasta Carbonara').closest('[class*="MuiCard"]');
      expect(within(pastaCard!).getByText('Classic Italian pasta')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('30 min')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('4 servings')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('medium')).toBeInTheDocument();

      // Check AI badge
      expect(within(pastaCard!).getByText('Claude AI')).toBeInTheDocument();
    });

    test('should display health status', async () => {
      await renderSavedRecipes();

      await waitFor(() => {
        expect(screen.getByText(/✅ Healthy - 2 recipes found/)).toBeInTheDocument();
      });
    });
  });

  describe('Recipe Actions', () => {
    test('should open recipe details dialog when View is clicked', async () => {
      await renderSavedRecipes();

      const viewButtons = screen.getAllByText('View Recipe');
      fireEvent.click(viewButtons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('recipe-instructions')).toBeInTheDocument();
        // Verify the RecipeInstructions component receives correct props
        expect(screen.getByText('Prep time: 30 minutes')).toBeInTheDocument();
        expect(screen.getByText('Cook pasta')).toBeInTheDocument();
      });
    });

    test('should open menu when more options button is clicked', async () => {
      await renderSavedRecipes();

      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      
      fireEvent.click(moreButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
        expect(screen.getByText('Rate Recipe')).toBeInTheDocument();
        expect(screen.getByText('Delete Recipe')).toBeInTheDocument();
      });
    });

    test('should delete recipe when delete is confirmed', async () => {
      mockRecipeHooks.deleteRecipe.mockResolvedValue(true);
      await renderSavedRecipes();

      // Open menu
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      // Click delete
      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete Recipe'));
      });

      expect(mockRecipeHooks.deleteRecipe).toHaveBeenCalledWith('1');
    });

    test('should open edit dialog when Edit Recipe is clicked', async () => {
      await renderSavedRecipes();

      // Open menu
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      // Click edit
      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit Recipe'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
    });

    test('should open rating dialog when Rate Recipe is clicked', async () => {
      mockRecipeHooks.getRecipeRatings.mockResolvedValue([]);
      await renderSavedRecipes();

      // Open menu
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      // Click rate
      await waitFor(() => {
        fireEvent.click(screen.getByText('Rate Recipe'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('rate-recipe-dialog')).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filtering', () => {
    test('should search recipes by name', async () => {
      await renderSavedRecipes();

      const searchInput = screen.getByLabelText('Search recipes');
      fireEvent.change(searchInput, { target: { value: 'pasta' } });

      // Trigger search
      fireEvent.click(screen.getByText('Search'));

      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalledWith('pasta', '');
    });

    test('should filter recipes by difficulty', async () => {
      await renderSavedRecipes();

      // Find the select element by its role
      const difficultySelect = screen.getByRole('combobox');
      fireEvent.mouseDown(difficultySelect);

      // Wait for listbox to appear
      await waitFor(() => {
        const listbox = screen.getByRole('listbox');
        expect(listbox).toBeInTheDocument();
      });

      // Select Easy option
      const listbox = screen.getByRole('listbox');
      const easyOption = within(listbox).getByText('Easy');
      fireEvent.click(easyOption);

      // The filter triggers immediately on selection
      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalledWith('', 'Easy');
    });

    test('should clear error when clear error button is clicked', async () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        error: 'Some error',
      });

      await renderSavedRecipes();

      // Find the error alert specifically by looking for the error text
      const errorAlert = screen.getByText('Some error').closest('[role="alert"]');
      expect(errorAlert).toBeInTheDocument();
      
      // Find the close button within the error alert
      const closeButton = within(errorAlert!).getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      expect(mockRecipeHooks.clearError).toHaveBeenCalled();
    });

    test('should refresh recipes when refresh button is clicked', async () => {
      await renderSavedRecipes();

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalled();
    });
  });

  describe('Recipe Creation', () => {
    test('should open create recipe dialog when Create Recipe button is clicked', async () => {
      await renderSavedRecipes();

      // Find the Create Recipe button (not the dialog title)
      const createButtons = screen.getAllByText('Create Recipe');
      const createButton = createButtons[0]; // The button in the header
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
        // Check for the presence of the form, not the duplicate text
        expect(screen.getByText('Save Recipe')).toBeInTheDocument();
      });
    });

    test('should save new recipe when form is submitted', async () => {
      mockRecipeHooks.saveRecipe.mockResolvedValue(mockRecipes[0]);
      await renderSavedRecipes();

      // Open create dialog
      const createButton = screen.getByText('Create Recipe');
      fireEvent.click(createButton);

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
      });

      // Submit form
      const saveButton = screen.getByText('Save Recipe');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockRecipeHooks.saveRecipe).toHaveBeenCalled();
      });
    });

    test('should update existing recipe when edit form is submitted', async () => {
      mockRecipeHooks.updateRecipe.mockResolvedValue(mockRecipes[0]);
      await renderSavedRecipes();

      // Open menu and edit
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit Recipe'));
      });

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
      });

      // Submit form
      const saveButton = screen.getByText('Save Recipe');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockRecipeHooks.updateRecipe).toHaveBeenCalled();
      });
    });
  });

  describe('Recipe Rating', () => {
    test('should create new rating when submitted', async () => {
      mockRecipeHooks.getRecipeRatings.mockResolvedValue([]);
      mockRecipeHooks.createRecipeRating.mockResolvedValue(mockRating);
      await renderSavedRecipes();

      // Open menu and rate
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Rate Recipe'));
      });

      // Submit rating
      await waitFor(() => {
        const submitButton = screen.getByText('Submit Rating');
        fireEvent.click(submitButton);
      });

      expect(mockRecipeHooks.createRecipeRating).toHaveBeenCalledWith('1', {
        rating: 5,
        review_text: 'Great!'
      });
    });

    test('should update existing rating when user has already rated', async () => {
      mockRecipeHooks.getRecipeRatings.mockResolvedValue([mockRating]);
      mockRecipeHooks.updateRecipeRating.mockResolvedValue(mockRating);
      await renderSavedRecipes();

      // Open menu and rate
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Rate Recipe'));
      });

      // Submit rating update
      await waitFor(() => {
        const submitButton = screen.getByText('Submit Rating');
        fireEvent.click(submitButton);
      });

      expect(mockRecipeHooks.updateRecipeRating).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      mockApiRequest.mockRejectedValue(new Error('Network error'));
      await renderSavedRecipes();

      await waitFor(() => {
        expect(screen.getByText(/❌ Unhealthy - Network Error/)).toBeInTheDocument();
      });
    });

    test('should handle recipe deletion errors', async () => {
      mockRecipeHooks.deleteRecipe.mockResolvedValue(false);
      await renderSavedRecipes();

      // Try to delete a recipe
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete Recipe'));
      });

      expect(mockRecipeHooks.deleteRecipe).toHaveBeenCalled();
    });
  });

  describe('Responsive Design', () => {
    test('should render grid layout properly', async () => {
      await renderSavedRecipes();

      // Check for the grid container by its class or structure
      const gridElements = document.querySelectorAll('[class*="Grid"]');
      expect(gridElements.length).toBeGreaterThan(0);
    });

    test('should handle mobile view', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      window.dispatchEvent(new Event('resize'));

      await renderSavedRecipes();

      // Component should still render without errors
      expect(screen.getByText('Saved Recipes')).toBeInTheDocument();
    });
  });

  describe('Dialog Management', () => {
    test('should close recipe details dialog when backdrop is clicked', async () => {
      await renderSavedRecipes();

      // Open dialog
      const viewButton = screen.getAllByText('View Recipe')[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(screen.getByTestId('recipe-instructions')).toBeInTheDocument();
      });

      // Since we're testing the real Dialog component, find and click the close button
      const closeButton = screen.getByText('Close');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('recipe-instructions')).not.toBeInTheDocument();
      });
    });

    test('should close menus when clicking away', async () => {
      await renderSavedRecipes();

      // Open menu
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });

      // Find and click the MUI backdrop to close menu
      const backdrop = document.querySelector('.MuiBackdrop-root');
      if (backdrop) {
        fireEvent.click(backdrop);
      } else {
        // Fallback: press Escape key to close menu
        fireEvent.keyDown(document.body, { key: 'Escape', code: 'Escape' });
      }

      await waitFor(() => {
        expect(screen.queryByText('Edit Recipe')).not.toBeInTheDocument();
      });
    });
  });
});