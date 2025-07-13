import React, { useState } from 'react';
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
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Close as CloseIcon, AutoFixHigh, Psychology } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { BookCreate, ReadingStatus } from '../../types';
import { booksApi } from '../../services/booksApi';

const bookSchema = z.object({
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

type BookFormData = z.infer<typeof bookSchema>;

interface AddBookDialogProps {
  open: boolean;
  onClose: () => void;
  onBookAdded: () => void;
}

const AddBookDialog: React.FC<AddBookDialogProps> = ({
  open,
  onClose,
  onBookAdded,
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
    resolver: zodResolver(bookSchema),
    defaultValues: {
      title: '',
      author: '',
      description: '',
      genre: '',
      isbn: '',
      pages: undefined,
      publication_year: undefined,
      cover_image_url: '',
      reading_status: 'want_to_read',
      current_page: 0,
      is_favorite: false,
      user_notes: '',
    },
  });

  const readingStatus = watch('reading_status');
  const pages = watch('pages');

  // Genre suggestions
  const commonGenres = [
    'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction', 
    'Fantasy', 'Biography', 'History', 'Self-Help', 'Business',
    'Health', 'Travel', 'Cooking', 'Art', 'Philosophy', 'Psychology',
    'Science', 'Technology', 'Poetry', 'Drama', 'Thriller', 'Horror',
    'Young Adult', 'Children\'s', 'Comics', 'Memoir'
  ];

  const handleClose = () => {
    reset();
    setError(null);
    setAutoFilledFields(new Set());
    onClose();
  };

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
      
      // Auto-fill fields that are empty or unchanged
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

  const getAutoFilledFieldProps = (fieldName: string) => ({
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
      : undefined,
    FormHelperTextProps: autoFilledFields.has(fieldName) ? {
      sx: { color: 'success.main' }
    } : undefined,
  });

  const onSubmit = async (data: BookFormData) => {
    try {
      setLoading(true);
      setError(null);

      // Clean up data
      const bookData: BookCreate = {
        title: data.title,
        author: data.author,
        description: data.description || undefined,
        genre: data.genre || undefined,
        isbn: data.isbn || undefined,
        pages: data.pages === null ? undefined : data.pages,
        publication_year: data.publication_year === null ? undefined : data.publication_year,
        cover_image_url: data.cover_image_url || undefined,
        reading_status: data.reading_status,
        user_notes: data.user_notes || undefined,
        current_page: data.current_page || 0,
        is_favorite: data.is_favorite || false,
      };

      await booksApi.createBook(bookData);
      onBookAdded();
      handleClose();
    } catch (error: any) {
      console.error('Error adding book:', error);
      setError(error.response?.data?.detail || 'Failed to add book. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
        <Typography variant="h6" component="div">
          📚 Add New Book
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
                  autoFocus
                />
                
                <TextField
                  {...register('author')}
                  label="Author *"
                  fullWidth
                  error={!!errors.author}
                  helperText={errors.author?.message}
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
                    {autoFillLoading ? 'Fetching Details...' : 'Auto-fill Book Details'}
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
                          helperText={errors.genre?.message}
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
                  helperText={errors.description?.message || getAutoFilledFieldProps('description').helperText}
                  FormHelperTextProps={getAutoFilledFieldProps('description').FormHelperTextProps}
                  sx={getAutoFilledFieldProps('description').sx}
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
                    helperText={errors.isbn?.message}
                  />
                  
                  <TextField
                    {...register('pages', { 
                      setValueAs: (v) => (v === '' ? undefined : Number(v))
                    })}
                    label="Total Pages (Optional)"
                    type="number"
                    fullWidth
                    error={!!errors.pages}
                    helperText={errors.pages?.message}
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
                    helperText={errors.publication_year?.message}
                    inputProps={{ min: 1, max: new Date().getFullYear() + 1 }}
                  />
                </Box>
                
                <TextField
                  {...register('cover_image_url')}
                  label="Cover Image URL"
                  fullWidth
                  error={!!errors.cover_image_url}
                  helperText={errors.cover_image_url?.message}
                  placeholder="https://example.com/book-cover.jpg"
                />
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
                
                {readingStatus === 'reading' && (
                  <TextField
                    {...register('current_page', { valueAsNumber: true })}
                    label="Current Page"
                    type="number"
                    fullWidth
                    error={!!errors.current_page}
                    helperText={errors.current_page?.message || (pages ? `Out of ${pages} pages` : '')}
                    inputProps={{ min: 0, max: pages || undefined }}
                  />
                )}
                
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
            {loading ? 'Adding...' : 'Add Book'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AddBookDialog;