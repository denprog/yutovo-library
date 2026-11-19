# `.yut` document format reference

Construction knowledge for building `.yut` documents by hand. The element type
table and translation rules are in `AGENTS.md`; this file covers layouts,
verbatim examples and field semantics. The authoritative source for element
type numbers is `enum class ElementType` in
`yutovo-editor/src/editor_utils.h` (sibling repo `../yutovo-editor`).

## Boilerplate

The canonical set of `string_formats` and `paragraph_formats` (all 8 styles)
lives in `library/ru/Справка/Ютово.yut` — copy it verbatim for new documents.
Every document defines all 8 paragraph formats in this order:

| # | Name (ru) | Style | Metrics (all except Код identical) |
|---|-----------|-------|------------------------------------|
| 1 | Основной текст | Arial 14 | `alignment 0, word_wrap 1, line_spacing 5, indent_before/after 10, indent_first_line 0, spacing_before/after 10` |
| 2 | Заголовок 1 | Arial 30 bold | same metrics |
| 3 | Заголовок 2 | Arial 26 bold | same metrics |
| 4 | Заголовок 3 | Arial 22 bold | same metrics |
| 5 | Заголовок 4 | Arial 16 bold | same metrics |
| 6 | Пример | Arial 14 italic | same metrics |
| 7 | Моноширинный | FreeMono 12 | same metrics |
| 8 | Код | FreeMono 14 | `word_wrap 0, line_spacing 2, indent_before/after 2, spacing_before/after 2` |

A typical document additionally carries a few extra `string_formats`: the one
actually referenced by body strings (often a byte-identical duplicate of the
"Основной текст" default — harmless), an empty-string style, and a **link
style**: `underline: true, text_color: 4278190335` (blue).

`string_formats` UUIDs are document-local references — copying them between
documents is fine. Only `file_guid` must be globally unique.

### `config` variants

Always present: `language`, `use_tabs`, `tab_spaces`, `real_result`,
`integer_result`, `rational_result`, `complex_result`, `auto_result`,
`include_documents`.

Optional (both occur in help articles and calculators — copy from the template):
- `scale` (e.g. `1.0`) — UI scale factor.
- Syntax-highlight colors: `code_block_border_color`, `numbers_color`,
  `variables_color`, `functions_color`, `units_color`, `shapes_color`,
  `error_marks_color`, `formula_bg_color`, `bg_selection_color` — **signed**
  32-bit ints (e.g. `-16776961`), unlike the unsigned ARGB ints in
  `string_formats`.

A full help-article config example: `library/ru/Справка/Ютово.yut` lines 3–74.

### Including documents (`include_documents`)

`config.include_documents` is a list of `{ "file_name": "…" }` entries. The
path is **absolute from the language tree root** (leading `/`):

```json
"include_documents": [ { "file_name": "/Финансы/Вклады/Простой процент.yut" } ]
```

Effect: the included document's paragraphs are **prepended** to the document,
and the document's own paragraph ids start at the included paragraph count.
Real example — `Финансы/Вклады/Простой процент.yut` (article) has paragraphs
`0,0` (intro) and `0,1` (code block); the including stub
`Калькуляторы/Финансы/Вклады/Простой процент.yut` has its own paragraphs at
`0,2`, `0,3`, `0,4` (repeated intro, "Меняйте исходные данные…" line, own
interactive code block).

Rules:
- Every document still has its own unique `file_guid`.
- `format_name`/`format_id` references resolve within each file's own
  `paragraph_formats`/`string_formats` — the stub must define the formats it
  uses itself.
- This pattern is used by all 16 finance calculator stubs
  (`Калькуляторы/Финансы/Вклады|Облигации` → `Финансы/Вклады|Облигации`).

## Body elements

Ordinary paragraph (`Основной текст`, body string):

