---
name: yutovo-doc
description: Create, edit, translate and validate Yutovo `.yut` documents (help articles, calculators) in the yutovo-library repository. Use whenever the task involves creating a new document or calculator, editing paragraphs/formulas/navigation links inside a .yut or .yut.in file, adding a document to a .order file, or translating documents between library languages (ru/en/es/pt_BR/de) — even if the user just says "add an article", "add a calculator" or "fix the links".
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
   (ru=2, en=1, es=3, pt_BR=4, de=5).
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

### Math notation (hard rules)

The editor has a fixed notation set. Documents must not invent alternatives:

- **Derivative = Leibniz fraction.** Write derivatives as the `d/dx` fraction
  (`DIVISION` with `d` tokens, higher order `d²/dx²` — see
  `references/document-format.md`). Do **not** use the `derivative(...)` function
  call in documents when the fraction exists, and do **not** use prime/stroke
  notation (`f'`, `y'`, `U+2032`) anywhere — the app has no such notation.
- **Limits = native `LIMIT` element (type 62).** Display limits use the
  `LIMIT` element — the big `lim` with a `variable → value` condition row
  underneath — exactly as `Справка/Вычисления/Пределы.yut` does (the shipped
  help corpus uses type 62 in every language). Do **not** fake it with `lim` +
  `SUBSCRIPT`, and never write a limit inline in prose (`lim_{x→2} x² = 4`) —
  put it in a `TEXT_BLOCK`. In *solved* equations build the left row as
  `[LIMIT element, body…]`: the `CODE_ROW` serializer emits the
  `limit(body, var, value)` call itself; a one-sided limit is a trailing
  `POWER` with exponent `+`/`-` in the value row (serialized as the 4th
  argument). Compatibility: desktop builds before Nov 2026 do not parse
  type 62 — the library has already crossed that line (help files ship it),
  so new documents target the newer builds; do not "fix" a type 62 document
  back to lim+subscript.
- **Comparisons = native comparison elements (types 67–72).** An `=`, `>`, `<`,
  `⩾`, `⩽`, `≠` between two operands is a comparison element with children
  `[CODE_ROW left, SHAPE, CODE_ROW right]` (like `EQUATION`, but no
  `result_type` and no `symbol` field) — see `references/document-format.md`.
  Never leave comparison operators inside `CODE_STRING`s (`"if(x>0,…)"`): the
  calculator parses a comparison only in parentheses, and the element
  serializer is what parenthesizes it (`x>0` → `(x>0)`, `x=5` → `(x==5)`,
  `x≠2` → `(x<>2)`); a string operator reaches the solver unparenthesized and
  is a syntax error. Display signs: `= < > ⩾ ⩽ ≠` (U+2A7E/U+2A7D for the
  or-equal signs — FreeMono has them); in prose (Arial) write `≤ ≥ ≠`
  instead, Arial lacks U+2A7D/U+2A7E.
- **Formulas are native end-to-end.** Inside code blocks every bracket,
  comma, `+`, `-`, multiplication, assignment and comparison is an element;
  `CODE_STRING`s carry **only identifiers and numbers** (a call is `["if",
  "(", …]`, a product `[a, MULTIPLY, b]` — MULTIPLY's symbol is `·` U+00B7
  and it serializes to the solver as `·`). A negative literal is `[MINUS,
  "5"]`, never `"-5"`. Whole-formula strings like `"for(i=1,i<=5,…)"` are the
  legacy form — do not write them in new documents (see
  `Справка/Вычисления/Управляющие конструкции/` for the fully native
  pattern and `references/document-format.md` for the split rules).
- **Subscripts in formulas are `SUBSCRIPT` elements** (type 28), never
  `x_0`-style strings with underscores inside `CODE_STRING`s.
- **Prose super/subscripts are character formats, not elements and not
  Unicode chars.** The «Верхний индекс»/«Нижний индекс» toolbar buttons
  create a *string format* with `superscript: true` / `subscript: true`
  (`Document::SetSuperscript` → a format differing from the body format only
  in that flag) — the only correct way to raise/lower text in prose. Never
  use Unicode super/subscript characters (`⁻⁶`, `ⁿ`, `₀`) — the font lacks
  most of them and they render as boxes (plain `²`/`³` do exist but are
  converted too, for consistency). A prose index is a base STRING + a
  subscript-format STRING (`a` + `n`), never `a_n`. A `POWER` element must
  not be placed inside a text `ROW` — the release build segfaults on it.
- **Compound math lives in `TEXT_BLOCK`s, not in prose.** A compound
  fraction (`(x²−9)/(x−3)`), a function definition carrying a fraction or an
  exponent (`f(x) = …`, `s(t) = …`, `a_(n+1) = …`), and any inline limit
  expression are written as: prose announces → `TEXT_BLOCK` with native
  elements → prose continues («Функция» → block → «в точке 3 не
  определена…»). Simple mentions (`x → 0`, `1/2`, `x²` as a format run) may
  stay in prose; when a definition block already exists above, prose refers
  to it («первая последовательность») instead of repeating the formula.
- **No empty or padded `CODE_STRING`s**: a `CODE_STRING` must contain visible
  content; never emit `" "`, `""`, `" = "`, `"k = "` (leading/trailing spaces).
  Put equalities into `TEXT_EQUATION`/`TEXT_ASSIGNMENT` instead of hand-made
  `=` strings.
- **Minimal brackets**: fraction operands and power exponents never need
  grouping brackets — the fraction bar and the superscript slot group visually.
  A hand-authoring parser must drop redundant parentheses: `(x^2+1)/(x-2)` is a
  `DIVISION` with plain rows, `e^(sin(2*x))` a `POWER` whose exponent row is
  `sin(2·x)` (built natively: `"sin"`, `(`, `"2"`, `·`, `"x"`, `)`). Keep
  brackets only where precedence truly requires them (a sum inside a product,
  a sum as power base).
