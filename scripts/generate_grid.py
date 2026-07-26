# -*- coding: utf-8 -*-
import json, re, unicodedata, textwrap
"""Génération de app/data/grid.py depuis grid.json.

Usage :
    python scripts/extract_grid_from_xlsx.py "Grille ....xlsx"   # produit grid.json
    python scripts/generate_grid.py                              # produit grid_gen.py
    mv grid_gen.py app/data/grid.py && pytest tests/test_grid.py
"""

grid = json.load(open('grid.json'))

def slug(s, maxlen=40):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip('_').lower()
    return s[:maxlen].rstrip('_')

DIM_CODES = {
 'Gouvernance des données': ('governance', 'Gouvernance', '#4F46E5'),
 'Qualité des données': ('quality', 'Qualité', '#0891B2'),
 'Sécurité des données': ('security', 'Sécurité', '#DC2626'),
 'Intégration des données': ('integration', 'Intégration', '#EA580C'),
 'Analyse des données': ('analytics', 'Analyse', '#16A34A'),
 'Culture et compétences': ('culture', 'Culture', '#9333EA'),
 'Infrastructure des données': ('infrastructure', 'Infrastructure', '#0F766E'),
}

lines = []
lines.append('"""Grille de maturité Data — Limpida Consulting 2024.')
lines.append('')
lines.append('Module généré automatiquement depuis "Grille de maturité Data_Limpida_2024.xlsx".')
lines.append('NE PAS ÉDITER À LA MAIN : régénérer via scripts/generate_grid.py.')
lines.append('')
lines.append('Structure : 7 dimensions, 45 critères, score maximum 768 points.')
lines.append('Formule de score : réponse (0-3) x poids_critère x poids_dimension.')
lines.append('"""')
lines.append('')
lines.append('from __future__ import annotations')
lines.append('')
lines.append('from dataclasses import dataclass, field')
lines.append('from typing import Dict, List')
lines.append('')
lines.append('')
lines.append('@dataclass(frozen=True)')
lines.append('class Criterion:')
lines.append('    """Un critère d\'évaluation, noté de 0 à 3."""')
lines.append('')
lines.append('    code: str')
lines.append('    name: str')
lines.append('    weight: int  # 1 = Pas important, 2 = Important, 3 = Très important')
lines.append('    levels: List[str]  # 4 libellés (niveaux 0 à 3)')
lines.append('    dimension_code: str = ""')
lines.append('    dimension_weight: int = 1')
lines.append('')
lines.append('    @property')
lines.append('    def max_score(self) -> int:')
lines.append('        return 3 * self.weight * self.dimension_weight')
lines.append('')
lines.append('    def score(self, answer: int) -> int:')
lines.append('        return int(answer) * self.weight * self.dimension_weight')
lines.append('')
lines.append('')
lines.append('@dataclass(frozen=True)')
lines.append('class Dimension:')
lines.append('    """Un thème de la grille regroupant plusieurs critères."""')
lines.append('')
lines.append('    code: str')
lines.append('    name: str')
lines.append('    short_name: str')
lines.append('    weight: int')
lines.append('    color: str')
lines.append('    criteria: List[Criterion] = field(default_factory=list)')
lines.append('')
lines.append('    @property')
lines.append('    def max_score(self) -> int:')
lines.append('        return sum(c.max_score for c in self.criteria)')
lines.append('')
lines.append('')
lines.append('def _d(code, name, short, weight, color, criteria):')
lines.append('    crits = [')
lines.append('        Criterion(')
lines.append('            code=f"{code}.{c[0]}",')
lines.append('            name=c[1],')
lines.append('            weight=c[2],')
lines.append('            levels=list(c[3]),')
lines.append('            dimension_code=code,')
lines.append('            dimension_weight=weight,')
lines.append('        )')
lines.append('        for c in criteria')
lines.append('    ]')
lines.append('    return Dimension(code=code, name=name, short_name=short, weight=weight, color=color, criteria=crits)')
lines.append('')
lines.append('')
lines.append('DIMENSIONS: List[Dimension] = [')

for d in grid:
    code, short, color = DIM_CODES[d['name']]
    lines.append('    _d(')
    lines.append(f'        {code!r},')
    lines.append(f'        {d["name"]!r},')
    lines.append(f'        {short!r},')
    lines.append(f'        {d["weight"]},')
    lines.append(f'        {color!r},')
    lines.append('        [')
    seen = {}
    for c in d['criteria']:
        s = slug(c['name'])
        if s in seen:
            seen[s] += 1
            s = f"{s}_{seen[s]}"
        else:
            seen[s] = 1
        lines.append('            (')
        lines.append(f'                {s!r},')
        lines.append(f'                {c["name"]!r},')
        lines.append(f'                {c["weight"]},')
        lines.append('                (')
        for lv in c['levels']:
            lines.append(f'                    {lv!r},')
        lines.append('                ),')
        lines.append('            ),')
    lines.append('        ],')
    lines.append('    ),')
lines.append(']')
lines.append('')
lines.append('DIMENSIONS_BY_CODE: Dict[str, Dimension] = {d.code: d for d in DIMENSIONS}')
lines.append('')
lines.append('ALL_CRITERIA: List[Criterion] = [c for d in DIMENSIONS for c in d.criteria]')
lines.append('')
lines.append('CRITERIA_BY_CODE: Dict[str, Criterion] = {c.code: c for c in ALL_CRITERIA}')
lines.append('')
lines.append('MAX_TOTAL_SCORE: int = sum(d.max_score for d in DIMENSIONS)')
lines.append('')
lines.append('CRITERIA_COUNT: int = len(ALL_CRITERIA)')
lines.append('')
lines.append('WEIGHT_LABELS: Dict[int, str] = {')
lines.append('    1: "Pas important",')
lines.append('    2: "Important",')
lines.append('    3: "Très important",')
lines.append('}')
lines.append('')
lines.append('GRID_SOURCE = "Grille de maturité Data — Limpida Consulting 2024"')
lines.append('')
open('grid_gen.py','w').write('\n'.join(lines) + '\n')
print("written", len('\n'.join(lines).splitlines()), "lines")
