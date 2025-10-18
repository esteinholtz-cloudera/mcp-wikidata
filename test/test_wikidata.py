#PURPOSE: Test the search_wikidata function for both entity and property searches.

import asyncio
from mcp_wikidata.server import search_wikidata, search_entity, search_property

async def main():
    # Test with an entity query (e.g., "Leo Tolstoy")
    entity_queries = ["Leo Tolstoy", "War and Peace", "Björn Borg", "tennis", "Douglas Adams", "hitchhiker's guide to the galaxy"]
    
    print("Testing entity searches:")
    for query in entity_queries:
        results = await search_entity(query, limit=5)
        # results = await search_wikidata(query, is_entity=True, limit=5)
        print(f"Results for '{query}': {results}")    
    
    # Test with a property query (e.g., "author")
    property_queries = ["author", "writer", "narrator", "sport", "birthplace", "occupation"]
    
    print("\nTesting property searches:")

    for query in property_queries:
        results = await search_property(query, limit=5)
        print(f"Results for '{query}': {results}")

if __name__ == "__main__":
    asyncio.run(main())