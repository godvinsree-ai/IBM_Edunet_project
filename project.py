
import streamlit as st
from google import genai
import os
from collections import Counter

api_key='AIzaSyCcgsb4JI0nFkUkSCmS3ok0DvvCYJpKvZg'
client = genai.Client(api_key='AIzaSyCcgsb4JI0nFkUkSCmS3ok0DvvCYJpKvZg')


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
    try:
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Error generating recipe: {e}"

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
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Error generating suggestions: {e}"


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
            st.markdown("--- athletic")
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