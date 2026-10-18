import streamlit as st
from brain import answer_question, llm_available, LLMError
from config import GRAPH_NAME, OLLAMA_MODEL

st.set_page_config(page_title="Company Brain", page_icon="🧠")
st.title("🧠 Company Brain")
st.caption("Ask who should own a bug. The answer comes from a FalkorDB graph, with proof.")

with st.sidebar:
    st.subheader("Status")
    st.write(f"Graph: `{GRAPH_NAME}`")
    st.write(f"LLM: on (`{OLLAMA_MODEL}`)" if llm_available() else "LLM: off")
    st.subheader("Try these")
    examples = [
        "There is an issue in the production order API. Who should I assign it to?",
        "Payment is timing out for UPI users, who knows this?",
        "Stock count is going negative, who should fix it?",
        "SMS are not going out, who owns this?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["q"] = ex

question = st.text_input("Your question", key="q", placeholder="e.g. Issue in the production order API, who should I assign it to?")

if st.button("Ask", type="primary") and question.strip():
    try:
        with st.spinner("Searching the graph..."):
            res = answer_question(question.strip())
    except LLMError as ex:
        st.error(str(ex))
        st.stop()
    except Exception as ex:
        st.error(f"Could not reach FalkorDB. Is Docker running? ({ex})")
        st.stop()

    st.subheader("Answer")
    st.markdown(res["answer"])

    st.divider()
    st.subheader("How the brain got this")
    st.write(f"**Step 1:** the LLM picked the service: `{res['service']}`")

    if res["experts"]:
        st.write("**Step 2:** FalkorDB ranked the people (score = commits + 3 x bugs fixed)")
        st.table([
            {"Person": e["name"], "Role": e["role"], "Commits": e["commit_count"],
             "Bugs fixed": e["bug_count"], "Score": e["score"]}
            for e in res["experts"]
        ])
    if res["deps"]:
        st.write("**Extra (graph walk):** people who know services this one depends on")
        st.table(res["deps"])

    with st.expander("Show the Cypher queries that ran"):
        st.code(res["queries"]["experts"], language="cypher")
        st.code(res["queries"]["dependencies"], language="cypher")