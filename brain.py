import requests
from falkordb import FalkorDB
from config import FALKOR_HOST, FALKOR_PORT, GRAPH_NAME, OLLAMA_URL, OLLAMA_MODEL


class LLMError(Exception):
    pass


Q_SERVICES = "MATCH (s:Service) RETURN s.name, s.description ORDER BY s.name"

# score = commits + 3 x bugs fixed
Q_EXPERTS = """
MATCH (s:Service {name: $service})
MATCH (e:Employee)
OPTIONAL MATCH (e)-[:MADE]->(c:Commit)-[:CHANGED]->(s)
WITH s, e, collect(DISTINCT c.message + ' (' + c.date + ')') AS commits
OPTIONAL MATCH (e)-[:FIXED]->(b:Bug)-[:AFFECTED]->(s)
WITH e, commits, collect(DISTINCT b.title + ' (' + b.date + ')') AS bugs
WHERE size(commits) + size(bugs) > 0
RETURN e.name AS name,
       e.role AS role,
       size(commits) AS commit_count,
       size(bugs) AS bug_count,
       size(commits) + 3 * size(bugs) AS score,
       commits,
       bugs
ORDER BY score DESC
LIMIT 3
"""

# people who work on the services this service depends on
Q_DEPENDENCY_EXPERTS = """
MATCH (s:Service {name: $service})-[:DEPENDS_ON]->(d:Service)
MATCH (e:Employee)-[:MADE]->(c:Commit)-[:CHANGED]->(d)
RETURN e.name AS name, d.name AS dependency, count(c) AS commits
ORDER BY commits DESC
LIMIT 3
"""


def get_graph():
    return FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT).select_graph(GRAPH_NAME)


def llm_available() -> bool:
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


def ask_llm(system: str, user: str) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=180,
        )
    except requests.exceptions.RequestException:
        raise LLMError("Cannot reach Ollama. Start Ollama and try again.")
    if r.status_code == 404:
        raise LLMError(f"Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
    if r.status_code != 200:
        raise LLMError(f"Ollama error {r.status_code}: {r.text[:200]}")
    return r.json()["message"]["content"].strip()


def pick_service(question, services):
    system = (
        "You match a user question to ONE service name. "
        "Reply with the exact service name from the list, and nothing else. "
        "If none match, reply NONE."
    )
    user = "Services:\n" + "\n".join(f"- {n}: {d}" for n, d in services) + f"\n\nQuestion: {question}"
    answer = ask_llm(system, user).strip().strip("\"'").rstrip(".")

    names = [n for n, _ in services]
    for n in names:
        if n.lower() == answer.lower():
            return n
    found = [n for n in names if n.lower() in answer.lower()]
    return found[0] if len(found) == 1 else None


def write_answer(question, service, experts, deps):
    system = (
        "You are a company brain assistant. Decide who should get a bug. "
        "Use ONLY the facts given. Do not invent names, commits or dates. "
        "Answer in simple English, short. First line: who to assign and why. "
        "Then a 'Proof:' list using the commits and bugs from the facts. "
        "Then one line with a backup person if there is one."
    )
    facts = [f"Service: {service}"]
    for e in experts:
        facts.append(
            f"Person: {e['name']} ({e['role']}), score {e['score']}, "
            f"{e['commit_count']} commits, {e['bug_count']} bugs fixed"
        )
        facts += [f"  commit: {c}" for c in e["commits"]]
        facts += [f"  bug fixed: {b}" for b in e["bugs"]]
    if deps:
        facts.append("People who know the services this one depends on: " + ", ".join(
            f"{d['name']} ({d['dependency']}, {d['commits']} commits)" for d in deps))
    return ask_llm(system, f"Question: {question}\n\nFacts from the graph:\n" + "\n".join(facts))


def answer_question(question: str) -> dict:
    g = get_graph()
    services = [(r[0], r[1]) for r in g.query(Q_SERVICES).result_set]

    result = {
        "question": question,
        "service": None,
        "experts": [],
        "deps": [],
        "answer": "",
        "queries": {"experts": Q_EXPERTS.strip(), "dependencies": Q_DEPENDENCY_EXPERTS.strip()},
    }

    service = pick_service(question, services)
    result["service"] = service
    if not service:
        result["answer"] = "I could not find which service this is about. Try naming it, for example: Order API."
        return result

    rows = g.query(Q_EXPERTS, {"service": service}).result_set
    result["experts"] = [
        {"name": r[0], "role": r[1], "commit_count": r[2], "bug_count": r[3],
         "score": r[4], "commits": r[5], "bugs": r[6]}
        for r in rows
    ]
    result["deps"] = [
        {"name": r[0], "dependency": r[1], "commits": r[2]}
        for r in g.query(Q_DEPENDENCY_EXPERTS, {"service": service}).result_set
    ]

    if not result["experts"]:
        result["answer"] = f"No one has recorded work on {service}."
        return result

    result["answer"] = write_answer(question, service, result["experts"], result["deps"])
    return result


if __name__ == "__main__":
    out = answer_question("There is an issue in the production order API. Who should I assign?")
    print("Service:", out["service"])
    print(out["answer"])