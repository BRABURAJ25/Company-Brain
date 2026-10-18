# Submission form answers (copy into the WeMakeDevs page)

- **Project Name:** Company Brain
- **Chosen Track(s):** Track 03: Company Brain
- **Short Description:** A company-wide assistant that answers "who should I assign this bug to?" by searching a FalkorDB graph of employees, commits, bugs and services, and replies with the person and proof of their past work.
- **Tech Stack:** FalkorDB, Cypher, Python, Streamlit, Ollama (local LLM, llama3.2:3b), Docker
- **Key Cypher Queries / Graph Traversal Logic:**
  1. `Employee -[:MADE]-> Commit -[:CHANGED]-> Service` and `Employee -[:FIXED]-> Bug -[:AFFECTED]-> Service`, ranked by score (commits + 3 x bugs fixed), returning commit messages and bug titles as proof.
  2. `Service -[:DEPENDS_ON]-> Service <-[:CHANGED]- Commit <-[:MADE]- Employee` to find people who know the dependencies.
  (Full queries are in README.md)
- **Repository Link:** [PASTE YOUR GITHUB URL]
- **Demo Video Link:** [PASTE YOUR YOUTUBE / LOOM LINK]
- **Live Demo Link (or Docker run command):** `docker compose up -d && pip install -r requirements.txt && python seed.py && streamlit run app.py`
- **AI Tools Used:** Claude (Anthropic) for writing code and README

---

# Demo video checklist (about 3 minutes)

1. (20 sec) The problem: nobody knows who worked on what.
2. (40 sec) Open http://localhost:3000, pick `company_brain`, run
   `MATCH (n) OPTIONAL MATCH (n)-[e]-(m) RETURN * LIMIT 200`. Explain the nodes and relationships.
3. (60 sec) Open the Streamlit page. Ask: "There is an issue in the production order API. Who should I assign it to?" Show the answer, the proof, and the table.
4. (30 sec) Click "Show the Cypher queries that ran". Say: this is FalkorDB doing the work.
5. (20 sec) Ask a second question (Payment API) to show it is not hard-coded.
6. (10 sec) Say: without the graph, the agent has no proof and no answer.
