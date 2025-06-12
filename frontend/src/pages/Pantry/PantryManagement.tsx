import React, { useState, useEffect } from 'react';
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
  ingredient_id: z.string().min(1, 'Please select an ingredient'),
  quantity: z.number().min(0.1, 'Quantity must be greater than 0'),
  expiration_date: z.string().optional().or(z.literal('')),
});

type PantryItemFormData = {
  ingredient_id: string;
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

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PantryItemFormData>({
    resolver: zodResolver(pantryItemSchema),
  });

  const fetchPantryItems = async () => {
    try {
      setLoading(true);
      const items = await apiRequest<PantryItem[]>('GET', '/pantry');
      setPantryItems(items);
      setError(null);
    } catch (error: any) {
      setError('Failed to fetch pantry items');
      console.error('Error fetching pantry items:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchIngredients = async () => {
    try {
      const allIngredients = await apiRequest<Ingredient[]>('GET', '/ingredients');
      setIngredients(allIngredients);
    } catch (error: any) {
      console.error('Error fetching ingredients:', error);
    }
  };

  useEffect(() => {
    fetchPantryItems();
    fetchIngredients();
  }, []);

  const handleAddItem = () => {
    setEditingItem(null);
    reset({ ingredient_id: '', quantity: 1, expiration_date: '' });
    setIsDialogOpen(true);
  };

  const handleEditItem = (item: PantryItem) => {
    setEditingItem(item);
    reset({
      ingredient_id: item.ingredient_id,
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
      await fetchPantryItems();
    } catch (error: any) {
      setError('Failed to remove pantry item');
      console.error('Error removing pantry item:', error);
    }
  };

  const onSubmit = async (data: PantryItemFormData) => {
    try {
      setLoading(true);
      const itemData: PantryItemCreate = {
        ingredient_id: data.ingredient_id,
        quantity: data.quantity,
        expiration_date: data.expiration_date || undefined,
      };

      if (editingItem) {
        await apiRequest('PUT', `/pantry/${editingItem.ingredient_id}`, {
          quantity: itemData.quantity,
          expiration_date: itemData.expiration_date,
        });
      } else {
        await apiRequest('POST', '/pantry', itemData);
      }

      await fetchPantryItems();
      setIsDialogOpen(false);
      reset();
      setError(null);
    } catch (error: any) {
      setError(editingItem ? 'Failed to update pantry item' : 'Failed to add pantry item');
      console.error('Error saving pantry item:', error);
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

      <Dialog open={isDialogOpen} onClose={() => setIsDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>
            {editingItem ? 'Edit Pantry Item' : 'Add Pantry Item'}
          </DialogTitle>
          <DialogContent>
            <Controller
              name="ingredient_id"
              control={control}
              render={({ field }) => (
                <Autocomplete
                  {...field}
                  options={ingredients}
                  getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
                  value={ingredients.find(ing => ing.id === field.value) || null}
                  onChange={(_, value) => field.onChange(value?.id || '')}
                  disabled={!!editingItem}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Ingredient"
                      fullWidth
                      margin="dense"
                      variant="outlined"
                      error={!!errors.ingredient_id}
                      helperText={errors.ingredient_id?.message}
                    />
                  )}
                  renderOption={(props, option) => (
                    <li {...props}>
                      <Box>
                        <Typography variant="body1">{option.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {option.category} • {option.unit}
                        </Typography>
                      </Box>
                    </li>
                  )}
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
            <Button onClick={() => setIsDialogOpen(false)} disabled={loading}>
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