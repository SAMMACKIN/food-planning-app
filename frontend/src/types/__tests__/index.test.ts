import type { 
  User, 
  FamilyMember, 
  MealRecommendation, 
  LoginRequest, 
  RegisterRequest 
} from '../index';

describe('Type Definitions', () => {
  test('User type has required fields', () => {
    const user: User = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      timezone: 'UTC',
      is_active: true,
      is_admin: false,
      created_at: '2024-01-01T00:00:00Z',
    };

    expect(user.id).toBe('1');
    expect(user.email).toBe('test@example.com');
    expect(user.is_active).toBe(true);
    expect(user.is_admin).toBe(false);
  });

  test('FamilyMember type has required fields', () => {
    const familyMember: FamilyMember = {
      id: '1',
      user_id: 'user-1',
      name: 'John Doe',
      age: 25,
      dietary_restrictions: ['vegetarian'],
      preferences: {
        likes: ['pasta'],
        dislikes: ['mushrooms'],
        preferred_cuisines: ['italian'],
        spice_level: 2,
      },
      created_at: '2024-01-01T00:00:00Z',
    };

    expect(familyMember.name).toBe('John Doe');
    expect(familyMember.dietary_restrictions).toContain('vegetarian');
    expect(familyMember.preferences.favorite_cuisines).toContain('italian');
  });

  test('MealRecommendation type has required fields', () => {
    const recommendation: MealRecommendation = {
      name: 'Pasta Primavera',
      description: 'Fresh vegetable pasta',
      prep_time: 30,
      difficulty: 'Easy',
      servings: 4,
      ingredients_needed: [
        {
          name: 'pasta',
          quantity: '1 lb',
          unit: 'lb',
          have_in_pantry: false,
        }
      ],
      instructions: ['Boil water', 'Cook pasta'],
      tags: ['vegetarian', 'quick'],
      nutrition_notes: 'High in fiber',
      pantry_usage_score: 0.8,
      ai_generated: true,
      ai_provider: 'claude',
    };

    expect(recommendation.name).toBe('Pasta Primavera');
    expect(recommendation.prep_time).toBe(30);
    expect(recommendation.difficulty).toBe('Easy');
    expect(recommendation.ai_generated).toBe(true);
  });

  test('LoginRequest type validation', () => {
    const loginRequest: LoginRequest = {
      email: 'test@example.com',
      password: 'password123',
    };

    expect(loginRequest.email).toContain('@');
    expect(loginRequest.password.length).toBeGreaterThan(0);
  });

  test('RegisterRequest type validation', () => {
    const registerRequest: RegisterRequest = {
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    };

    expect(registerRequest.email).toContain('@');
    expect(registerRequest.password.length).toBeGreaterThan(0);
    expect(registerRequest.name!.length).toBeGreaterThan(0);
  });
});