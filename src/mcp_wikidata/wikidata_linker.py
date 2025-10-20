from mcp_wikidata.server import link_triple

import asyncio
import sys
import argparse
import ast
import json

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
    print(json.dumps(result))

if __name__ == "__main__":
    asyncio.run(main())

