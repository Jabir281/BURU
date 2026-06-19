import re
import numpy as np

OTHER_UNIVERSITIES = [
    "harvard", "mit", "stanford", "oxford", "cambridge", "yale",
    "princeton", "columbia", "buet", "du", "cu", "ru", "juniv",
    "north south", "north-south", "northsouth", "australian", "east west",
    "daffodil", "ulab", "uiu", "iub", "independent", "american",
]

def mentions_other_university(query):
    q = query.lower()
    for uni in OTHER_UNIVERSITIES:
        if uni in q and "brac" not in q:
            return True
    return False

def is_relevant_by_similarity(query_embedding, retrieved_embeddings, threshold=0.3):
    if retrieved_embeddings is None or len(retrieved_embeddings) == 0:
        return False
    q_vec = np.array(query_embedding).flatten()
    similarities = []
    for r in retrieved_embeddings:
        r_vec = np.array(r).flatten()
        if np.linalg.norm(q_vec) == 0 or np.linalg.norm(r_vec) == 0:
            continue
        sim = np.dot(q_vec, r_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(r_vec))
        similarities.append(sim)
    if not similarities:
        return False
    return max(similarities) >= threshold

def get_rejection_message(reason="off_topic"):
    messages = {
        "other_university": "I can only help with questions related to BRAC University. You mentioned another institution. Please ask me about BRACU instead!",
        "off_topic": "I can only answer questions about BRAC University \u2014 admissions, academics, scholarships, student life, and more. Ask me something BRACU-related!",
        "no_info": "I don\u2019t have that information in my current knowledge base. Please check the official BRACU website or contact the relevant office directly.",
    }   
    return messages.get(reason, messages["off_topic"])
