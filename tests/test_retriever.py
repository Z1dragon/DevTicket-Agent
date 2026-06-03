from devticket_agent.retriever import KeywordRetriever


def test_retriever_cache_counts_hits_and_misses():
    retriever = KeywordRetriever()
    query = "DB_CONN_TIMEOUT 怎么排查"

    first = retriever.search(query)
    second = retriever.search(query)

    assert first == second
    assert retriever.cache_misses == 1
    assert retriever.cache_hits == 1
