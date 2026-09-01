# Navigation and `.order` reference

How the navigation chain works and how to insert/remove documents correctly.
The navigation *rules* (chain connectivity, order, formatting preservation) are
in `AGENTS.md` → "Navigation Style"; this file adds the JSON mechanics and
procedures.

## `.order` files

One `.order` per directory, one name per line, no blank lines or comments:

- Folders: name only, no extension.
- Documents: name **with** `.yut` extension (even when the physical file is a
  `.yut.in` — `.order` keeps referencing the `.yut` name).

The order defines the app's navigation sequence and the folder display order.

Known gaps in the current library (do not "fix" silently — mention them):
- Folders without `.order`: `Другое`/`Others`, `Размерности`/`Units`,
  `Физика/Динамика`/`Physics/Dynamics` (pt_BR notably has `.order` in Outros
  and Unidades).
- `ru/Математика/.order` lists `Алгебра` which does not exist there (Алгебра
  lives under Калькуляторы).
- `en` quirks: `Piramid.yut` (typo), a doubled `….yut.yut` file name in
  Electrical engineering, and a stray `Circular sector.yut.tmp_unpacked`.

## Navigation paragraph — verbatim shape

Navigation links are the last paragraph of help articles, preceded by an
**empty paragraph**. From `library/ru/Справка/Начало работы/Блок калькулятора.yut`:

```json
{
  "id": "0,4", "type": 2,
  "elements": [ { "id": "0,4,0", "type": 3,
    "elements": [
      { "id": "0,4,0,0", "type": 4, "elements": "", "format_id": "<empty-string format>" }
    ] } ],
  "format_name": "Основной текст", "format_alignment": 0
}
```

```json
{
  "id": "0,5", "type": 2,
  "elements": [
    { "id": "0,5,0", "type": 3,
      "elements": [
        { "id": "0,5,0,0", "type": 39,
          "elements": "<- ../Введение/Политика конфиденциальности",
          "format_id": "<link format>",
          "url": "../Введение/Политика конфиденциальности.yut" },
        { "id": "0,5,0,1", "type": 4,
          "elements": "  ",
          "format_id": "<body format>" },
        { "id": "0,5,0,2", "type": 39,
          "elements": "Курсор ->",
          "format_id": "<link format>",
          "url": "./Курсор.yut" }
      ] }
  ],
  "format_name": "Основной текст", "format_alignment": 0
}
```

Facts:

- Previous link first, separator `"  "` (two spaces; some older docs use one),
  next link last. A single-link document (first/last in section) has just the
  one link and no separator.
- Link `url` always includes the `.yut` extension in new links. A handful of
  old documents have extension-less urls — leave them unless asked, but never
  create new ones.
- `format_id` of the links points at the document's link style
  (underline + blue); the separator uses the body style. When editing, keep the
  original `format_id`, `level`, `format_name`, alignment and spacing — change
  only `elements` text and `url`.
- Link text: previous is `<- Document name` or `<- Section/Document name`;
  next is `Document name ->` / `Section/Document name ->`. Cross-section
  targets include their section prefix as shown above.
- Url forms: within the same directory `./Document.yut`; inside a subsection
  `./Folder/Document.yut`; into a sibling section `../Section/Document.yut`.
- Calculators and the first page have no navigation links.

## Inserting a document into a section

Given: section directory with `.order`, new document `N.yut` to be placed
between existing `A.yut` and `B.yut` (adjacent in `.order`).

1. **Add to `.order`**: insert `N.yut` on its own line between the `A.yut` and
   `B.yut` lines.
2. **New document's links**: append the empty paragraph + navigation paragraph
   with `<- A` (url `./A.yut`) and `B ->` (url `./B.yut`). Use the document's
   own link/body `format_id`s. If the new document is first in the section,
   its only link is the next document; if last — only the previous one.
3. **Update neighbors**:
   - `A.yut`: its "next" link (text and `url`) must now point to `N`.
   - `B.yut`: its "previous" link must now point to `N`.
   - If the new doc is first, the old first document must **gain** a previous
     link (add link + separator into its navigation paragraph, keeping the
     paragraph's existing formatting); if last — the old last document gains
     a next link.
4. **Section boundaries**: if the section sits inside the help tree, the first
   document of a section links to the last document of the previous section
   (cross-section url `../…`) — follow the existing chain in the neighboring
   documents to see what the boundary convention is for that spot.
5. **Renumber ids** in every edited document if paragraphs were added/removed;
   fix `caret` if its target id shifted.

When in doubt about the chain at a given spot, dump the neighbors' current
links first:

```bash
jq -c '.text.elements[-1]' "<file>.yut"        # last paragraph (usually nav)
jq -r '.. | objects | select(.type? == 39) | "\(.elements) -> \(.url)"' "<file>.yut"
```

## Verifying links

From the repo root, check that every internal url resolves to an existing
file (`.yut`, `.yut.in` or a directory listed file) relative to the document:

```bash
find library \( -name '*.yut' -o -name '*.yut.in' \) | while read -r f; do
  dir=$(dirname "$f")
  jq -r '.. | objects | select(.type? == 39) | .url // empty' "$f" 2>/dev/null |
  grep -v '^http' | while read -r url; do
    [ -e "$dir/$url" ] || [ -e "${dir}/${url%.yut}.yut.in" ] || echo "BROKEN: $f -> $url"
  done
done
```

Also confirm every internal link target is listed in the `.order` of its
directory (Workflow Rules in `AGENTS.md` require reporting unlisted targets).
