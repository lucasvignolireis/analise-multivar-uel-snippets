#!/usr/bin/env bash

# Evita erros silenciosos, abortando o script se algum erro acontecer
set -euo pipefail 

# Vai para esse diretório onde o arquivo se encontra
cd "$(dirname "$0")"

INPUT="relatorios/hello_world.typ"
OUTPUT="relatorios/gerados/hello_world.pdf"

echo "Gerando um relatório de teste baseado em relatorios/gerados/hello_world.typ"
echo "comando usado typst compile \"$INPUT\" \"$OUTPUT\""

unset SOURCE_DATE_EPOCH

typst compile "$INPUT" "$OUTPUT"

echo "OK: $OUTPUT"