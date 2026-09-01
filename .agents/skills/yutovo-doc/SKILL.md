---
name: yutovo-doc
description: Create, edit, translate and validate Yutovo `.yut` documents (help articles, calculators) in the yutovo-library repository. Use whenever the task involves creating a new document or calculator, editing paragraphs/formulas/navigation links inside a .yut or .yut.in file, adding a document to a .order file, or translating documents between library languages (ru/en/es/pt_BR) — even if the user just says "add an article", "add a calculator" or "fix the links".
---

# Yutovo document authoring

This skill produces `.yut` files — strict JSON documents for the Yutovo editor.
The editor and desktop app are strict: deviations usually cause `document not parsed`
or a crash. When in doubt, copy from an existing document rather than inventing.

The format schema (top-level fields, element type table, translation rules) lives in
`AGENTS.md` at the repo root and is always in context. This skill adds the
construction knowledge: templates, verbatim examples, procedures.

## Workflow

1. **Decide the document type** (see "Document types" below) and pick a template
   document of the same type from the same language tree.
2. **Copy the boilerplate** from the template: `config`, `string_formats`,
   `paragraph_formats`. Generate a fresh `file_guid` (the only UUID that must be
   unique per file — `string_formats` UUIDs are document-local and may be copied
   verbatim). Set `config.language` to match the target folder
   (ru=2, en=1, es=3, pt_BR=4).
3. **Write the body** following the conventions in "Conventions" below.
   For formulas, code blocks and equations, read `references/document-format.md`.
4. **Add navigation links** if this is a help article, and update the section's
   `.order` file and the neighbors' links. Read `references/navigation.md`.
5. **Renumber element ids** from the root after the tree is final
   (see "Element ids" below). Set `caret` to `{"id": "0,0,0,0"}` and
   `selection` to `[]`.
6. **Validate** (see "Validation").

## Document types

| Type | Template (ru) | Notes |
|------|---------------|-------|
| Help article | `library/ru/Справка/Ютово.yut` (minimal), `library/ru/Справка/Начало работы/Блок калькулятора.yut` (typical, with formulas and images) | Ends with navigation links; participates in the help navigation chain |
| Calculator | `library/ru/Калькуляторы/Электротехника/Однофазный ток/Частота генератора.yut` | Intro paragraph + one or more code blocks with assignments/equations; **no navigation links** |
| First page | `library/ru/Другое/Первая страница.yut.in` | `.yut.in` (web/library variants merged); edit carefully, keep `#ifdef` blocks intact |

Language policy: new documents are created in `ru/` first; translations into
`en/`, `es/`, `pt_BR/` are separate tasks (follow the Translation Rules in
`AGENTS.md`).

Finance calculators are **pairs of documents** (name-for-name, own `file_guid`
each):
- `library/ru/Финансы/<sub>/<Name>.yut` — the source article: description +
  formulas (e.g. `library/ru/Финансы/Вклады/Простой процент.yut`).
- `library/ru/Калькуляторы/Финансы/<sub>/<Name>.yut` — a thin calculator that
  includes the article via
  `config.include_documents: [{ "file_name": "/Финансы/<sub>/<Name>.yut" }]`
  (path is absolute from the language tree root) and adds its own interactive
  code block (e.g. `library/ru/Калькуляторы/Финансы/Вклады/Простой процент.yut`).

Because the included article's paragraphs are prepended, the stub's own
paragraph ids start at the article's paragraph count (see "Element ids").
When adding a new finance calculator, create both documents.

## Conventions

These come from how every existing document is built; follow them for new ones.

- **No title paragraph.** The app shows the file name as the document title.
  The first paragraph is ordinary body text (`Основной текст` /
  `Text body` / …). Do not use `Заголовок 1`–`Заголовок 3` — they are declared
  in every document but never used. Use `Заголовок 4` for in-document section
  headings.
- **Alignment is always `0`** (left) on every paragraph in the library.
- **No list markers.** Documents use plain paragraphs; the `"marker"` field only
  appears as a cursor placeholder (`"█"`) on `CODE_PARAGRAPH`s in saved files —
  do not add it by hand.
- **"Пример" paragraphs** are ordinary paragraphs with format `Пример` whose
  text starts with `Пример:` (localized).
- **One paragraph usually has one `ROW`** with all its strings. Multiple `ROW`s
  inside a paragraph correspond to hard line breaks — allowed, but not needed
  for new text (the editor re-wraps automatically).
- **`level` is optional.** Some documents carry `"level": 1` on every element,
  others omit it entirely. Either works; omitting is simpler.
- **`block_formats` is never present** in repository files — omit it.

## Element ids

Hierarchical: `"0"` (root), `"0,0"`, `"0,0,0"`, … Paragraph indices start at `0`.
Ids must be dense and match the actual tree position — after building or editing
the tree, reassign all ids from the root.

Exception: documents with non-empty `config.include_documents` — the included
documents' paragraphs are prepended, so the document's own paragraphs start at
the total paragraph count of the included documents (e.g. including one
10-paragraph document → own paragraphs are `0,10`, `0,11`, …). Only the second
id component (paragraph index) shifts.

`caret.id` must point to an existing element (a `STRING` path like `"0,0,0,0"`).

## Validation

1. `jq empty <file>.yut` — must parse.
2. Check every internal link target exists (see `references/navigation.md`).
3. Open the file with `yutovo-desktop` / `yutovo-editor`: it must load without
   `document not parsed`. `Parser exception` in the log is a formula/solver
   error, not a loading error.
4. For `.yut.in` files: `cpp -P -x c <file>.yut.in /tmp/out.json && jq empty /tmp/out.json`
   must produce valid JSON (run twice, with and without `-DWEB`).

## Final checklist

- [ ] `file_guid` is a fresh UUID; `config.language` matches the folder
- [ ] `paragraph_formats` contains every `format_name` referenced in the text,
      with localized names
- [ ] every `format_id` matches a `string_formats` UUID
- [ ] ids dense and matching the tree; `caret` points to an existing STRING
- [ ] `selection` is `[]`
- [ ] internal links resolve to existing `.yut`/`.yut.in` files listed in `.order`
- [ ] (help articles) `.order` updated; previous/next documents' links updated
- [ ] (translations) imaginary unit is `j` in ru, `i` elsewhere; new `file_guid`
