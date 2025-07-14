import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import MealPlanning from '../MealPlanning';
import { apiRequest } from '../../../services/api';

// Mock the API service
jest.mock('../../../services/api', () => ({
  apiRequest: jest.fn(),
}));

const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

// Mock data
const mockMealPlans = [
  {
    id: '1',
    date: '2024-01-15',
    meal_type: 'breakfast',
    meal_name: 'Oatmeal with Berries',
    meal_description: 'Healthy breakfast option',
    recipe_data: {
      prep_time: 10,
      difficulty: 'easy',
      servings: 2,
      ingredients_needed: [],
      instructions: ['Add water', 'Cook oats'],
      tags: ['healthy', 'quick'],
      nutrition_notes: 'High fiber',
      pantry_usage_score: 0.8
    },
    ai_generated: true,
    ai_provider: 'claude'
  },
  {
    id: '2',
    date: '2024-01-15',
    meal_type: 'lunch',
    meal_name: 'Chicken Salad',
    meal_description: 'Fresh and light lunch',
    ai_generated: false
  },
];

const mockRecommendations = [
  {
    name: 'Pasta Carbonara',
    description: 'Classic Italian pasta dish',
    prep_time: 20,
    difficulty: 'medium',
    servings: 4,
    ingredients_needed: [
      { name: 'pasta', quantity: '400g', unit: 'g', have_in_pantry: true },
      { name: 'eggs', quantity: '4', unit: 'pieces', have_in_pantry: true },
    ],
    instructions: ['Cook pasta', 'Make sauce', 'Combine'],
    tags: ['italian', 'pasta'],
    nutrition_notes: 'Rich in protein',
    pantry_usage_score: 0.9,
    ai_generated: true,
    ai_provider: 'claude'
  },
  {
    name: 'Grilled Chicken',
    description: 'Simple grilled chicken breast',
    prep_time: 25,
    difficulty: 'easy',
    servings: 2,
    ingredients_needed: [],
    instructions: ['Season chicken', 'Grill'],
    tags: ['protein', 'healthy'],
    nutrition_notes: 'High protein',
    pantry_usage_score: 0.7,
    ai_generated: false
  },
];

const mockReviews = [
  {
    id: 'review1',
    meal_plan_id: '1',
    rating: 5,
    review_text: 'Delicious and easy to make!',
    would_make_again: true,
    preparation_notes: 'Added extra berries',
    reviewed_at: '2024-01-15T10:00:00Z'
  }
];

