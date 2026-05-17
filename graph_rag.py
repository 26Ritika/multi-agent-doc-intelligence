import networkx as nx
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key="YOUR_GEMINI_API_KEY"
)

# Global graph
doc_graph = nx.Graph()

def build_graph(text, chunks):
    global doc_graph
    doc_graph = nx.Graph()

    # Add chunks as nodes
    for i, chunk in enumerate(chunks):
        doc_graph.add_node(i, text=chunk)

    # Add edges between related chunks
    for i in range(len(chunks)):
        for j in range(i+1, len(chunks)):
            # Find common words between chunks
            words_i = set(chunks[i].lower().split())
            words_j = set(chunks[j].lower().split())
            common = words_i.intersection(words_j)

            # Remove common stop words
            stopwords = {"the","a","an","is","in","of","to","and","or","that","this","it","was","for","on","are","with","as","at","be","by","from","has","have","he","she","they","we","you","i","not","but","what","all","were","when","there","can","an"}
            common = common - stopwords

            # If enough common words → add connection
            if len(common) > 3:
                doc_graph.add_edge(i, j, weight=len(common))

    return doc_graph

def graph_search(question, chunks, n_results=3):
    if not doc_graph.nodes:
        return ""

    # Find most relevant chunk using keywords
    question_words = set(question.lower().split())
    scores = []

    for i, chunk in enumerate(chunks):
        chunk_words = set(chunk.lower().split())
        score = len(question_words.intersection(chunk_words))
        scores.append((score, i))

    scores.sort(reverse=True)

    if not scores or scores[0][0] == 0:
        return " ".join(chunks[:n_results])

    # Get best matching chunk
    best_node = scores[0][1]

    # Get connected chunks from graph
    connected = list(doc_graph.neighbors(best_node))
    connected = sorted(
        connected,
        key=lambda x: doc_graph[best_node][x].get('weight', 0),
        reverse=True
    )

    # Combine best chunk + connected chunks
    result_chunks = [chunks[best_node]]
    for node in connected[:n_results-1]:
        if node < len(chunks):
            result_chunks.append(chunks[node])

    return " ".join(result_chunks)