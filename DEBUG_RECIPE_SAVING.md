# Recipe Saving Debug Guide

The recipe saving functionality has been thoroughly tested and the backend API works correctly. The issue is likely in the frontend authentication or data flow.

## Quick Test Steps

1. **Open the app in your browser** (http://localhost:3000)

2. **Open browser developer tools** (F12 or right-click → Inspect)

3. **Go to the Console tab**

4. **Copy and paste this test script:**

```javascript
// Test script to verify recipe saving functionality
async function testRecipeSaving() {
    console.log('🧪 Testing recipe saving functionality...');
    
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    console.log('🔑 Token exists:', !!token);
    
    if (!token) {
        console.error('❌ No access token found - user needs to login first');
        return;
    }
    
    // Test API connection
    const apiUrl = 'http://localhost:8001/api/v1';
    console.log('🔗 Testing API connection to:', apiUrl);
    
    try {
        // Test authentication
        const authResponse = await fetch(`${apiUrl}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!authResponse.ok) {
            console.error('❌ Authentication failed:', authResponse.status, await authResponse.text());
            return;
        }
        
        const user = await authResponse.json();
        console.log('✅ User authenticated:', user.email);
        
        // Test recipe saving
        const testRecipe = {
            name: "Test Recipe from Console",
            description: "A test recipe to verify saving functionality",
            prep_time: 30,
            difficulty: "Easy",
            servings: 4,
            ingredients_needed: [
                { name: "test ingredient", quantity: "1", unit: "cup", have_in_pantry: true }
            ],
            instructions: ["Step 1: Test", "Step 2: Verify"],
            tags: ["test", "console"],
            nutrition_notes: "Test nutrition notes",
            pantry_usage_score: 80,
            ai_generated: false,
            source: "test"
        };
        
        console.log('📤 Attempting to save recipe:', testRecipe.name);
        
        const saveResponse = await fetch(`${apiUrl}/recipes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testRecipe)
        });
        
        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            console.error('❌ Recipe saving failed:', saveResponse.status, errorText);
            return;
        }
        
        const savedRecipe = await saveResponse.json();
        console.log('✅ Recipe saved successfully:', savedRecipe.id);
        console.log('📋 Saved recipe details:', savedRecipe);
        
        console.log('🎉 Recipe saving test completed successfully!');
        
    } catch (error) {
        console.error('❌ Test failed with error:', error);
    }
}

testRecipeSaving();
```

5. **Run the test and check the console output**

## Expected Results

### If Everything Works:
- ✅ Token exists: true
- ✅ User authenticated: your@email.com
- ✅ Recipe saved successfully: [some-uuid]
- 🎉 Recipe saving test completed successfully!

### If Authentication is the Issue:
- ❌ No access token found - user needs to login first
- OR ❌ Authentication failed: 401 Unauthorized

### If There's a Backend Issue:
- ❌ Recipe saving failed: [error code] [error message]

## Next Steps Based on Results

### If authentication is the issue:
1. Try logging out and logging back in
2. Check if the login process completed successfully
3. Verify that localStorage has the access_token

### If the test works but the UI doesn't:
1. Try saving a recipe through the UI
2. Check the console for error messages
3. Look for red error messages in the UI

### If there are network issues:
1. Verify both frontend (port 3000) and backend (port 8001) are running
2. Check if there are CORS errors in the console

## Enhanced Debugging

I've added enhanced logging to the recipe saving functionality. Now when you try to save a recipe through the UI, you'll see detailed console logs that will help identify the exact issue:

- 🍽️ Saving recipe: [recipe name]
- 📋 Recipe data: [full recipe object]
- ✅ Recipe saved successfully: [saved recipe]
- OR ❌ Error saving recipe: [detailed error info]

## Common Issues and Solutions

1. **User not logged in**: Login first
2. **Invalid token**: Logout and login again  
3. **Backend not running**: Start the backend with `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`
4. **CORS issues**: Check that both frontend and backend are running on correct ports
5. **Database schema issues**: Run the migration script: `cd backend && python migrate_meal_plans.py`

The backend API has been thoroughly tested and works correctly, so the issue is most likely in the frontend authentication flow or user session management.