- **Formula blocks stay formulas**: prose annotations («при любом n») belong in
  body paragraphs, not in code strings.

### Examples and cross-links

- An example starts with a paragraph of format `Пример` (localized) whose whole
  text is `Пример:`; the description follows in ordinary body paragraphs.
- When an article mentions a topic covered by another library document, add an
  inline `LINK` element to that document (link format, `url` relative to the
  current file; from depth two use `../../Section/...`). Verify the target is
  listed in the target directory's `.order`.

- **No title paragraph.** The app shows the file name as the document title.
  The first paragraph is ordinary body text (`Основной текст` /
  `Text body` / …). Do not use `Заголовок 1`–`Заголовок 3` — they are declared
  in every document but never used. Use `Заголовок 4` for in-document section
  headings.
- **Alignment is always `0`** (left) on every paragraph in the library.
- **Unordered lists use paragraph markers.** A list item is an ordinary
  paragraph carrying `"marker": "•"` (valid glyphs: `•`, `●`, `♦`, `■`) and
  `"marker_format_id"` — normally the same UUID as the paragraph format's
  `default_string_format`. The bullet glyph must NOT be repeated in the text.
  `paragraph_formats` holds a marker variant of the format (same localized
  `name`, same fields, plus `"marker": "•"`). Do not confuse these with the
  `"█"` cursor placeholder on `CODE_PARAGRAPH`s in saved files — never add
  that one by hand.
- **"Пример" paragraphs** are ordinary paragraphs with format `Пример` whose
  text starts with `Пример:` (localized).
- **One paragraph usually has one `ROW`** with all its strings. Multiple `ROW`s
  inside a paragraph correspond to hard line breaks — allowed, but not needed
  for new text (the editor re-wraps automatically).
- **A text paragraph's own row is a `ROW` (3), never a `CODE_ROW` (7).** A
  `CODE_ROW` placed as the paragraph's row loads and solves fine, but the
  renderer drops the spaces on the paragraph's *first wrapped line*: the text
  comes out visually glued («Пределотвечаетнавопрос…»), and copying
  reproduces the gluing. `CODE_ROW` belongs inside `CODE_BLOCK`/`TEXT_BLOCK`
  hierarchies only.
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
3. Open the file with `yutovo-desktop` headless — it must load without
   `document not parsed`, and ideally solve without `Solver error`:

   ```bash
   QT_QPA_PLATFORM=offscreen timeout 12 <desktop> <file.yut> 2>&1 |
       grep -iE "not parsed|Solver error"
   ```

   - The desktop opens **one** document per launch (pass a single file, one
     run per file); the log names the file only for load errors, not solver
     errors.
   - **An empty log is a meaningless pass.** The desktop is single-instance
     (`/tmp/yutovo_instance` local socket): launched right after a previous
     instance was killed (e.g. by `timeout`), the new process hands the file
     to the dying one and exits instantly with an empty log. Wait ≥3 s
     between runs and require the log to be non-empty (> ~50 bytes) before
     trusting "0 errors".
   - **Offscreen solver verdicts are unreliable for structural limits.**
     `QT_QPA_PLATFORM=offscreen` produces spurious `Unknown identifier` /
     `Syntax error` on native `LIMIT` equations — including in shipped help
     articles. If such a document reports solver errors headless, re-check
     in a real GUI (Xvfb + screenshot) before treating it as a defect.
   - **Solved if/for equations report `Unknown identifier` / `Syntax error`
     until the if/for solver lands** (work in progress in the editor repo as
     of 19 Nov 2026). Native comparison elements themselves solve (all 9
     `SolverAutoTest.comparison*` tests pass, variables included); only the
     call evaluation is missing. The «Управляющие конструкции» documents are
     structurally final — see the compatibility notes in
     `references/document-format.md`.
   - Validate against **both** binaries if available:
     `deploy/bin/yutovo-desktop` (release, Oct 2026 — predates type 62, so
     documents using the native `LIMIT` element legitimately fail there) and
     the freshest `deploy/bin/yutovo-desktopd` / debug build (newest
     features). The compatibility baseline is the **newest shipped corpus**
     (help files already use type 62), not the old release binary.
   - The debug solver is nondeterministic under load: judge a document by its
     blocks (split each `CODE_BLOCK` into a one-block document and run those),
     and treat a whole-document error that does not reproduce across runs as
     build noise.
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
- [ ] notation: derivatives as d/dx fractions (no `derivative()` where a
      fraction exists, no primes), limits as native `LIMIT` elements
      (no lim+subscript, never inline in prose), subscripts as `SUBSCRIPT`
      elements, comparisons as native comparison elements 67–72
      (no `== < > <= >= <>` inside `CODE_STRING`s), formulas native
      end-to-end (brackets/commas/`+ - ·`/assignments as elements,
      `CODE_STRING`s only identifiers and numbers)
- [ ] prose: text paragraphs' rows are `ROW` (3); no Unicode
      super/subscript chars (⁻⁶, ₀ — use format runs); no `a_n` underscore
      indices (use subscript-format runs); compound fractions, function
      definitions with fractions/exponents and inline limits are in
      `TEXT_BLOCK`s
- [ ] no empty/padded `CODE_STRING`s, no redundant grouping brackets in
      fractions and exponents, no prose inside formula strings
- [ ] examples open with a `Пример`-format paragraph reading `Пример:`;
      topic mentions link to the covering document when one exists
- [ ] document loads in the newest desktop build (see Validation for the
      release-binary caveat on type 62)
