import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Container,
  Card,
  CardContent,
  CardMedia,
  Button,
  Chip,
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
  InputAdornment,
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
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  Stack,
  Badge,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  PlayCircle as WatchingIcon,
  BookmarkAdd as WantToWatchIcon,
  CheckCircle as CompletedIcon,
  Cancel as DroppedIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  ViewList as TableViewIcon,
  ViewModule as GridViewIcon,
  Tv as TVIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  SkipNext as NextEpisodeIcon,
  Done as DoneIcon,
  DoneAll as DoneAllIcon,
} from '@mui/icons-material';

import { TVShow, TVShowCreate, TVShowUpdate, EpisodeWatch } from '../../types';
import { tvShowsApi, tvShowHelpers } from '../../services/tvShowsApi';
import AddTVShowDialog from './AddTVShowDialog';
import EditTVShowDialog from './EditTVShowDialog';
import EpisodeTracker from './EpisodeTracker';

type ViewMode = 'grid' | 'table';

const TVShowsManagement: React.FC = () => {
  const navigate = useNavigate();
  
  // State for TV shows data
  const [tvShows, setTVShows] = useState<TVShow[]>([]);
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
  const [statusFilter, setStatusFilter] = useState<TVShow['viewing_status'] | ''>('');
  const [genreFilter, setGenreFilter] = useState('');
  const [networkFilter, setNetworkFilter] = useState('');
  const [favoriteFilter, setFavoriteFilter] = useState<string>('');
  
  // Dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [episodeDialogOpen, setEpisodeDialogOpen] = useState(false);
  const [selectedTVShow, setSelectedTVShow] = useState<TVShow | null>(null);
  
  // Menu state
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTVShow, setMenuTVShow] = useState<TVShow | null>(null);
  
  // Load TV shows
  const loadTVShows = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await tvShowsApi.getTVShows({
        page,
        page_size: pageSize,
        viewing_status: statusFilter || undefined,
        genre: genreFilter || undefined,
        network: networkFilter || undefined,
        is_favorite: favoriteFilter === 'true' ? true : favoriteFilter === 'false' ? false : undefined,
        search: searchTerm || undefined,
        include_episodes: false,
      });
      
      setTVShows(response.tv_shows);
      setTotal(response.total);
      setTotalPages(response.pages);
    } catch (err: any) {
      setError(err.message || 'Failed to load TV shows');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, genreFilter, networkFilter, favoriteFilter, searchTerm]);
  
  // Effects
  useEffect(() => {
    loadTVShows();
  }, [loadTVShows]);
  
  // Handlers
  const handleSearch = () => {
    setPage(1);
    loadTVShows();
  };
  
  const handleAddTVShow = async (tvShowData: TVShowCreate): Promise<boolean> => {
    try {
      await tvShowsApi.createTVShow(tvShowData);
      await loadTVShows();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to add TV show');
      return false;
    }
  };
  
  const handleUpdateTVShow = async (tvShowData: TVShowUpdate): Promise<boolean> => {
    if (!selectedTVShow) return false;
    
    try {
      await tvShowsApi.updateTVShow(selectedTVShow.id, tvShowData);
      await loadTVShows();
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to update TV show');
      return false;
    }
  };
  
  const handleDeleteTVShow = async (tvShow: TVShow) => {
    if (window.confirm(`Are you sure you want to delete "${tvShow.title}"?`)) {
      try {
        await tvShowsApi.deleteTVShow(tvShow.id);
        await loadTVShows();
      } catch (err: any) {
        setError(err.message || 'Failed to delete TV show');
      }
    }
  };
  
  const handleToggleFavorite = async (tvShow: TVShow) => {
    try {
      await tvShowsApi.toggleFavorite(tvShow);
      await loadTVShows();
    } catch (err: any) {
      setError(err.message || 'Failed to update favorite status');
    }
  };
  
  const handleUpdateStatus = async (tvShow: TVShow, status: TVShow['viewing_status']) => {
    try {
      await tvShowsApi.updateViewingStatus(tvShow, status);
      await loadTVShows();
    } catch (err: any) {
      setError(err.message || 'Failed to update viewing status');
    }
  };
  
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, tvShow: TVShow) => {
    setMenuAnchorEl(event.currentTarget);
    setMenuTVShow(tvShow);
  };
  
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuTVShow(null);
  };
  
  const handleEditClick = () => {
    if (menuTVShow) {
      setSelectedTVShow(menuTVShow);
      setEditDialogOpen(true);
    }
    handleMenuClose();
  };
  
  const handleEpisodesClick = () => {
    if (menuTVShow) {
      setSelectedTVShow(menuTVShow);
      setEpisodeDialogOpen(true);
    }
    handleMenuClose();
  };
  
  const handleDeleteClick = () => {
    if (menuTVShow) {
      handleDeleteTVShow(menuTVShow);
    }
    handleMenuClose();
  };
  
  const getStatusIcon = (status: TVShow['viewing_status']) => {
    switch (status) {
      case 'want_to_watch':
        return <WantToWatchIcon />;
      case 'watching':
        return <WatchingIcon />;
      case 'completed':
        return <CompletedIcon />;
      case 'dropped':
        return <DroppedIcon />;
      default:
        return null;
    }
  };
  
  const getStatusColor = (status: TVShow['viewing_status']) => {
    switch (status) {
      case 'want_to_watch':
        return 'info';
      case 'watching':
        return 'warning';
      case 'completed':
        return 'success';
      case 'dropped':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Render grid view
  const renderGridView = () => (
    <Box sx={{ 
      display: 'grid', 
      gridTemplateColumns: { 
        xs: '1fr', 
        sm: 'repeat(2, 1fr)', 
        md: 'repeat(3, 1fr)', 
        lg: 'repeat(4, 1fr)' 
      }, 
      gap: 3 
    }}>
      {tvShows.map((tvShow) => (
          <Card key={tvShow.id} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ position: 'relative' }}>
              <CardMedia
                component="img"
                height="350"
                image={tvShow.poster_image_url || '/placeholder-poster.jpg'}
                alt={tvShow.title}
                sx={{ objectFit: 'cover' }}
              />
              <IconButton
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  bgcolor: 'background.paper',
                  '&:hover': { bgcolor: 'background.paper' },
                }}
                onClick={(e) => handleMenuOpen(e, tvShow)}
              >
                <MoreVertIcon />
              </IconButton>
              {tvShow.is_favorite && (
                <FavoriteIcon
                  sx={{
                    position: 'absolute',
                    top: 8,
                    left: 8,
                    color: 'error.main',
                  }}
                />
              )}
              {tvShow.progress_percentage !== undefined && tvShow.progress_percentage > 0 && (
                <Box
                  sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    bgcolor: 'rgba(0,0,0,0.7)',
                    p: 1,
                  }}
                >
                  <LinearProgress
                    variant="determinate"
                    value={tvShow.progress_percentage}
                    sx={{ mb: 0.5 }}
                  />
                  <Typography variant="caption" color="white">
                    {tvShow.episodes_watched} / {tvShow.total_episodes || '?'} episodes
                  </Typography>
                </Box>
              )}
            </Box>
            <CardContent sx={{ flexGrow: 1 }}>
              <Typography variant="h6" noWrap gutterBottom>
                {tvShow.title}
              </Typography>
              <Stack spacing={1}>
                <Chip
                  icon={getStatusIcon(tvShow.viewing_status)}
                  label={tvShow.viewing_status.replace('_', ' ')}
                  size="small"
                  color={getStatusColor(tvShow.viewing_status)}
                />
                {tvShow.network && (
                  <Typography variant="body2" color="text.secondary">
                    {tvShow.network}
                  </Typography>
                )}
                {tvShow.total_seasons && (
                  <Typography variant="body2" color="text.secondary">
                    {tvShow.total_seasons} season{tvShow.total_seasons > 1 ? 's' : ''}
                  </Typography>
                )}
                {tvShow.viewing_status === 'watching' && (
                  <Typography variant="body2" color="primary">
                    Currently on: {tvShowHelpers.formatEpisode(tvShow.current_season, tvShow.current_episode)}
                  </Typography>
                )}
              </Stack>
            </CardContent>
          </Card>
      ))}
    </Box>
  );
  
  // Render table view
  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Title</TableCell>
            <TableCell>Network</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Current Episode</TableCell>
            <TableCell align="center">Favorite</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {tvShows.map((tvShow) => (
            <TableRow key={tvShow.id}>
              <TableCell>
                <Typography variant="body1">{tvShow.title}</Typography>
              </TableCell>
              <TableCell>{tvShow.network || '-'}</TableCell>
              <TableCell>
                <Chip
                  icon={getStatusIcon(tvShow.viewing_status)}
                  label={tvShow.viewing_status.replace('_', ' ')}
                  size="small"
                  color={getStatusColor(tvShow.viewing_status)}
                />
              </TableCell>
              <TableCell>
                {tvShow.total_episodes ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={tvShow.progress_percentage || 0}
                      sx={{ width: 100 }}
                    />
                    <Typography variant="body2">
                      {tvShow.episodes_watched}/{tvShow.total_episodes}
                    </Typography>
                  </Box>
                ) : (
                  '-'
                )}
              </TableCell>
              <TableCell>
                {tvShow.viewing_status === 'watching' && 
                  tvShowHelpers.formatEpisode(tvShow.current_season, tvShow.current_episode)}
              </TableCell>
              <TableCell align="center">
                <IconButton
                  size="small"
                  onClick={() => handleToggleFavorite(tvShow)}
                >
                  {tvShow.is_favorite ? <FavoriteIcon color="error" /> : <FavoriteBorderIcon />}
                </IconButton>
              </TableCell>
              <TableCell align="right">
                <IconButton
                  size="small"
                  onClick={(e) => handleMenuOpen(e, tvShow)}
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
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TVIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Typography variant="h4" component="h1" fontWeight="bold">
              TV Shows
            </Typography>
            <Chip label={`${total} shows`} color="primary" />
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add TV Show
          </Button>
        </Box>
        
        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <Box sx={{ flexGrow: 1, minWidth: { xs: '100%', sm: 'auto' }, maxWidth: { xs: '100%', md: '300px' } }}>
              <TextField
                fullWidth
                placeholder="Search TV shows..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            <Box sx={{ minWidth: { xs: '100%', sm: 'auto' }, width: { xs: '100%', sm: '200px' } }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as TVShow['viewing_status'] | '')}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="want_to_watch">Want to Watch</MenuItem>
                  <MenuItem value="watching">Watching</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="dropped">Dropped</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ minWidth: { xs: '100%', sm: 'auto' }, width: { xs: '100%', sm: '200px' } }}>
              <TextField
                fullWidth
                label="Genre"
                value={genreFilter}
                onChange={(e) => setGenreFilter(e.target.value)}
              />
            </Box>
            <Box sx={{ minWidth: { xs: '100%', sm: 'auto' }, width: { xs: '100%', sm: '200px' } }}>
              <TextField
                fullWidth
                label="Network"
                value={networkFilter}
                onChange={(e) => setNetworkFilter(e.target.value)}
              />
            </Box>
            <Box sx={{ minWidth: { xs: '100%', sm: 'auto' }, width: { xs: '100%', sm: '200px' } }}>
              <FormControl fullWidth>
                <InputLabel>Favorites</InputLabel>
                <Select
                  value={favoriteFilter}
                  onChange={(e) => setFavoriteFilter(e.target.value)}
                  label="Favorites"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Favorites Only</MenuItem>
                  <MenuItem value="false">Non-favorites</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ minWidth: { xs: '100%', sm: 'auto' }, width: { xs: '100%', sm: '100px' } }}>
              <Button
                fullWidth
                variant="outlined"
                onClick={handleSearch}
                startIcon={<SearchIcon />}
              >
                Search
              </Button>
            </Box>
          </Box>
        </Paper>
        
        {/* View Mode Toggle */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, newMode) => newMode && setViewMode(newMode)}
              size="small"
            >
              <ToggleButton value="grid">
                <GridViewIcon />
              </ToggleButton>
              <ToggleButton value="table">
                <TableViewIcon />
              </ToggleButton>
            </ToggleButtonGroup>
            <FormControl size="small">
              <Select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
              >
                <MenuItem value={10}>10 per page</MenuItem>
                <MenuItem value={20}>20 per page</MenuItem>
                <MenuItem value={50}>50 per page</MenuItem>
                <MenuItem value={100}>100 per page</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <IconButton onClick={loadTVShows}>
            <RefreshIcon />
          </IconButton>
        </Box>
        
        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {/* Content */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : tvShows.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <TVIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No TV shows found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {searchTerm || statusFilter || genreFilter || networkFilter || favoriteFilter
                ? 'Try adjusting your filters'
                : 'Click "Add TV Show" to start tracking your shows'}
            </Typography>
          </Box>
        ) : viewMode === 'grid' ? (
          renderGridView()
        ) : (
          renderTableView()
        )}
        
        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, value) => setPage(value)}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        )}
        
        {/* Context Menu */}
        <Menu
          anchorEl={menuAnchorEl}
          open={Boolean(menuAnchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleEpisodesClick}>
            <PlayIcon sx={{ mr: 1 }} /> Track Episodes
          </MenuItem>
          <MenuItem onClick={handleEditClick}>
            <EditIcon sx={{ mr: 1 }} /> Edit
          </MenuItem>
          <MenuItem onClick={() => menuTVShow && handleToggleFavorite(menuTVShow)}>
            {menuTVShow?.is_favorite ? (
              <>
                <FavoriteBorderIcon sx={{ mr: 1 }} /> Remove from Favorites
              </>
            ) : (
              <>
                <FavoriteIcon sx={{ mr: 1 }} /> Add to Favorites
              </>
            )}
          </MenuItem>
          <MenuItem divider />
          <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
            <DeleteIcon sx={{ mr: 1 }} /> Delete
          </MenuItem>
        </Menu>
        
        {/* Dialogs */}
        <AddTVShowDialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
          onAdd={handleAddTVShow}
        />
        
        {selectedTVShow && (
          <>
            <EditTVShowDialog
              open={editDialogOpen}
              tvShow={selectedTVShow}
              onClose={() => {
                setEditDialogOpen(false);
                setSelectedTVShow(null);
              }}
              onUpdate={handleUpdateTVShow}
            />
            
            <EpisodeTracker
              open={episodeDialogOpen}
              tvShow={selectedTVShow}
              onClose={() => {
                setEpisodeDialogOpen(false);
                setSelectedTVShow(null);
                loadTVShows(); // Refresh to show updated progress
              }}
            />
          </>
        )}
      </Box>
    </Container>
  );
};

export default TVShowsManagement;