from qdrant_client import QdrantClient, models 
from app.core.config import settings
from app.services.vector_store import get_embeddings_model
from loguru import logger 

def setup_qdrant():
    """Creates the Qdrant collection and insersts initial recipe data."""
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    embeddings_model = get_embeddings_model()

    try:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        logger.info(f"Collection '{settings.QDRANT_COLLECTION_NAME}' created successfully")
    
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
    
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

    try:
        points = []
        for i, recipe in enumerate(recipes):
            recipe_text = f"{recipe['name']} {recipe['ingredients']} {recipe['instructions']}"
            embedding = embeddings_model.embed_query(recipe_text)
            points.append(models.PointStruct(id=i, vector=embedding, payload=recipe))
            client.upsert(collection_name=settings.QDRANT_COLLECTION_NAME, points=points, wait=True)
            logger.info(f"Inserted {len(recipes)} into '{settings.QDRANT_COLLECTION_NAME}'")
        
    
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
    
if __name__ == "__main__":
    setup_qdrant()