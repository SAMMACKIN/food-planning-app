import { api } from './api';

// Types
export interface EpisodeWatch {
  id: string;
  tv_show_id: string;
  season_number: number;
  episode_number: number;
  episode_title?: string;
  watched: boolean;
  watch_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TVShow {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  genre?: string;
  network?: string;
  total_seasons?: number;
  total_episodes?: number;
  status?: string; // ended, returning, canceled, running
  first_air_date?: string;
  last_air_date?: string;
  poster_image_url?: string;
  tmdb_id?: string;
  tvmaze_id?: string;
  imdb_id?: string;
  viewing_status: 'want_to_watch' | 'watching' | 'completed' | 'dropped';
  current_season: number;
  current_episode: number;
  episodes_watched: number;
  date_started?: string;
  date_finished?: string;
  user_notes?: string;
  is_favorite: boolean;
  source: string;
  created_at: string;
  updated_at: string;
  progress_percentage?: number;
  watched_episodes?: EpisodeWatch[];
}

export interface TVShowCreate {
  title: string;
  description?: string;
  genre?: string;
  network?: string;
  total_seasons?: number;
  total_episodes?: number;
  status?: string;
  first_air_date?: string;
  last_air_date?: string;
  poster_image_url?: string;
  tmdb_id?: string;
  tvmaze_id?: string;
  imdb_id?: string;
  viewing_status?: 'want_to_watch' | 'watching' | 'completed' | 'dropped';
  current_season?: number;
  current_episode?: number;
  user_notes?: string;
  is_favorite?: boolean;
  source?: string;
}

export interface TVShowUpdate {
  title?: string;
  description?: string;
  genre?: string;
  network?: string;
  total_seasons?: number;
  total_episodes?: number;
  status?: string;
  first_air_date?: string;
  last_air_date?: string;
  poster_image_url?: string;
  viewing_status?: 'want_to_watch' | 'watching' | 'completed' | 'dropped';
  current_season?: number;
  current_episode?: number;
  date_started?: string;
  date_finished?: string;
  user_notes?: string;
  is_favorite?: boolean;
}

export interface TVShowFilters {
  page?: number;
  page_size?: number;
  viewing_status?: string;
  genre?: string;
  network?: string;
  is_favorite?: boolean;
  search?: string;
  include_episodes?: boolean;
}

export interface TVShowListResponse {
  tv_shows: TVShow[];
  total: number;
  page: number;
  pages: number;
}

export interface EpisodeWatchCreate {
  season_number: number;
  episode_number: number;
  episode_title?: string;
  watched?: boolean;
  watch_date?: string;
}

// API Service
export const tvShowsApi = {
  // TV Show CRUD
  async createTVShow(tvShow: TVShowCreate): Promise<TVShow> {
    const response = await api.post('/tv-shows', tvShow);
    return response.data;
  },

  async getTVShows(filters: TVShowFilters = {}): Promise<TVShowListResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.viewing_status) params.append('viewing_status', filters.viewing_status);
    if (filters.genre) params.append('genre', filters.genre);
    if (filters.network) params.append('network', filters.network);
    if (filters.is_favorite !== undefined) params.append('is_favorite', filters.is_favorite.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.include_episodes !== undefined) params.append('include_episodes', filters.include_episodes.toString());
    
    const response = await api.get(`/tv-shows?${params.toString()}`);
    return response.data;
  },

  async getTVShow(id: string, includeEpisodes: boolean = true): Promise<TVShow> {
    const response = await api.get(`/tv-shows/${id}?include_episodes=${includeEpisodes}`);
    return response.data;
  },

  async updateTVShow(id: string, updates: TVShowUpdate): Promise<TVShow> {
    const response = await api.put(`/tv-shows/${id}`, updates);
    return response.data;
  },

  async deleteTVShow(id: string): Promise<void> {
    await api.delete(`/tv-shows/${id}`);
  },

  // Episode tracking
  async markEpisodeWatched(tvShowId: string, episode: EpisodeWatchCreate): Promise<EpisodeWatch> {
    const response = await api.post(`/tv-shows/${tvShowId}/episodes`, episode);
    return response.data;
  },

  async getWatchedEpisodes(tvShowId: string, season?: number): Promise<EpisodeWatch[]> {
    const params = season ? `?season=${season}` : '';
    const response = await api.get(`/tv-shows/${tvShowId}/episodes${params}`);
    return response.data;
  },

  async bulkMarkEpisodes(
    tvShowId: string, 
    seasonNumber: number, 
    episodes: number[], 
    watched: boolean = true
  ): Promise<void> {
    await api.post(`/tv-shows/${tvShowId}/episodes/bulk`, {
      season_number: seasonNumber,
      episodes,
      watched
    });
  },

  // Helper methods
  toggleFavorite(tvShow: TVShow): Promise<TVShow> {
    return this.updateTVShow(tvShow.id, { is_favorite: !tvShow.is_favorite });
  },

  updateViewingStatus(tvShow: TVShow, status: TVShow['viewing_status']): Promise<TVShow> {
    const updates: TVShowUpdate = { viewing_status: status };
    
    if (status === 'watching' && !tvShow.date_started) {
      updates.date_started = new Date().toISOString();
    } else if (status === 'completed' && !tvShow.date_finished) {
      updates.date_finished = new Date().toISOString();
    }
    
    return this.updateTVShow(tvShow.id, updates);
  },

  markSeasonWatched(tvShowId: string, seasonNumber: number, totalEpisodes: number): Promise<void> {
    const episodes = Array.from({ length: totalEpisodes }, (_, i) => i + 1);
    return this.bulkMarkEpisodes(tvShowId, seasonNumber, episodes, true);
  },
};

// Helper functions
export const tvShowHelpers = {
  formatEpisode(season: number, episode: number): string {
    return `S${season.toString().padStart(2, '0')}E${episode.toString().padStart(2, '0')}`;
  },

  calculateProgress(tvShow: TVShow): number {
    if (!tvShow.total_episodes || tvShow.total_episodes === 0) return 0;
    return Math.round((tvShow.episodes_watched / tvShow.total_episodes) * 100);
  },

  getStatusColor(status: TVShow['viewing_status']): string {
    const colors = {
      'want_to_watch': 'info',
      'watching': 'warning',
      'completed': 'success',
      'dropped': 'error'
    };
    return colors[status] || 'default';
  },

  getStatusIcon(status: TVShow['viewing_status']): string {
    const icons = {
      'want_to_watch': 'BookmarkAdd',
      'watching': 'PlayCircle',
      'completed': 'CheckCircle',
      'dropped': 'Cancel'
    };
    return icons[status] || 'Info';
  },

  formatRuntime(seasons?: number, episodes?: number): string {
    if (!seasons && !episodes) return 'Unknown';
    
    const parts = [];
    if (seasons) parts.push(`${seasons} season${seasons > 1 ? 's' : ''}`);
    if (episodes) parts.push(`${episodes} episode${episodes > 1 ? 's' : ''}`);
    
    return parts.join(', ');
  },

  isNewEpisode(tvShow: TVShow, airDate?: string): boolean {
    if (!airDate) return false;
    const date = new Date(airDate);
    const now = new Date();
    const daysSince = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    return daysSince <= 7 && tvShow.viewing_status === 'watching';
  },
};