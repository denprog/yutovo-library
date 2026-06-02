# Agent Instructions for Yutovo Library

## Project Overview

Yutovo library is a documentation system consisting of `.yut` files — a JSON-based document format. The library provides help articles, scientific articles, calculators, examples and other info for the Yutovo calculator app.

## File Format: `.yut`

- `.yut` files are **JSON documents** with a specific schema.
- Key top-level fields:
  - `config`: document metadata
    - `language`: integer language code (ru=2, en=3, es=4, pt_BR=5)
    - `file_guid`: unique UUID per file (must **not** be shared across translations)
  - `text`: document body containing paragraphs and inline elements
  - `string_formats`: text formatting definitions
  - `block_formats`: paragraph formatting definitions

## Document Structure

The `text.elements` array contains paragraphs (`type: 2`). Each paragraph has `elements` which can be:

| Type | Meaning |
|------|---------|
| `type: 2` | Paragraph |
| `type: 3` | Inline group (span) |
| `type: 4` | Plain text — **this is the only type whose `elements` string should be translated** |
| `type: 39` | Hyperlink (`url` field contains the target path) |

## Library Directory Structure

```
library/
├── ru/          # Russian (language=2)
├── en/          # English (language=3)
├── es/          # Spanish (language=4)
└── pt_BR/       # Portuguese (Brazil) (language=5)
```

Each language directory mirrors the same logical structure:
- `Help/Calculations/` — help articles about calculations
- `Calculators/` — calculator documents
- `Others/` — misc documents like "First page"

## `.order` Files

Each directory may contain a `.order` file listing folder/document names in display order:
- Folder names are listed without extension
- Document names are listed **with** `.yut` extension
- Order matters — it defines the navigation sequence in the app

## Translation Rules

1. **Translate `type: 4` text elements.**
2. **Preserve JSON structure, IDs, formats, and all numeric values exactly.**
3. **Update `config.language`** to match the target language code.
4. **Generate a new `file_guid`** for every translated file — never reuse the Russian UUID.
5. **Translate navigation paths:** type 39 `url` fields must point to the translated document names.
6. **Navigation text** (type 39 `elements`) must also be translated.
7. **Translate `paragraph_formats` names** and corresponding `format_name` values in `text.elements` to the target language.

## Navigation Style

Navigation links are `type: 39` elements appended at the end of `text.elements` (after an empty paragraph):

- **Within-section links**: use `./Document.yut` or `./Folder/Document.yut`
- **Cross-section links**: use `../Section/Document.yut`

Navigation text format:
- Previous doc: `<- Document name` or `<- Section/Document name`
- Next doc: `Document name ->` or `Section/Document name ->`

### Paragraph Format Translations

| Russian | English | Spanish | Portuguese (pt_BR) |
|---------|---------|---------|-------------------|
| Основной текст | Text body | Cuerpo de texto | Corpo do texto |
| Заголовок 1 | Header 1 | Encabezado 1 | Cabeçalho 1 |
| Заголовок 2 | Header 2 | Encabezado 2 | Cabeçalho 2 |
| Заголовок 3 | Header 3 | Encabezado 3 | Cabeçalho 3 |
| Заголовок 4 | Header 4 | Encabezado 4 | Cabeçalho 4 |
| Пример | Example | Ejemplo | Exemplo |
| Моноширинный | Monospace | Monoespaciado | Monoespaçado |
| Код | Code | Código | Código |

## Workflow Rules

- **Never run `git commit`, `git push`, `git reset`, `git rebase` or any git mutations unless explicitly asked to do so.** Always ask for confirmation before committing.

## Language Codes Reference

| Language | Code |
|----------|------|
| Russian (ru) | 2 |
| English (en) | 3 |
| Spanish (es) | 4 |
| Portuguese Brazil (pt_BR) | 5 |
