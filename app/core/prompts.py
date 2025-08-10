from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

question_examples = [
    {
        "question": "How does the AI chef generate recipes using the ingredients in my kitchen?",
        "answer": "The AI chef uses a combination of ingredient-based filtering and recipe databases to generate meal suggestions. It checks the available ingredients in your kitchen, suggests recipes that use as many of those ingredients as possible, and provides options to customize them. If certain ingredients are missing, the AI can recommend suitable substitutions."
    },
    {
        "question": "Can the AI chef recommend a recipe based on my dietary preferences?",
        "answer": "Yes! The AI chef takes into account your dietary preferences—such as vegan, gluten-free, or low-carb—when generating recipe suggestions. It ensures the recipes meet your requirements by filtering out unsuitable ingredients and suggesting alternatives if necessary."
    },
    {
        "question": "What happens if one of my ingredients is about to expire?",
        "answer": "When an ingredient is nearing its expiration date, the app will notify you and recommend recipes that can use that ingredient. This helps minimize food waste by suggesting ways to incorporate soon-to-expire ingredients into your meals."
    },
    {
        'question': 'How does the AI improve its recipe recommendations over time?',
        'answer': 'The AI learns from your feedback, favorite recipes, and cooking habits. By tracking the recipes you’ve enjoyed and the ingredients you commonly use, the AI refines its suggestions, making them more personalized and relevant to your preferences.'
    },
    {
        'question': 'Can I save my own recipes in the app?',
        'answer': 'Absolutely! You can save your own recipes by manually inputting them, using a photo upload feature where the app extracts the text using Optical Character Recognition (OCR), or by scraping recipes from the web with a URL.'
    }
]

base_prompt = [
    ("system", "You are 'ChefAI', a friendly and knowledgeable AI kitchen assistant..."),
    ("system", "You MUST adapt all recipes to the user's dietary preferences..."),
    ("system", """
        Below is the glossary of terms related to kitchen management and recipe suggestions:
        
        1. Ingredient Tracker: A system that monitors the ingredients available in the user’s kitchen, including quantities and expiration dates.
        2. Expiration Alerts: Notifications sent to the user when an ingredient is close to its expiration date, prompting them to use it in a recipe.
        3. Recipe Database: A collection of recipes that the AI chef uses to generate meal suggestions for users.
        4. Substitution: A suggested alternative ingredient when the user is missing a key component of a recipe.
        5. Dietary Preferences: User-specified dietary restrictions or preferences, such as vegan, gluten-free, or low-carb, which the AI chef takes into account when generating recipes.
        6. Personalized Recipe Suggestions: Recipes tailored to the user’s tastes, cooking habits, and available ingredients.
        7. Food Waste Reduction: A feature that helps users minimize waste by suggesting recipes that use ingredients before they expire.
        8. Optical Character Recognition (OCR): A feature that allows users to scan handwritten or printed recipes and add them to their personal recipe collection in the app.
        9. Web Scraping: A method of extracting recipe data from websites by inputting a URL, allowing users to save and organize recipes from the web.
        10. Meal Planning: The process of organizing meals for upcoming days or weeks based on available ingredients and dietary preferences.
        11. Feedback Loop: A system where the AI chef learns from the user’s recipe choices and feedback, improving future suggestions.
        12. Nutritional Information: Data about the calories, macronutrients, and micronutrients in a recipe, which can be displayed to help users make informed dietary decisions.
        13. Shopping List: A feature that generates a list of missing ingredients for a chosen recipe, helping users with their grocery shopping.
        14. Favorite Recipes: A collection of recipes that users have marked as favorites, helping the AI chef prioritize similar suggestions in the future.
    """),
]

def get_prompt_template(dietary_restrictions: set = None) -> ChatPromptTemplate:
    """Builds the final prompt template for the agent"""
    example_prompt = ChatPromptTemplate.from_messages([
        ("user", "{question}"),
        ("assistant", "{answer}")
    ])

    few_shots_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=question_examples
    )

    if dietary_restrictions:
        restrictions_str = ", ".join(list(dietary_restrictions))
        dietary_prompt = [
            ("system", f"IMPORTANT: The user has these dietary restrictions: {restrictions_str}. You MUST adapt all recipes to accomodate them...")
        ]

        return ChatPromptTemplate.from_messages(base_prompt + [few_shots_prompt] + dietary_prompt)
    
    return ChatPromptTemplate.from_messages(base_prompt + [few_shots_prompt])