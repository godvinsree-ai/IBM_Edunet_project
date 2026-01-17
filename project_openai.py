
import streamlit as st
from openai import OpenAI
import os
from collections import Counter
import hashlib
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
api_key = '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'

# Create client with proper error handling
if api_key and api_key != 'your-api-key-here':
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        client = None
else:
    client = None

# Mock recipes for fallback when API quota is exceeded
MOCK_RECIPES = {
    "italian_chicken": "# Creamy Tuscan Chicken\n\n## Description\nA delightful Italian-inspired dish with tender chicken in a sun-dried tomato and cream sauce.\n\n## Ingredients\n- 500g chicken breast, cubed\n- 200ml heavy cream\n- 100g sun-dried tomatoes\n- 3 cloves garlic, minced\n- 2 tbsp olive oil\n- 50g parmesan cheese\n- Salt and pepper to taste\n\n## Instructions\n1. Heat olive oil in a large pan over medium heat\n2. Add garlic and cook for 1 minute until fragrant\n3. Add chicken cubes and cook until golden (5-7 minutes)\n4. Stir in sun-dried tomatoes and cream\n5. Simmer for 10 minutes until chicken is cooked through\n6. Season with salt, pepper and top with parmesan\n7. Serve over pasta or with crusty bread\n\n## Serving Size\n2-3 servings\n\n## Time\nPrep: 10 mins | Cook: 20 mins",
    "mexican_chicken": "# Spicy Chicken Tacos\n\n## Description\nAuthentic Mexican-style tacos with seasoned chicken and fresh toppings.\n\n## Ingredients\n- 500g chicken breast, sliced\n- 2 tbsp cumin\n- 1 tbsp chili powder\n- Corn tortillas\n- Fresh cilantro\n- Lime wedges\n- Salsa\n\n## Instructions\n1. Season chicken with cumin and chili powder\n2. Cook in a hot skillet for 6-8 minutes\n3. Warm tortillas on a griddle\n4. Assemble tacos with chicken and toppings\n5. Serve with lime and salsa\n\n## Serving Size\n2-3 servings\n\n## Time\nPrep: 5 mins | Cook: 15 mins"
}

# Initialize recipe cache
if 'recipe_cache' not in st.session_state:
    st.session_state.recipe_cache = {}

# Initialize session state for recipe history if it doesn't exist
if 'recipe_history' not in st.session_state:
    st.session_state.recipe_history = []

st.set_page_config(layout='wide')

# Create three columns for the layout
col1, col2, col3 = st.columns(3)

# Ensure your API key is stored securely, e.g., in environment variables
# For this example, we'll assume it's set as an environment variable.
# Alternatively, you could use st.secrets for Streamlit deployment.

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyCcgsb4JI0nFkUkSCmS3ok0DvvCYJpKvZg')



def generate_recipe(ingredients, style, meal_type, hunger_level):
    # Create a cache key
    cache_key = hashlib.md5(f"{ingredients}_{style}_{meal_type}".encode()).hexdigest()
    
    # Check if recipe is in cache
    if cache_key in st.session_state.recipe_cache:
        return st.session_state.recipe_cache[cache_key]
    
    prompt = f"""Generate a detailed and creative {style} {meal_type} recipe.
    The recipe should primarily use the following ingredients: {ingredients}.
    The hunger level of the person for whom this recipe is being prepared is {hunger_level} out of 10 (1 being not hungry, 10 being very hungry), so adjust the portion size/complexity accordingly.
    Please include:
    - A catchy title
    - A brief description
    - Ingredients list with quantities
    - Step-by-step instructions
    - Suggested serving size
    - Estimated preparation and cooking time
    """
    
    if not client:
        # Use mock recipe as fallback when API key not set
        mock_key = f"{style.lower()}_{meal_type.lower()}".replace(" ", "_")
        recipe = MOCK_RECIPES.get(mock_key, f"""# {style.title()} {meal_type}

## ⚠️ API Key Not Configured

Please set your OpenAI API key to generate recipes. Run:
```bash
OPENAI_API_KEY='sk-your-key-here' python3 -m streamlit run project.py
```

## Sample Ingredients
- {ingredients}

This is a demonstration. Full recipes require a valid OpenAI API key.""")
    else:
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are a helpful culinary assistant that generates creative and detailed recipes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            recipe = response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Use mock recipe as fallback
            mock_key = f"{style.lower()}_{meal_type.lower()}".replace(" ", "_")
            recipe = MOCK_RECIPES.get(mock_key, f"""# {style.title()} {meal_type}

## ⚠️ API Error

Error: {error_msg}

Please check:
1. Your OpenAI API key is valid
2. You have credits/quota remaining
3. Your API key environment variable is set

## Sample Ingredients
- {ingredients}""")
    
    # Cache the recipe
    st.session_state.recipe_cache[cache_key] = recipe
    return recipe

