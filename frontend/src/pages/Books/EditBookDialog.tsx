import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  IconButton,
  Alert,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Close as CloseIcon, AutoFixHigh, Psychology } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Book, BookUpdate, ReadingStatus } from '../../types';
import { booksApi, bookHelpers } from '../../services/booksApi';

const bookUpdateSchema = z.object({
  title: z.string().min(1, 'Title is required').max(500, 'Title is too long'),
  author: z.string().min(1, 'Author is required').max(300, 'Author name is too long'),
  description: z.string().max(5000, 'Description is too long').optional().or(z.literal('')),
  genre: z.string().max(100, 'Genre is too long').optional().or(z.literal('')),
  isbn: z.string().max(20, 'ISBN is too long').optional().or(z.literal('')),
  pages: z.union([
    z.number().min(1, 'Pages must be at least 1').max(10000, 'Pages must be less than 10,000'),
    z.nan(),
    z.undefined()
  ]).optional(),
  publication_year: z.union([
    z.number().min(1, 'Year must be valid').max(new Date().getFullYear() + 1, 'Year cannot be in the future'),
    z.nan(),
    z.undefined()
  ]).optional(),
  cover_image_url: z.string().url('Invalid URL').optional().or(z.literal('')),
  reading_status: z.enum(['want_to_read', 'reading', 'read'] as const),
  current_page: z.number().min(0, 'Current page cannot be negative').optional(),
  is_favorite: z.boolean().optional(),
  user_notes: z.string().max(5000, 'Notes are too long').optional().or(z.literal('')),
});

type BookFormData = z.infer<typeof bookUpdateSchema>;

interface EditBookDialogProps {
  open: boolean;
  book: Book | null;
  onClose: () => void;
  onBookUpdated: () => void;
}

