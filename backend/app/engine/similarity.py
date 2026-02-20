import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.engine.normalizer import extract_field_set, normalize_expression, normalize_name

logger = logging.getLogger(__name__)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def name_similarity(name_a: str, name_b: str) -> float:
    """Compute token-based similarity between two report names."""
    tokens_a = set(normalize_name(name_a).split())
    tokens_b = set(normalize_name(name_b).split())
    return jaccard_similarity(tokens_a, tokens_b)


def expression_similarity(expr_a: str | None, expr_b: str | None) -> float:
    """Compute similarity between two DAX/SQL expressions."""
    norm_a = normalize_expression(expr_a)
    norm_b = normalize_expression(expr_b)

    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    # Token-based comparison
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    return jaccard_similarity(tokens_a, tokens_b)


def compute_report_similarity(report_a: dict, report_b: dict) -> float:
    """Compute composite similarity score between two reports.

    Weights:
    - 0.30 structural (field overlap)
    - 0.25 query similarity
    - 0.20 name similarity
    - 0.25 field-level overlap
    """
    fields_a = extract_field_set(report_a)
    fields_b = extract_field_set(report_b)

    structural_sim = jaccard_similarity(fields_a, fields_b)
    name_sim = name_similarity(report_a.get("name", ""), report_b.get("name", ""))

    # Expression similarity from measures
    measures_a = report_a.get("measures", [])
    measures_b = report_b.get("measures", [])
    if measures_a and measures_b:
        expr_sims = []
        for ma in measures_a:
            for mb in measures_b:
                if normalize_name(ma.get("name", "")) == normalize_name(mb.get("name", "")):
                    expr_sims.append(
                        expression_similarity(ma.get("expression"), mb.get("expression"))
                    )
        query_sim = sum(expr_sims) / len(expr_sims) if expr_sims else 0.0
    else:
        query_sim = 0.0

    composite = 0.30 * structural_sim + 0.25 * query_sim + 0.20 * name_sim + 0.25 * structural_sim

    return round(composite, 4)


def build_similarity_matrix(reports: list[dict]) -> np.ndarray:
    """Build an NxN similarity matrix for a list of reports."""
    n = len(reports)
    if n == 0:
        return np.array([])

    matrix = np.eye(n)

    for i in range(n):
        for j in range(i + 1, n):
            sim = compute_report_similarity(reports[i], reports[j])
            matrix[i][j] = sim
            matrix[j][i] = sim

    return matrix


def compute_tfidf_similarity(field_lists: list[list[str]]) -> np.ndarray:
    """Compute TF-IDF cosine similarity across report field lists.

    Each report's field list is joined into a document, then TF-IDF
    vectors are computed and compared.
    """
    if not field_lists:
        return np.array([])

    documents = [" ".join(normalize_name(f) for f in fields) for fields in field_lists]

    # Filter out empty documents
    if all(not doc.strip() for doc in documents):
        return np.eye(len(field_lists))

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    return cosine_similarity(tfidf_matrix)
