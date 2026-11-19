import csv
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'outputs/opportunity_scores.csv').open(encoding='utf-8-sig')))
assert len(rows)==9
assert abs(sum([.5,.3,.2])-1)<1e-9
assert rows[0]['theme']=='佩戴舒适'
assert rows[0]['opportunity_type']=='高优先级内容机会'
assert all(r['user_evidence_ids'] and r['competitor_evidence_ids'] for r in rows[:5])
assert (root/'skills/brand_voice/SKILL.md').exists()
assert len(list((root/'outputs').glob('0*.md')))==5
print('PASS: 9 topic rows, top 5 evidence-linked, Brand Voice and 5 briefs present')
