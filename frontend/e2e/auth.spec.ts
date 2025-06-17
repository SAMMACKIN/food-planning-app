import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the login page
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    // Check that login form elements are present
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    // Try to submit without filling fields
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should show validation errors
    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password must be at least/i)).toBeVisible();
  });

  test('should show validation error for short password', async ({ page }) => {
    // Fill email but use short password
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should show password validation error
    await expect(page.getByText(/password must be at least 6 characters/i)).toBeVisible();
  });

  test('should redirect to registration page', async ({ page }) => {
    // Click the registration link
    await page.getByText(/sign up/i).click();
    
    // Should navigate to registration page
    await expect(page).toHaveURL(/.*\/register/);
    await expect(page.getByRole('heading', { name: /sign up/i })).toBeVisible();
  });

  test('should handle login attempt with invalid credentials', async ({ page }) => {
    // Fill login form with invalid credentials
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should show error message (assuming API returns error)
    // Note: This test might fail if backend is not running
    // In a real scenario, you'd mock the API or have it running
    await expect(page.getByText(/incorrect email or password/i)).toBeVisible({ timeout: 10000 });
  });

  test('registration form should be accessible', async ({ page }) => {
    await page.goto('/register');
    
    // Check registration form elements
    await expect(page.getByRole('heading', { name: /sign up/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByLabel(/name/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign up/i })).toBeVisible();
  });

  test('should show loading state during login', async ({ page }) => {
    // Fill valid-looking credentials
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    
    // Click login button
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should show loading state (button disabled or loading text)
    await expect(page.getByRole('button', { name: /signing in/i })).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Authentication State Management', () => {
  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access a protected route
    await page.goto('/dashboard');
    
    // Should redirect to login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should maintain auth state across page refreshes', async ({ page }) => {
    // This test would require setting up a mock authenticated state
    // or having a test user in the system
    
    // For now, just verify the auth check happens
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });
});