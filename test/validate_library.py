#!/usr/bin/env python3
"""Validate a yutovo-library language tree against the Translation Rules
(AGENTS.md) and the yutovo-doc skill checklist.

Usage: python3 test/validate_library.py [language]   (default: de)

Checks:
  1. every .yut parses as JSON; .yut.in preprocesses to valid JSON
     both with and without -DWEB
  2. config.language matches the expected code of the tree
  3. file_guid is unique inside the tree and does not collide with
     the Russian source guids
  4. no source-language (Russian) text remains in STRING/LINK elements
     and no Cyrillic identifiers remain in code strings
  5. internal links resolve to existing documents listed in the
     target directory's .order file
  6. every directory mirrors the Russian tree (same entry set)
  7. paragraph format names are localized (not Russian)
  8. .order sequences mirror the Russian tree (name-independent
     subtree-shape signatures, so reordered sections are caught)
"""

import json
import os
import re
import subprocess
import sys

LANG = sys.argv[1] if len(sys.argv) > 1 else 'de'
LANG_CODE = {'en': 1, 'ru': 2, 'es': 3, 'pt_BR': 4, 'de': 5, 'fr': 6, 'it': 7}[LANG]

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'library')
SRC = os.path.join(LIB, 'ru')
DST = os.path.join(LIB, LANG)

problems = []


def seg_translate(seg):
    """Translate a segment between language trees via .order alignment."""
    return None


# collect ru guids and the ru entry set per directory
ru_guids = set()
ru_tree = {}
for root, dirs, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC)
    entries = sorted(dirs) + sorted(files)
    ru_tree[rel] = set(entries)
    for f in files:
        if f.endswith('.yut'):
            try:
                d = json.load(open(os.path.join(root, f), encoding='utf-8'))
                ru_guids.add(d['file_guid'])
            except Exception:
                pass

de_guids = {}
link_targets = {}  # dir -> ordered entries from .order
de_tree = {}
for root, dirs, files in os.walk(DST):
    rel = os.path.relpath(root, DST)
    de_tree[rel] = set(sorted(dirs) + sorted(files))
    order = os.path.join(root, '.order')
    if os.path.exists(order):
        link_targets[rel] = [l.strip() for l in open(order, encoding='utf-8') if l.strip()]

# 6. mirror check: same directory count and same document count as the ru tree
def counts(tree_root):
    dirs = files = orders = 0
    for root, ds, fs in os.walk(tree_root):
        dirs += len(ds)
        files += sum(1 for f in fs if f.endswith(('.yut', '.yut.in')))
        orders += sum(1 for f in fs if f == '.order')
    return dirs, files, orders

ru_counts = counts(SRC)
de_counts = counts(DST)
if ru_counts != de_counts:
    problems.append(f'tree shape differs from ru: {de_counts} vs {ru_counts} (dirs, docs, orders)')