```json
{
  "id": "0,0", "type": 2,
  "elements": [
    { "id": "0,0,0", "type": 3,
      "elements": [
        { "id": "0,0,0,0", "type": 4, "elements": "Text goes here",
          "format_id": "02546dfa-a44e-4781-8924-23b0f7a49fb0" }
      ] }
  ],
  "format_name": "Основной текст", "format_alignment": 0
}
```

Section heading (`Заголовок 4`; note: no `format_alignment` — optional,
defaults to 0):

```json
{
  "id": "0,1", "type": 2,
  "elements": [
    { "id": "0,1,0", "type": 3,
      "elements": [
        { "id": "0,1,0,0", "type": 4, "elements": "Вкладка Результат",
          "format_id": "9a687d97-ef48-4587-91ec-b82063ff8da9" }
      ] }
  ],
  "format_name": "Заголовок 4"
}
```

### Prose typography (learned the hard way)

- **The paragraph's own row is a `ROW` (3).** A `CODE_ROW` (7) as the
  paragraph's row loads and solves, but the renderer drops the spaces on the
  first wrapped line — text displays and copies glued
  («Пределотвечаетнавопрос…»). `CODE_ROW` only inside block hierarchies.
- **Raised/lowered text = string-format runs.** Superscript in prose is a
  separate `STRING` whose format is a clone of the body format with
  `"superscript": true` (subscript analogously). This is what the
  «Верхний индекс»/«Нижний индекс» buttons create (`Document::SetSuperscript`
  — a character format, *not* an element). Example: `10⁻⁶` → three strings
  `10` (body), `−6` (superscript), `.` (body). Unicode superscript/subscript
  characters (`⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺ⁿ`, `₀₁…`) must be converted this way — the
  font lacks most of them and they render as boxes.
- **Indices in prose**: `a_n` / `a_(n+1)` → base string + subscript-format
  string (`a`, `n`). Never leave underscore notation in visible text.
- **A `POWER` element must not sit inside a text `ROW`** — the release build
  segfaults on such a document.
- **Compound math goes to a `TEXT_BLOCK`**, never into prose: compound
  fractions `(a)/(b)`, function definitions with a fraction or exponent
  (`f(x) = …`), inline limits. Pattern: prose announces → block → prose
  continues. Simple mentions (`x → 0`, `1/2`, `x²` as a run) are fine in
  prose; when a definition block sits above, prose refers to it («первая
  последовательность») rather than repeating the formula.


Inline image (`type: 34`, PNG as base64, `elements` always `[]`):

```json
{ "id": "0,0,0,1", "type": 34, "elements": [], "image_base64": "iVBORw0KGgo..." }
```

## Code blocks and formulas

Hierarchy (strict):

```
PARAGRAPH (2) → ROW (3) → CODE_BLOCK (5) → CODE_PARAGRAPH (6) → CODE_ROW (7) → CODE_STRING (8) / formula elements
```

- Never mix `STRING` (4) and code/formula elements in the same `ROW`.
- `CODE_PARAGRAPH` has `format_name` = the code format (`Код`) and usually
  `format_alignment: 0`.
- `CODE_STRING` must live inside a `CODE_BLOCK` hierarchy to resolve its code
  context. Its `can_merge` flag: `true` for numbers and identifiers,
  `false` for unit suffixes (`"ч"`, `"мин"`, `"Гц"`, `"мм"`, …). It is editor
  bookkeeping (controls token merging while typing) — when in doubt set
  `true` for the token and `false` for a unit written right after a number.

### `code_id` — shared calculation spaces

`CODE_BLOCK` carries an integer `code_id`. **Blocks with the same `code_id`
form one calculation space**: assignments in one block are visible in the
others, and a change re-solves all blocks of that id. A new `code_id` creates
an isolated space.

- A simple calculator or help article: **use `code_id: 1` for all blocks**
  (this is what real documents do — e.g. all four blocks of
  `Выполнение вычислений.yut` share `1`).
- Use a different id only to deliberately isolate calculations.

### Real example (calculator, trimmed)

