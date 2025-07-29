import React from 'react';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import BooksManagement from '../BooksManagement';
import { booksApi } from '../../../services/booksApi';
import { useAuthStore } from '../../../store/authStore';

// Mock dependencies
jest.mock('../../../services/booksApi');
jest.mock('../../../store/authStore');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

// Mock child components
jest.mock('../AddBookDialog', () => {
  return function MockAddBookDialog({ open, onClose, onBookAdded }: any) {
    if (!open) return null;
    return (
      <div data-testid="add-book-dialog">
        <h2>Add Book</h2>
        <button onClick={() => {
          onBookAdded({ id: 'new-book', title: 'New Book' });
          onClose();
        }}>
          Add Book
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

jest.mock('../EditBookDialog', () => {
  return function MockEditBookDialog({ open, onClose, book, onBookUpdated }: any) {
    if (!open) return null;
    return (
      <div data-testid="edit-book-dialog">
        <h2>Edit Book</h2>
        <div>Editing: {book?.title}</div>
        <button onClick={() => {
          onBookUpdated({ ...book, title: 'Updated Book' });
          onClose();
        }}>
          Save Changes
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    );
  };
});

// Mock data
const mockBooks = [
  {
    id: '1',
    user_id: 'user1',
    title: 'The Great Gatsby',
    author: 'F. Scott Fitzgerald',
    isbn: '9780743273565',
    genre: 'Fiction',
    publication_year: 1925,
    page_count: 180,
    reading_status: 'read' as const,
    current_page: 180,
    is_favorite: true,
    date_started: '2024-01-01',
    date_finished: '2024-01-10',
    my_rating: 5,
    notes: 'A classic American novel',
    cover_image_url: 'https://example.com/gatsby.jpg',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
  },
  {
    id: '2',
    user_id: 'user1',
    title: '1984',
    author: 'George Orwell',
    isbn: '9780451524935',
    genre: 'Dystopian',
    publication_year: 1949,
    page_count: 328,
    reading_status: 'reading' as const,
    current_page: 150,
    is_favorite: false,
    date_started: '2024-01-15',
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-20T00:00:00Z',
  },
  {
    id: '3',
    user_id: 'user1',
    title: 'To Kill a Mockingbird',
    author: 'Harper Lee',
    genre: 'Fiction',
    reading_status: 'want_to_read' as const,
    is_favorite: false,
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
  },
];

const mockBooksApi = booksApi as jest.Mocked<typeof booksApi>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('BooksManagement', () => {
  const mockListResponse = {
    items: mockBooks,
    total: 3,
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
    mockBooksApi.list.mockResolvedValue(mockListResponse);
    mockBooksApi.checkHealth.mockResolvedValue({ status: 'healthy', book_count: 3 });
  });

  const renderBooksManagement = async () => {
    let result;
    await act(async () => {
      result = render(
        <MemoryRouter>
          <BooksManagement />
        </MemoryRouter>
      );
    });
    // Wait for initial data load
    await waitFor(() => {
      expect(mockBooksApi.list).toHaveBeenCalled();
    });
    return result!;
  };

  describe('Component Rendering', () => {
    test('should render books management page', async () => {
      await renderBooksManagement();

      expect(screen.getByText('My Books')).toBeInTheDocument();
      expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
      expect(screen.getByText('1984')).toBeInTheDocument();
      expect(screen.getByText('To Kill a Mockingbird')).toBeInTheDocument();
    });

    test('should display loading state', async () => {
      mockBooksApi.list.mockImplementation(() => new Promise(() => {})); // Never resolves
      
      await act(async () => {
        render(
          <MemoryRouter>
            <BooksManagement />
          </MemoryRouter>
        );
      });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('should display error state', async () => {
      mockBooksApi.list.mockRejectedValue(new Error('Failed to load books'));
      
      await renderBooksManagement();

      await waitFor(() => {
        expect(screen.getByText('Failed to load books')).toBeInTheDocument();
      });
    });

    test('should display empty state when no books', async () => {
      mockBooksApi.list.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        pages: 0,
      });

      await renderBooksManagement();

      expect(screen.getByText(/No books found/)).toBeInTheDocument();
      expect(screen.getByText(/Start building your library/)).toBeInTheDocument();
    });

    test('should display book cards with correct information', async () => {
      await renderBooksManagement();

      // Check The Great Gatsby card
      const gatsbyCard = screen.getByText('The Great Gatsby').closest('[class*="MuiCard"]');
      expect(within(gatsbyCard!).getByText('F. Scott Fitzgerald')).toBeInTheDocument();
      expect(within(gatsbyCard!).getByText('Fiction')).toBeInTheDocument();
      expect(within(gatsbyCard!).getByText('180 pages')).toBeInTheDocument();
      expect(within(gatsbyCard!).getByTestId('FavoriteIcon')).toBeInTheDocument();
      
      // Check reading progress for 1984
      const orwellCard = screen.getByText('1984').closest('[class*="MuiCard"]');
      expect(within(orwellCard!).getByText('150 / 328')).toBeInTheDocument();
      expect(within(orwellCard!).getByText('46%')).toBeInTheDocument();
    });

    test('should toggle between grid and table view', async () => {
      await renderBooksManagement();

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

  describe('Book Actions', () => {
    test('should open add book dialog when Add button is clicked', async () => {
      await renderBooksManagement();

      const addButton = screen.getByRole('button', { name: /add book/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('add-book-dialog')).toBeInTheDocument();
      });
    });

    test('should add book and refresh list', async () => {
      await renderBooksManagement();

      const addButton = screen.getByRole('button', { name: /add book/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const dialogAddButton = within(screen.getByTestId('add-book-dialog')).getByText('Add Book');
        fireEvent.click(dialogAddButton);
      });

      // Should refresh the list after adding
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledTimes(2); // Initial load + refresh
      });
    });

    test('should open edit dialog when Edit is clicked', async () => {
      await renderBooksManagement();

      // Open menu for first book
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      // Click edit
      await waitFor(() => {
        fireEvent.click(screen.getByText('Edit'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('edit-book-dialog')).toBeInTheDocument();
        expect(screen.getByText('Editing: The Great Gatsby')).toBeInTheDocument();
      });
    });

    test('should delete book when Delete is clicked', async () => {
      mockBooksApi.delete.mockResolvedValue(undefined);
      window.confirm = jest.fn().mockReturnValue(true);
      
      await renderBooksManagement();

      // Open menu for first book
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      // Click delete
      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete'));
      });

      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete "The Great Gatsby"?');
      expect(mockBooksApi.delete).toHaveBeenCalledWith('1');
      
      // Should refresh the list after deleting
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledTimes(2);
      });
    });

    test('should toggle favorite status', async () => {
      mockBooksApi.update.mockResolvedValue({ ...mockBooks[0], is_favorite: false });
      
      await renderBooksManagement();

      // Find and click the favorite icon for The Great Gatsby
      const gatsbyCard = screen.getByText('The Great Gatsby').closest('[class*="MuiCard"]');
      const favoriteButton = within(gatsbyCard!).getByTestId('FavoriteIcon').closest('button');
      
      fireEvent.click(favoriteButton!);

      await waitFor(() => {
        expect(mockBooksApi.update).toHaveBeenCalledWith('1', { is_favorite: false });
      });
    });

    test('should update reading status', async () => {
      mockBooksApi.updateReadingStatus.mockResolvedValue({
        ...mockBooks[2],
        reading_status: 'reading',
        date_started: '2024-01-25',
      });
      
      await renderBooksManagement();

      // Open menu for "To Kill a Mockingbird"
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[2]);

      // Click "Start Reading"
      await waitFor(() => {
        fireEvent.click(screen.getByText('Start Reading'));
      });

      expect(mockBooksApi.updateReadingStatus).toHaveBeenCalledWith('3', 'reading');
      
      // Should refresh the list
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledTimes(2);
      });
    });

    test('should update reading progress', async () => {
      mockBooksApi.updateProgress.mockResolvedValue({
        ...mockBooks[1],
        current_page: 200,
      });
      
      await renderBooksManagement();

      // Open menu for "1984"
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[1]);

      // Click "Update Progress"
      await waitFor(() => {
        fireEvent.click(screen.getByText('Update Progress'));
      });

      // Mock prompt for page number
      window.prompt = jest.fn().mockReturnValue('200');

      expect(mockBooksApi.updateProgress).toHaveBeenCalledWith('2', 200);
    });
  });

  describe('Search and Filtering', () => {
    test('should search books by title or author', async () => {
      await renderBooksManagement();

      const searchInput = screen.getByPlaceholderText('Search by title or author...');
      fireEvent.change(searchInput, { target: { value: 'gatsby' } });

      // Wait for debounce
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith({
          page: 1,
          page_size: 20,
          search: 'gatsby',
          reading_status: '',
          genre: '',
          is_favorite: undefined,
        });
      }, { timeout: 600 });
    });

    test('should filter by reading status', async () => {
      await renderBooksManagement();

      // Open status filter
      const statusSelect = screen.getByLabelText('Reading Status');
      fireEvent.mouseDown(statusSelect);

      // Select "Read"
      await waitFor(() => {
        const readOption = screen.getByRole('option', { name: 'Read' });
        fireEvent.click(readOption);
      });

      expect(mockBooksApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          reading_status: 'read',
        })
      );
    });

    test('should filter by genre', async () => {
      await renderBooksManagement();

      const genreInput = screen.getByLabelText('Genre');
      fireEvent.change(genreInput, { target: { value: 'Fiction' } });

      // Wait for debounce
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            genre: 'Fiction',
          })
        );
      }, { timeout: 600 });
    });

    test('should filter by favorites', async () => {
      await renderBooksManagement();

      // Open favorites filter
      const favoritesSelect = screen.getByLabelText('Favorites');
      fireEvent.mouseDown(favoritesSelect);

      // Select "Favorites Only"
      await waitFor(() => {
        const favoritesOption = screen.getByRole('option', { name: 'Favorites Only' });
        fireEvent.click(favoritesOption);
      });

      expect(mockBooksApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          is_favorite: true,
        })
      );
    });

    test('should clear filters when clear button is clicked', async () => {
      await renderBooksManagement();

      // Apply some filters first
      const searchInput = screen.getByPlaceholderText('Search by title or author...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Wait for search to be applied
      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'test',
          })
        );
      }, { timeout: 600 });

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);

      expect(mockBooksApi.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 20,
        search: '',
        reading_status: '',
        genre: '',
        is_favorite: undefined,
      });
    });
  });

  describe('Pagination', () => {
    test('should handle page navigation', async () => {
      mockBooksApi.list.mockResolvedValue({
        items: mockBooks,
        total: 50,
        page: 1,
        pages: 3,
      });

      await renderBooksManagement();

      // Find pagination component
      const pagination = screen.getByRole('navigation');
      const page2Button = within(pagination).getByRole('button', { name: 'Go to page 2' });
      
      fireEvent.click(page2Button);

      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 2,
          })
        );
      });
    });

    test('should change page size', async () => {
      await renderBooksManagement();

      // Open page size selector
      const pageSizeSelect = screen.getByRole('combobox', { name: /rows per page/i });
      fireEvent.mouseDown(pageSizeSelect);

      // Select 50 items per page
      await waitFor(() => {
        const option50 = screen.getByRole('option', { name: '50' });
        fireEvent.click(option50);
      });

      expect(mockBooksApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page_size: 50,
          page: 1, // Reset to page 1 when changing page size
        })
      );
    });

    test('should navigate to first and last page', async () => {
      mockBooksApi.list.mockResolvedValue({
        items: mockBooks,
        total: 100,
        page: 3,
        pages: 5,
      });

      await renderBooksManagement();

      // Navigate to first page
      const firstPageButton = screen.getByRole('button', { name: /first page/i });
      fireEvent.click(firstPageButton);

      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 1,
          })
        );
      });

      // Navigate to last page
      const lastPageButton = screen.getByRole('button', { name: /last page/i });
      fireEvent.click(lastPageButton);

      await waitFor(() => {
        expect(mockBooksApi.list).toHaveBeenCalledWith(
          expect.objectContaining({
            page: 5,
          })
        );
      });
    });
  });

  describe('Book Recommendations', () => {
    test('should navigate to recommendations page', async () => {
      const mockNavigate = jest.fn();
      jest.spyOn(require('react-router-dom'), 'useNavigate').mockReturnValue(mockNavigate);

      await renderBooksManagement();

      const recommendationsButton = screen.getByRole('button', { name: /get book recommendations/i });
      fireEvent.click(recommendationsButton);

      expect(mockNavigate).toHaveBeenCalledWith('/books/recommendations');
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      mockBooksApi.checkHealth.mockRejectedValue(new Error('Network error'));
      
      await renderBooksManagement();

      // Should still render the page
      expect(screen.getByText('My Books')).toBeInTheDocument();
    });

    test('should show error when book update fails', async () => {
      mockBooksApi.update.mockRejectedValue(new Error('Update failed'));
      
      await renderBooksManagement();

      // Try to toggle favorite
      const favoriteButton = screen.getAllByRole('button')[2]; // Adjust index as needed
      fireEvent.click(favoriteButton);

      await waitFor(() => {
        expect(screen.getByText('Update failed')).toBeInTheDocument();
      });
    });

    test('should handle delete cancellation', async () => {
      window.confirm = jest.fn().mockReturnValue(false);
      
      await renderBooksManagement();

      // Open menu and try to delete
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[0]);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete'));
      });

      expect(mockBooksApi.delete).not.toHaveBeenCalled();
    });

    test('should handle invalid page number input for progress update', async () => {
      await renderBooksManagement();

      // Open menu for "1984"
      const moreButtons = screen.getAllByTestId('MoreVertIcon');
      fireEvent.click(moreButtons[1]);

      // Click "Update Progress"
      await waitFor(() => {
        fireEvent.click(screen.getByText('Update Progress'));
      });

      // Mock prompt with invalid input
      window.prompt = jest.fn().mockReturnValue('invalid');

      expect(mockBooksApi.updateProgress).not.toHaveBeenCalled();
    });
  });

  describe('Table View', () => {
    test('should display books in table format', async () => {
      await renderBooksManagement();

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Check table headers
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Author')).toBeInTheDocument();
      expect(screen.getByText('Genre')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('Rating')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();

      // Check table rows
      const rows = screen.getAllByRole('row');
      expect(rows).toHaveLength(4); // Header + 3 books
    });

    test('should display reading progress in table', async () => {
      await renderBooksManagement();

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Check progress for "1984"
      const rows = screen.getAllByRole('row');
      const orwellRow = rows[2]; // Second data row
      expect(within(orwellRow).getByText('150/328')).toBeInTheDocument();
    });

    test('should handle actions in table view', async () => {
      await renderBooksManagement();

      // Switch to table view
      const tableViewButton = screen.getByRole('button', { name: /table view/i });
      fireEvent.click(tableViewButton);

      // Click favorite in table
      const favoriteButtons = screen.getAllByTestId('FavoriteBorderIcon');
      fireEvent.click(favoriteButtons[0].closest('button')!);

      await waitFor(() => {
        expect(mockBooksApi.update).toHaveBeenCalled();
      });
    });
  });

  describe('Reading Statistics', () => {
    test('should display reading statistics', async () => {
      await renderBooksManagement();

      // Check statistics display
      expect(screen.getByText('Total Books: 3')).toBeInTheDocument();
      expect(screen.getByText(/Read: 1/)).toBeInTheDocument();
      expect(screen.getByText(/Reading: 1/)).toBeInTheDocument();
      expect(screen.getByText(/Want to Read: 1/)).toBeInTheDocument();
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

      await renderBooksManagement();

      // Component should still render
      expect(screen.getByText('My Books')).toBeInTheDocument();
    });

    test('should adjust grid columns for different screen sizes', async () => {
      await renderBooksManagement();

      const gridContainer = screen.getAllByRole('article')[0].parentElement;
      expect(gridContainer).toHaveClass('MuiGrid-container');
    });
  });
});