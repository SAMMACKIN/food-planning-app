import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Autocomplete,
  IconButton,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { Add, Edit, Delete, Kitchen, Search } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { PantryItem, PantryItemCreate, Ingredient } from '../../types';
import { apiRequest } from '../../services/api';

const pantryItemSchema = z.object({
  ingredient_ids: z.array(z.string()).min(1, 'Please select at least one ingredient'),
  quantity: z.number().min(0.1, 'Quantity must be greater than 0'),
  expiration_date: z.string().optional().or(z.literal('')),
});

type PantryItemFormData = {
  ingredient_ids: string[];
  quantity: number;
  expiration_date?: string;
};

const PantryManagement: React.FC = () => {
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [ingredientSearchTerm, setIngredientSearchTerm] = useState('');
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const lastScrollPosition = useRef<number>(0);

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PantryItemFormData>({
    resolver: zodResolver(pantryItemSchema),
  });

  const saveScrollPosition = () => {
    if (scrollContainerRef.current) {
      lastScrollPosition.current = scrollContainerRef.current.scrollTop;
    }
  };

  const restoreScrollPosition = () => {
    setTimeout(() => {
      if (scrollContainerRef.current && lastScrollPosition.current > 0) {
        scrollContainerRef.current.scrollTop = lastScrollPosition.current;
      }
    }, 50);
  };

  const fetchPantryItems = async (preserveScroll = false) => {
    console.log('🍴 fetchPantryItems called - starting fetch...');
    try {
      setLoading(true);
      
      // Save scroll position if requested
      if (preserveScroll) {
        saveScrollPosition();
      }
      
      const items = await apiRequest<PantryItem[]>('GET', '/pantry', null, { requestType: 'navigation' });
      setPantryItems(items);
      setError(null);
      
      // Restore scroll position after a short delay to allow rendering
      if (preserveScroll) {
        restoreScrollPosition();
      }
    } catch (error: any) {
      setError('Failed to fetch pantry items');
      console.error('Error fetching pantry items:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchIngredients = async (search = '') => {
    try {
      const endpoint = search.trim() 
        ? `/ingredients/search?q=${encodeURIComponent(search.trim())}`
        : '/ingredients';
      const allIngredients = await apiRequest<Ingredient[]>('GET', endpoint);
      setIngredients(allIngredients);
    } catch (error: any) {
      console.error('Error fetching ingredients:', error);
    }
  };

  useEffect(() => {
    console.log('🥘 PantryManagement mounted - fetching data...');
    fetchPantryItems();
    fetchIngredients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search ingredients when search term changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (ingredientSearchTerm.trim()) {
        fetchIngredients(ingredientSearchTerm);
      } else {
        fetchIngredients();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [ingredientSearchTerm]);

  const handleAddItem = () => {
    saveScrollPosition();
    setEditingItem(null);
    reset({ ingredient_ids: [], quantity: 1, expiration_date: '' });
    setIsDialogOpen(true);
  };

  const handleEditItem = (item: PantryItem) => {
    saveScrollPosition();
    setEditingItem(item);
    reset({
      ingredient_ids: [item.ingredient_id],
      quantity: item.quantity,
      expiration_date: item.expiration_date || '',
    });
    setIsDialogOpen(true);
  };

  const handleDeleteItem = async (ingredientId: string) => {
    if (!window.confirm('Are you sure you want to remove this item from your pantry?')) {
      return;
    }

    try {
      await apiRequest('DELETE', `/pantry/${ingredientId}`);
      await fetchPantryItems(true); // Preserve scroll position
    } catch (error: any) {
      setError('Failed to remove pantry item');
      console.error('Error removing pantry item:', error);
    }
  };

  const onSubmit = async (data: PantryItemFormData) => {
    try {
      setLoading(true);
      
      if (editingItem) {
        // For editing, we only update the single item
        await apiRequest('PUT', `/pantry/${editingItem.ingredient_id}`, {
          quantity: data.quantity,
          expiration_date: data.expiration_date || undefined,
        });
      } else {
        // For adding new items, create multiple items if multiple ingredients selected
        const promises = data.ingredient_ids.map(ingredientId => {
          const itemData: PantryItemCreate = {
            ingredient_id: ingredientId,
            quantity: data.quantity,
            expiration_date: data.expiration_date || undefined,
          };
          return apiRequest('POST', '/pantry', itemData);
        });
        
        await Promise.all(promises);
      }

      await fetchPantryItems(true); // Preserve scroll position
      setIsDialogOpen(false);
      reset();
      setError(null);
      restoreScrollPosition(); // Restore scroll after dialog closes
    } catch (error: any) {
      setError(editingItem ? 'Failed to update pantry item' : 'Failed to add pantry items');
      console.error('Error saving pantry items:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = pantryItems.filter(item =>
    item.ingredient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.ingredient.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const groupedItems = filteredItems.reduce((acc, item) => {
    const category = item.ingredient.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {} as Record<string, PantryItem[]>);

  const formatExpirationDate = (dateString?: string) => {
    if (!dateString) return 'No expiration';
    const date = new Date(dateString);
    const today = new Date();
    const diffTime = date.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Expired';
    if (diffDays === 0) return 'Expires today';
    if (diffDays === 1) return 'Expires tomorrow';
    return `Expires in ${diffDays} days`;
  };

  const getExpirationColor = (dateString?: string) => {
    if (!dateString) return 'default';
    const date = new Date(dateString);
    const today = new Date();
    const diffTime = date.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'error';
    if (diffDays <= 3) return 'warning';
    return 'success';
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Pantry Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleAddItem}
          disabled={loading}
        >
          Add Item
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search ingredients..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
      </Box>

      <Box 
        ref={scrollContainerRef}
        sx={{ 
          maxHeight: 'calc(100vh - 200px)', 
          overflowY: 'auto', 
          pr: 1 
        }}
      >
        {filteredItems.length === 0 && !loading ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Kitchen sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {pantryItems.length === 0 ? 'Your pantry is empty' : 'No items match your search'}
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={3}>
                {pantryItems.length === 0 
                  ? 'Add ingredients to start tracking your pantry inventory'
                  : 'Try adjusting your search terms'
                }
              </Typography>
              {pantryItems.length === 0 && (
                <Button variant="contained" startIcon={<Add />} onClick={handleAddItem}>
                  Add Your First Item
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          Object.entries(groupedItems).map(([category, items]) => (
            <Box key={category} mb={4}>
              <Typography variant="h6" gutterBottom sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
                {category}
              </Typography>
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Ingredient</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell>Expiration</TableCell>
                      <TableCell>Allergens</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item) => (
                      <TableRow key={item.ingredient_id}>
                        <TableCell>
                          <Typography variant="body1">{item.ingredient.name}</Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {item.quantity} {item.ingredient.unit}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={formatExpirationDate(item.expiration_date)}
                            color={getExpirationColor(item.expiration_date) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" flexWrap="wrap" gap={0.5}>
                            {item.ingredient.allergens.map((allergen, index) => (
                              <Chip key={index} label={allergen} size="small" variant="outlined" />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() => handleEditItem(item)}
                            disabled={loading}
                          >
                            <Edit />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteItem(item.ingredient_id)}
                            disabled={loading}
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ))
        )}
      </Box>

      <Dialog 
        open={isDialogOpen} 
        onClose={() => {
          setIsDialogOpen(false);
          restoreScrollPosition();
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>
            {editingItem ? 'Edit Pantry Item' : 'Add Pantry Items'}
          </DialogTitle>
          <DialogContent>
            <Controller
              name="ingredient_ids"
              control={control}
              render={({ field }) => (
                <Autocomplete
                  multiple={!editingItem}
                  options={ingredients}
                  getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
                  value={editingItem 
                    ? ingredients.filter(ing => field.value.includes(ing.id))
                    : ingredients.filter(ing => field.value.includes(ing.id))
                  }
                  onChange={(_, value) => {
                    const ids = Array.isArray(value) 
                      ? value.map(v => typeof v === 'string' ? v : v.id)
                      : [typeof value === 'string' ? value : value?.id || ''];
                    field.onChange(ids.filter(Boolean));
                  }}
                  disabled={!!editingItem}
                  filterSelectedOptions
                  loading={loading}
                  disableCloseOnSelect={!editingItem}
                  onInputChange={(_, newInputValue, reason) => {
                    if (reason === 'input') {
                      setIngredientSearchTerm(newInputValue);
                    }
                  }}
                  groupBy={(option) => option.category}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={editingItem ? "Ingredient" : "Ingredients (select multiple)"}
                      fullWidth
                      margin="dense"
                      variant="outlined"
                      error={!!errors.ingredient_ids}
                      helperText={errors.ingredient_ids?.message || (!editingItem ? "Type to search ingredients, select multiple with checkboxes" : "")}
                      InputProps={{
                        ...params.InputProps,
                        startAdornment: (
                          <>
                            <Search sx={{ mr: 1, color: 'text.secondary' }} />
                            {params.InputProps.startAdornment}
                          </>
                        ),
                      }}
                    />
                  )}
                  renderOption={(props, option, { selected }) => (
                    <li {...props}>
                      <Box display="flex" alignItems="center" width="100%">
                        {!editingItem && (
                          <Box component="span" sx={{ width: 17, height: 17, mr: 1, flexShrink: 0 }}>
                            {selected ? '✓' : ''}
                          </Box>
                        )}
                        <Box flex={1}>
                          <Typography variant="body1">{option.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {option.category} • {option.unit} • {option.calories_per_unit} cal/{option.unit}
                          </Typography>
                        </Box>
                      </Box>
                    </li>
                  )}
                  renderGroup={(params) => (
                    <Box key={params.key}>
                      <Typography variant="subtitle2" sx={{ px: 2, py: 1, fontWeight: 'bold', color: 'primary.main' }}>
                        {params.group}
                      </Typography>
                      {params.children}
                    </Box>
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option.name}
                        {...getTagProps({ index })}
                        key={option.id}
                        size="small"
                        color="primary"
                      />
                    ))
                  }
                />
              )}
            />
            <TextField
              margin="dense"
              label="Quantity"
              type="number"
              fullWidth
              variant="outlined"
              inputProps={{ step: "0.1", min: "0.1" }}
              {...register('quantity', { valueAsNumber: true })}
              error={!!errors.quantity}
              helperText={errors.quantity?.message}
              sx={{ mt: 2 }}
            />
            <TextField
              margin="dense"
              label="Expiration Date (optional)"
              type="date"
              fullWidth
              variant="outlined"
              InputLabelProps={{ shrink: true }}
              {...register('expiration_date')}
              error={!!errors.expiration_date}
              helperText={errors.expiration_date?.message}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={() => {
                setIsDialogOpen(false);
                restoreScrollPosition();
              }} 
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? 'Saving...' : editingItem ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default PantryManagement;