From `library/ru/Калькуляторы/Электротехника/Однофазный ток/Частота генератора.yut` —
one paragraph, one code block, three code paragraphs: two assignments and the
equation `f = p·ω/2π`:

```json
{
  "id": "0,1", "type": 2,
  "elements": [
    { "id": "0,1,0", "type": 3,
      "elements": [
        { "id": "0,1,0,0", "type": 5, "code_id": 1,
          "elements": [

            { "id": "0,1,0,0,0", "type": 6, "format_name": "Код", "format_alignment": 0,
              "elements": [
                { "id": "0,1,0,0,0,0", "type": 7,
                  "elements": [
                    { "id": "0,1,0,0,0,0,0", "type": 27, "auto_solve": true,
                      "elements": [
                        { "id": "…,0", "type": 7, "elements": [
                          { "type": 8, "elements": "p", "format_id": "…", "can_merge": true } ] },
                        { "id": "…,1", "type": 10, "elements": [] },
                        { "id": "…,2", "type": 7, "elements": [
                          { "type": 8, "elements": "1", "format_id": "…", "can_merge": true } ] }
                      ] }
                  ] }
              ] },

            { "id": "0,1,0,0,3", "type": 6, "format_name": "Код", "format_alignment": 0,
              "elements": [
                { "id": "0,1,0,0,3,0", "type": 7,
                  "elements": [
                    { "id": "0,1,0,0,3,0,0", "type": 18, "result_type": 5,
                      "elements": [
                        { "id": "…,0", "type": 7, "elements": [
                          { "type": 8, "elements": "f", "format_id": "…", "can_merge": true } ] },
                        { "id": "…,1", "type": 10, "elements": [] },
                        { "id": "…,2", "type": 7,
                          "elements": [
                            { "id": "…,2,0", "type": 25, "elements": [],
                              "result_auto_advance": true,
                              "results_order": [1, 2, 3, 4],
                              "real_config":     { "precision": 3, "exp": 10, "default_angle_measure": 0,
                                                   "result_angle_measure": 0, "show_angle_measure": false },
                              "integer_config":  { "result_notation": 2, "default_notation": 2, "show_notation": true },
                              "rational_config": { "fraction_form": 1 },
                              "complex_config":  { "precision": 3, "exp": 10, "default_angle_measure": 0,
                                                   "result_angle_measure": 0, "show_angle_measure": false,
                                                   "form": 0, "max_count": 10 } }
                          ] }
                      ] }
                  ] }
              ] }
          ] }
      ] }
  ],
  "format_name": "Основной текст", "format_alignment": 0
}
```

Units are plain `CODE_STRING`s written after the value with
`can_merge: false` (e.g. `"1"` true + `"Гц"` false).

This example is verbatim corpus content in the **legacy** string style
(`x*x`-style operands). New documents write solved formulas fully native
(see "Formulas are native end-to-end" below); units stay `CODE_STRING`s
either way.

## Assignments and equations

- `ASSIGNMENT` (27): `[CODE_ROW left, SHAPE, CODE_ROW right]`, optional
  `auto_solve: true` (recalculate when dependencies change).
- `EQUATION` (18): same layout `[CODE_ROW left, SHAPE, CODE_ROW right]`, must
  have `result_type`, and the right `CODE_ROW` contains exactly one result
  element. Must be inside a `CODE_BLOCK`.
- To **display** a formula without solving it, use a `CODE_BLOCK` with plain
  `CODE_ROW`s (no `EQUATION`).

### `result_type` values

`result_type` uses the solver's `ResultType` enum (`yutovo-solver/src/types.h`) —
**the values do not equal element type numbers**:

