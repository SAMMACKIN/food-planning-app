import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MealRecommendations from './MealRecommendations';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApiRequest = api.apiRequest as jest.MockedFunction<typeof api.apiRequest>;

// Mock recommendations data
const mockRecommendations = [
  {
    name: 'Test AI Recipe',
    description: 'AI generated test recipe',
    prep_time: 30,
    difficulty: 'Easy',
    servings: 4,
    ingredients_needed: [
      { name: 'Test Ingredient', quantity: '1', unit: 'cup', have_in_pantry: true }
    ],
    instructions: ['Step 1: Test instruction'],
    tags: ['AI-Generated', 'test'],
    nutrition_notes: 'Test nutrition info',
    pantry_usage_score: 90,
    ai_generated: true
  }
];

const mockClaudeStatus = {
  claude_available: true,
  message: 'Claude API is available'
};

// Simple render function for testing
const renderComponent = (component: React.ReactElement) => {
  return render(component);
};

describe('MealRecommendations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders meal recommendations page', () => {
    mockApiRequest.mockResolvedValueOnce(mockClaudeStatus);
    mockApiRequest.mockResolvedValueOnce(mockRecommendations);

    renderComponent(<MealRecommendations />);
    
    expect(screen.getByText('Meal Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Get New Ideas')).toBeInTheDocument();
  });

  test('displays loading state while fetching recommendations', async () => {
    mockApiRequest.mockResolvedValueOnce(mockClaudeStatus);
    mockApiRequest.mockImplementationOnce(() => new Promise(resolve => 
      setTimeout(() => resolve(mockRecommendations), 100)
    ));

    renderComponent(<MealRecommendations />);
    
    expect(screen.getByText(/AI is crafting personalized recommendations/)).toBeInTheDocument();
  });

  test('displays AI generated recommendations', async () => {
    mockApiRequest.mockResolvedValueOnce(mockClaudeStatus);
    mockApiRequest.mockResolvedValueOnce(mockRecommendations);

    renderComponent(<MealRecommendations />);
    
    await waitFor(() => {
      expect(screen.getByText('Test AI Recipe')).toBeInTheDocument();
      expect(screen.getByText('AI Generated')).toBeInTheDocument();
    });
  });

  test('handles refresh button click', async () => {
    mockApiRequest.mockResolvedValue(mockClaudeStatus);
    mockApiRequest.mockResolvedValue(mockRecommendations);

    renderComponent(<MealRecommendations />);
    
    const refreshButton = screen.getByText('Get New Ideas');
    fireEvent.click(refreshButton);

    expect(mockApiRequest).toHaveBeenCalledWith('POST', '/recommendations', expect.any(Object));
  });

  test('displays fallback message when Claude is not available', async () => {
    mockApiRequest.mockResolvedValueOnce({ claude_available: false, message: 'Claude not available' });
    mockApiRequest.mockResolvedValueOnce([]);

    renderComponent(<MealRecommendations />);
    
    await waitFor(() => {
      expect(screen.getByText(/Using fallback recommendations/)).toBeInTheDocument();
    });
  });

  test('opens recipe detail dialog when View Recipe is clicked', async () => {
    mockApiRequest.mockResolvedValueOnce(mockClaudeStatus);
    mockApiRequest.mockResolvedValueOnce(mockRecommendations);

    renderComponent(<MealRecommendations />);
    
    await waitFor(() => {
      const viewRecipeButton = screen.getByText('View Recipe');
      fireEvent.click(viewRecipeButton);
      
      expect(screen.getByText('Test AI Recipe')).toBeInTheDocument();
      expect(screen.getByText('Ingredients (1)')).toBeInTheDocument();
    });
  });
});