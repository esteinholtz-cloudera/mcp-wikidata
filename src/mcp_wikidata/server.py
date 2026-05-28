
import httpx
import json
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

server = FastMCP("Wikidata MCP Server")

WIKIDATA_URL = "https://www.wikidata.org/w/api.php"
HEADER = {"Accept": "application/json", "User-Agent": "foobar"}


async def search_wikidata(query: str, is_entity: bool = True, limit: int = 1) -> List[str]:
    """
    Search for a Wikidata item or property ID by label/alias match.
    Uses wbsearchentities for items (label/alias search) and the text search
    API for properties, which don't support wbsearchentities.
    """
    if is_entity:
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "type": "item",
            "limit": limit,
            "format": "json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
        response.raise_for_status()
        results = response.json().get("search", [])
        if not results:
            return "No results found. Consider changing the search term."
        return [r["id"] for r in results]
    else:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": 120,
            "srlimit": limit,
            "srqiprofile": "classic",
            "srwhat": "text",
            "format": "json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
        response.raise_for_status()
        try:
            search_results = response.json()["query"]["search"]
            if not search_results:
                return "No results found. Consider changing the search term."
            return [r["title"].split(":")[-1] for r in search_results]
        except KeyError:
            return "No results found. Consider changing the search term."


@server.tool()
async def search_entity(query: str, limit: int = 5) -> List[str]:
    """
    Search for a Wikidata entity ID by its query.

    Args:
        query (str): The query to search for. The query should be unambiguous enough to uniquely identify the entity.

    Returns:
        str: The Wikidata entity ID corresponding to the given query."
    """
    return await search_wikidata(query, limit=limit, is_entity=True)


@server.tool()
async def search_property(query: str, limit: int = 5) -> List[str]:
    """
    Search for a Wikidata property ID by its query.

    Args:
        query (str): The query to search for. The query should be unambiguous enough to uniquely identify the property.

    Returns:
        str: The Wikidata property ID corresponding to the given query."
    """
    return await search_wikidata(query, is_entity=False, limit=limit)


@server.tool()
async def get_properties(entity_id: str) -> List[str]:
    """
    Get the properties associated with a given Wikidata entity ID.

    Args:
        entity_id (str): The entity ID to retrieve properties for. This should be a valid Wikidata entity ID.

    Returns:
        list: A list of property IDs associated with the given entity ID. If no properties are found, an empty list is returned.
    """
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "claims",
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
    response.raise_for_status()
    data = response.json()
    return list(data.get("entities", {}).get(entity_id, {}).get("claims", {}).keys())


@server.tool()
async def execute_sparql(sparql_query: str) -> List[Dict[str, Any]]:
    """
    Execute a SPARQL query on Wikidata.

    You may assume the following prefixes:
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX ps: <http://www.wikidata.org/prop/statement/>

    Args:
        sparql_query (str): The SPARQL query to execute.

    Returns:
        List[Dict[str, Any]]: The result of the SPARQL query execution. If there are no results, an empty list will be returned.
    """
    url = "https://query.wikidata.org/sparql"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url, params={"query": sparql_query, "format": "json"}
        )
    response.raise_for_status()
    result = response.json()["results"]["bindings"]  # This is already a list
    return result  # Return as a list directly

@server.tool()
async def get_metadata(entity_id: str, language: str = "en") -> Dict[str, str]:
    """
    Retrieve the English label and description for a given Wikidata entity ID.

    Args:
        entity_id (str): The entity ID to retrieve metadata for.
        language (str): The language code for the label and description (default is "en"). Use ISO 639-1 codes.

    Returns:
        dict: A dictionary containing the label and description of the entity, if available.
    """
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": "labels|descriptions",
        "languages": language,
        "format": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WIKIDATA_URL, headers=HEADER, params=params)
    response.raise_for_status()
    data = response.json()
    entity_data = data.get("entities", {}).get(entity_id, {})
    label = entity_data.get("labels", {}).get(language, {}).get("value", "")
    description = entity_data.get("descriptions", {}).get(language, {}).get("value", "")
    return {"label": label, "description": description}

@server.tool()
async def link_triple(triple: Dict) -> List[Dict]:
    '''validate and link a triple to wikidata
     Args:
        triple (Dict): A dictionary with keys 'subject', 'predicate', and 'object'.
    Returns:
        one or more matching triples from wikidata, in the form of a list of dicts, however adhering to wikidata's sparql json format
        'subject', 'property', 'object'.
    '''

    subject_candidates = await search_entity(triple["subject"], limit=20)
    object_candidates = await search_entity(triple["object"], limit=20)
    property_candidates = await search_property(triple["predicate"], limit=20)

    if not subject_candidates: 
        return "[{}]"
    if not object_candidates:
        return "[{}]"
    if not property_candidates:
        return "[{}]"
        
    values_subject_clause = "\n".join(f"wd:{item}" for item in subject_candidates)
    values_property_clause = "\n".join(f"wdt:{item}" for item in property_candidates)
    values_object_clause = "\n".join(f"wd:{item}" for item in object_candidates)

    sparql_query = f"""
        SELECT ?subject ?subjectLabel ?property ?propertyLabel ?object ?objectLabel
        WHERE {{
            {{
                ?subject ?property ?object .
            }}
            UNION
            {{
                ?object ?property ?subject .
            }}
        VALUES ?subject {{
            {values_subject_clause}
        }}
        VALUES ?property {{
            {values_property_clause}
        }}
        VALUES ?object {{
            {values_object_clause}
        }}

        }}  LIMIT 10
    """

    sparql_result = await execute_sparql(sparql_query)

    #if sparql_result and sparql_result != "{}":
    return sparql_result
    #return "[{}]"  


@server.tool()
async def link_triples(triples: List[Dict]) -> List[List[Dict]]:
    '''validate and link multiple triples to wikidata
        Args:
        triples (List[Dict]): A list of dictionaries each with keys 'subject', 'predicate', and 'object'.
    Returns:
        A list of results, each being one or more matching triples from wikidata, in the form of a list of dicts, however adhering to wikidata's sparql json format
        'subject', 'property', 'object'.
    '''
    results = []
    for triple in triples:
        result = await link_triple(triple)
        results.append(result)
    return results

def main():
    print("Starting mcp-wikidata server")
    server.run()


if __name__ == "__main__":
    print("Starting mcp-wikidata server")
    server.run()

