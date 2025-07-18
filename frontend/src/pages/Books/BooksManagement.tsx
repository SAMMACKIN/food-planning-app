import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
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
  Paper,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
  useDroppable,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
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
  ViewModule as GridViewIcon,
  ViewList as TableViewIcon,
  DragIndicator as DragIcon,
} from '@mui/icons-material';
import { Book, ReadingStatus, BookFilters } from '../../types';
import { booksApi, bookHelpers } from '../../services/booksApi';
import AddBookDialog from './AddBookDialog';
import EditBookDialog from './EditBookDialog';
import GoodreadsImportDialog from './GoodreadsImportDialog';
import StarRating from '../../components/Recipe/StarRating';

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
  const [pageSize, setPageSize] = useState(20);
  const [bookRatings, setBookRatings] = useState<Record<string, number>>({});
  
  // Filter and search state
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'title' | 'author' | 'updated_at' | 'created_at' | 'progress'>('updated_at');
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const [isDragMode, setIsDragMode] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  
  // Dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [bookMenuAnchorEl, setBookMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuBook, setMenuBook] = useState<Book | null>(null);
  
  // Drag and drop state
  const [activeBook, setActiveBook] = useState<Book | null>(null);
  
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Droppable column component
  const DroppableColumn: React.FC<{
    id: string;
    title: string;
    icon: React.ReactNode;
    books: Book[];
    children: React.ReactNode;
  }> = ({ id, title, icon, books, children }) => {
    const { isOver, setNodeRef } = useDroppable({
      id,
    });

    return (
      <Paper
        ref={setNodeRef}
        sx={{
          flex: 1,
          minWidth: 300,
          p: 2,
          minHeight: 400,
          bgcolor: isOver ? 'action.hover' : 'background.paper',
          border: isOver ? `2px dashed ${theme.palette.primary.main}` : '2px dashed transparent',
          transition: 'background-color 0.2s ease, border-color 0.2s ease',
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          {icon} {title}
          <Chip size="small" label={books.length} />
        </Typography>
        <SortableContext items={books.map(b => b.id)} strategy={verticalListSortingStrategy}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {children}
          </Box>
        </SortableContext>
      </Paper>
    );
  };

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
        page_size: pageSize,
        ...(tabs[selectedTab].status && { reading_status: tabs[selectedTab].status }),
        ...(searchTerm && { search: searchTerm }),
      };
      
      const response = await booksApi.getBooks(params);
      
      // Sort books on frontend
      const sortedBooks = bookHelpers.sortBooks(response.books, sortBy);
      
      setBooks(sortedBooks);
      setTotalBooks(response.total);
      setTotalPages(response.total_pages);
      
      // Load ratings for all books
      const ratings: Record<string, number> = {};
      await Promise.all(
        sortedBooks.map(async (book) => {
          try {
            const ratingData = await booksApi.getBookRating(book.id);
            if (ratingData.rating !== null) {
              ratings[book.id] = ratingData.rating;
            }
          } catch (error) {
            // Ignore errors for individual rating fetches
          }
        })
      );
      setBookRatings(ratings);
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
  }, [selectedTab, searchTerm, currentPage, sortBy, viewMode, pageSize]);
  
  // Update page size when view mode changes
  useEffect(() => {
    if (viewMode === 'table') {
      setPageSize(50);
    } else {
      setPageSize(20);
    }
    setCurrentPage(1); // Reset to first page when changing view
  }, [viewMode]);

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

  const handleRateBook = async (book: Book, rating: number) => {
    try {
      await booksApi.rateBook(book.id, rating);
      setBookRatings(prev => ({ ...prev, [book.id]: rating }));
    } catch (error: any) {
      console.error('Error rating book:', error);
      setError('Failed to rate book. Please try again.');
    }
  };

  // Drag and drop handlers
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    setActiveBook(books.find(book => book.id === active.id) || null);
  };

  const handleDragOver = (event: DragOverEvent) => {
    // Handle drag over logic if needed
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveBook(null);

    if (!over) return;

    const draggedBook = books.find(book => book.id === active.id);
    if (!draggedBook) return;

    // Determine new status based on drop zone
    let newStatus: ReadingStatus;
    const overId = over.id as string;
    
    if (overId === 'want_to_read') {
      newStatus = 'want_to_read';
    } else if (overId === 'reading') {
      newStatus = 'reading';
    } else if (overId === 'read') {
      newStatus = 'read';
    } else {
      return; // Invalid drop zone
    }

    if (draggedBook.reading_status === newStatus) return; // No change needed

    try {
      await booksApi.updateBook(draggedBook.id, { reading_status: newStatus });
      await loadBooks();
    } catch (error: any) {
      console.error('Error updating reading status:', error);
      setError('Failed to update reading status. Please try again.');
    }
  };

  // Draggable book card component
  const DraggableBookCard: React.FC<{ book: Book }> = ({ book }) => {
    const {
      attributes,
      listeners,
      setNodeRef,
      transform,
      transition,
      isDragging,
    } = useSortable({ 
      id: book.id,
      disabled: !isDragMode
    });

    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
      opacity: isDragging ? 0.5 : 1,
    };

    const progressPercent = bookHelpers.getProgressPercentage(book);
    const statusColor = bookHelpers.getStatusColor(book.reading_status);
    const estimatedTime = bookHelpers.getEstimatedReadingTime(book);
    
    // Create drag handle for specific area only
    const dragHandleProps = isDragMode ? { ...attributes, ...listeners } : {};
    
    return (
      <Card 
        ref={setNodeRef}
        style={style}
        sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          cursor: 'default',
          '&:hover': {
            transform: isDragMode ? 'scale(1.02)' : 'translateY(-2px)',
            boxShadow: theme.shadows[4],
          }
        }}
      >
        {/* Book cover placeholder or image */}
        <Box
          {...dragHandleProps}
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
            cursor: isDragMode ? 'grab' : 'default',
            '&:active': {
              cursor: isDragMode ? 'grabbing' : 'default',
            }
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
            onClick={(e) => {
              e.stopPropagation();
              handleBookMenuOpen(e, book);
            }}
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
          
          {/* Rating */}
          <Box sx={{ mt: 1 }}>
            <StarRating
              rating={bookRatings[book.id] || 0}
              onRatingChange={(rating) => handleRateBook(book, rating)}
              size="small"
              showZero={true}
            />
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
            onClick={(e) => {
              e.stopPropagation();
              handleEditBook(book);
            }}
            startIcon={<EditIcon />}
          >
            Edit
          </Button>
          {book.reading_status === 'reading' && (
            <Button
              size="small"
              color="primary"
              onClick={(e) => {
                e.stopPropagation();
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
    );
  };

  // Render book card (wrapper for backward compatibility)
  const renderBookCard = (book: Book) => {
    return <DraggableBookCard key={book.id} book={book} />;
  };

  // Render table view
  const renderTableView = () => {
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Cover</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Author</TableCell>
              <TableCell>Genre</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Rating</TableCell>
              <TableCell>Pages</TableCell>
              <TableCell>Year</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {books.map((book) => (
              <TableRow key={book.id} hover>
                <TableCell sx={{ width: 60 }}>
                  {book.cover_image_url ? (
                    <img
                      src={book.cover_image_url}
                      alt={book.title}
                      style={{
                        width: 40,
                        height: 60,
                        objectFit: 'cover',
                        borderRadius: 4,
                      }}
                    />
                  ) : (
                    <Box
                      sx={{
                        width: 40,
                        height: 60,
                        bgcolor: 'grey.200',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <BookIcon sx={{ color: 'grey.500' }} />
                    </Box>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
                    {book.title}
                  </Typography>
                  {book.is_favorite && (
                    <StarIcon sx={{ fontSize: 16, color: 'warning.main', ml: 0.5 }} />
                  )}
                </TableCell>
                <TableCell>{book.author}</TableCell>
                <TableCell>{book.genre || '-'}</TableCell>
                <TableCell>
                  <Chip
                    label={bookHelpers.getStatusDisplayText(book.reading_status)}
                    color={bookHelpers.getStatusColor(book.reading_status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <StarRating
                    rating={bookRatings[book.id] || 0}
                    onRatingChange={(rating) => handleRateBook(book, rating)}
                    size="small"
                    showZero={true}
                  />
                </TableCell>
                <TableCell>{book.pages || '-'}</TableCell>
                <TableCell>{book.publication_year || '-'}</TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => handleEditBook(book)}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleToggleFavorite(book)}
                  >
                    {book.is_favorite ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      setBookMenuAnchorEl(e.currentTarget);
                      setMenuBook(book);
                    }}
                  >
                    <MoreVertIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
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
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddDialogOpen(true)}
            >
              Add Book
            </Button>
            <Button
              variant="outlined"
              onClick={() => setImportDialogOpen(true)}
            >
              Import from Goodreads
            </Button>
          </Box>
        )}
      </Box>

      {/* Controls */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          {viewMode === 'grid' && (
            <Button
              variant={isDragMode ? 'contained' : 'outlined'}
              onClick={() => setIsDragMode(!isDragMode)}
              sx={{ textTransform: 'none' }}
            >
              {isDragMode ? '📚 Drag Mode: ON' : '🖱️ Enable Drag Mode'}
            </Button>
          )}
          
          <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, newMode) => newMode && setViewMode(newMode)}
              size="small"
            >
              <ToggleButton value="grid">
                <GridViewIcon fontSize="small" />
              </ToggleButton>
              <ToggleButton value="table">
                <TableViewIcon fontSize="small" />
              </ToggleButton>
            </ToggleButtonGroup>
            
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
        />
        
        {isDragMode && (
          <Alert severity="info" sx={{ mt: 2 }}>
            💡 Drag books between sections to change their reading status
          </Alert>
        )}
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

      {/* Books Content */}
      {!loading && (
        <>
          {books.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <BookIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm ? 'No books found' : 'No books yet'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {searchTerm 
                  ? 'Try adjusting your search terms'
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
          ) : viewMode === 'table' ? (
            // Table view
            renderTableView()
          ) : (
            // Grid view with drag and drop
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
            >
              {isDragMode ? (
                // Kanban-style layout for drag mode
                <Box sx={{ display: 'flex', gap: 3, overflowX: 'auto', minHeight: 400 }}>
                  {/* Want to Read Column */}
                  <DroppableColumn
                    id="want_to_read"
                    title="Want to Read"
                    icon={<WantToReadIcon />}
                    books={books.filter(b => b.reading_status === 'want_to_read')}
                  >
                    {books.filter(b => b.reading_status === 'want_to_read').map(book => (
                      <DraggableBookCard key={book.id} book={book} />
                    ))}
                  </DroppableColumn>

                  {/* Currently Reading Column */}
                  <DroppableColumn
                    id="reading"
                    title="Currently Reading"
                    icon={<ReadingIcon />}
                    books={books.filter(b => b.reading_status === 'reading')}
                  >
                    {books.filter(b => b.reading_status === 'reading').map(book => (
                      <DraggableBookCard key={book.id} book={book} />
                    ))}
                  </DroppableColumn>

                  {/* Read Column */}
                  <DroppableColumn
                    id="read"
                    title="Read"
                    icon={<CompletedIcon />}
                    books={books.filter(b => b.reading_status === 'read')}
                  >
                    {books.filter(b => b.reading_status === 'read').map(book => (
                      <DraggableBookCard key={book.id} book={book} />
                    ))}
                  </DroppableColumn>
                </Box>
              ) : (
                // Normal grid layout
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr', lg: '1fr 1fr 1fr 1fr' }, gap: 3 }}>
                  {books.map(book => (
                    <DraggableBookCard key={book.id} book={book} />
                  ))}
                </Box>
              )}

              <DragOverlay>
                {activeBook ? <DraggableBookCard book={activeBook} /> : null}
              </DragOverlay>
            </DndContext>
          )}
          
          {/* Pagination */}
          {(totalPages > 1 || totalBooks > 0) && (
            <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              {totalPages > 1 && (
                <Pagination
                  count={totalPages}
                  page={currentPage}
                  onChange={(event, page) => setCurrentPage(page)}
                  color="primary"
                  size={isMobile ? 'small' : 'medium'}
                  showFirstButton
                  showLastButton
                />
              )}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Page {currentPage} of {totalPages} • Showing {books.length} of {totalBooks} books
                </Typography>
                {viewMode === 'table' && (
                  <TextField
                    select
                    size="small"
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    sx={{ width: 100 }}
                  >
                    <MenuItem value={20}>20 per page</MenuItem>
                    <MenuItem value={50}>50 per page</MenuItem>
                    <MenuItem value={100}>100 per page</MenuItem>
                  </TextField>
                )}
              </Box>
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
      
      <GoodreadsImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onImportComplete={() => {
          setImportDialogOpen(false);
          loadBooks();
        }}
      />
    </Box>
  );
};

export default BooksManagement;