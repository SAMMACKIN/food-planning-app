import { Movie, MovieCreate, MovieUpdate, MovieListResponse, MovieFilters, ViewingStatus } from '../types';
import { apiRequest } from './api';

export const moviesApi = {
  // Get all movies with pagination and filters
  getMovies: async (params?: {
    page?: number;
    page_size?: number;
    viewing_status?: ViewingStatus;
    genre?: string;
    is_favorite?: boolean;
    search?: string;
  }): Promise<MovieListResponse> => {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params?.viewing_status) searchParams.append('viewing_status', params.viewing_status);
    if (params?.genre) searchParams.append('genre', params.genre);
    if (params?.is_favorite !== undefined) searchParams.append('is_favorite', params.is_favorite.toString());
    if (params?.search) searchParams.append('search', params.search);
    
    const queryString = searchParams.toString();
    const url = queryString ? `/movies?${queryString}` : '/movies';
    
    return apiRequest<MovieListResponse>('GET', url, null, { requestType: 'data' });
  },

  // Get a single movie by ID
  getMovie: async (movieId: string): Promise<Movie> => {
    return apiRequest<Movie>('GET', `/movies/${movieId}`, null, { requestType: 'data' });
  },

  // Create a new movie
  createMovie: async (movieData: MovieCreate): Promise<Movie> => {
    return apiRequest<Movie>('POST', '/movies', movieData, { requestType: 'data' });
  },

  // Update an existing movie
  updateMovie: async (movieId: string, movieData: MovieUpdate): Promise<Movie> => {
    return apiRequest<Movie>('PUT', `/movies/${movieId}`, movieData, { requestType: 'data' });
  },

  // Delete a movie
  deleteMovie: async (movieId: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>('DELETE', `/movies/${movieId}`, null, { requestType: 'data' });
  },

  // Update viewing status
  updateViewingStatus: async (movieId: string, viewingStatus: ViewingStatus): Promise<{
    message: string;
    viewing_status: ViewingStatus;
    date_watched?: string;
  }> => {
    return apiRequest('PATCH', `/movies/${movieId}/viewing-status?viewing_status=${viewingStatus}`, null, { requestType: 'data' });
  },

  // Health check
  healthCheck: async (): Promise<{
    status: string;
    service: string;
    user_id: string;
    user_movie_count: number;
    database_connected: boolean;
    table_accessible: boolean;
  }> => {
    return apiRequest('GET', '/movies/debug/health', null, { requestType: 'data' });
  }
};

// Helper functions for working with movies data
export const movieHelpers = {
  // Get viewing status display text
  getStatusDisplayText: (status: ViewingStatus): string => {
    switch (status) {
      case 'want_to_watch': return 'Want to Watch';
      case 'watched': return 'Watched';
      default: return status;
    }
  },

  // Get viewing status color
  getStatusColor: (status: ViewingStatus): 'default' | 'primary' | 'secondary' | 'success' => {
    switch (status) {
      case 'want_to_watch': return 'default';
      case 'watched': return 'success';
      default: return 'default';
    }
  },

  // Format movie for display
  formatMovieTitle: (movie: Movie): string => {
    return movie.release_year ? `${movie.title} (${movie.release_year})` : movie.title;
  },

  // Format runtime display
  formatRuntime: (runtime?: number): string | null => {
    if (!runtime) return null;
    
    const hours = Math.floor(runtime / 60);
    const minutes = runtime % 60;
    
    if (hours === 0) {
      return `${minutes}m`;
    } else if (minutes === 0) {
      return `${hours}h`;
    } else {
      return `${hours}h ${minutes}m`;
    }
  },

  // Check if movie was recently updated (within 24 hours)
  isRecentlyUpdated: (movie: Movie): boolean => {
    const updatedAt = new Date(movie.updated_at);
    const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return updatedAt > twentyFourHoursAgo;
  },

  // Filter movies by status
  filterByStatus: (movies: Movie[], status: ViewingStatus): Movie[] => {
    return movies.filter(movie => movie.viewing_status === status);
  },

  // Sort movies by various criteria
  sortMovies: (movies: Movie[], sortBy: 'title' | 'director' | 'release_year' | 'updated_at' | 'created_at' | 'runtime'): Movie[] => {
    return [...movies].sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'director':
          return (a.director || '').localeCompare(b.director || '');
        case 'release_year':
          return (b.release_year || 0) - (a.release_year || 0);
        case 'runtime':
          return (b.runtime || 0) - (a.runtime || 0);
        case 'updated_at':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'created_at':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        default:
          return 0;
      }
    });
  }
};