| `result_type` | Meaning | Result element (type) on the right |
|---------------|---------|-----------------------------------|
| 1 | REAL | `REAL_RESULT` (21) |
| 2 | INTEGER | `INTEGER_RESULT` (22) |
| 3 | RATIONAL | `RATIONAL_RESULT` (23) |
| 4 | COMPLEX | `COMPLEX_RESULT` (24) |
| 5 | AUTO | `AUTO_RESULT` (25) — the default everywhere |
| 6 | ARRAY_REAL | `ARRAY_REAL_RESULT` (42) |
| 7 | SYMBOLIC_REAL | `SYMBOLIC_REAL_RESULT` (45) |
| 8 | SYMBOLIC_RATIONAL | `SYMBOLIC_RATIONAL_RESULT` (46) |
| 9 | SYMBOLIC_COMPLEX | `SYMBOLIC_COMPLEX_RESULT` (47) |

`AUTO_RESULT` carries a full inline copy of the result configs (see example
above) — copy it from a similar equation and adjust. Optional extras seen in
calculators: `unit: "(мин)"` on individual result configs, and `with_angle_measure`
on symbolic complex configs. `results_order` may be a subset of the document
default (e.g. `[1,2,3,4,6]` to stop auto-advance at arrays).

## Formula element child layouts

Verified against real library documents:

| Element (type) | Children |
|----------------|----------|
| `DIVISION` (14) | `[CODE_ROW numerator, SHAPE, CODE_ROW denominator]` |
| `POWER` (15) | `[CODE_ROW base, SHAPE, CODE_ROW exponent]` |
| `SQUARE_ROOT` (16) | `[SHAPE, CODE_ROW radicand]` |
| `NTH_ROOT` (17) | `[CODE_ROW degree, SHAPE, CODE_ROW radicand]` |
| `ASSIGNMENT` (27) | `[CODE_ROW left, SHAPE, CODE_ROW right]` |
| `SUBSCRIPT` (28) | `[CODE_ROW base, SHAPE, CODE_ROW subscript]` |
| `SUM` (35) | `[ASSIGNMENT lower, SHAPE, CODE_ROW upper, CODE_ROW body]` |
| `PRODUCT` (36) | same layout as `SUM` |
| `UNIT` (37) | `[CODE_ROW name, SHAPE, CODE_ROW value]`; name is usually `SUBSCRIPT` of identifier + system; optional `auto_solve: true` |
| `DEFINITE_INTEGRAL` (49) | `[CODE_ROW lower, SHAPE, CODE_ROW upper, CODE_ROW integrand, CODE_STRING "d", CODE_ROW variable]` |
| `INDEFINITE_INTEGRAL` (50) | `[SHAPE, CODE_ROW integrand, CODE_STRING "d", CODE_ROW variable]` |
| `EQUAL`…`NOT_EQUAL` (67–72) | `[CODE_ROW left, SHAPE, CODE_ROW right]` — see "Comparison elements" below |

Operators and brackets (`PLUS` 11, `MINUS` 12, `MULTIPLY` 13, `COMMA` 38,
brackets 19/20/40/41) are `OnlyShapeFormula` elements: **one `SHAPE` child
plus a `symbol` string field** (older saved files may carry extra `SHAPE`s —
`AfterFromJson` trims them to one on load, so one is the canonical form):

```json
{ "type": 11, "elements": [ {"type":10,"elements":[]} ], "symbol": "+" }
{ "type": 12, "elements": [ {"type":10,"elements":[]} ], "symbol": "-" }
{ "type": 13, "elements": [ {"type":10,"elements":[]} ], "symbol": "·" }
{ "type": 38, "elements": [ {"type":10,"elements":[]} ], "symbol": "," }
{ "type": 19, "elements": [ {"type":10,"elements":[]} ], "symbol": "(" }
{ "type": 20, "elements": [ {"type":10,"elements":[]} ], "symbol": ")" }
```

`symbol` is validated on load (exactly one char, not checked against the
type — write the correct one). Serialization to the parser is the symbol
itself; **`MULTIPLY` serializes as `·` (U+00B7), not `*`** — the solver
accepts `·`, and a `*` may not appear inside a `CODE_STRING`. A unary minus
is the same `MINUS` element placed before the operand: `-5` → `[MINUS,
CODE_STRING "5"]`.

## Comparison elements (types 67–72)

