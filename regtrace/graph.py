"""Load devices and predicate links into Neo4j.

Graph shape:
  (:Device {k_number})-[:HAS_PRODUCT_CODE]->(:ProductCode {code})
  (:ProductCode)-[:UNDER_REGULATION]->(:Regulation {number})
  (:Device)-[:CITES_PREDICATE {page}]->(:Device)

Every write uses MERGE, so loading twice does not create duplicates.
"""

DEVICE_Q = """
UNWIND $rows AS r
MERGE (d:Device {k_number: r.k_number})
  SET d.name = r.device_name, d.applicant = r.applicant, d.decision_date = r.decision_date,
      d.device_class = r.device_class
WITH d, r WHERE r.product_code IS NOT NULL
MERGE (p:ProductCode {code: r.product_code})
MERGE (d)-[:HAS_PRODUCT_CODE]->(p)
WITH p, r WHERE r.regulation_number IS NOT NULL
MERGE (g:Regulation {number: r.regulation_number})
MERGE (p)-[:UNDER_REGULATION]->(g)
"""

PREDICATE_Q = """
UNWIND $rows AS r
MERGE (a:Device {k_number: r.k_number})
MERGE (b:Device {k_number: r.predicate_k})
MERGE (a)-[e:CITES_PREDICATE]->(b)
  SET e.page = r.page, e.method = r.method
"""

# Predicate chain: what did this device's predicates cite, up to `depth` hops back.
LINEAGE_Q = """
MATCH path = (d:Device {k_number: $k})-[:CITES_PREDICATE*1..%d]->(p:Device)
RETURN [n IN nodes(path) | n.k_number] AS chain
"""


def load_devices(session, rows: list[dict], batch: int = 500) -> None:
    for i in range(0, len(rows), batch):
        session.run(DEVICE_Q, rows=rows[i:i + batch])


def load_predicates(session, k_number: str, preds: list[dict], method: str) -> None:
    rows = [{"k_number": k_number, "predicate_k": p["k_number"], "page": p["page"], "method": method}
            for p in preds]
    if rows:
        session.run(PREDICATE_Q, rows=rows)


def lineage(session, k_number: str, depth: int = 3) -> list[list[str]]:
    depth = max(1, min(int(depth), 5))  # bounded so a query can't explode
    result = session.run(LINEAGE_Q % depth, k=k_number)
    return [rec["chain"] for rec in result]
