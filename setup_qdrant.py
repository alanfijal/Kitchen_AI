from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import AzureOpenAIEmbeddings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Qdrant client
client = QdrantClient("localhost", port=6333)

# Initialize the OpenAI embedding model
embeddings_model = AzureOpenAIEmbeddings(
    model='text-embedding-ada-002',
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ADA"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_ADA"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION_ADA"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_ADA")
)

# Define the collection name
COLLECTION_NAME = "recipes"

# Create the collection
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)

# Sample recipe data
recipes = [
    {
        "name": "Spaghetti Carbonara",
        "ingredients": "spaghetti, eggs, pancetta, Pecorino Romano cheese, black pepper",
        "instructions": "Cook pasta. Fry pancetta. Mix eggs and cheese. Combine all ingredients."
    },
    {
        "name": "Chicken Stir Fry",
        "ingredients": "chicken breast, mixed vegetables, soy sauce, garlic, ginger",
        "instructions": "Cut chicken. Stir-fry with vegetables. Add sauce and seasonings."
    },
    {
        "name": "Vegetable Soup",
        "ingredients": "carrots, celery, onions, potatoes, vegetable broth, herbs",
        "instructions": "Chop vegetables. Simmer in broth. Add herbs and season to taste."
    },
    {
        "name": "Chocolate Chip Cookies",
        "ingredients": "flour, butter, sugar, eggs, chocolate chips, vanilla extract",
        "instructions": "Mix ingredients. Form dough balls. Bake until golden brown."
    },
    {
        "name": "Greek Salad",
        "ingredients": "tomatoes, cucumbers, red onion, feta cheese, olives, olive oil",
        "instructions": "Chop vegetables. Combine in bowl. Add cheese and olives. Dress with olive oil."
    }
]

# Prepare the data for insertion
points = []
for i, recipe in enumerate(recipes):
    # Create the embedding for the recipe
    recipe_text = f"{recipe['name']} {recipe['ingredients']} {recipe['instructions']}"
    embedding = embeddings_model.embed_query(recipe_text)
    
    # Create the point
    points.append(models.PointStruct(
        id=i,
        vector=embedding,
        payload=recipe
    ))

# Insert the points into the collection
client.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print(f"Created collection '{COLLECTION_NAME}' and inserted {len(recipes)} recipes.")
