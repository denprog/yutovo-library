#!/usr/bin/env bash

set -euo pipefail

find ./library -type f -name "*.yut" -print0 | while IFS= read -r -d '' file; do
    echo "Packing: $file"

    tmp="${file}.tmp_gzip"

    # упаковка
    gzip -c "$file" > "$tmp"

    # заменяем исходный файл
    mv "$tmp" "$file"
done

echo "Done."