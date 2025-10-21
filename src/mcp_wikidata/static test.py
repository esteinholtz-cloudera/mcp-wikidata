from mcp_wikidata.server import link_triple, search_entity, search_property, execute_sparql, get_properties

import asyncio
import sys
import argparse
import ast
import json

async def main():
    print ("Testing wikidata linker")
    E1 = await search_entity("Leo Tolstoy", limit=5)
    print (json.dumps(E1, indent=2))
    P1 = await get_properties(E1[0])
    print (json.dumps(P1, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
