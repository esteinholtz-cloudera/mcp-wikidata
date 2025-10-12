import asyncio
from src.server import search_wikidata  # This correctly references the function from the server module

async def main():
    # Test with an entity query (e.g., "Leo Tolstoy")
    entity_queries = ["Leo Tolstoy", "War and Peace"]
    
    print("Testing entity searches:")
    for query in entity_queries:
        results = await search_wikidata(query, is_entity=True, limit=5)
        print(f"Results for '{query}': {results}")
    
    # Test with a property query (e.g., "author")
    property_queries = ["author", "writer", "narrator"]
    
    print("\nTesting property searches:")
    for query in property_queries:
        results = await search_wikidata(query, is_entity=False, limit=5)
        print(f"Results for '{query}': {results}")

if __name__ == "__main__":
    asyncio.run(main())