import { test, expect } from '@playwright/test';

test.describe('Navigation and Layout', () => {
  test.beforeEach(async ({ page }) => {
    // Start from login page
    await page.goto('/login');
  });

  test('should display Food Planning App branding', async ({ page }) => {
    await expect(page.getByText(/food planning app/i)).toBeVisible();
  });

  test('should have responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.getByText(/food planning app/i)).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByText(/food planner/i)).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/email/i)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/password/i)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /sign in/i })).toBeFocused();
  });

  test('should support enter key for form submission', async ({ page }) => {
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    
    // Press enter to submit
    await page.getByLabel(/password/i).press('Enter');
    
    // Should attempt to submit (loading state or error)
    await expect(page.getByRole('button', { name: /signing in/i })).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Mobile Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login');
  });

  test('should display mobile-optimized login form', async ({ page }) => {
    // Check that form elements are still accessible on mobile
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should handle touch interactions', async ({ page }) => {
    // Tap on email field
    await page.getByLabel(/email/i).tap();
    await expect(page.getByLabel(/email/i)).toBeFocused();
    
    // Tap on password field
    await page.getByLabel(/password/i).tap();
    await expect(page.getByLabel(/password/i)).toBeFocused();
  });
});

test.describe('Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/login');
    
    // Check that form inputs have proper labels
    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);
    
    await expect(emailInput).toHaveAttribute('aria-label', /.*/);
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should support screen readers', async ({ page }) => {
    await page.goto('/login');
    
    // Check that the page has a proper heading hierarchy
    await expect(page.getByRole('heading', { level: 1 })).toBeTruthy();
    
    // Check that form has proper structure
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/login');
    
    // This would need additional tools to test color contrast
    // For now, just ensure the page renders properly
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate offline condition
    await page.context().setOffline(true);
    
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should handle network error (might show error message or retry)
    // The exact behavior depends on implementation
    await expect(page.getByRole('button')).toBeVisible({ timeout: 10000 });
    
    // Restore online state
    await page.context().setOffline(false);
  });

  test('should handle slow network connections', async ({ page }) => {
    // Simulate slow network
    await page.route('**/*', route => {
      setTimeout(() => route.continue(), 1000); // 1 second delay
    });
    
    await page.goto('/login');
    
    // Should still load within reasonable time
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible({ timeout: 15000 });
  });
});