// Recipe Saving Diagnostic Script
// Copy and paste this entire script into your browser console when the app is open

console.log('🔧 Recipe Saving Diagnostic Test - Starting...');

async function testRecipeSaving() {
    console.log('📋 Step 1: Checking API Configuration');
    
    // Check if we're in the right environment
    const apiUrl = 'http://localhost:8001/api/v1';
    console.log('🔗 API URL:', apiUrl);
    
    // Check authentication
    const token = localStorage.getItem('access_token');
    console.log('🔑 Token exists:', !!token);
    console.log('🔑 Token length:', token ? token.length : 0);
    
    if (!token) {
        console.error('❌ No authentication token found. Please log in first.');
        return;
    }
    
    console.log('📋 Step 2: Testing Authentication');
    
    try {
        const authResponse = await fetch(`${apiUrl}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🔐 Auth response status:', authResponse.status);
        
        if (!authResponse.ok) {
            const errorText = await authResponse.text();
            console.error('❌ Authentication failed:', authResponse.status, errorText);
            if (authResponse.status === 401) {
                console.error('🚨 Token appears to be invalid. Try logging out and logging back in.');
            }
            return;
        }
        
        const user = await authResponse.json();
        console.log('✅ Authentication successful. User:', user.email);
        
    } catch (error) {
        console.error('❌ Network error during auth test:', error);
        console.error('🚨 Backend may not be running. Check if http://localhost:8001 is accessible.');
        return;
    }
    
    console.log('📋 Step 3: Testing Recipe Save API');
    
    const testRecipe = {
        name: "Test Recipe Save",
        description: "Testing recipe saving functionality",
        prep_time: 30,
        difficulty: "Easy",
        servings: 4,
        ingredients_needed: [
            { name: "test ingredient", quantity: "1", unit: "cup", have_in_pantry: true }
        ],
        instructions: ["Step 1: Test save", "Step 2: Verify result"],
        tags: ["test", "debug"],
        nutrition_notes: "Test nutrition info",
        pantry_usage_score: 75,
        ai_generated: false,
        source: "test"
    };
    
    try {
        console.log('📤 Sending recipe save request...');
        console.log('📋 Recipe data:', testRecipe);
        
        const saveResponse = await fetch(`${apiUrl}/recipes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testRecipe)
        });
        
        console.log('💾 Save response status:', saveResponse.status);
        console.log('💾 Save response headers:', Object.fromEntries(saveResponse.headers.entries()));
        
        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            console.error('❌ Recipe save failed:', saveResponse.status, errorText);
            
            try {
                const errorJson = JSON.parse(errorText);
                console.error('📋 Error details:', errorJson);
            } catch (e) {
                console.error('📋 Raw error text:', errorText);
            }
            
            if (saveResponse.status === 401) {
                console.error('🚨 Authentication failed during save. Token may have expired.');
            } else if (saveResponse.status === 422) {
                console.error('🚨 Validation error. Recipe data format may be incorrect.');
            } else if (saveResponse.status === 500) {
                console.error('🚨 Server error. Backend may have crashed or database issues.');
            }
            
            return;
        }
        
        const savedRecipe = await saveResponse.json();
        console.log('✅ Recipe saved successfully!');
        console.log('📋 Saved recipe ID:', savedRecipe.id);
        console.log('📋 Full saved recipe:', savedRecipe);
        
        console.log('📋 Step 4: Testing Recipe Rating');
        
        const ratingData = {
            recipe_id: savedRecipe.id,
            rating: 5,
            review_text: "Test rating",
            would_make_again: true,
            cooking_notes: "Test cooking notes"
        };
        
        const ratingResponse = await fetch(`${apiUrl}/recipes/${savedRecipe.id}/ratings`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ratingData)
        });
        
        console.log('⭐ Rating response status:', ratingResponse.status);
        
        if (!ratingResponse.ok) {
            const errorText = await ratingResponse.text();
            console.error('❌ Recipe rating failed:', ratingResponse.status, errorText);
        } else {
            const rating = await ratingResponse.json();
            console.log('✅ Recipe rated successfully!');
            console.log('⭐ Rating details:', rating);
        }
        
        console.log('📋 Step 5: Testing Add to Meal Plan');
        
        const today = new Date().toISOString().split('T')[0];
        const mealPlanResponse = await fetch(`${apiUrl}/recipes/${savedRecipe.id}/add-to-meal-plan?meal_date=${today}&meal_type=dinner`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('📅 Meal plan response status:', mealPlanResponse.status);
        
        if (!mealPlanResponse.ok) {
            const errorText = await mealPlanResponse.text();
            console.error('❌ Add to meal plan failed:', mealPlanResponse.status, errorText);
        } else {
            const mealPlan = await mealPlanResponse.json();
            console.log('✅ Added to meal plan successfully!');
            console.log('📅 Meal plan details:', mealPlan);
        }
        
        console.log('🎉 ALL TESTS COMPLETED!');
        
    } catch (error) {
        console.error('❌ Unexpected error during recipe save test:', error);
        console.error('🚨 This might be a network issue or the backend server is not running.');
    }
}

// Instructions
console.log(`
🔧 Recipe Saving Diagnostic Test Loaded

To run the test:
1. Make sure you're logged into the app
2. Open browser developer tools (F12)
3. Go to Console tab
4. Run: testRecipeSaving()

This will test:
- Authentication
- Recipe saving
- Recipe rating  
- Adding to meal plan

Look for ✅ (success) or ❌ (error) indicators in the output.
`);

// Auto-run if you want (comment out if you prefer to run manually)
// testRecipeSaving();