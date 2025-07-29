# TASK_014: Recipe Rating System V2

## Status: PENDING

## Overview
Redesign and implement a rating system compatible with the RecipeV2 architecture. The previous rating system was removed due to infinite loop issues with the recipe fetching logic.

## Objectives
1. Design a clean rating system for RecipeV2 model
2. Create rating API endpoints that don't interfere with recipe fetching
3. Build rating UI components with proper state management
4. Add rating aggregation and display

## Implementation Steps

### 1. Backend Model Updates
```python
# backend/app/models/recipe_v2.py - Add rating fields
class RecipeV2(Base):
    # ... existing fields ...
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

# backend/app/models/content.py - Use existing ContentRating model
class ContentRating(Base):
    # Already supports recipe_id field
    recipe_id = Column(UUID(as_uuid=True), ForeignKey('recipes_v2.id'), nullable=True)
```

### 2. API Endpoints
```python
# backend/app/api/recipes.py - Add rating endpoints
@router.post("/recipes/{recipe_id}/rate")
async def rate_recipe(
    recipe_id: str,
    rating: int = Body(..., ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user already rated
    existing_rating = db.query(ContentRating).filter(
        ContentRating.user_id == current_user.id,
        ContentRating.recipe_id == recipe_id
    ).first()
    
    if existing_rating:
        existing_rating.rating = rating
        existing_rating.updated_at = datetime.utcnow()
    else:
        new_rating = ContentRating(
            user_id=current_user.id,
            recipe_id=recipe_id,
            rating=rating
        )
        db.add(new_rating)
    
    # Update recipe average
    update_recipe_average_rating(recipe_id, db)
    db.commit()

@router.get("/recipes/{recipe_id}/rating")
async def get_recipe_rating(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recipe = db.query(RecipeV2).filter(RecipeV2.id == recipe_id).first()
    user_rating = db.query(ContentRating).filter(
        ContentRating.user_id == current_user.id,
        ContentRating.recipe_id == recipe_id
    ).first()
    
    return {
        "average_rating": recipe.average_rating,
        "rating_count": recipe.rating_count,
        "user_rating": user_rating.rating if user_rating else None
    }
```

### 3. Frontend Components
```typescript
// frontend/src/components/Recipe/RecipeRating.tsx
interface RecipeRatingProps {
  recipeId: string;
  averageRating: number;
  ratingCount: number;
  userRating?: number;
  onRate: (rating: number) => void;
  size?: 'small' | 'medium' | 'large';
}

// Separate component to avoid re-render issues
export const RecipeRating: React.FC<RecipeRatingProps> = ({...}) => {
  // Implement star rating UI
  // Use optimistic updates
  // Debounce rating submissions
}
```

### 4. State Management
```typescript
// frontend/src/hooks/useRecipeRating.ts
export const useRecipeRating = (recipeId: string) => {
  const [rating, setRating] = useState<RatingData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Fetch rating separately from recipe data
  // Implement optimistic updates
  // Cache ratings locally
  
  return { rating, isLoading, rateRecipe };
};
```

### 5. Integration Points
- Add rating display to SavedRecipes.tsx recipe cards
- Add rating component to recipe detail views
- Show average ratings in meal recommendations
- Include ratings in recipe search/filter

## Key Differences from V1
1. **Separate API calls**: Rating fetches are independent of recipe fetches
2. **Optimistic updates**: UI updates immediately, syncs in background
3. **Debounced submissions**: Prevents rapid API calls
4. **Local caching**: Reduces unnecessary API calls
5. **Component isolation**: Rating component doesn't trigger recipe re-fetches

## Success Criteria
- Users can rate recipes 1-5 stars
- Ratings update without page refresh
- No infinite loops or performance issues
- Average ratings visible on recipe cards
- User's own ratings are highlighted

## Dependencies
- RecipeV2 model
- ContentRating model
- SavedRecipes component
- Recipe API endpoints

## Estimated Time: 2-3 days