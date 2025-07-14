import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Button,
  Chip,
  Grid,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Alert,
  CircularProgress,
  Pagination,
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Visibility as WatchedIcon,
  BookmarkAdd as WantToWatchIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  ViewList as TableViewIcon,
  ViewModule as GridViewIcon,
  Movie as MovieIcon,
  Star as StarIcon,
  AccessTime as RuntimeIcon,
  CalendarToday as YearIcon,
  Person as DirectorIcon,
  Category as GenreIcon,
} from '@mui/icons-material';

import { Movie, MovieCreate, MovieUpdate, ViewingStatus } from '../../types';
import { moviesApi, movieHelpers } from '../../services/moviesApi';

type ViewMode = 'grid' | 'table';

const MoviesManagement: React.FC = () => {
  // State for movies data
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [pageSize, setPageSize] = useState(20);
  
  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<ViewingStatus | ''>('');
  const [genreFilter, setGenreFilter] = useState('');
  const [favoriteFilter, setFavoriteFilter] = useState<boolean | ''>('');
  
  // Dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  
  // Menu state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuMovie, setMenuMovie] = useState<Movie | null>(null);

  // Load movies
  const loadMovies = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await moviesApi.getMovies({
        page,
        page_size: pageSize,
        viewing_status: statusFilter || undefined,
        genre: genreFilter || undefined,
        is_favorite: favoriteFilter !== '' ? favoriteFilter : undefined,
        search: searchTerm || undefined,
      });
      
      setMovies(response.movies);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load movies');
    } finally {
      setLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    loadMovies();
  }, [page, pageSize, statusFilter, genreFilter, favoriteFilter]);

  // Handlers
  const handleSearch = () => {
    setPage(1);
    loadMovies();
  };

  const handleAddMovie = async (movieData: MovieCreate): Promise<boolean> => {
    try {
      await moviesApi.createMovie(movieData);
      loadMovies();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to add movie');
      return false;
    }
  };

  const handleUpdateMovie = async (movieData: MovieUpdate): Promise<boolean> => {
    if (!selectedMovie) return false;
    
    try {
      await moviesApi.updateMovie(selectedMovie.id, movieData);
      loadMovies();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to update movie');
      return false;
    }
  };

  const handleDeleteMovie = async (movie: Movie) => {
    if (!window.confirm(`Are you sure you want to delete "${movie.title}"?`)) {
      return;
    }
    
    try {
      await moviesApi.deleteMovie(movie.id);
      loadMovies();
      handleMenuClose();
    } catch (err: any) {
      setError(err.message || 'Failed to delete movie');
    }
  };

  const handleToggleFavorite = async (movie: Movie) => {
    try {
      await moviesApi.updateMovie(movie.id, { is_favorite: !movie.is_favorite });
      loadMovies();
    } catch (err: any) {
      setError(err.message || 'Failed to update favorite status');
    }
  };

  const handleUpdateStatus = async (movie: Movie, newStatus: ViewingStatus) => {
    try {
      await moviesApi.updateViewingStatus(movie.id, newStatus);
      loadMovies();
      handleMenuClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update viewing status');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, movie: Movie) => {
    setMenuAnchorEl(event.currentTarget);
    setMenuMovie(movie);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuMovie(null);
  };

  const handleViewModeChange = (newMode: ViewMode) => {
    setViewMode(newMode);
    // Adjust page size based on view mode
    setPageSize(newMode === 'table' ? 50 : 20);
    setPage(1);
  };

  // Render functions
  const renderMovieCard = (movie: Movie) => (
    <Grid item xs={12} sm={6} md={4} lg={3} key={movie.id}>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {movie.poster_image_url && (
          <CardMedia
            component="img"
            height="300"
            image={movie.poster_image_url}
            alt={movie.title}
            sx={{ objectFit: 'cover' }}
          />
        )}
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', flexGrow: 1 }}>
              {movie.title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <IconButton
                size="small"
                onClick={() => handleToggleFavorite(movie)}
                sx={{ color: movie.is_favorite ? 'red' : 'grey.400' }}
              >
                {movie.is_favorite ? <FavoriteIcon /> : <FavoriteBorderIcon />}
              </IconButton>
              <IconButton
                size="small"
                onClick={(e) => handleMenuOpen(e, movie)}
              >
                <MoreVertIcon />
              </IconButton>
            </Box>
          </Box>
          
          {movie.director && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Directed by {movie.director}
            </Typography>
          )}
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            <Chip
              label={movieHelpers.getStatusDisplayText(movie.viewing_status)}
              color={movieHelpers.getStatusColor(movie.viewing_status)}
              size="small"
            />
            {movie.release_year && (
              <Chip size="small" label={movie.release_year} variant="outlined" />
            )}
            {movie.runtime && (
              <Chip size="small" label={movieHelpers.formatRuntime(movie.runtime)} variant="outlined" />
            )}
            {movie.genre && (
              <Chip size="small" label={movie.genre} variant="outlined" />
            )}
          </Box>
          
          {movie.description && (
            <Typography variant="body2" color="text.secondary" sx={{ 
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
            }}>
              {movie.description}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Grid>
  );

  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Poster</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>Director</TableCell>
            <TableCell>Genre</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Runtime</TableCell>
            <TableCell>Year</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {movies.map((movie) => (
            <TableRow key={movie.id} hover>
              <TableCell>
                {movie.poster_image_url ? (
                  <img
                    src={movie.poster_image_url}
                    alt={movie.title}
                    style={{ width: 40, height: 60, objectFit: 'cover', borderRadius: 4 }}
                  />
                ) : (
                  <Box sx={{ width: 40, height: 60, bgcolor: 'grey.200', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <MovieIcon sx={{ color: 'grey.400' }} />
                  </Box>
                )}
              </TableCell>
              <TableCell>{movie.title}</TableCell>
              <TableCell>{movie.director || '-'}</TableCell>
              <TableCell>{movie.genre || '-'}</TableCell>
              <TableCell>
                <Chip
                  label={movieHelpers.getStatusDisplayText(movie.viewing_status)}
                  color={movieHelpers.getStatusColor(movie.viewing_status)}
                  size="small"
                />
              </TableCell>
              <TableCell>{movieHelpers.formatRuntime(movie.runtime) || '-'}</TableCell>
              <TableCell>{movie.release_year || '-'}</TableCell>
              <TableCell align="center">
                <IconButton
                  size="small"
                  onClick={() => handleToggleFavorite(movie)}
                  sx={{ color: movie.is_favorite ? 'red' : 'grey.400' }}
                >
                  {movie.is_favorite ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                </IconButton>
                <IconButton
                  size="small"
                  onClick={(e) => handleMenuOpen(e, movie)}
                >
                  <MoreVertIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MovieIcon color="primary" />
          Movies Collection
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, newMode) => newMode && handleViewModeChange(newMode)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon />
            </ToggleButton>
            <ToggleButton value="table">
              <TableViewIcon />
            </ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add Movie
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          label="Search movies"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ minWidth: 200 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => setStatusFilter(e.target.value as ViewingStatus | '')}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="want_to_watch">Want to Watch</MenuItem>
            <MenuItem value="watched">Watched</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Genre"
          variant="outlined"
          size="small"
          value={genreFilter}
          onChange={(e) => setGenreFilter(e.target.value)}
          sx={{ minWidth: 120 }}
        />
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Favorites</InputLabel>
          <Select
            value={favoriteFilter}
            label="Favorites"
            onChange={(e) => setFavoriteFilter(e.target.value as boolean | '')}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value={true}>Favorites</MenuItem>
            <MenuItem value={false}>Not Favorites</MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          onClick={handleSearch}
        >
          Search
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            setSearchTerm('');
            setStatusFilter('');
            setGenreFilter('');
            setFavoriteFilter('');
            setPage(1);
            loadMovies();
          }}
        >
          Clear
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Content */}
      {!loading && (
        <>
          {/* Stats */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Showing {movies.length} of {total} movies
              {(statusFilter || genreFilter || favoriteFilter !== '' || searchTerm) && ' (filtered)'}
            </Typography>
          </Box>

          {/* Movies Display */}
          {viewMode === 'grid' ? (
            <Grid container spacing={3}>
              {movies.map(renderMovieCard)}
            </Grid>
          ) : (
            renderTableView()
          )}

          {/* Empty State */}
          {movies.length === 0 && !loading && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <MovieIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No movies found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {searchTerm || statusFilter || genreFilter || favoriteFilter !== ''
                  ? 'Try adjusting your filters or search term.'
                  : 'Add your first movie to get started!'}
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setAddDialogOpen(true)}
              >
                Add Movie
              </Button>
            </Box>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      )}

      {/* Movie Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        {menuMovie && (
          <>
            <MenuItem onClick={() => {
              setSelectedMovie(menuMovie);
              setEditDialogOpen(true);
              handleMenuClose();
            }}>
              <EditIcon sx={{ mr: 1 }} />
              Edit Movie
            </MenuItem>
            
            {menuMovie.viewing_status === 'want_to_watch' ? (
              <MenuItem onClick={() => handleUpdateStatus(menuMovie, 'watched')}>
                <WatchedIcon sx={{ mr: 1 }} />
                Mark as Watched
              </MenuItem>
            ) : (
              <MenuItem onClick={() => handleUpdateStatus(menuMovie, 'want_to_watch')}>
                <WantToWatchIcon sx={{ mr: 1 }} />
                Mark as Want to Watch
              </MenuItem>
            )}
            
            <MenuItem onClick={() => handleToggleFavorite(menuMovie)}>
              {menuMovie.is_favorite ? <FavoriteBorderIcon sx={{ mr: 1 }} /> : <FavoriteIcon sx={{ mr: 1 }} />}
              {menuMovie.is_favorite ? 'Remove from Favorites' : 'Add to Favorites'}
            </MenuItem>
            
            <MenuItem 
              onClick={() => handleDeleteMovie(menuMovie)}
              sx={{ color: 'error.main' }}
            >
              <DeleteIcon sx={{ mr: 1 }} />
              Delete Movie
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Add/Edit Movie Dialog - Placeholder for now */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Movie</DialogTitle>
        <DialogContent>
          <Typography>Movie creation form will be implemented next</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Movie</DialogTitle>
        <DialogContent>
          <Typography>Movie editing form will be implemented next</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MoviesManagement;