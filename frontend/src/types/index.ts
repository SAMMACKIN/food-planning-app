export interface User {
  id: string;
  email: string;
  name?: string;
  timezone: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface UserPreferences {
  [key: string]: any;
}

export interface FamilyMember {
  id: string;
  user_id: string;
  name: string;
  age?: number;
  dietary_restrictions: string[];
  preferences: FamilyMemberPreferences;
  created_at: string;
}

export interface FamilyMemberCreate {
  name: string;
  age?: number;
  dietary_restrictions?: string[];
  preferences?: FamilyMemberPreferences;
}

export interface FamilyMemberUpdate {
  name?: string;
  age?: number;
  dietary_restrictions?: string[];
  preferences?: FamilyMemberPreferences;
}

export interface DietaryRestriction {
  id: string;
  name: string;
  description: string;
  type: 'allergy' | 'intolerance' | 'preference' | 'medical';
}

export interface FamilyMemberPreferences {
  likes: string[];
  dislikes: string[];
  preferred_cuisines: string[];
  spice_level: number;
  [key: string]: any;
}

export interface Ingredient {
  id: string;
  name: string;
  category: string;
  unit: string;
  calories_per_unit: number;
  protein_per_unit: number;
  carbs_per_unit: number;
  fat_per_unit: number;
  allergens: string[];
  created_at: string;
}

export interface IngredientCreate {
  name: string;
  category: string;
  unit: string;
  calories_per_unit?: number;
  protein_per_unit?: number;
  carbs_per_unit?: number;
  fat_per_unit?: number;
  allergens?: string[];
}

export interface NutritionalInfo {
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber?: number;
  sugar?: number;
  sodium?: number;
}

export interface PantryItem {
  user_id: string;
  ingredient_id: string;
  ingredient: Ingredient;
  quantity: number;
  expiration_date?: string;
  updated_at: string;
}

export interface PantryItemCreate {
  ingredient_id: string;
  quantity: number;
  expiration_date?: string;
}

export interface PantryItemUpdate {
  quantity?: number;
  expiration_date?: string;
}

export interface Meal {
  id: string;
  name: string;
  description: string;
  prep_time: number;
  cook_time: number;
  difficulty: number;
  servings: number;
  instructions: string[];
  ingredients: MealIngredient[];
  categories: MealCategory[];
  image_url?: string;
  nutritional_info?: NutritionalInfo;
}

export interface MealIngredient {
  meal_id: string;
  ingredient_id: string;
  ingredient: Ingredient;
  quantity: number;
  unit: string;
  optional: boolean;
}

export interface MealCategory {
  id: string;
  name: string;
  type: 'diet' | 'cuisine' | 'meal_type' | 'health' | 'difficulty';
}

export interface MealPlan {
  id: string;
  user_id: string;
  week_start_date: string;
  planned_meals: PlannedMeal[];
  created_at: string;
}

export interface PlannedMeal {
  id: string;
  plan_id: string;
  meal_id: string;
  meal: Meal;
  date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  attendee_count: number;
  attendees: FamilyMember[];
}

export interface MealRating {
  user_id: string;
  meal_id: string;
  rating: number;
  feedback?: string;
  created_at: string;
}

export interface MealRecommendation {
  name: string;
  description: string;
  prep_time: number;
  difficulty: string;
  servings: number;
  ingredients_needed: IngredientNeeded[];
  instructions: string[];
  tags: string[];
  nutrition_notes: string;
  pantry_usage_score: number;
  ai_generated?: boolean;
  ai_provider?: string;
}

export interface IngredientNeeded {
  name: string;
  quantity: string;
  unit: string;
  have_in_pantry: boolean;
}

export interface MealRecommendationRequest {
  num_recommendations?: number;
  meal_type?: string;
  preferences?: Record<string, any>;
  ai_provider?: string;
}

export interface Recipe {
  id: string;
  user_id: string;
  name: string;
  description: string;
  prep_time: number;
  difficulty: string;
  servings: number;
  ingredients_needed: IngredientNeeded[];
  instructions: string[];
  tags: string[];
  nutrition_notes: string;
  pantry_usage_score: number;
  ai_generated: boolean;
  ai_provider?: string;
  source: string;
  rating?: number; // Average rating from backend
  created_at: string;
  updated_at: string;
}

export interface RecipeCreate {
  name: string;
  description: string;
  prep_time: number;
  difficulty: string;
  servings: number;
  ingredients_needed: IngredientNeeded[];
  instructions: string[];
  tags: string[];
  nutrition_notes: string;
  pantry_usage_score: number;
  ai_generated?: boolean;
  ai_provider?: string;
  source?: string;
}

export interface RecipeUpdate {
  name?: string;
  description?: string;
  prep_time?: number;
  difficulty?: string;
  servings?: number;
  ingredients_needed?: IngredientNeeded[];
  instructions?: string[];
  tags?: string[];
  nutrition_notes?: string;
  pantry_usage_score?: number;
  source?: string;
}

export interface RecipeRating {
  id: string;
  recipe_id: string;
  user_id: string;
  rating: number; // 1-5 stars
  review_text?: string;
  would_make_again: boolean;
  cooking_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface RecipeRatingCreate {
  rating: number;
  review_text?: string;
  would_make_again: boolean;
  cooking_notes?: string;
}

export interface RecipeRatingUpdate {
  rating?: number;
  review_text?: string;
  would_make_again?: boolean;
  cooking_notes?: string;
}

export interface ShoppingListItem {
  ingredient: Ingredient;
  quantity: number;
  unit: string;
  estimated_cost?: number;
  meals: string[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Books and Content Types
export type ReadingStatus = 'want_to_read' | 'reading' | 'read';

export interface Book {
  id: string;
  user_id: string;
  title: string;
  author: string;
  description?: string;
  genre?: string;
  isbn?: string;
  pages?: number;
  publication_year?: number;
  cover_image_url?: string;
  google_books_id?: string;
  open_library_id?: string;
  current_page: number;
  reading_status: ReadingStatus;
  date_started?: string;
  date_finished?: string;
  user_notes?: string;
  is_favorite: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface BookCreate {
  title: string;
  author: string;
  description?: string;
  genre?: string;
  isbn?: string;
  pages?: number;
  publication_year?: number;
  cover_image_url?: string;
  google_books_id?: string;
  open_library_id?: string;
  current_page?: number;
  reading_status?: ReadingStatus;
  date_started?: string;
  date_finished?: string;
  user_notes?: string;
  is_favorite?: boolean;
  source?: string;
}

export interface BookUpdate {
  title?: string;
  author?: string;
  description?: string;
  genre?: string;
  isbn?: string;
  pages?: number;
  publication_year?: number;
  cover_image_url?: string;
  google_books_id?: string;
  open_library_id?: string;
  current_page?: number;
  reading_status?: ReadingStatus;
  date_started?: string;
  date_finished?: string;
  user_notes?: string;
  is_favorite?: boolean;
  source?: string;
}

export interface BookListResponse {
  books: Book[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BookFilters {
  reading_status?: ReadingStatus;
  genre?: string;
  is_favorite?: boolean;
  search?: string;
}

// Movies and Content Types
export type ViewingStatus = 'want_to_watch' | 'watched';

export interface Movie {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  genre?: string;
  director?: string;
  release_year?: number;
  runtime?: number; // minutes
  poster_image_url?: string;
  tmdb_id?: string;
  imdb_id?: string;
  omdb_id?: string;
  viewing_status: ViewingStatus;
  date_watched?: string;
  user_notes?: string;
  is_favorite: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MovieCreate {
  title: string;
  description?: string;
  genre?: string;
  director?: string;
  release_year?: number;
  runtime?: number;
  poster_image_url?: string;
  tmdb_id?: string;
  imdb_id?: string;
  omdb_id?: string;
  viewing_status?: ViewingStatus;
  date_watched?: string;
  user_notes?: string;
  is_favorite?: boolean;
  source?: string;
}

export interface MovieUpdate {
  title?: string;
  description?: string;
  genre?: string;
  director?: string;
  release_year?: number;
  runtime?: number;
  poster_image_url?: string;
  tmdb_id?: string;
  imdb_id?: string;
  omdb_id?: string;
  viewing_status?: ViewingStatus;
  date_watched?: string;
  user_notes?: string;
  is_favorite?: boolean;
  source?: string;
}

export interface MovieListResponse {
  movies: Movie[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MovieFilters {
  viewing_status?: ViewingStatus;
  genre?: string;
  is_favorite?: boolean;
  search?: string;
}