`EQUAL` (67), `GREATER` (68), `LESS` (69), `GREATER_EQUAL` (70),
`LESS_EQUAL` (71), `NOT_EQUAL` (72) — the comparison operators added in
Nov 2026 editor builds. Children are exactly `[CODE_ROW left, SHAPE,
CODE_ROW right]` (like `EQUATION`, but **no `result_type` and no `symbol`
field** — the sign is drawn from the element type; `EQUAL` renders bold).
Both operand rows must be non-empty, otherwise the equation reports
`Expression expected`.

| Element | Type | Displays | Parser output |
|---------|------|----------|---------------|
| `EQUAL` | 67 | `=` (bold) | `(left==right)` |
| `GREATER` | 68 | `>` | `(left>right)` |
| `LESS` | 69 | `<` | `(left<right)` |
| `GREATER_EQUAL` | 70 | `⩾` (U+2A7E) | `(left>=right)` |
| `LESS_EQUAL` | 71 | `⩽` (U+2A7D) | `(left<=right)` |
| `NOT_EQUAL` | 72 | `≠` (U+2260) | `(left<>right)` |

The comparison always wraps itself in parentheses when serialized — "the
calculator parses a comparison only in parentheses" (`formulas/comparison.cpp`).

## Formulas are native end-to-end

Inside **solved** code blocks (`CODE_BLOCK`) every bracket, comma, `+`,
`-`, `·`, assignment and comparison is an element; `CODE_STRING`s carry
only identifiers and numbers (`if`, `for`, `x`, `10`, `0.25`).
Whole-formula strings (`"for(i=1,i<=5,i=i+1,(f=f*i))"`) are the legacy
form and a syntax error for the current solver — new documents are fully
native. Reference implementation:
`Справка/Вычисления/Управляющие конструкции/` («Условное выражение if»,
«Цикл for»).

Display `TEXT_BLOCK`s are **exempt**: nothing inside them is serialized
to the solver, and the shipped corpus (Математика/Производные,
Математика/Пределы — 71 occurrences) freely mixes native structural
elements (derivative fractions, `LIMIT`) with flat operand strings
(`"2*x"`, `"3*x^2"`). Keep that style there; apply full nativization to
solved code only.

Verbatim — the equation `if(x>0,(x),(-x))` (EQUATION left row; the shape,
the result row and configs are omitted):

```json
{ "type": 7, "elements": [
    { "type": 8, "elements": "if", "format_id": "<code format>", "can_merge": true },
    { "type": 19, "elements": [ { "type": 10, "elements": [] } ], "symbol": "(" },
    { "type": 68, "elements": [
        { "type": 7, "elements": [
            { "type": 8, "elements": "x", "format_id": "<code format>", "can_merge": true } ] },
        { "type": 10, "elements": [] },
        { "type": 7, "elements": [
            { "type": 8, "elements": "0", "format_id": "<code format>", "can_merge": true } ] }
      ] },
    { "type": 38, "elements": [ { "type": 10, "elements": [] } ], "symbol": "," },
    { "type": 19, "elements": [ { "type": 10, "elements": [] } ], "symbol": "(" },
    { "type": 8, "elements": "x", "format_id": "<code format>", "can_merge": true },
    { "type": 20, "elements": [ { "type": 10, "elements": [] } ], "symbol": ")" },
    { "type": 38, "elements": [ { "type": 10, "elements": [] } ], "symbol": "," },
    { "type": 19, "elements": [ { "type": 10, "elements": [] } ], "symbol": "(" },
    { "type": 12, "elements": [ { "type": 10, "elements": [] } ], "symbol": "-" },
    { "type": 8, "elements": "x", "format_id": "<code format>", "can_merge": true },
    { "type": 20, "elements": [ { "type": 10, "elements": [] } ], "symbol": ")" },
    { "type": 20, "elements": [ { "type": 10, "elements": [] } ], "symbol": ")" }
  ] }
```

