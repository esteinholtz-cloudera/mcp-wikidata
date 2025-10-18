from mcp_wikidata.server import search_entity, search_property, execute_sparql

import asyncio
import sys
import argparse
import ast

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
    parser = argparse.ArgumentParser(description="Process triples and format output.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Subparser for plain format
    plain_parser = subparsers.add_parser('plain', help='Input S, P, O as positional arguments.')
    plain_parser.add_argument('subject', type=str, help='The subject of the triple.')
    plain_parser.add_argument('predicate', type=str, help='The predicate of the triple.')
    plain_parser.add_argument('object', type=str, help='The object of the triple.')

    # Subparser for json format
    json_parser = subparsers.add_parser('json', help='Input a JSON representation of the triple.')
    json_parser.add_argument('triple', type=str, help='A string representation of the triple in JSON format.')

    args = parser.parse_args()

    if args.command == 'plain':
        triple = {
            "subject": args.subject,
            "predicate": args.predicate,
            "object": args.object
        }
    elif args.command == 'json':
        # Convert triple from string representation of dict to actual dict
        triple = ast.literal_eval(args.triple)

    print(f"input: {triple}", file=sys.stderr)

    result = await link_triple(triple)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())

