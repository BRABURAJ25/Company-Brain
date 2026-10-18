"""Loads fake company data into FalkorDB.

Safe to run many times: it deletes the old graph first, so no duplicates.
Run:  python seed.py
"""
from falkordb import FalkorDB
from config import FALKOR_HOST, FALKOR_PORT, GRAPH_NAME

# ---------------------------------------------------------------- data
EMPLOYEES = [
    # name, role
    ("Prabhu", "Backend Developer"),
    ("Ganesh", "Backend Developer"),
    ("Hari", "Senior Backend Developer"),
    ("Divya", "Full Stack Developer"),
    ("Karthik", "DevOps Engineer"),
    ("Meena", "QA Engineer"),
]

SERVICES = [
    # name, aliases (words people use for it), description
    ("Order API", "production order api,orders,order service,checkout order", "Creates and tracks customer orders"),
    ("Payment API", "payments,payment gateway,billing", "Handles card and UPI payments"),
    ("Inventory Service", "stock,inventory,warehouse", "Keeps product stock counts"),
    ("Auth Service", "login,authentication,auth,token", "Login and tokens"),
    ("Notification Service", "email,sms,notifications", "Sends email and SMS"),
]

# Order API depends on these (Order API -> Payment API means Order API calls Payment API)
DEPENDS_ON = [
    ("Order API", "Payment API"),
    ("Order API", "Inventory Service"),
    ("Order API", "Auth Service"),
    ("Notification Service", "Order API"),
]

COMMITS = [
    # id, employee, service, message, date
    ("c1", "Prabhu", "Order API", "Add order creation endpoint", "2026-06-02"),
    ("c2", "Prabhu", "Order API", "Fix duplicate order on retry", "2026-06-19"),
    ("c3", "Prabhu", "Order API", "Add idempotency key to POST /orders", "2026-07-08"),
    ("c4", "Prabhu", "Order API", "Optimise order list query (added index)", "2026-08-14"),
    ("c5", "Ganesh", "Order API", "Update order status enum", "2026-07-01"),
    ("c6", "Hari", "Order API", "Refactor order controller", "2026-05-11"),
    ("c7", "Hari", "Payment API", "Add UPI payment support", "2026-06-25"),
    ("c8", "Hari", "Payment API", "Fix payment timeout handling", "2026-08-03"),
    ("c9", "Hari", "Payment API", "Add refund endpoint", "2026-09-02"),
    ("c10", "Ganesh", "Inventory Service", "Reduce stock after order confirm", "2026-07-15"),
    ("c11", "Ganesh", "Inventory Service", "Fix negative stock bug", "2026-08-20"),
    ("c12", "Divya", "Notification Service", "Add order confirmation email", "2026-07-22"),
    ("c13", "Divya", "Notification Service", "Add SMS retry logic", "2026-09-10"),
    ("c14", "Karthik", "Auth Service", "Rotate JWT signing keys", "2026-08-05"),
    ("c15", "Karthik", "Auth Service", "Add token refresh endpoint", "2026-09-18"),
    ("c16", "Karthik", "Order API", "Add health check for Order API", "2026-09-25"),
    ("c17", "Meena", "Order API", "Add integration tests for order flow", "2026-09-01"),
]

BUGS = [
    # id, title, service, fixed_by, date
    ("b1", "Order API returns 500 when cart is empty", "Order API", "Prabhu", "2026-07-12"),
    ("b2", "Order total wrong when coupon applied", "Order API", "Prabhu", "2026-08-30"),
    ("b3", "Orders stuck in PENDING after payment success", "Order API", "Ganesh", "2026-09-07"),
    ("b4", "Payment double charge on timeout", "Payment API", "Hari", "2026-08-08"),
    ("b5", "Stock goes negative on parallel orders", "Inventory Service", "Ganesh", "2026-08-21"),
    ("b6", "SMS not sent after retry", "Notification Service", "Divya", "2026-09-12"),
    ("b7", "Token expires too early", "Auth Service", "Karthik", "2026-09-19"),
]


def main():
    db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)

    # start clean so running twice never makes duplicates
    try:
        db.select_graph(GRAPH_NAME).delete()
    except Exception:
        pass  # graph did not exist yet
    g = db.select_graph(GRAPH_NAME)

    # indexes = faster lookup by name (like MySQL indexes)
    for q in (
        "CREATE INDEX FOR (e:Employee) ON (e.name)",
        "CREATE INDEX FOR (s:Service) ON (s.name)",
    ):
        try:
            g.query(q)
        except Exception as ex:
            print("index skipped:", ex)

    for name, role in EMPLOYEES:
        g.query("CREATE (:Employee {name: $name, role: $role})", {"name": name, "role": role})

    for name, aliases, desc in SERVICES:
        g.query(
            "CREATE (:Service {name: $name, aliases: $aliases, description: $desc})",
            {"name": name, "aliases": aliases, "desc": desc},
        )

    for a, b in DEPENDS_ON:
        g.query(
            "MATCH (a:Service {name: $a}), (b:Service {name: $b}) CREATE (a)-[:DEPENDS_ON]->(b)",
            {"a": a, "b": b},
        )

    for cid, emp, svc, msg, date in COMMITS:
        g.query(
            """
            MATCH (e:Employee {name: $emp}), (s:Service {name: $svc})
            CREATE (e)-[:MADE]->(:Commit {id: $cid, message: $msg, date: $date})-[:CHANGED]->(s)
            """,
            {"emp": emp, "svc": svc, "cid": cid, "msg": msg, "date": date},
        )

    for bid, title, svc, emp, date in BUGS:
        g.query(
            """
            MATCH (e:Employee {name: $emp}), (s:Service {name: $svc})
            CREATE (e)-[:FIXED]->(:Bug {id: $bid, title: $title, date: $date})-[:AFFECTED]->(s)
            """,
            {"emp": emp, "svc": svc, "bid": bid, "title": title, "date": date},
        )

    nodes = g.query("MATCH (n) RETURN count(n)").result_set[0][0]
    rels = g.query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]
    print(f"Done. Graph '{GRAPH_NAME}' has {nodes} nodes and {rels} relationships.")
    print("Open http://localhost:3000 , pick graph", GRAPH_NAME, "and run:")
    print("  MATCH (n) OPTIONAL MATCH (n)-[e]-(m) RETURN * LIMIT 200")


if __name__ == "__main__":
    main()
