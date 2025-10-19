# The intent of the script is to extract AI responses from a JSON file.
# It uses 'jq' to filter and format the relevant data.
cat $1 | jq -r '.messages[] | select(.role=="ai" and .content != "") | .content' |jq