#!/usr/bin/env bash

set -euo pipefail

find ./library -type f -name "*.yut" -print0 | while IFS= read -r -d '' file; do
    echo "Unpacking: $file"
    
    # создаём временный файл
    tmp="${file}.tmp_unpacked"
    
    # распаковка
    gzip -dc "$file" > "$tmp"
    
    # заменяем исходный файл
    mv "$tmp" "$file"
done

echo "Done."