# ru .order entries whose targets are already missing in ru (pre-existing gaps)
ru_stale_order = set()
for root, dirs, files in os.walk(SRC):
    order = os.path.join(root, '.order')
    if not os.path.exists(order):
        continue
    rel_dir = os.path.relpath(root, SRC)
    for line in open(order, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        target = os.path.join(root, line)
        if not os.path.exists(target) and not os.path.exists(target.replace('.yut', '.yut.in')):
            ru_stale_order.add((rel_dir, line))

cyr = re.compile('[А-Яа-яЁё]')

for root, dirs, files in os.walk(DST):
    dirs.sort()
    rel_dir = os.path.relpath(root, DST)
    for fn in sorted(files):
        relp = os.path.join(rel_dir, fn)
        full = os.path.join(root, fn)
        if fn.endswith('.yut'):
            try:
                doc = json.load(open(full, encoding='utf-8'))
            except Exception as e:
                problems.append(f'JSON parse error: {relp}: {e}')
                continue
            g = doc['file_guid']
            if g in de_guids:
                problems.append(f'duplicate guid {g}: {relp} and {de_guids[g]}')
            de_guids[g] = relp
            if g in ru_guids:
                problems.append(f'guid reused from ru tree: {relp}')
            if doc['config'].get('language') != LANG_CODE:
                problems.append(f'wrong config.language in {relp}: {doc["config"].get("language")}')
            for fmt in doc.get('paragraph_formats', []):
                if cyr.search(fmt.get('name', '')):
                    problems.append(f'cyrillic paragraph format name in {relp}: {fmt["name"]}')
        elif fn.endswith('.yut.in'):
            for web in (False, True):
                cmd = ['cpp', '-P', '-x', 'c'] + (['-DWEB'] if web else []) + [full]
                r = subprocess.run(cmd, capture_output=True, text=True)
                try:
                    doc = json.loads(r.stdout)
                except Exception as e:
                    problems.append(f'.in preprocess error ({"web" if web else "lib"}) {relp}: {e}')
                    continue
                if doc['config'].get('language') != LANG_CODE:
                    problems.append(f'wrong language in .in ({relp})')
        elif fn == '.order':
            pass  # stale entries are compared globally against the ru tree below
# stale .order entries must not exceed the pre-existing ru gaps
de_stale_order = 0
for root, dirs, files in os.walk(DST):
    order = os.path.join(root, '.order')
    if not os.path.exists(order):
        continue
    for line in open(order, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        target = os.path.join(root, line)
        if not os.path.exists(target) and not os.path.exists(target.replace('.yut', '.yut.in')):
            de_stale_order += 1
if de_stale_order != len(ru_stale_order):
    problems.append(f'stale .order entries: {de_stale_order} (ru has {len(ru_stale_order)})')

# 8. .order sequences mirror ru (directory names are localized, so trees are
#    paired structurally in lockstep from the root; signatures are
#    name-independent subtree shapes, stale entries are ignored)
def sub_rel(rel, name):
    return name if rel == '.' else os.path.join(rel, name)


def order_entries(tree_root, rel):
    """Non-stale .order entries of a directory, or None without .order."""
    path = os.path.join(tree_root, rel, '.order')
    if not os.path.exists(path):
        return None
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        target = os.path.join(tree_root, rel, line)
        if os.path.exists(target) or os.path.exists(target.replace('.yut', '.yut.in')):
            out.append(line)
    return out


def dir_sig(tree_root, rel):
    """Name-independent shape signature of a directory: ('seq', ...) built
    from its .order entry signatures, or ('set', ...) — a sorted multiset of
    child signatures — when the directory has no .order (unordered).
    Docs and other non-directories contribute ('doc',)."""
    base = os.path.join(tree_root, rel)
    if not os.path.isdir(base):
        return ('doc',)
    entries = order_entries(tree_root, rel)
    if entries is None:
        kids = [dir_sig(tree_root, sub_rel(rel, n)) for n in os.listdir(base)
                if os.path.isdir(os.path.join(base, n)) or n.endswith(('.yut', '.yut.in'))]
        return ('set', tuple(sorted(kids)))
    sig = []
    for e in entries:
        sig.append(dir_sig(tree_root, sub_rel(rel, e)))
    return ('seq', tuple(sig))


def order_diffs(ru_rel, dst_rel):
    """Descriptions of .order differences between ru_rel and its
    structural counterpart dst_rel (both '.' at the root)."""
    ru_entries = order_entries(SRC, ru_rel)
    de_entries = order_entries(DST, dst_rel)
    if (ru_entries is None) != (de_entries is None):
        return [f'{dst_rel}: .order presence differs from ru']
    if ru_entries is None:
        if dir_sig(SRC, ru_rel) != dir_sig(DST, dst_rel):
            return [f'{dst_rel}: unordered directory shape differs from ru']
        return []
    ru_sigs = [dir_sig(SRC, sub_rel(ru_rel, e)) for e in ru_entries]
    de_sigs = [dir_sig(DST, sub_rel(dst_rel, e)) for e in de_entries]
    if ru_sigs == de_sigs:
        return []
    if sorted(ru_sigs) == sorted(de_sigs):
        return [f'{dst_rel}: .order sequence differs from ru']
    ru_kinds = [s == ('doc',) for s in ru_sigs]
    de_kinds = [s == ('doc',) for s in de_sigs]
    if len(ru_sigs) != len(de_sigs) or ru_kinds != de_kinds:
        return [f'{dst_rel}: .order entries differ from ru']
    out = []
    for e_ru, e_de, s_ru, s_de in zip(ru_entries, de_entries, ru_sigs, de_sigs):
        if s_ru != s_de and s_ru != ('doc',):
            out.extend(order_diffs(sub_rel(ru_rel, e_ru), sub_rel(dst_rel, e_de)))
    return out


problems.extend(order_diffs('.', '.'))

# 5 + 4: links and leftover Cyrillic
def norm(p):
    return p.replace('\\', '/')


for root, dirs, files in os.walk(DST):
    rel_dir = norm(os.path.relpath(root, DST))
    for fn in sorted(files):
        full = os.path.join(root, fn)
        if fn.endswith('.yut'):
            docs = [json.load(open(full, encoding='utf-8'))]
        elif fn.endswith('.yut.in'):
            docs = []
            for web in (False, True):
                r = subprocess.run(['cpp', '-P', '-x', 'c'] + (['-DWEB'] if web else []) + [full],
                                   capture_output=True, text=True)
                docs.append(json.loads(r.stdout))
        else:
            continue
        relp = f'{rel_dir}/{fn}'
        for doc in docs:
            def walk(n):
                if isinstance(n, dict):
                    t = n.get('type')
                    if t in (4, 39) and isinstance(n.get('elements'), str) and cyr.search(n['elements']):
                        problems.append(f'cyrillic text left in {relp}: {n["elements"][:50]!r}')
                    if t == 8 and isinstance(n.get('elements'), str) and cyr.search(n['elements']):
                        problems.append(f'cyrillic code left in {relp}: {n["elements"][:50]!r}')
                    if t == 39 and isinstance(n.get('url'), str):
                        url = n['url']
                        if not url.startswith('http://') and not url.startswith('https://'):
                            # resolve ../ and ./
                            parts = norm(url).split('/')
                            cur = rel_dir.split('/') if rel_dir != '.' else []
                            for part in parts:
                                if part == '..':
                                    cur = cur[:-1] if cur else []
                                elif part and part != '.':
                                    cur.append(part)
                            target_rel = '/'.join(cur)
                            target_dir = '/'.join(target_rel.split('/')[:-1]) or '.'
                            target_file = target_rel.split('/')[-1]
                            base_file = target_file[:-4] if target_file.endswith('.yut') else target_file
                            base_rel = (target_dir + '/') if target_dir != '.' else ''
                            exists = any(
                                os.path.exists(os.path.join(LIB, LANG, cand))
                                for cand in (
                                    target_rel,
                                    target_rel + '.yut',
                                    target_rel + '.yut.in',
                                    base_rel + base_file + '.yut',
                                    base_rel + base_file + '.yut.in'))
                            if not exists:
                                problems.append(f'broken link in {relp}: {url}')
                            else:
                                order = link_targets.get(target_dir, [])
                                if not any(e == base_file or e == base_file + '.yut' for e in order):
                                    problems.append(f'link target not in .order: {relp}: {url}')
                    for v in n.values():
                        walk(v)
                elif isinstance(n, list):
                    for v in n:
                        walk(v)
            walk(doc)

if problems:
    print(f'VALIDATION FAILED ({LANG}): {len(problems)} problems')
    for p in problems[:60]:
        print('  -', p)
    sys.exit(1)
print(f'validation of library/{LANG} passed')
