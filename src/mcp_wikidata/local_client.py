import os
import sys
import json
import argparse
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

def get_model(args):
    """Initialize the model based on command line arguments."""
    if args.provider == "ollama":
        return ChatOllama(model=args.model)
    elif args.provider == "openai":
        if not args.api_key:
            # Try to get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key must be provided either via --api-key or OPENAI_API_KEY environment variable")
        else:
            api_key = args.api_key
        return ChatOpenAI(model=args.model, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {args.provider}")


# attempt to locate server.py in the same directory as this client script

try:
    # server_py = "uvx --from git+https://github.com/esteinholtz-cloudera/mcp-wikidata mcp-wikidata"
    server_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")

except Exception as e:
    print(f"Error locating server.py: {e}", file=sys.stderr)
    try:
        server_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
        # server_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "mcp_wikidata", "server.py")
    except Exception as e2:
        print(f"Error locating server.py in fallback location: {e2}", file=sys.stderr)
        sys.exit(1)

server_params = StdioServerParameters(
     command="python",
     args=[server_py],
)

def make_serializable(obj):
    """Convert an object to a JSON-serializable format."""
    if hasattr(obj, '__dict__'):
        return {k: make_serializable(v) for k, v in obj.__dict__.items() 
               if not k.startswith('_')}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    return str(obj) if callable(obj) else obj

def format_response(response, format_type="default", pretty=False):
    """Format the response based on the specified format type."""
    messages = response["messages"]
    
    # Convert messages to the verbose format
    verbose_messages = []
    for msg in messages:
        role = "human" if "HumanMessage" in str(type(msg)) else "ai" if "AIMessage" in str(type(msg)) else "tool"
        message_dict = {
            "role": role,
            "content": msg.content,
            "metadata": make_serializable(msg.response_metadata) if hasattr(msg, 'response_metadata') else {},
            "tool_calls": make_serializable(msg.tool_calls) if hasattr(msg, 'tool_calls') else None
        }
        verbose_messages.append(message_dict)

    # Log the complete conversation except the last message to stderr
    conversation_log = {
        "messages": verbose_messages[:-1]  # All but last message to stderr
    }
    print(json.dumps(conversation_log, indent=2), file=sys.stderr)
    print(file=sys.stderr)
    
    # Return complete message log as JSON (matching the format in inception_openai_movie.json)
    full_response = {
        "messages": verbose_messages  # Include all messages
    }
    
    if pretty:
        return json.dumps(full_response, indent=2)
    return json.dumps(full_response)

async def main(args):
    # Log configuration to stderr as JSON
    if not args.quiet:
        config = {
            "type": "configuration",
            "configuration": {
                "provider": args.provider,
                "model": args.model,
                "question": args.question,
                "openai_api_key": "Set" if (args.provider == "openai" and (args.api_key or os.getenv("OPENAI_API_KEY"))) else "Not Set"
            }
        }
        print(json.dumps(config, indent=2), file=sys.stderr)
        print(file=sys.stderr)

    # Initialize the model
    model = get_model(args)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

                #prompt="You are a helpful assistant. Answer the user's questions based on Wikidata.",

                #4. When a SPO match seems plausible based on context, Validate relationship with a query: SPARQL: #SELECT ?s WHERE { wd:SUBJECT_ID wdt:PROPERTY_ID wd:OBJECT_ID }

            # Create and run the agent
            agent = create_react_agent(
                model,
                tools,                
                prompt="""You are a highly skilled and precise entity linker. Link the user's input to Wikidata, both entities and properties. If you cannot find an exact match, choose the closest match. If no match is found, respond with 'No match found'. Always provide the entity ID (e.g., Q42) or property ID (e.g., P31) in your response. Do not provide any additional information or context beyond the ID. Your responses should be concise and to the point.

                IMPORTANT: After finding the entities and property, you MUST validate the relationship exists by executing a SPARQL query. Only return the JSON-LD if the relationship is confirmed to exist.
                
                Workflow:
                1. Find subject entity IDs: <list> SUBJECT_IDs
                2. Find object entity IDs: <list> OBJECT_IDs
                3. Find property IDs: <list> PROPERTY_IDs
                4. Execute SPARQL query to validate the possible SPOs or OPSs with the found IDs:

                SELECT ?subject ?subjectLabel ?object ?objectLabel
WHERE {
  {
    ?subject ?predicate ?object .
  }
  UNION
  {
    ?object ?predicate ?subject .
  }
  VALUES ?object {
    all OBJECT_IDs  }
  VALUES ?predicate {
    all PROPERTY_IDs  }
  VALUES ?subject {
    all SUBJECT_IDs }
}

LIMIT 100 # 
                
                5. Return JSON-LD if matches are found, otherwise try the next "Relationship not found in Wikidata"

                format:
                ================
                Input: RDF SPO triple in the format {Subject: 'subject', Predicate: 'predicate', Object: 'object'} example:
                {Subject: 'Douglas Adams', Predicate: 'writer_of', Object: 'Hitchhikers guide to the galaxy'} 
                
                Output: JSON-LD with the linked entities and properties, e.g.:
                {
                    "@context": {
                        "wd": "http://www.wikidata.org/entity/",
                        "wdt": "http://www.wikidata.org/prop/direct/",
                        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                        "authorOf": {
                            "@id": "wdt:P50"
                         }
                    },
                    "@id": "wd:Q42",
                    "rdfs:label": "Douglas Adams",
                    "authorOf": {
                        "@id": "wd:Q3107323",
                        "rdfs:label": "The Hitchhiker's Guide to the Galaxy"
                    }
                }
                """ 

            )
            
            agent_response = await agent.ainvoke(
                {
                    "messages": args.question,
                }
            )
            
            # Process and output the response
            formatted_response = format_response(agent_response, args.format, args.pretty)
            
            # Print final response to stdout (assuming it's JSON-LD)
            print(formatted_response, file=sys.stdout)


if __name__ == "__main__":
    import asyncio
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Wikidata question-answering client")
    parser.add_argument("question", help="The question to ask", nargs="+")
    parser.add_argument("--provider", "-p", choices=["ollama", "openai"], default="openai",
                      help="The model provider to use (default: openai)")
    parser.add_argument("--model", "-m", default="gpt-4o-mini",
                      help="The model to use (default: gpt-oss:20b for Ollama, gpt-4o-mini for OpenAI)")
    parser.add_argument("--api-key", help="OpenAI API key (only needed for OpenAI provider)")
    parser.add_argument("--format", "-f", choices=["default", "json", "simple"], default="default",
                      help="Output format (default: default)")
    parser.add_argument("--pretty", action="store_true",
                      help="Pretty print the output (only applies to JSON format)")
    parser.add_argument("--quiet", "-q", action="store_true",
                      help="Suppress configuration output")
    
    args = parser.parse_args()
    
    # Join the question words into a single string
    args.question = " ".join(args.question)
    
    # Set default OpenAI model if not specified
    if not args.provider:
        args.provider = "openai"

    # If using OpenAI but still have the Ollama default model, switch to OpenAI default
    if args.provider == "openai" and args.model == "gpt-oss:20b":
        args.model = "gpt-4o-mini"

    asyncio.run(main(args))