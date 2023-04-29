#!/bin/bash

for file in *.md; do
    # Get the file name without path
    filename=$(basename "$file")

    # Get the creation date from Git
    creation_date=$(git log --diff-filter=A --pretty=format:"%ad" --date=short --name-only -- "*${filename}" | tail -n 2 | head -n 1)


    # Check if a creation date was found
    if [ -n "$creation_date" ]; then
        # Rename the file with the creation date as a prefix
        mv "$file" "${creation_date}-${file}"
    else
        # Use the fallback date as a prefix
        mv "$file" "0001-01-01-${file}"
    fi
done

