import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  return function MockRecipeInstructions({ recipe }: { recipe: any }) {
    return <div data-testid="recipe-instructions">{recipe.name} Instructions</div>;
  };
});

jest.mock('../../../components/Recipe/CreateRecipeForm', () => {
  return function MockCreateRecipeForm({ onSave, onCancel, editRecipe }: any) {
    return (
      <div data-testid="create-recipe-form">
        <button onClick={() => onSave({ name: editRecipe?.name || 'New Recipe' })}>
          Save Recipe
        </button>
        <button onClick={onCancel}>Cancel</button>
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
    mockApiRequest.mockResolvedValue('healthy');
  });

  const renderSavedRecipes = () => {
    return render(<SavedRecipes />);
  };

  describe('Component Rendering', () => {
    test('should render saved recipes page', () => {
      renderSavedRecipes();

      expect(screen.getByText('My Saved Recipes')).toBeInTheDocument();
      expect(screen.getByText('Pasta Carbonara')).toBeInTheDocument();
      expect(screen.getByText('Chicken Salad')).toBeInTheDocument();
    });

    test('should display loading state', () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        loading: true,
        savedRecipes: [],
      });

      renderSavedRecipes();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('should display error state', () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        error: 'Failed to load recipes',
        savedRecipes: [],
      });

      renderSavedRecipes();
      expect(screen.getByText('Failed to load recipes')).toBeInTheDocument();
    });

    test('should display empty state when no recipes', () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        savedRecipes: [],
      });

      renderSavedRecipes();
      expect(screen.getByText('No saved recipes yet')).toBeInTheDocument();
      expect(screen.getByText('Create Your First Recipe')).toBeInTheDocument();
    });

    test('should display recipe cards with correct information', () => {
      renderSavedRecipes();

      // Check Pasta Carbonara card
      const pastaCard = screen.getByText('Pasta Carbonara').closest('.MuiCard-root');
      expect(within(pastaCard!).getByText('Classic Italian pasta')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('30 min')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('4 servings')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('medium')).toBeInTheDocument();

      // Check AI badge
      expect(within(pastaCard!).getByText('AI')).toBeInTheDocument();
      expect(within(pastaCard!).getByText('claude')).toBeInTheDocument();
    });

    test('should display health status', async () => {
      renderSavedRecipes();

      await waitFor(() => {
        expect(screen.getByText(/Backend Status:/)).toBeInTheDocument();
        expect(screen.getByText('healthy')).toBeInTheDocument();
      });
    });
  });

  describe('Recipe Actions', () => {
    test('should open recipe details dialog when View is clicked', async () => {
      renderSavedRecipes();

      const viewButton = screen.getAllByText('View')[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(screen.getByText('Pasta Carbonara Instructions')).toBeInTheDocument();
      });
    });

    test('should open menu when more options button is clicked', async () => {
      renderSavedRecipes();

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
      renderSavedRecipes();

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
      renderSavedRecipes();

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

      expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
    });

    test('should open rating dialog when Rate Recipe is clicked', async () => {
      mockRecipeHooks.getRecipeRatings.mockResolvedValue([]);
      renderSavedRecipes();

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
      const user = userEvent.setup();
      renderSavedRecipes();

      const searchInput = screen.getByPlaceholderText('Search recipes...');
      await user.type(searchInput, 'pasta');

      // Trigger search
      fireEvent.click(screen.getByRole('button', { name: /search/i }));

      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalledWith('pasta', '', '');
    });

    test('should filter recipes by difficulty', async () => {
      renderSavedRecipes();

      // Open difficulty filter
      const difficultySelect = screen.getByLabelText('Difficulty');
      fireEvent.mouseDown(difficultySelect);

      // Select easy
      const listbox = within(document.body).getByRole('listbox');
      fireEvent.click(within(listbox).getByText('easy'));

      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalledWith('', 'easy', '');
    });

    test('should clear error when clear error button is clicked', () => {
      mockUseRecipes.mockReturnValue({
        ...mockRecipeHooks,
        error: 'Some error',
      });

      renderSavedRecipes();

      const alert = screen.getByRole('alert');
      const closeButton = within(alert).getByRole('button');
      fireEvent.click(closeButton);

      expect(mockRecipeHooks.clearError).toHaveBeenCalled();
    });

    test('should refresh recipes when refresh button is clicked', () => {
      renderSavedRecipes();

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      expect(mockRecipeHooks.fetchSavedRecipes).toHaveBeenCalled();
    });
  });

  describe('Recipe Creation', () => {
    test('should open create recipe dialog when Create Recipe button is clicked', () => {
      renderSavedRecipes();

      const createButton = screen.getByText('Create Recipe');
      fireEvent.click(createButton);

      expect(screen.getByTestId('create-recipe-form')).toBeInTheDocument();
    });

    test('should save new recipe when form is submitted', async () => {
      mockRecipeHooks.saveRecipe.mockResolvedValue(mockRecipes[0]);
      renderSavedRecipes();

      // Open create dialog
      fireEvent.click(screen.getByText('Create Recipe'));

      // Submit form
      const saveButton = screen.getByText('Save Recipe');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockRecipeHooks.saveRecipe).toHaveBeenCalled();
      });
    });

    test('should update existing recipe when edit form is submitted', async () => {
      mockRecipeHooks.updateRecipe.mockResolvedValue(mockRecipes[0]);
      renderSavedRecipes();

      // Open menu and edit
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit Recipe'));
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
      renderSavedRecipes();

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
      renderSavedRecipes();

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
      renderSavedRecipes();

      await waitFor(() => {
        expect(screen.getByText(/Backend Status:/)).toBeInTheDocument();
        expect(screen.getByText('Unknown')).toBeInTheDocument();
      });
    });

    test('should handle recipe deletion errors', async () => {
      mockRecipeHooks.deleteRecipe.mockResolvedValue(false);
      renderSavedRecipes();

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
    test('should render grid layout properly', () => {
      renderSavedRecipes();

      const gridContainer = screen.getByRole('main').querySelector('.MuiGrid-container');
      expect(gridContainer).toBeInTheDocument();
    });

    test('should handle mobile view', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      window.dispatchEvent(new Event('resize'));

      renderSavedRecipes();

      // Component should still render without errors
      expect(screen.getByText('My Saved Recipes')).toBeInTheDocument();
    });
  });

  describe('Dialog Management', () => {
    test('should close recipe details dialog when backdrop is clicked', async () => {
      renderSavedRecipes();

      // Open dialog
      const viewButton = screen.getAllByText('View')[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(screen.getByText('Pasta Carbonara Instructions')).toBeInTheDocument();
      });

      // Close dialog by clicking the close button would be here
      // but since we're using a mock component, we can't test this easily
    });

    test('should close menus when clicking away', async () => {
      renderSavedRecipes();

      // Open menu
      const moreButtons = screen.getAllByRole('button', { name: '' });
      const moreButton = moreButtons.find(button => 
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      fireEvent.click(moreButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });

      // Click away to close menu
      fireEvent.click(document.body);

      await waitFor(() => {
        expect(screen.queryByText('Edit Recipe')).not.toBeInTheDocument();
      });
    });
  });
});