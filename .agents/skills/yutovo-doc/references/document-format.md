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

Operators and brackets (`PLUS` 11, `MINUS` 12, `MULTIPLY` 13, `COMMA` 38,
brackets 19/20/40/41) contain an array of `SHAPE` placeholders plus a `symbol`
string field. **`MINUS` and `MULTIPLY` carry 3 `SHAPE`s** (the sign glyph is
composite); `PLUS`, `COMMA` and brackets carry 1:

```json
{ "type": 12, "elements": [ {"type":10,"elements":[]}, {"type":10,"elements":[]}, {"type":10,"elements":[]} ], "symbol": "-" }
{ "type": 11, "elements": [ {"type":10,"elements":[]} ], "symbol": "+" }
```

Note: elements inside code (below a `CODE_BLOCK`) are usually written **without
`id` fields** in saved files — the editor tolerates both; for hand-authored
documents, giving every element a dense `id` is safest and matches the id
renumbering rule.

## Graphs

`GRAPH_LINE` (43) is rare (see `Справка/Вычисления/Графики/`): carries
`graph_format` (`width`, `height`, `color`, `grid_width`) and `plots` with
per-plot `plot_format`; children are `[CODE_ROW, CODE_PARAGRAPHS_BLOCK, CODE_ROW,
CODE_ROW, CODE_ROW, CODE_ROW, SHAPE]`. Copy from an existing graph document
when needed.
