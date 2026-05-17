import time
from datetime import datetime

metrics_store = {
    "total_documents": 0,
    "total_questions": 0,
    "total_processing_time": [],
    "agent_times": {
        "orchestrator": [],
        "summarizer": [],
        "analyzer": [],
        "qa": [],
        "evaluator": [],
        "aggregator": []
    },
    "retry_counts": [],
    "languages_detected": {},
    "documents_processed": []
}

def record_document(filename, pages, word_count, processing_time):
    metrics_store["total_documents"] += 1
    metrics_store["total_processing_time"].append(processing_time)
    metrics_store["documents_processed"].append({
        "filename": filename,
        "pages": pages,
        "word_count": word_count,
        "processing_time": round(processing_time, 2),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

def record_question(language, retry_count):
    metrics_store["total_questions"] += 1
    metrics_store["retry_counts"].append(retry_count)
    lang = metrics_store["languages_detected"]
    lang[language] = lang.get(language, 0) + 1

def get_metrics():
    times = metrics_store["total_processing_time"]
    retries = metrics_store["retry_counts"]
    return {
        "total_documents": metrics_store["total_documents"],
        "total_questions": metrics_store["total_questions"],
        "avg_processing_time": round(sum(times)/len(times), 2) if times else 0,
        "min_processing_time": round(min(times), 2) if times else 0,
        "max_processing_time": round(max(times), 2) if times else 0,
        "avg_retries": round(sum(retries)/len(retries), 2) if retries else 0,
        "languages_detected": metrics_store["languages_detected"],
        "recent_documents": metrics_store["documents_processed"][-5:]
    }