def generate_suggestions(history):
    if not history:
        return "No history to generate suggestions from."

    # Extract preferences from history
    all_ingredients = []
    all_styles = []
    all_meal_types = []

    for recipe_data in history:
        all_ingredients.extend([ing.strip() for ing in recipe_data['ingredients'].split(',')])
        all_styles.append(recipe_data['style'])
        all_meal_types.append(recipe_data['meal_type'])

    # Get most common preferences
    most_common_ingredients = ", ".join([item[0] for item in Counter(all_ingredients).most_common(3)])
    most_common_style = Counter(all_styles).most_common(1)[0][0] if all_styles else "diverse"
    most_common_meal_type = Counter(all_meal_types).most_common(1)[0][0] if all_meal_types else "any"

    prompt = f"""Based on the user's past recipe generations, which primarily involved ingredients like {most_common_ingredients},
    often in a {most_common_style} style, and frequently for {most_common_meal_type} meals, suggest 2-3 NEW and relevant recipe ideas.
    Each suggestion should include only the recipe title and a very brief description (1-2 sentences).
    Avoid suggesting recipes that use exactly the same ingredients as the ones provided in '{most_common_ingredients}' if possible, focus on new ideas.
    """
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a helpful culinary assistant that suggests creative recipe ideas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback suggestions when API is unavailable
        suggestions = f"""### Suggested Recipes Based on Your Preferences

**Based on your preferences for {most_common_style} {most_common_meal_type} meals:**

1. **Garlic Butter Pasta with Fresh Herbs** - A simple yet elegant dish combining creamy pasta with fresh seasonal herbs and garlic. Perfect for quick weeknight dinners.

2. **Herb-Crusted Fish with Roasted Vegetables** - A healthy and flavorful option featuring white fish with a crispy herb coating, served alongside colorful roasted vegetables.

3. **Mediterranean Grain Bowl** - A nutritious and colorful bowl combining quinoa, fresh vegetables, feta cheese, and a lemon vinaigrette. Great for meal prep.

*Note: Full personalized suggestions require API access. These are sample recommendations based on your cooking style preferences.*"""
        return suggestions


with col1:
    st.header("Recipe Generator Inputs")
    st.subheader("Enter Recipe Details")
    ingredients = st.text_input("Ingredients (comma-separated)", "chicken, broccoli, rice")
    style = st.selectbox("Cooking Style", ["Italian", "Mexican", "Asian", "Indian", "Mediterranean", "American", "Other"])
    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Dessert", "Snack"])
    hunger_level = st.slider("Hunger Level", 1, 10, 5) # 1 (not hungry) to 10 (very hungry)

    st.write(f"Selected Ingredients: {ingredients}")
    st.write(f"Selected Style: {style}")
    st.write(f"Selected Meal Type: {meal_type}")
    st.write(f"Selected Hunger Level: {hunger_level}")

    if st.button("Generate Recipe"):
        with col2:
            with st.spinner("Generating your delicious recipe..."):
                generated_recipe = generate_recipe(ingredients, style, meal_type, hunger_level)
                st.subheader("Your Generated Recipe:")
                st.markdown(generated_recipe)
                # Store the generated recipe in history
                st.session_state.recipe_history.append({
                    'ingredients': ingredients,
                    'style': style,
                    'meal_type': meal_type,
                    'hunger_level': hunger_level,
                    'recipe_text': generated_recipe
                })

with col2:
    st.header("Generated Recipe")

with col3:
    st.header("Suggestions & Trends")
    st.subheader("Your Recent Recipe History")
    if st.session_state.recipe_history:
        # Display the last few recipes from history
        for i, recipe_data in enumerate(reversed(st.session_state.recipe_history[-5:])): # Show last 5
            st.markdown(f"**{recipe_data['style']} {recipe_data['meal_type']} with {recipe_data['ingredients']}**")
            with st.expander(f"View Recipe #{len(st.session_state.recipe_history) - i}"):
                st.markdown(recipe_data['recipe_text'])
            st.markdown("---")
    else:
        st.info("Generate a recipe to see your history here!")

    st.subheader("Personalized Recipe Suggestions")
    if st.session_state.recipe_history:
        with st.spinner("Generating personalized suggestions..."):
            suggestions = generate_suggestions(st.session_state.recipe_history)
            st.markdown(suggestions)
        st.markdown("**Legend**: These suggestions are based on your most frequently used ingredients, cooking styles, and meal types from your past generated recipes.")
    else:
        st.info("Generate a recipe first to get personalized suggestions!")

    st.subheader("Trending Items (Placeholder)")
    st.write("Trending recipes will appear here. e.g., 'Spicy Chicken Tacos', 'Vegan Buddha Bowl', 'Quick Pasta Alfredo'")