Serializer output of that row: `if((x>0),(x),(-x))`.

**Split rules** when decomposing a written formula (they mirror
`Comparison::AfterInsert` / `Assignment::AfterInsert` — where the editor
wraps the typed left part when an operator is inserted):

- An `ASSIGNMENT` (27) or comparison wraps the preceding row elements as
  its left side, going back until: a comma of the same argument list, the
  open bracket of the enclosing call (`if(`, `for(`, a function), another
  assignment/comparison at the same level, or the row start. Balanced call
  brackets belong to the operand (`f(2)` is the whole left side).
- The right side runs forward until a comma of the same argument list or
  the closing bracket of the enclosing call; everything inside nested
  brackets belongs to the right side.
- `for(i=1,i<=5,i=i+1,(f=f*i))` decomposes to
  `["for", (, ASSIGN[i|1], ",", i, LEQ[i|5], ",", ASSIGN[i| i+1], ",", (,
  ASSIGN[f| f·i], ), )]` — assignments of the head and body sit in the row
  as siblings between the commas, with no `auto_solve`.
- In the app, typing `<` / `>` inside a formula inserts the comparison
  element directly; `Ctrl+=` inserts `EQUAL`, `Ctrl+Shift+=` — `NOT_EQUAL`,
  `Ctrl+Shift+>`/`Ctrl+Shift+.` — `GREATER_EQUAL`,
  `Ctrl+Shift+<`/`Ctrl+Shift+,` — `LESS_EQUAL`.

Note: elements inside code (below a `CODE_BLOCK`) are usually written **without
`id` fields** in saved files — the editor tolerates both; for hand-authored
documents, giving every element a dense `id` is safest and matches the id
renumbering rule.


## TEXT_BLOCK: display-only formulas (types 55/56/57)

A `TEXT_BLOCK` (55) looks like a code block but never solves: equations and
assignments inside are not computed, identifiers are not registered in the
solver, and the right part of every equality stays editable. Use it to *show*
formulas (definitions, theorems, derivations) instead of computing them.
First used at scale by `library/ru/Темы/Производные/`.

Hierarchy (identical to a code block, but no `code_id` — the field is absent):

```
PARAGRAPH (2) → ROW (3) → TEXT_BLOCK (55) → CODE_PARAGRAPH (6) → CODE_ROW (7) → CODE_STRING (8) / formula elements / TEXT_EQUATION (56) / TEXT_ASSIGNMENT (57)
```

Verbatim minimal example — a definition and an equality:

```json
{ "type": 55, "elements": [
  { "type": 6, "format_name": "Код", "format_alignment": 0, "elements": [
    { "type": 7, "elements": [
      { "type": 57, "elements": [
        { "type": 7, "elements": [ { "type": 8, "elements": "y", "format_id": "…", "can_merge": true } ] },
        { "type": 10, "elements": [] },
        { "type": 7, "elements": [ { "type": 8, "elements": "x^2", "format_id": "…", "can_merge": false } ] }
      ] }
    ] }
  ] }
] }
```

- `TEXT_ASSIGNMENT` (57) — display-only definition (`y = x^2`), children
  `[CODE_ROW left, SHAPE, CODE_ROW right]`, both sides plain editable rows.
- `TEXT_EQUATION` (56) — display-only equality, same 3-child layout; there is
  **no** result element and no `result_type`.
- Plain display formulas (no equality) are ordinary `CODE_ROW`s with formula
  elements (`DIVISION`, `POWER`, `SUBSCRIPT`, `SUM`, integrals, …).
- `CODE_STRING`s inside a text block follow the same rules as in code blocks
  (single string, `format_id`, `can_merge`) and must contain visible content.
- Text blocks are **exempt** from the native-end-to-end rule: they never
  serialize to the solver, so flat operand strings (`"2*x"`, `"x^2"`) next to
  native structural elements are the established corpus style here.

### Derivative/limit notation for display

The app notation for a derivative is the Leibniz fraction — build it as a
`DIVISION`, do **not** use prime marks:

