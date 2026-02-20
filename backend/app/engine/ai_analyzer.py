import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI-powered semantic analysis using Claude API.

    Provides semantic similarity assessment, KPI conflict resolution
    recommendations, and report classification.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        if not self._client:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def assess_semantic_similarity(
        self, measure_a: dict, measure_b: dict
    ) -> dict[str, Any]:
        """Assess whether two measures compute the same business concept.

        Returns a dict with:
        - is_semantically_equivalent: bool
        - confidence: float (0-1)
        - explanation: str
        """
        client = await self._get_client()

        prompt = f"""Analyze whether these two BI measure definitions compute the same business concept.

Measure A:
- Name: {measure_a.get('name', '')}
- Expression: {measure_a.get('expression', 'N/A')}
- Description: {measure_a.get('description', 'N/A')}
- Source: {measure_a.get('source', 'N/A')}

Measure B:
- Name: {measure_b.get('name', '')}
- Expression: {measure_b.get('expression', 'N/A')}
- Description: {measure_b.get('description', 'N/A')}
- Source: {measure_b.get('source', 'N/A')}

Respond in JSON format:
{{
  "is_semantically_equivalent": true/false,
  "confidence": 0.0 to 1.0,
  "explanation": "brief explanation"
}}"""

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI semantic similarity failed: {e}")
            return {
                "is_semantically_equivalent": False,
                "confidence": 0.0,
                "explanation": f"Analysis failed: {e}",
            }

    async def recommend_canonical_kpi(
        self, conflicting_definitions: list[dict]
    ) -> dict[str, Any]:
        """Recommend which KPI definition should be canonical.

        Returns a dict with:
        - recommended_index: int (index into conflicting_definitions)
        - recommendation: str
        - rationale: str
        """
        client = await self._get_client()

        defs_text = "\n".join(
            f"Definition {i+1}:\n"
            f"  Expression: {d.get('expression', 'N/A')}\n"
            f"  Used by {d.get('count', 0)} source(s)\n"
            f"  Sources: {json.dumps(d.get('sources', []))}"
            for i, d in enumerate(conflicting_definitions)
        )

        prompt = f"""These are conflicting KPI definitions for the same measure name in an enterprise BI environment.
Recommend which definition should become the canonical (standard) one.

{defs_text}

Consider:
- Business correctness and completeness
- Wider adoption / more usage
- Clearer expression logic
- Better data governance practices

Respond in JSON format:
{{
  "recommended_index": <1-based index>,
  "recommendation": "Use definition X because...",
  "rationale": "detailed rationale"
}}"""

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI KPI recommendation failed: {e}")
            # Fallback: recommend the most-used definition
            max_count = 0
            best_idx = 1
            for i, d in enumerate(conflicting_definitions):
                if d.get("count", 0) > max_count:
                    max_count = d.get("count", 0)
                    best_idx = i + 1
            return {
                "recommended_index": best_idx,
                "recommendation": f"Using definition {best_idx} (most widely used)",
                "rationale": "AI analysis unavailable; defaulting to most-used definition.",
            }

    async def classify_report_purpose(self, report: dict) -> dict[str, Any]:
        """Classify a report's business purpose/function.

        Returns a dict with:
        - category: str (e.g., "Financial", "Operations", "HR", "Sales")
        - subcategory: str
        - confidence: float
        """
        client = await self._get_client()

        prompt = f"""Classify this BI report by its business purpose based on its metadata.

Report Name: {report.get('name', '')}
Path: {report.get('path', '')}
Type: {report.get('report_type', '')}
Fields Used: {json.dumps(report.get('fields_used', [])[:50])}

Respond in JSON format:
{{
  "category": "one of: Financial, Operations, HR, Sales, Marketing, IT, Executive, Compliance, Other",
  "subcategory": "more specific classification",
  "confidence": 0.0 to 1.0
}}"""

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI report classification failed: {e}")
            return {
                "category": "Other",
                "subcategory": "Unclassified",
                "confidence": 0.0,
            }

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
