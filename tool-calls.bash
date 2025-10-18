# The intent of the script is to extract tool call information from a JSON file.
# It uses 'jq' to filter and format the relevant data.
cat $1 | jq '.messages[] | select(.tool_calls != null or .role == "tool") | {call: .tool_calls[0].name, args: .tool_calls[0].args, response: .content} | select(.call != null or .response != null)'