- first order: `DIVISION[ [d, expr], , [d, x] ]` (numerator row: `d` then the
  expression; denominator row: `d` then the variable)
- higher order: numerator `POWER(d, n)` then the expression; denominator a
  single `POWER` whose *base row* holds `d` and the variable together and whose
  exponent is `n` (`can_merge: true` on `d` and the exponent matters for the
  solver serialization — copy from
  `Справка/Вычисления/Символьные вычисления/Дифференцирование.yut`)
- "derivative at a point": append an `EVALUATION_BAR_SUBSCRIPT` (54) after the
  fraction; its children are `[SHAPE, CODE_PARAGRAPHS_BLOCK_ASSIGNMENT (53) →
  CODE_PARAGRAPH_ASSIGNMENT (52, format «Код») → CODE_ROW_ASSIGNMENT (51) →
  ASSIGNMENT (var = value, no auto_solve)]`
- display limits: the **native `LIMIT` element (type 62)** — the same element
  the «Предел» toolbar button inserts. Do **not** fake it with `SUBSCRIPT` +
  `lim`. Verbatim (from `Справка/Вычисления/Пределы.yut`):

```json
{ "type": 62,
  "elements": [
    { "type": 8, "elements": "lim", "format_id": "<code format>", "can_merge": false },
    { "type": 7, "elements": [
        { "type": 8, "elements": "x", "format_id": "<condition format>", "can_merge": true } ] },
    { "type": 8, "elements": "→", "format_id": "<condition format>", "can_merge": false },
    { "type": 7, "elements": [
        { "type": 8, "elements": "0", "format_id": "<condition format>", "can_merge": true } ] }
  ] }
```

  Facts (editor source: `formulas/limit.cpp`):
  - Exactly 4 children `[CODE_STRING "lim", CODE_ROW var, CODE_STRING "→",
    CODE_ROW value]`; `AfterFromJson` rejects anything else. The `lim` and
    `→` strings are non-editable at runtime (`editable` is not serialized).
  - The condition strings use a **smaller format** — FreeMono 12 in the help
    corpus (`f37ecfa8-6343-4fe3-aa2b-9c488bc14fff`) vs FreeMono 14 for code;
    the "lim" sign itself uses the normal code format. `level` on the element
    is optional — the editor recalculates it via `UpdateLevel` on load.
  - A **one-sided limit**: the value row ends with a `POWER` whose exponent
    row is `"+"` or `"-"` (e.g. value row `[0, POWER(0, +)]` for `x → 0+`);
    `GetDirection` reads it and the serializer emits the 4th argument.
  - In a **solved equation** the left `CODE_ROW` is `[LIMIT, body…]` — the
    body elements follow the element in the same row, and
    `CodeRow::ToParserString` wraps them into `limit(body, var, value[, ±1])`.
    Do not hand-write `limit(...)` as a `CODE_STRING`; build the element pair
    and let the serializer produce the call. Do not put two such limit
    equations in one `code_id`.
  - Compatibility: builds before Nov 2026 do not parse type 62 at all
    (`document not parsed`). The library corpus already ships type 62
    (help «Пределы» in every language), so new documents target the newer
    builds and must not be "downgraded" to lim+subscript.

## Compatibility notes for solved blocks (learned the hard way)

Verified on the release `deploy/bin/yutovo-desktop` (Oct 2026 build) and the
then-current debug build; re-check when the solver evolves:

- The d/dx fraction (with `EVALUATION_BAR_SUBSCRIPT` for points) solves fine,
  including symbolic results (`result_type` 7). Prefer it over `derivative()`.
- `result_type` 8 (SYMBOLIC_RATIONAL) fails on a d/dx fraction whose expression
  calls a user function (`d f(x)/dx` with `f(x)=…` assigned) — use 7 there.
- INTEGER result (2) for a *numeric derivative at a point* fails; integers work
  for plain integer-valued expressions.
