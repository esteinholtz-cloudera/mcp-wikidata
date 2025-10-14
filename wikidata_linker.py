from src.server import search_entity, search_property, execute_sparql

async def link_triple(triple: dict) -> str:
    subject_candidates = await search_entity(triple["subject"], limit=20)
    object_candidates = await search_entity(triple["object"], limit=20)
    property_candidates = await search_property(triple["predicate"], limit=20)

    if not subject_candidates: 
        return "No subject match found"
    if not object_candidates:
        return "No object match found"
    if not property_candidates:
        return "No property match found"

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

    if sparql_result and sparql_result != "{}":
        return sparql_result
    return "No match found"

async def main():
    subject = "Douglas Adams"
    property = "author of"
    object = "The Hitchhiker's Guide to the Galaxy"

    # read arguments from command line if provided
    import sys
    triple_i = sys.argv[1]

# convert triple_i from string representation of dict to actual dict
    import ast
    triple = ast.literal_eval(triple_i)

    result = await link_triple(triple)
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