const EditBookDialog: React.FC<EditBookDialogProps> = ({
  open,
  book,
  onClose,
  onBookUpdated,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [autoFilledFields, setAutoFilledFields] = useState<Set<string>>(new Set());

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BookFormData>({
    resolver: zodResolver(bookUpdateSchema),
  });

  const readingStatus = watch('reading_status');
  const pages = watch('pages');
  const currentPage = watch('current_page');

  // Genre suggestions
  const commonGenres = [
    'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction', 
    'Fantasy', 'Biography', 'History', 'Self-Help', 'Business',
    'Health', 'Travel', 'Cooking', 'Art', 'Philosophy', 'Psychology',
    'Science', 'Technology', 'Poetry', 'Drama', 'Thriller', 'Horror',
    'Young Adult', 'Children\'s', 'Comics', 'Memoir'
  ];

  // Initialize form when book changes
  useEffect(() => {
    if (book) {
      reset({
        title: book.title,
        author: book.author,
        description: book.description || '',
        genre: book.genre || '',
        isbn: book.isbn || '',
        pages: book.pages || undefined,
        publication_year: book.publication_year || undefined,
        cover_image_url: book.cover_image_url || '',
        reading_status: book.reading_status,
        current_page: book.current_page,
        is_favorite: book.is_favorite,
        user_notes: book.user_notes || '',
      });
      setError(null);
    }
  }, [book, reset]);

  const handleClose = () => {
    setError(null);
    setAutoFilledFields(new Set());
    onClose();
  };

  const getAutoFilledFieldProps = (fieldName: string, originalHelperText?: string) => ({
    sx: autoFilledFields.has(fieldName) ? {
      '& .MuiOutlinedInput-root': {
        backgroundColor: 'success.light',
        '& fieldset': {
          borderColor: 'success.main',
        },
      },
      '& .MuiInputLabel-root': {
        color: 'success.main',
      },
    } : undefined,
    helperText: autoFilledFields.has(fieldName) 
      ? '✨ Auto-filled by AI' 
      : originalHelperText,
    FormHelperTextProps: autoFilledFields.has(fieldName) ? {
      sx: { color: 'success.main' }
    } : undefined,
  });

  const handleAutoFill = async () => {
    const title = watch('title');
    const author = watch('author');
    
    if (!title.trim()) {
      setError('Please enter a book title before using auto-fill');
      return;
    }
    
    try {
      setAutoFillLoading(true);
      setError(null);
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/books/fetch-details`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          title: title.trim(),
          author: author.trim() || null
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch book details');
      }
      
      const bookDetails = await response.json();
      const newAutoFilledFields = new Set<string>();
      
      // Auto-fill fields that are empty or significantly different
      if (bookDetails.publication_year && !watch('publication_year')) {
        setValue('publication_year', bookDetails.publication_year);
        newAutoFilledFields.add('publication_year');
      }
      
      if (bookDetails.pages && !watch('pages')) {
        setValue('pages', bookDetails.pages);
        newAutoFilledFields.add('pages');
      }
      
      if (bookDetails.genre && !(watch('genre') || '').trim()) {
        setValue('genre', bookDetails.genre);
        newAutoFilledFields.add('genre');
      }
      
      if (bookDetails.description && !(watch('description') || '').trim()) {
        setValue('description', bookDetails.description);
        newAutoFilledFields.add('description');
      }
      
      if (bookDetails.isbn && !(watch('isbn') || '').trim()) {
        setValue('isbn', bookDetails.isbn);
        newAutoFilledFields.add('isbn');
      }
      
      if (bookDetails.cover_image_url && !(watch('cover_image_url') || '').trim()) {
        setValue('cover_image_url', bookDetails.cover_image_url);
        newAutoFilledFields.add('cover_image_url');
      }
      
      // Update author if it was empty and we got a better match
      if (bookDetails.author && !author.trim()) {
        setValue('author', bookDetails.author);
        newAutoFilledFields.add('author');
      }
      
      setAutoFilledFields(newAutoFilledFields);
      
      if (newAutoFilledFields.size > 0) {
        // Show success message
        const filledCount = newAutoFilledFields.size;
        setError(`✅ Auto-filled ${filledCount} field${filledCount > 1 ? 's' : ''} successfully!`);
        setTimeout(() => setError(null), 3000);
      } else {
        setError('No additional book details found to auto-fill');
        setTimeout(() => setError(null), 3000);
      }
      
    } catch (error) {
      console.error('Auto-fill error:', error);
      setError('Failed to fetch book details. Please try again or fill in manually.');
    } finally {
      setAutoFillLoading(false);
    }
  };

  const onSubmit = async (data: BookFormData) => {
    if (!book) return;

    try {
      setLoading(true);
      setError(null);

      // Clean up data - only send changed fields
      const updateData: BookUpdate = {};
      
      if (data.title !== book.title) updateData.title = data.title;
      if (data.author !== book.author) updateData.author = data.author;
      if (data.description !== (book.description || '')) updateData.description = data.description || undefined;
      if (data.genre !== (book.genre || '')) updateData.genre = data.genre || undefined;
      if (data.isbn !== (book.isbn || '')) updateData.isbn = data.isbn || undefined;
      if (data.pages !== book.pages) updateData.pages = data.pages || undefined;
      if (data.publication_year !== book.publication_year) updateData.publication_year = data.publication_year || undefined;
      if (data.cover_image_url !== (book.cover_image_url || '')) updateData.cover_image_url = data.cover_image_url || undefined;
      if (data.reading_status !== book.reading_status) updateData.reading_status = data.reading_status;
      if (data.current_page !== book.current_page) updateData.current_page = data.current_page || 0;
      if (data.is_favorite !== book.is_favorite) updateData.is_favorite = data.is_favorite;
      if (data.user_notes !== (book.user_notes || '')) updateData.user_notes = data.user_notes || undefined;

      await booksApi.updateBook(book.id, updateData);
      onBookUpdated();
    } catch (error: any) {
      console.error('Error updating book:', error);
      setError(error.response?.data?.detail || 'Failed to update book. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickProgressUpdate = async (newPage: number) => {
    if (!book) return;

    try {
      await booksApi.updateReadingProgress(book.id, newPage);
      setValue('current_page', newPage);
      
      // Update status based on progress
      if (newPage === 0) {
        setValue('reading_status', 'want_to_read');
      } else if (pages && newPage >= pages) {
        setValue('reading_status', 'read');
      } else {
        setValue('reading_status', 'reading');
      }
    } catch (error: any) {
      console.error('Error updating progress:', error);
      setError('Failed to update reading progress. Please try again.');
    }
  };

  if (!book) return null;

  const progressPercent = pages ? Math.round(((currentPage || 0) / pages) * 100) : 0;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
      PaperProps={{
        sx: {
          borderRadius: isMobile ? 0 : 2,
          ...(isMobile && {
            margin: 0,
            width: '100%',
            height: '100%',
          }),
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 2,
        }}
      >
        <Typography variant="h6" component="div" noWrap>
          📝 Edit "{book.title}"
        </Typography>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent sx={{ pb: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Reading Progress Card (if reading) */}
            {readingStatus === 'reading' && pages && (
              <Box
                sx={{
                  p: 2,
                  border: 1,
                  borderColor: 'primary.main',
                  borderRadius: 2,
                  bgcolor: 'primary.50',
                }}
              >
                <Typography variant="subtitle2" gutterBottom>
                  📖 Quick Progress Update
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    Page {currentPage || 0} of {pages}
                  </Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {progressPercent}%
                  </Typography>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={progressPercent}
                  sx={{ height: 8, borderRadius: 4, mb: 2 }}
                />
                
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleQuickProgressUpdate((currentPage || 0) + 10)}
                    disabled={!pages || (currentPage || 0) >= pages}
                  >
                    +10 pages
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleQuickProgressUpdate((currentPage || 0) + 25)}
                    disabled={!pages || (currentPage || 0) >= pages}
                  >
                    +25 pages
                  </Button>
                  {pages && (
                    <Button
                      size="small"
                      variant="contained"
                      color="success"
                      onClick={() => handleQuickProgressUpdate(pages)}
                      disabled={(currentPage || 0) >= pages}
                    >
                      Finished!
                    </Button>
                  )}
                </Box>
              </Box>
            )}

            {/* Basic Information */}
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Basic Information
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  {...register('title')}
                  label="Title *"
                  fullWidth
                  error={!!errors.title}
                  helperText={errors.title?.message}
                />
                
                <TextField
                  {...register('author')}
                  label="Author *"
                  fullWidth
                  error={!!errors.author}
                  {...getAutoFilledFieldProps('author', errors.author?.message)}
                />
                
                {/* Auto-fill Button */}
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
                  <Button
                    variant="outlined"
                    onClick={handleAutoFill}
                    disabled={autoFillLoading || !watch('title').trim()}
                    startIcon={autoFillLoading ? <Psychology sx={{ animation: 'pulse 2s infinite' }} /> : <AutoFixHigh />}
                    sx={{
                      borderColor: 'primary.main',
                      color: 'primary.main',
                      '&:hover': {
                        backgroundColor: 'primary.main',
                        color: 'white',
                      },
                      '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.5 },
                        '100%': { opacity: 1 },
                      },
                    }}
                  >
                    {autoFillLoading ? 'Fetching Details...' : 'Auto-fill Missing Details'}
                  </Button>
                </Box>
                
                <Controller
                  name="genre"
                  control={control}
                  render={({ field }) => (
                    <Autocomplete
                      {...field}
                      options={commonGenres}
                      freeSolo
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Genre"
                          error={!!errors.genre}
                          {...getAutoFilledFieldProps('genre', errors.genre?.message)}
                        />
                      )}
                      onChange={(_, value) => field.onChange(value || '')}
                      value={field.value || ''}
                    />
                  )}
                />
                
                <TextField
                  {...register('description')}
                  label="Description"
                  fullWidth
                  multiline
                  rows={3}
                  error={!!errors.description}
                  {...getAutoFilledFieldProps('description', errors.description?.message)}
                />
              </Box>
            </Box>

            {/* Book Details */}
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Book Details
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, flexDirection: isMobile ? 'column' : 'row' }}>
                  <TextField
                    {...register('isbn')}
                    label="ISBN"
                    fullWidth
                    error={!!errors.isbn}
                    {...getAutoFilledFieldProps('isbn', errors.isbn?.message)}
                  />
                  
                  <TextField
                    {...register('pages', { 
                      setValueAs: (v) => (v === '' ? undefined : Number(v))
                    })}
                    label="Total Pages (Optional)"
                    type="number"
                    fullWidth
                    error={!!errors.pages}
                    {...getAutoFilledFieldProps('pages', errors.pages?.message)}
                    inputProps={{ min: 1, max: 10000 }}
                  />
                  
                  <TextField
                    {...register('publication_year', { 
                      setValueAs: (v) => (v === '' ? undefined : Number(v))
                    })}
                    label="Publication Year (Optional)"
                    type="number"
                    fullWidth
                    error={!!errors.publication_year}
                    {...getAutoFilledFieldProps('publication_year', errors.publication_year?.message)}
                    inputProps={{ min: 1, max: new Date().getFullYear() + 1 }}
                  />
                </Box>
                
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <TextField
                    {...register('cover_image_url')}
                    label="Cover Image URL"
                    fullWidth
                    error={!!errors.cover_image_url}
                    {...getAutoFilledFieldProps('cover_image_url', errors.cover_image_url?.message)}
                    placeholder="https://example.com/book-cover.jpg"
                  />
                  
                  {/* Cover Image Preview */}
                  {watch('cover_image_url') && (
                    <Box
                      sx={{
                        minWidth: 80,
                        height: 120,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 1,
                        overflow: 'hidden',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: 'grey.50'
                      }}
                    >
                      <img
                        src={watch('cover_image_url')}
                        alt="Book cover preview"
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                          (e.target as HTMLImageElement).parentElement!.innerHTML = '📖';
                        }}
                      />
                    </Box>
                  )}
                </Box>
              </Box>
            </Box>

            {/* Reading Information */}
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Reading Information
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Controller
                  name="reading_status"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth>
                      <InputLabel>Reading Status</InputLabel>
                      <Select {...field} label="Reading Status">
                        <MenuItem value="want_to_read">Want to Read</MenuItem>
                        <MenuItem value="reading">Currently Reading</MenuItem>
                        <MenuItem value="read">Read</MenuItem>
                      </Select>
                    </FormControl>
                  )}
                />
                
                <TextField
                  {...register('current_page', { valueAsNumber: true })}
                  label="Current Page"
                  type="number"
                  fullWidth
                  error={!!errors.current_page}
                  helperText={errors.current_page?.message || (pages ? `Out of ${pages} pages` : '')}
                  inputProps={{ min: 0, max: pages || undefined }}
                />
                
                <TextField
                  {...register('user_notes')}
                  label="Personal Notes"
                  fullWidth
                  multiline
                  rows={2}
                  error={!!errors.user_notes}
                  helperText={errors.user_notes?.message}
                  placeholder="Your thoughts, quotes, or reminders about this book..."
                />
                
                <Controller
                  name="is_favorite"
                  control={control}
                  render={({ field }) => (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Button
                        variant={field.value ? 'contained' : 'outlined'}
                        color={field.value ? 'warning' : 'inherit'}
                        onClick={() => field.onChange(!field.value)}
                        size="small"
                      >
                        {field.value ? '⭐ Favorite' : '☆ Add to Favorites'}
                      </Button>
                    </Box>
                  )}
                />
              </Box>
            </Box>
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button
            onClick={handleClose}
            disabled={loading}
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            sx={{ minWidth: 100 }}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default EditBookDialog;