- Two solved derivative equations in **one** `code_id` — one "at point" plus one
  symbolic/nested — can produce `Incorrect operation` (order-dependent solver
  bug). Keep one derivative equation per code block, or keep a block's
  derivative equations of one kind.
- `if(cond,(a),(b))` with a **native comparison element** as the condition is
  the correct form (see `Справка/Вычисления/Управляющие конструкции/`); with
  comparison operators left in strings the equations are syntax errors. As of
  19 Nov 2026 the *evaluation* of if/for calls still fails in the newest
  debug build (`Unknown identifier` / `Syntax error` on every if/for equation,
  reproduced block-by-block — while standalone comparison equations solve,
  variables included, all 9 `SolverAutoTest.comparison*` tests pass): the
  solver support is work in progress in the editor repo. The documents are
  structurally final; re-check solving once the if/for solver lands.
- Definite/indefinite integrals and π in limits solve fine; partial-derivative
  (∂) blocks need the newest solver. A solved limit built as `[LIMIT, body]`
  (see the display-notation section) solves in Nov 2026+ builds; a
  hand-written `limit(...)` `CODE_STRING` does not solve — and never mix the
  two spellings.
- Units: values with unit suffixes and unit arithmetic solve; a derivative over
  a unit-valued *variable* does not.

## Graphs

`GRAPH_LINE` (43) is rare (see `Справка/Вычисления/Графики/`): carries
`graph_format` (`width`, `height`, `color`, `grid_width`) and `plots` with
per-plot `plot_format`; children are `[CODE_ROW, CODE_PARAGRAPHS_BLOCK, CODE_ROW,
CODE_ROW, CODE_ROW, CODE_ROW, SHAPE]`. Copy from an existing graph document
when needed.

`GRAPH_SURFACE` (58) is the 3D surface graph of a function of two variables
(see `Справка/Вычисления/Графики/График поверхности.yut`). Same `graph_format`
as `GRAPH_LINE`, plus `rot_x`/`rot_z` (view rotation angles, doubles).
`plots` holds one entry per expression paragraph; each `plot_format` is
`{ "width", "color", "style" }` where `style` selects the surface rendering:
`0` color by height, `1` solid color, `2` color by height with mesh,
`3` wireframe, `4` points. Children — exactly 8, validated on load:

```
[CODE_ROW y_top, CODE_PARAGRAPHS_BLOCK expressions, CODE_ROW y_var,
 CODE_ROW y_bottom, CODE_ROW x_left, CODE_ROW x_var, CODE_ROW x_right, SHAPE]
```

`level` is 2 on the bound rows and the y-variable row, 1 on the expressions
block, the x-variable row and the SHAPE. Each expression paragraph may carry
the colored `marker` + `marker_format_id` matching the plot color. Expressions
use the two axis variables, which must be distinct identifiers. The element
must sit inside a `CODE_BLOCK` (like all solved code).

`GRAPH_HISTOGRAM` (59) is the histogram graph of arrays of values
(see `Справка/Вычисления/Графики/Гистограмма.yut`). Same `graph_format` as
`GRAPH_LINE`, plus `plots` with one entry per expression paragraph; **no**
`rot_x`/`rot_z` (the view is fixed — bars are placed by their indices and the
graph cannot be panned or zoomed with the mouse). Each expression must
evaluate to an array (`[1, 5, 3, 2]`, a variable holding an array, a function
call, …). Children — exactly 2, validated on load:

```
[CODE_PARAGRAPHS_BLOCK expressions, SHAPE]
```

`level` is 1 on both children. Each expression paragraph (one array of bars)
may carry the colored `marker` + `marker_format_id` matching the plot color;
the editor also sets these markers automatically on load. `plot_format.style`
stores `HistogramStyle` values, interpreted by the graph type (the numeric
range overlaps the surface styles): `0` bars, `1` bars with line, `2` bars
without gaps, `3` stems, `4` area, `5` step, `6` marks — the plot-format
dialog writes these directly.
