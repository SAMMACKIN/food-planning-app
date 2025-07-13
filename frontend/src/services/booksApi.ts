import { Book, BookCreate, BookUpdate, BookListResponse, BookFilters, ReadingStatus } from '../types';
import { apiRequest } from './api';

export const booksApi = {
  // Get all books with pagination and filters
  getBooks: async (params?: {
    page?: number;
    page_size?: number;
    reading_status?: ReadingStatus;
    genre?: string;
    is_favorite?: boolean;
    search?: string;
  }): Promise<BookListResponse> => {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params?.reading_status) searchParams.append('reading_status', params.reading_status);
    if (params?.genre) searchParams.append('genre', params.genre);
    if (params?.is_favorite !== undefined) searchParams.append('is_favorite', params.is_favorite.toString());
    if (params?.search) searchParams.append('search', params.search);
    
    const queryString = searchParams.toString();
    const url = queryString ? `/books?${queryString}` : '/books';
    
    return apiRequest<BookListResponse>('GET', url, null, { requestType: 'data' });
  },

  // Get a single book by ID
  getBook: async (bookId: string): Promise<Book> => {
    return apiRequest<Book>('GET', `/books/${bookId}`, null, { requestType: 'data' });
  },

  // Create a new book
  createBook: async (bookData: BookCreate): Promise<Book> => {
    return apiRequest<Book>('POST', '/books', bookData, { requestType: 'data' });
  },

  // Update an existing book
  updateBook: async (bookId: string, bookData: BookUpdate): Promise<Book> => {
    return apiRequest<Book>('PUT', `/books/${bookId}`, bookData, { requestType: 'data' });
  },

  // Delete a book
  deleteBook: async (bookId: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>('DELETE', `/books/${bookId}`, null, { requestType: 'data' });
  },

  // Update reading progress
  updateReadingProgress: async (bookId: string, currentPage: number): Promise<{
    message: string;
    current_page: number;
    total_pages?: number;
    progress_percent: number;
    reading_status: ReadingStatus;
  }> => {
    return apiRequest('PATCH', `/books/${bookId}/reading-progress?current_page=${currentPage}`, null, { requestType: 'data' });
  },

  // Health check
  healthCheck: async (): Promise<{
    status: string;
    service: string;
    user_id: string;
    user_book_count: number;
    database_connected: boolean;
    table_accessible: boolean;
  }> => {
    return apiRequest('GET', '/books/debug/health', null, { requestType: 'data' });
  }
};

// Helper functions for working with books data
export const bookHelpers = {
  // Calculate reading progress percentage
  getProgressPercentage: (book: Book): number => {
    if (!book.pages || book.pages === 0) return 0;
    return Math.round((book.current_page / book.pages) * 100);
  },

  // Get reading status display text
  getStatusDisplayText: (status: ReadingStatus): string => {
    switch (status) {
      case 'want_to_read': return 'Want to Read';
      case 'reading': return 'Currently Reading';
      case 'read': return 'Read';
      default: return status;
    }
  },

  // Get reading status color
  getStatusColor: (status: ReadingStatus): 'default' | 'primary' | 'secondary' | 'success' => {
    switch (status) {
      case 'want_to_read': return 'default';
      case 'reading': return 'primary';
      case 'read': return 'success';
      default: return 'default';
    }
  },

  // Format book for display
  formatBookTitle: (book: Book): string => {
    return `${book.title} by ${book.author}`;
  },

  // Get estimated reading time remaining (assumes 250 words per page, 200 words per minute)
  getEstimatedReadingTime: (book: Book): string | null => {
    if (!book.pages || book.current_page >= book.pages) return null;
    
    const remainingPages = book.pages - book.current_page;
    const wordsPerPage = 250;
    const wordsPerMinute = 200;
    
    const totalMinutes = (remainingPages * wordsPerPage) / wordsPerMinute;
    const hours = Math.floor(totalMinutes / 60);
    const minutes = Math.round(totalMinutes % 60);
    
    if (hours === 0) {
      return `${minutes} min left`;
    } else if (minutes === 0) {
      return `${hours}h left`;
    } else {
      return `${hours}h ${minutes}m left`;
    }
  },

  // Check if book was recently updated (within 24 hours)
  isRecentlyUpdated: (book: Book): boolean => {
    const updatedAt = new Date(book.updated_at);
    const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return updatedAt > twentyFourHoursAgo;
  },

  // Filter books by status
  filterByStatus: (books: Book[], status: ReadingStatus): Book[] => {
    return books.filter(book => book.reading_status === status);
  },

  // Sort books by various criteria
  sortBooks: (books: Book[], sortBy: 'title' | 'author' | 'updated_at' | 'created_at' | 'progress'): Book[] => {
    return [...books].sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'author':
          return a.author.localeCompare(b.author);
        case 'updated_at':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'created_at':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'progress':
          const progressA = bookHelpers.getProgressPercentage(a);
          const progressB = bookHelpers.getProgressPercentage(b);
          return progressB - progressA;
        default:
          return 0;
      }
    });
  }
};