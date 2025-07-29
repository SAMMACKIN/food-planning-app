import React from 'react';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import MoviesManagement from '../MoviesManagement';
import { moviesApi } from '../../../services/moviesApi';
import { useAuthStore } from '../../../store/authStore';

// Mock dependencies
jest.mock('../../../services/moviesApi');
jest.mock('../../../store/authStore');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

// Mock child components
jest.mock('../AddMovieDialog', () => {
  return function MockAddMovieDialog({ open, onClose, onMovieAdded }: any) {
    if (!open) return null;
    return (
      <div data-testid="add-movie-dialog">
        <h2>Add Movie</h2>
        <button onClick={() => {
          onMovieAdded({ id: 'new-movie', title: 'New Movie' });
          onClose();
        }}>
          Add Movie
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

jest.mock('../EditMovieDialog', () => {
  return function MockEditMovieDialog({ open, onClose, movie, onMovieUpdated }: any) {
    if (!open) return null;
    return (
      <div data-testid="edit-movie-dialog">
        <h2>Edit Movie</h2>
        <div>Editing: {movie?.title}</div>
        <button onClick={() => {
          onMovieUpdated({ ...movie, title: 'Updated Movie' });
          onClose();
        }}>
          Save Changes
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

jest.mock('../NetflixImportDialog', () => {
  return function MockNetflixImportDialog({ open, onClose, onImportComplete }: any) {
    if (!open) return null;
    return (
      <div data-testid="netflix-import-dialog">
        <h2>Import from Netflix</h2>
        <button onClick={() => {
          onImportComplete(3);
          onClose();
        }}>
          Import Movies
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

// Mock data
const mockMovies = [
  {
    id: '1',
    user_id: 'user1',
    title: 'Inception',
    release_year: 2010,
    director: 'Christopher Nolan',
    genre: 'Sci-Fi',
    runtime_minutes: 148,
    viewing_status: 'watched' as const,
    is_favorite: true,
    date_watched: '2024-01-15',
    my_rating: 9,
    poster_url: 'https://example.com/inception.jpg',
    tmdb_id: '27205',
    content_type: 'movie' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: '2',
    user_id: 'user1',
    title: 'Breaking Bad',
    release_year: 2008,
    genre: 'Drama',
    viewing_status: 'want_to_watch' as const,
    is_favorite: false,
    content_type: 'tv' as const,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

const mockMoviesApi = moviesApi as jest.Mocked<typeof moviesApi>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('MoviesManagement', () => {
  const mockListResponse = {
    items: mockMovies,
    total: 2,
    page: 1,
    pages: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
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

    // Default API responses
    mockMoviesApi.list.mockResolvedValue(mockListResponse);
    mockMoviesApi.checkHealth.mockResolvedValue({ status: 'healthy', movie_count: 2 });
  });

  const renderMoviesManagement = async () => {
    let result;
    await act(async () => {
      result = render(
        <MemoryRouter>
          <MoviesManagement />
        </MemoryRouter>
      );
    });
    // Wait for initial data load
    await waitFor(() => {
      expect(mockMoviesApi.list).toHaveBeenCalled();
    });
    return result!;
  };

  describe('Component Rendering', () => {
    test('should render movies management page', async () => {
      await renderMoviesManagement();

      expect(screen.getByText('TV & Movies')).toBeInTheDocument();
      expect(screen.getByText('Inception')).toBeInTheDocument();
      expect(screen.getByText('Breaking Bad')).toBeInTheDocument();
    });

    test('should display loading state', async () => {
      mockMoviesApi.list.mockImplementation(() => new Promise(() => {})); // Never resolves
      
      await act(async () => {
        render(
          <MemoryRouter>
            <MoviesManagement />
          </MemoryRouter>
        );
      });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('should display error state', async () => {
      mockMoviesApi.list.mockRejectedValue(new Error('Failed to load movies'));
      
      await renderMoviesManagement();

      await waitFor(() => {
        expect(screen.getByText('Failed to load movies')).toBeInTheDocument();
      });
    });

    test('should display empty state when no movies', async () => {
      mockMoviesApi.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        pages: 0,
      });

      await renderMoviesManagement();

      expect(screen.getByText(/No movies or TV shows found/)).toBeInTheDocument();
    });

    test('should display movie cards with correct information', async () => {
      await renderMoviesManagement();

      // Check Inception card
      const inceptionCard = screen.getByText('Inception').closest('[class*="MuiCard"]');
      expect(within(inceptionCard!).getByText('Christopher Nolan')).toBeInTheDocument();
      expect(within(inceptionCard!).getByText('2010')).toBeInTheDocument();
      expect(within(inceptionCard!).getByText('Sci-Fi')).toBeInTheDocument();
      expect(within(inceptionCard!).getByText('148 min')).toBeInTheDocument();
      expect(within(inceptionCard!).getByTestId('FavoriteIcon')).toBeInTheDocument();
    });

    test('should toggle between grid and table view', async () => {
      await renderMoviesManagement();

      // Initially in grid view
      expect(screen.getAllByTestId('GridViewIcon')).toHaveLength(1);

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Should show table
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Title')).toBeInTheDocument(); // Table header
    });
  });

  describe('Movie Actions', () => {
    test('should open add movie dialog when Add button is clicked', async () => {
      await renderMoviesManagement();

      const addButton = screen.getByRole('button', { name: /add movie/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('add-movie-dialog')).toBeInTheDocument();
      });
    });

    test('should add movie and refresh list', async () => {
      await renderMoviesManagement();

      const addButton = screen.getByRole('button', { name: /add movie/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const dialogAddButton = within(screen.getByTestId('add-movie-dialog')).getByText('Add Movie');
        fireEvent.click(dialogAddButton);
      });

      // Should refresh the list after adding
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledTimes(2); // Initial load + refresh
      });
    });

    test('should open edit dialog when Edit is clicked', async () => {
      await renderMoviesManagement();

      // Open menu for first movie
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      // Click edit
      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('edit-movie-dialog')).toBeInTheDocument();
        expect(screen.getByText('Editing: Inception')).toBeInTheDocument();
      });
    });

    test('should delete movie when Delete is clicked', async () => {
      mockMoviesApi.delete.mockResolvedValue(undefined);
      window.confirm = jest.fn().mockReturnValue(true);
      
      await renderMoviesManagement();

      // Open menu for first movie
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      // Click delete
      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete'));
      });

      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete "Inception"?');
      expect(mockMoviesApi.delete).toHaveBeenCalledWith('1');
      
      // Should refresh the list after deleting
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledTimes(2);
      });
    });

    test('should toggle favorite status', async () => {
      mockMoviesApi.update.mockResolvedValue({ ...mockMovies[0], is_favorite: false });
      
      await renderMoviesManagement();

      // Find and click the favorite icon for Inception
      const inceptionCard = screen.getByText('Inception').closest('[class*="MuiCard"]');
      const favoriteButton = within(inceptionCard!).getByTestId('FavoriteIcon').closest('button');
      
      fireEvent.click(favoriteButton!);

      await waitFor(() => {
        expect(mockMoviesApi.update).toHaveBeenCalledWith('1', { is_favorite: false });
      });
    });

    test('should update viewing status', async () => {
      mockMoviesApi.updateViewingStatus.mockResolvedValue({
        ...mockMovies[1],
        viewing_status: 'watched',
        date_watched: '2024-01-20',
      });
      
      await renderMoviesManagement();

      // Open menu for Breaking Bad
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[1]);

      // Click "Mark as Watched"
      await waitFor(() => {
        fireEvent.click(screen.getByText('Mark as Watched'));
      });

      expect(mockMoviesApi.updateViewingStatus).toHaveBeenCalledWith('2', 'watched');
      
      // Should refresh the list
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Search and Filtering', () => {
    test('should search movies by title', async () => {
      await renderMoviesManagement();

      const searchInput = screen.getByPlaceholderText('Search by title...');
      fireEvent.change(searchInput, { target: { value: 'inception' } });

      // Wait for debounce
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          search: 'inception',
          viewing_status: '',
          genre: '',
          is_favorite: undefined,
          content_type: undefined,
        });
      }, { timeout: 600 });
    });

    test('should filter by viewing status', async () => {
      await renderMoviesManagement();

      // Open status filter
      const statusSelect = screen.getByLabelText('Viewing Status');
      fireEvent.mouseDown(statusSelect);

      // Select "Watched"
      await waitFor(() => {
        const watchedOption = screen.getByRole('option', { name: 'Watched' });
        fireEvent.click(watchedOption);
      });

      expect(mockMoviesApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          viewing_status: 'watched',
        })
      );
    });

    test('should filter by genre', async () => {
      await renderMoviesManagement();

      const genreInput = screen.getByLabelText('Genre');
      fireEvent.change(genreInput, { target: { value: 'Sci-Fi' } });

      // Wait for debounce
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            genre: 'Sci-Fi',
          })
        );
      }, { timeout: 600 });
    });

    test('should filter by favorites', async () => {
      await renderMoviesManagement();

      // Open favorites filter
      const favoritesSelect = screen.getByLabelText('Favorites');
      fireEvent.mouseDown(favoritesSelect);

      // Select "Favorites Only"
      await waitFor(() => {
        const favoritesOption = screen.getByRole('option', { name: 'Favorites Only' });
        fireEvent.click(favoritesOption);
      });

      expect(mockMoviesApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          is_favorite: true,
        })
      );
    });

    test('should filter by content type', async () => {
      await renderMoviesManagement();

      // Click TV filter button
      const tvButton = screen.getByRole('button', { name: /tv shows/i });
      fireEvent.click(tvButton);

      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            content_type: 'tv',
          })
        );
      });
    });

    test('should clear filters when clear button is clicked', async () => {
      await renderMoviesManagement();

      // Apply some filters first
      const searchInput = screen.getByPlaceholderText('Search by title...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Wait for search to be applied
      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'test',
          })
        );
      }, { timeout: 600 });

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);

      expect(mockMoviesApi.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 20,
        search: '',
        viewing_status: '',
        genre: '',
        is_favorite: undefined,
        content_type: undefined,
      });
    });
  });

  describe('Pagination', () => {
    test('should handle page navigation', async () => {
      mockMoviesApi.list.mockResolvedValue({
        items: mockMovies,
        total: 50,
        page: 1,
        pages: 3,
      });

      await renderMoviesManagement();

      // Find pagination component
      const pagination = screen.getByRole('navigation');
      const page2Button = within(pagination).getByRole('button', { name: 'Go to page 2' });
      
      fireEvent.click(page2Button);

      await waitFor(() => {
        expect(mockMoviesApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 2,
          })
        );
      });
    });

    test('should change page size', async () => {
      await renderMoviesManagement();

      // Open page size selector
      const pageSizeSelect = screen.getByRole('combobox', { name: /rows per page/i });
      fireEvent.mouseDown(pageSizeSelect);

      // Select 50 items per page
      await waitFor(() => {
        const option50 = screen.getByRole('option', { name: '50' });
        fireEvent.click(option50);
      });

      expect(mockMoviesApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page_size: 50,
          page: 1, // Reset to page 1 when changing page size
        })
      );
    });
  });

  describe('Import and Recommendations', () => {
    test('should open Netflix import dialog', async () => {
      await renderMoviesManagement();

      const importButton = screen.getByRole('button', { name: /import from netflix/i });
      fireEvent.click(importButton);

      await waitFor(() => {
        expect(screen.getByTestId('netflix-import-dialog')).toBeInTheDocument();
      });
    });

    test('should refresh list after successful import', async () => {
      await renderMoviesManagement();

      const importButton = screen.getByRole('button', { name: /import from netflix/i });
      fireEvent.click(importButton);

      await waitFor(() => {
        const importMoviesButton = within(screen.getByTestId('netflix-import-dialog')).getByText('Import Movies');
        fireEvent.click(importMoviesButton);
      });

      // Should show success message and refresh list
      await waitFor(() => {
        expect(screen.getByText('Successfully imported 3 movies')).toBeInTheDocument();
        expect(mockMoviesApi.list).toHaveBeenCalledTimes(2); // Initial + after import
      });
    });

    test('should navigate to recommendations page', async () => {
      const mockNavigate = jest.fn();
      jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(mockNavigate);

      await renderMoviesManagement();

      const recommendationsButton = screen.getByRole('button', { name: /get ai recommendations/i });
      fireEvent.click(recommendationsButton);

      expect(mockNavigate).toHaveBeenCalledWith('/movies/recommendations');
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      mockMoviesApi.checkHealth.mockRejectedValue(new Error('Network error'));
      
      await renderMoviesManagement();

      // Should still render the page
      expect(screen.getByText('TV & Movies')).toBeInTheDocument();
    });

    test('should show error when movie update fails', async () => {
      mockMoviesApi.update.mockRejectedValue(new Error('Update failed'));
      
      await renderMoviesManagement();

      // Try to toggle favorite
      const favoriteButton = screen.getAllByRole('button')[2]; // Adjust index as needed
      fireEvent.click(favoriteButton);

      await waitFor(() => {
        expect(screen.getByText('Update failed')).toBeInTheDocument();
      });
    });

    test('should handle delete cancellation', async () => {
      window.confirm = jest.fn().mockReturnValue(false);
      
      await renderMoviesManagement();

      // Open menu and try to delete
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete'));
      });

      expect(mockMoviesApi.delete).not.toHaveBeenCalled();
    });
  });

  describe('Table View', () => {
    test('should display movies in table format', async () => {
      await renderMoviesManagement();

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Check table headers
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Year')).toBeInTheDocument();
      expect(screen.getByText('Director')).toBeInTheDocument();
      expect(screen.getByText('Genre')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();

      // Check table rows
      const rows = screen.getAllByRole('row');
      expect(rows).toHaveLength(3); // Header + 2 movies
    });

    test('should handle actions in table view', async () => {
      await renderMoviesManagement();

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Click favorite in table
      const favoriteButtons = screen.getAllByTestId('FavoriteBorderIcon');
      fireEvent.click(favoriteButtons[0].closest('button')!);

      await waitFor(() => {
        expect(mockMoviesApi.update).toHaveBeenCalled();
      });
    });
  });

  describe('Responsive Behavior', () => {
    test('should handle mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      window.dispatchEvent(new Event('resize'));

      await renderMoviesManagement();

      // Component should still render
      expect(screen.getByText('TV & Movies')).toBeInTheDocument();
    });

    test('should adjust grid columns for different screen sizes', async () => {
      await renderMoviesManagement();

      const gridContainer = screen.getAllByRole('article')[0].parentElement;
      expect(gridContainer).toHaveClass('MuiGrid-container');
    });
  });
});