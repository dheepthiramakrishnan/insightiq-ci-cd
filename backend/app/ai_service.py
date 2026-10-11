import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

_FALLBACK_INSIGHTS = {
    "executive_summary": (
        "AI insights are unavailable right now. Configure GROQ_API_KEY "
        "in your .env file to enable AI-generated business insights."
    ),
    "key_trends": [],
    "best_performing_products": [],
    "weak_performing_regions": [],
    "recommendations": [],
}

def _build_insights_prompt(kpi_data: dict, chart_data: dict) -> str:
    return f"""
You are a business intelligence analyst. Based on the sales data summary
below, generate concise, actionable business insights.

KPI SUMMARY:
{json.dumps(kpi_data, indent=2)}

CHART DATA SUMMARY:
{json.dumps(chart_data, indent=2, default=str)}

Respond ONLY with a valid JSON object (no markdown, no extra text) using
exactly this structure:
{{
  "executive_summary": "2-3 sentence overview of overall business performance",
  "key_trends": ["trend 1", "trend 2", "trend 3"],
  "best_performing_products": ["product or category insight 1", "insight 2"],
  "weak_performing_regions": ["region or category insight 1", "insight 2"],
  "recommendations": ["actionable recommendation 1", "recommendation 2", "recommendation 3"]
}}
"""

def generate_business_insights(kpi_data: dict, chart_data: dict) -> dict:
    if not _client:
        return _FALLBACK_INSIGHTS

    try:
        prompt = _build_insights_prompt(kpi_data, chart_data)
        response = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw_text = response.choices[0].message.content.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json\n"):
                raw_text = raw_text[5:]

        parsed = json.loads(raw_text)
        return {key: parsed.get(key, _FALLBACK_INSIGHTS[key]) for key in _FALLBACK_INSIGHTS}

    except Exception as e:
        fallback = dict(_FALLBACK_INSIGHTS)
        fallback["executive_summary"] = f"AI insight generation failed: {str(e)}"
        return fallback