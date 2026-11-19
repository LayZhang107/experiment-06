"""实验六：Content Gap 与 Brand Voice 内容机会引擎 v0.6
输入实验四、实验五的聚合成果，输出可复算的需求-竞品矩阵、机会评分和证据关联。
"""
from __future__ import annotations
import csv, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "data" / "inputs"
OUT = ROOT / "outputs"


def read_csv(name):
    with (IN / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, fields):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def build():
    pain = read_csv("pain_point_statistics.csv")
    coverage = read_csv("brand_topic_coverage.csv")
    user_ev = read_csv("consumer_evidence_table.csv")
    comp_ev = read_csv("competitive_evidence_table.csv")
    by_topic = defaultdict(list)
    for row in coverage:
        by_topic[row["topic"]].append(row)
    user_evidence = defaultdict(list)
    for row in user_ev:
        user_evidence[row["topic"]].append(row)
    comp_evidence = defaultdict(list)
    for row in comp_ev:
        text = (row.get("conclusion", "") + " " + row.get("review_text", ""))
        for topic in by_topic:
            if topic in text:
                comp_evidence[topic].append(row)
    max_importance = max(float(r["negative_rate"]) for r in pain)
    max_ev = max(len(v) for v in user_evidence.values()) or 1
    matrix, scores = [], []
    for r in pain:
        topic = r["topic"]
        cov_rows = by_topic[topic]
        avg_cov = sum(float(x["coverage_rate"]) for x in cov_rows) / len(cov_rows)
        importance = float(r["negative_rate"])
        importance_norm = importance / max_importance if max_importance else 0
        gap = 1 - avg_cov
        ev_strength = min(1.0, len(user_evidence[topic]) / max_ev)
        score = 100 * (0.50 * importance_norm + 0.30 * gap + 0.20 * ev_strength)
        if importance_norm < 0.25:
            kind = "伪机会：用户关注度不足"
        elif gap >= 0.80 and importance_norm >= 0.50:
            kind = "高优先级内容机会"
        elif gap >= 0.70:
            kind = "候选内容机会"
        else:
            kind = "竞争充分或优先级一般"
        ue = user_evidence[topic][:3]
        ce = comp_evidence[topic][:3]
        coverage_evidence_ids = [f"coverage:{x['brand']}:{topic}" for x in cov_rows[:4]]
        matrix.append({
            "theme": topic,
            "user_importance": f"{importance:.4f}",
            "user_importance_pct": f"{importance*100:.1f}%",
            "competitor_avg_coverage": f"{avg_cov:.4f}",
            "content_gap": f"{gap:.4f}",
            "evidence_strength": f"{ev_strength:.4f}",
            "opportunity_score": f"{score:.2f}",
            "opportunity_type": kind,
            "user_evidence_ids": ";".join(x.get("review_id", "") for x in ue),
            "competitor_evidence_ids": ";".join(coverage_evidence_ids),
        })
        scores.append((score, topic, kind))
    matrix.sort(key=lambda x: float(x["opportunity_score"]), reverse=True)
    write_csv("need_content_matrix.csv", matrix, list(matrix[0]))
    write_csv("opportunity_scores.csv", matrix, list(matrix[0]))
    evidence_rows=[]
    for row in matrix:
        for x in user_evidence[row["theme"]][:3]:
            evidence_rows.append({"theme":row["theme"],"evidence_type":"用户证据","evidence_id":x.get("review_id",""),"brand":x.get("brand",""),"evidence":x.get("evidence", ""),"review_text":x.get("review_text", ""),"source":"实验四 consumer_evidence_table.csv"})
        for x in by_topic[row["theme"]]:
            evidence_rows.append({"theme":row["theme"],"evidence_type":"竞品覆盖证据","evidence_id":f"coverage:{x['brand']}:{row['theme']}","brand":x.get("brand",""),"evidence":f"主题提及数={x.get('topic_mentions','')}; 覆盖率={x.get('coverage_rate','')}","review_text":"","source":"实验五 brand_topic_coverage.csv"})
        for x in comp_evidence[row["theme"]][:3]:
            evidence_rows.append({"theme":row["theme"],"evidence_type":"竞品评论证据","evidence_id":x.get("review_id",""),"brand":x.get("brand",""),"evidence":x.get("conclusion", ""),"review_text":x.get("review_text", ""),"source":"实验五 competitive_evidence_table.csv"})
    write_csv("evidence_records.csv", evidence_rows, ["theme","evidence_type","evidence_id","brand","evidence","review_text","source"])
    # JSON for downstream workflow
    brief_candidates=[x for x in matrix if x["opportunity_type"] in ("高优先级内容机会","候选内容机会")][:5]
    (OUT/"opportunity_summary.json").write_text(json.dumps({"version":"v0.6","formula":"score=100*(0.50*importance_norm+0.30*content_gap+0.20*evidence_strength)","candidates":brief_candidates},ensure_ascii=False,indent=2),encoding="utf-8")
    return matrix

if __name__ == "__main__":
    rows=build(); print(f"generated {len(rows)} topic rows and {sum(1 for r in rows if '机会' in r['opportunity_type'])} opportunity rows")