describe('MealPlanning', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock Date to ensure consistent testing
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-15'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const renderMealPlanning = () => {
    return render(<MealPlanning />);
  };

  describe('Component Rendering', () => {
    test('should render the meal planning header', () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      expect(screen.getByText('Meal Planning')).toBeInTheDocument();
      expect(screen.getByText(/Week of/)).toBeInTheDocument();
    });

    test('should render week navigation buttons', () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      expect(screen.getByText('Previous Week')).toBeInTheDocument();
      expect(screen.getByText('Next Week')).toBeInTheDocument();
    });

    test('should render all days of the week', () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      days.forEach(day => {
        expect(screen.getByText(day)).toBeInTheDocument();
      });
    });

    test('should render all meal types for each day', () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      const mealTypes = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];
      mealTypes.forEach(mealType => {
        const elements = screen.getAllByText(mealType);
        expect(elements.length).toBe(7); // One for each day
      });
    });
  });

  describe('Meal Plans Display', () => {
    test('should fetch and display meal plans', async () => {
      mockApiRequest.mockResolvedValue(mockMealPlans);
      renderMealPlanning();

      await waitFor(() => {
        expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
        expect(screen.getByText('Chicken Salad')).toBeInTheDocument();
      });

      expect(mockApiRequest).toHaveBeenCalledWith(
        'GET',
        expect.stringContaining('/meal-plans?start_date=')
      );
    });

    test('should display AI badge for AI-generated meals', async () => {
      mockApiRequest.mockResolvedValue(mockMealPlans);
      renderMealPlanning();

      await waitFor(() => {
        const aiBadge = screen.getByText('claude');
        expect(aiBadge).toBeInTheDocument();
      });
    });

    test('should display meal descriptions', async () => {
      mockApiRequest.mockResolvedValue(mockMealPlans);
      renderMealPlanning();

      await waitFor(() => {
        expect(screen.getByText('Healthy breakfast option')).toBeInTheDocument();
        expect(screen.getByText('Fresh and light lunch')).toBeInTheDocument();
      });
    });
  });

  describe('Adding Meals', () => {
    test('should open meal selection dialog when Add button is clicked', async () => {
      mockApiRequest.mockResolvedValueOnce([]); // Initial meal plans
      mockApiRequest.mockResolvedValueOnce(mockRecommendations); // Recommendations
      
      renderMealPlanning();

      // Find first Add button
      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Choose a meal for Monday breakfast/)).toBeInTheDocument();
      });
    });

    test('should display recommendations in the selection dialog', async () => {
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(mockRecommendations);
      
      renderMealPlanning();

      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Pasta Carbonara')).toBeInTheDocument();
        expect(screen.getByText('Grilled Chicken')).toBeInTheDocument();
      });
    });

    test('should assign meal when recommendation is clicked', async () => {
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(mockRecommendations);
      
      // Mock the POST request for creating meal plan
      const newMealPlan = {
        id: '3',
        date: '2024-01-15',
        meal_type: 'breakfast',
        meal_name: 'Pasta Carbonara',
        meal_description: 'Classic Italian pasta dish',
        ai_generated: true,
        ai_provider: 'claude'
      };
      mockApiRequest.mockResolvedValueOnce(newMealPlan);
      
      renderMealPlanning();

      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        const pastaOption = screen.getByText('Pasta Carbonara');
        fireEvent.click(pastaOption.closest('[role="button"]')!);
      });

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/meal-plans',
          expect.objectContaining({
            meal_name: 'Pasta Carbonara',
            meal_type: 'breakfast'
          })
        );
      });
    });

    test('should close dialog when Cancel is clicked', async () => {
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(mockRecommendations);
      
      renderMealPlanning();

      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        const cancelButton = screen.getByText('Cancel');
        fireEvent.click(cancelButton);
      });

      expect(screen.queryByText(/Choose a meal for/)).not.toBeInTheDocument();
    });
  });

  describe('Removing Meals', () => {
    test('should remove meal when delete button is clicked', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce(undefined); // DELETE response
      
      renderMealPlanning();

      await waitFor(() => {
        const deleteButtons = screen.getAllByTitle('Remove meal');
        fireEvent.click(deleteButtons[0]);
      });

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'DELETE',
          '/meal-plans/1'
        );
      });
    });

    test('should update UI after meal removal', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce(undefined);
      
      renderMealPlanning();

      await waitFor(() => {
        expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTitle('Remove meal');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.queryByText('Oatmeal with Berries')).not.toBeInTheDocument();
      });
    });
  });

  describe('Meal Reviews', () => {
    test('should open review dialog when review button is clicked', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce(mockReviews);
      
      renderMealPlanning();

      await waitFor(() => {
        const reviewButtons = screen.getAllByTitle('Review this meal');
        fireEvent.click(reviewButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Review: Oatmeal with Berries')).toBeInTheDocument();
      });
    });

    test('should display existing reviews', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce(mockReviews);
      
      renderMealPlanning();

      await waitFor(() => {
        const reviewButtons = screen.getAllByTitle('Review this meal');
        fireEvent.click(reviewButtons[0]);
      });

      await waitFor(() => {
        expect(screen.getByText('Delicious and easy to make!')).toBeInTheDocument();
        expect(screen.getByText('Would make again')).toBeInTheDocument();
        expect(screen.getByText('Notes: Added extra berries')).toBeInTheDocument();
      });
    });

    test('should submit new review', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce([]);
      
      const newReview = {
        id: 'review2',
        meal_plan_id: '1',
        rating: 4,
        review_text: 'Pretty good!',
        would_make_again: true,
        preparation_notes: 'Used almond milk',
        reviewed_at: '2024-01-15T12:00:00Z'
      };
      mockApiRequest.mockResolvedValueOnce(newReview);
      
      renderMealPlanning();

      await waitFor(() => {
        const reviewButtons = screen.getAllByTitle('Review this meal');
        fireEvent.click(reviewButtons[0]);
      });

      await waitFor(() => {
        const reviewInput = screen.getByLabelText('Review');
        fireEvent.change(reviewInput, { target: { value: 'Pretty good!' } });
        
        const notesInput = screen.getByLabelText('Preparation Notes');
        fireEvent.change(notesInput, { target: { value: 'Used almond milk' } });
        
        const submitButton = screen.getByText('Submit Review');
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/meal-plans/1/reviews',
          expect.objectContaining({
            review_text: 'Pretty good!',
            preparation_notes: 'Used almond milk'
          })
        );
      });
    });

    test('should update rating in review form', async () => {
      mockApiRequest.mockResolvedValueOnce(mockMealPlans);
      mockApiRequest.mockResolvedValueOnce([]);
      
      renderMealPlanning();

      await waitFor(() => {
        const reviewButtons = screen.getAllByTitle('Review this meal');
        fireEvent.click(reviewButtons[0]);
      });

      await waitFor(() => {
        const ratingStars = screen.getAllByRole('radio');
        fireEvent.click(ratingStars[3]); // Click 4th star
      });

      // Verify rating is selected (4 stars)
      const selectedStars = screen.getAllByRole('radio', { checked: true });
      expect(selectedStars).toHaveLength(4);
    });
  });

  describe('Week Navigation', () => {
    test('should navigate to previous week', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      const prevButton = screen.getByText('Previous Week');
      fireEvent.click(prevButton);

      await waitFor(() => {
        expect(screen.getByText(/Week of 1\/8\/2024/)).toBeInTheDocument();
      });
    });

    test('should navigate to next week', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      const nextButton = screen.getByText('Next Week');
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText(/Week of 1\/22\/2024/)).toBeInTheDocument();
      });
    });

    test('should fetch new meal plans when week changes', async () => {
      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      const nextButton = screen.getByText('Next Week');
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'GET',
          expect.stringContaining('/meal-plans?start_date=2024-01-22')
        );
      });
    });
  });

  describe('Error Handling', () => {
    test('should display error when fetching meal plans fails', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'));
      renderMealPlanning();

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch meal plans')).toBeInTheDocument();
      });
    });

    test('should display error when fetching recommendations fails', async () => {
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'));
      
      renderMealPlanning();

      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recommendations')).toBeInTheDocument();
      });
    });

    test('should display error when assigning meal fails', async () => {
      mockApiRequest.mockResolvedValueOnce([]);
      mockApiRequest.mockResolvedValueOnce(mockRecommendations);
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'));
      
      renderMealPlanning();

      const addButtons = await screen.findAllByText('Add');
      fireEvent.click(addButtons[0]);

      await waitFor(() => {
        const pastaOption = screen.getByText('Pasta Carbonara');
        fireEvent.click(pastaOption.closest('[role="button"]')!);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to assign meal')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    test('should render in mobile layout', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      window.dispatchEvent(new Event('resize'));

      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      // In mobile, cards should stack vertically
      const container = screen.getByRole('main').firstChild;
      expect(container).toHaveStyle({
        display: 'grid'
      });
    });

    test('should render in desktop layout', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1440,
      });
      window.dispatchEvent(new Event('resize'));

      mockApiRequest.mockResolvedValue([]);
      renderMealPlanning();

      // In desktop, should show all 7 days in a row
      const container = screen.getByRole('main').firstChild;
      expect(container).toHaveStyle({
        display: 'grid'
      });
    });
  });
});