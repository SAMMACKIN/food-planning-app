// Test script to verify recipe saving functionality
// Run this in the browser console when logged into the app

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
        
        // Test recipe fetching
        const fetchResponse = await fetch(`${apiUrl}/recipes`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!fetchResponse.ok) {
            console.error('❌ Recipe fetching failed:', fetchResponse.status);
            return;
        }
        
        const recipes = await fetchResponse.json();
        console.log('✅ Recipe fetching successful. Total recipes:', recipes.length);
        
        // Check if our test recipe is in the list
        const ourRecipe = recipes.find(r => r.id === savedRecipe.id);
        if (ourRecipe) {
            console.log('✅ Test recipe found in saved recipes list');
        } else {
            console.error('❌ Test recipe not found in saved recipes list');
        }
        
        console.log('🎉 Recipe saving test completed successfully!');
        
    } catch (error) {
        console.error('❌ Test failed with error:', error);
    }
}

// Instructions
console.log(`
🔧 Recipe Saving Test Script Loaded

To run the test:
1. Make sure you're logged into the app
2. Run: testRecipeSaving()

This will test the complete recipe saving flow and show you where any issues occur.
`);