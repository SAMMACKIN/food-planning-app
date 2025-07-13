import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  LinearProgress,
  Tooltip,
  Fab,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  MenuBook as BookIcon,
  PlayArrow as ReadingIcon,
  CheckCircle as CompletedIcon,
  BookmarkBorder as WantToReadIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { Book, ReadingStatus, BookFilters } from '../../types';
import { booksApi, bookHelpers } from '../../services/booksApi';
import AddBookDialog from './AddBookDialog';
import EditBookDialog from './EditBookDialog';

const BooksManagement: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // State management
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalBooks, setTotalBooks] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filter and search state
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'title' | 'author' | 'updated_at' | 'created_at' | 'progress'>('updated_at');
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  
  // Dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [bookMenuAnchorEl, setBookMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuBook, setMenuBook] = useState<Book | null>(null);

  // Tab definitions
  const tabs = [
    { label: 'All Books', status: undefined, icon: <BookIcon /> },
    { label: 'Want to Read', status: 'want_to_read' as ReadingStatus, icon: <WantToReadIcon /> },
    { label: 'Reading', status: 'reading' as ReadingStatus, icon: <ReadingIcon /> },
    { label: 'Read', status: 'read' as ReadingStatus, icon: <CompletedIcon /> },
  ];

  // Load books
  const loadBooks = async (preserveScroll = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page: currentPage,
        page_size: 20,
        ...(tabs[selectedTab].status && { reading_status: tabs[selectedTab].status }),
        ...(searchTerm && { search: searchTerm }),
      };
      
      const response = await booksApi.getBooks(params);
      
      // Sort books on frontend
      const sortedBooks = bookHelpers.sortBooks(response.books, sortBy);
      
      setBooks(sortedBooks);
      setTotalBooks(response.total);
      setTotalPages(response.total_pages);
    } catch (error: any) {
      console.error('Error loading books:', error);
      setError('Failed to load books. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    loadBooks();
  }, [selectedTab, searchTerm, currentPage, sortBy]);

  // Event handlers
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    setCurrentPage(1);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setCurrentPage(1);
  };

  const handleSortChange = (newSortBy: typeof sortBy) => {
    setSortBy(newSortBy);
    setFilterAnchorEl(null);
  };

  const handleBookMenuOpen = (event: React.MouseEvent<HTMLElement>, book: Book) => {
    setBookMenuAnchorEl(event.currentTarget);
    setMenuBook(book);
  };

  const handleBookMenuClose = () => {
    setBookMenuAnchorEl(null);
    setMenuBook(null);
  };

  const handleEditBook = (book: Book) => {
    setSelectedBook(book);
    setEditDialogOpen(true);
    handleBookMenuClose();
  };

  const handleDeleteBook = async (book: Book) => {
    if (!window.confirm(`Are you sure you want to delete "${book.title}"?`)) return;
    
    try {
      await booksApi.deleteBook(book.id);
      await loadBooks();
      handleBookMenuClose();
    } catch (error: any) {
      console.error('Error deleting book:', error);
      setError('Failed to delete book. Please try again.');
    }
  };

  const handleToggleFavorite = async (book: Book) => {
    try {
      await booksApi.updateBook(book.id, { is_favorite: !book.is_favorite });
      await loadBooks();
      handleBookMenuClose();
    } catch (error: any) {
      console.error('Error updating favorite status:', error);
      setError('Failed to update favorite status. Please try again.');
    }
  };

  const handleUpdateProgress = async (book: Book, newPage: number) => {
    try {
      await booksApi.updateReadingProgress(book.id, newPage);
      await loadBooks();
    } catch (error: any) {
      console.error('Error updating progress:', error);
      setError('Failed to update reading progress. Please try again.');
    }
  };

  // Render book card
  const renderBookCard = (book: Book) => {
    const progressPercent = bookHelpers.getProgressPercentage(book);
    const statusColor = bookHelpers.getStatusColor(book.reading_status);
    const estimatedTime = bookHelpers.getEstimatedReadingTime(book);
    
    return (
      <Grid item xs={12} sm={6} md={4} lg={3} key={book.id}>
        <Card 
          sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: theme.shadows[4],
            }
          }}
        >
          {/* Book cover placeholder or image */}
          <Box
            sx={{
              height: 120,
              bgcolor: 'grey.100',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              backgroundImage: book.cover_image_url ? `url(${book.cover_image_url})` : 'none',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          >
            {!book.cover_image_url && <BookIcon sx={{ fontSize: 48, color: 'grey.500' }} />}
            
            {/* Favorite indicator */}
            {book.is_favorite && (
              <IconButton
                size="small"
                sx={{ position: 'absolute', top: 4, left: 4, bgcolor: 'rgba(255,255,255,0.8)' }}
              >
                <StarIcon sx={{ color: 'warning.main', fontSize: 16 }} />
              </IconButton>
            )}
            
            {/* Menu button */}
            <IconButton
              size="small"
              onClick={(e) => handleBookMenuOpen(e, book)}
              sx={{ position: 'absolute', top: 4, right: 4, bgcolor: 'rgba(255,255,255,0.8)' }}
            >
              <MoreVertIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Box>
          
          <CardContent sx={{ flexGrow: 1, pb: 1 }}>
            <Typography variant="subtitle1" component="h3" noWrap title={book.title}>
              {book.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap title={book.author}>
              by {book.author}
            </Typography>
            
            {book.genre && (
              <Chip
                label={book.genre}
                size="small"
                sx={{ mt: 1, fontSize: '0.75rem' }}
              />
            )}
            
            {/* Reading status */}
            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={bookHelpers.getStatusDisplayText(book.reading_status)}
                size="small"
                color={statusColor}
                variant="outlined"
              />
              {bookHelpers.isRecentlyUpdated(book) && (
                <Chip label="Updated" size="small" color="info" />
              )}
            </Box>
            
            {/* Reading progress */}
            {book.reading_status === 'reading' && book.pages && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    Page {book.current_page} of {book.pages}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {progressPercent}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={progressPercent}
                  sx={{ height: 6, borderRadius: 3 }}
                />
                {estimatedTime && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {estimatedTime}
                  </Typography>
                )}
              </Box>
            )}
          </CardContent>
          
          <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
            <Button
              size="small"
              onClick={() => handleEditBook(book)}
              startIcon={<EditIcon />}
            >
              Edit
            </Button>
            {book.reading_status === 'reading' && (
              <Button
                size="small"
                color="primary"
                onClick={() => {
                  const newPage = prompt(
                    `Update reading progress for "${book.title}"\nCurrent page: ${book.current_page}${book.pages ? ` of ${book.pages}` : ''}\n\nEnter new page number:`,
                    book.current_page.toString()
                  );
                  if (newPage && !isNaN(Number(newPage))) {
                    handleUpdateProgress(book, Number(newPage));
                  }
                }}
              >
                Update Progress
              </Button>
            )}
          </CardActions>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ width: '100%', minHeight: '100vh' }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontSize: isMobile ? '1.75rem' : '2.125rem' }}>
            📚 My Books
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage your reading collection and track your progress
          </Typography>
        </Box>
        
        {!isMobile && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
            sx={{ alignSelf: 'flex-start' }}
          >
            Add Book
          </Button>
        )}
      </Box>

      {/* Tabs and Controls */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            variant={isMobile ? 'scrollable' : 'standard'}
            scrollButtons="auto"
            sx={{ flexGrow: 1 }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={index}
                label={tab.label}
                icon={tab.icon}
                iconPosition="start"
                sx={{ textTransform: 'none', minHeight: 48 }}
              />
            ))}
          </Tabs>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              onClick={(e) => setFilterAnchorEl(e.currentTarget)}
              color={filterAnchorEl ? 'primary' : 'default'}
            >
              <SortIcon />
            </IconButton>
          </Box>
        </Box>
        
        {/* Search */}
        <TextField
          fullWidth
          placeholder="Search books by title, author, or description..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />
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

      {/* Books Grid */}
      {!loading && (
        <>
          {books.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <BookIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm ? 'No books found' : 'No books in this category'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {searchTerm 
                  ? 'Try adjusting your search terms or browse all books'
                  : 'Start building your reading collection by adding your first book'
                }
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setAddDialogOpen(true)}
              >
                Add Your First Book
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {books.map(renderBookCard)}
            </Grid>
          )}
          
          {/* Stats */}
          {totalBooks > 0 && (
            <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
              <Typography variant="body2" color="text.secondary" align="center">
                Showing {books.length} of {totalBooks} books
                {selectedTab > 0 && ` in ${tabs[selectedTab].label}`}
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Mobile FAB */}
      {isMobile && (
        <Fab
          color="primary"
          aria-label="add book"
          onClick={() => setAddDialogOpen(true)}
          sx={{ position: 'fixed', bottom: 80, right: 16 }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Sort Menu */}
      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={() => setFilterAnchorEl(null)}
      >
        <MenuItem onClick={() => handleSortChange('updated_at')}>
          Recently Updated
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('created_at')}>
          Recently Added
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('title')}>
          Title (A-Z)
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('author')}>
          Author (A-Z)
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('progress')}>
          Reading Progress
        </MenuItem>
      </Menu>

      {/* Book Menu */}
      <Menu
        anchorEl={bookMenuAnchorEl}
        open={Boolean(bookMenuAnchorEl)}
        onClose={handleBookMenuClose}
      >
        <MenuItem onClick={() => menuBook && handleEditBook(menuBook)}>
          <EditIcon sx={{ mr: 1 }} /> Edit
        </MenuItem>
        <MenuItem onClick={() => menuBook && handleToggleFavorite(menuBook)}>
          {menuBook?.is_favorite ? <StarIcon sx={{ mr: 1 }} /> : <StarBorderIcon sx={{ mr: 1 }} />}
          {menuBook?.is_favorite ? 'Remove from Favorites' : 'Add to Favorites'}
        </MenuItem>
        <MenuItem 
          onClick={() => menuBook && handleDeleteBook(menuBook)}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>

      {/* Dialogs */}
      <AddBookDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onBookAdded={() => {
          setAddDialogOpen(false);
          loadBooks();
        }}
      />
      
      <EditBookDialog
        open={editDialogOpen}
        book={selectedBook}
        onClose={() => {
          setEditDialogOpen(false);
          setSelectedBook(null);
        }}
        onBookUpdated={() => {
          setEditDialogOpen(false);
          setSelectedBook(null);
          loadBooks();
        }}
      />
    </Box>
  );
};

export default BooksManagement;