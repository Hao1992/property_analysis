"""AI narrative generator.

Two backends, selected by environment:
  - Anthropic API (default, required for server deployment):
      ANTHROPIC_API_KEY must be set.
      Uses claude-sonnet-4-6 with prompt caching on the system prompts.
  - Claude CLI subprocess (local dev fallback):
      Set USE_CLAUDE_CLI=true to use `claude -p` from PATH instead.
      Useful when running locally with a Claude Code subscription and no API key.
"""
import json
import os
import re
import subprocess

import anthropic

_BUYER_PROFILE_CONTEXT = {
    "en": {
        "balanced":  "a balanced buyer weighing all factors equally",
        "family":    "a family with children — school quality and safety are the top priorities",
        "investor":  "a property investor focused on rental yield and capital appreciation",
        "retiree":   "a retiree prioritising quiet streets, accessibility, and proximity to medical care",
        "expat":     "an international buyer unfamiliar with Spanish property quirks, legal requirements, and hidden costs",
    },
    "zh": {
        "balanced":  "综合考量各方面因素的购房者",
        "family":    "有孩子的家庭——学校质量和治安安全是首要考量",
        "investor":  "关注租金回报和资本增值的房产投资者",
        "retiree":   "注重安静街区、无障碍设施和医疗配套的退休养老型购房者",
        "expat":     "对西班牙房产规则、法律要求和隐性成本不熟悉的外籍国际买家",
    },
}

_LANGUAGE_INSTRUCTIONS = {
    "en": "Write in English.",
    "zh": (
        "请用简体中文写作。所有输出必须是中文，包括 verdict、summary、key_risks、"
        "key_positives 和 negotiation_angle。verdict 为10-15个汉字的简短结论。"
        "negotiation_angle 是买家可以直接对卖家说的一句具体议价话术。"
    ),
}

_SYSTEM = """You are a transparent property buying advisor in Spain.
You receive structured analysis data about a property and produce a plain-language verdict that a buyer can read in 60 seconds.

Rules:
- Write as a knowledgeable friend, not an estate agent. Be direct.
- Be specific: cite actual numbers from the data (scores, distances, percentages).
- If something is a serious red flag, say so clearly — do not soften it.
- key_risks must be actionable ("Request ITE report before signing arras", not just "building is old").
- negotiation_angle must be one concrete sentence the buyer can say to the seller.
- Output strict JSON only, no code fences, no preamble.

CRITICAL rules about missing data:
- If year_built, surface_m2, energy_cert, or ITE status is null/missing, this means the data was NOT FOUND in the public cadastral registry. It does NOT mean the property is bad or undocumented. Tell the buyer to REQUEST these documents from the seller — do not treat absence as a red flag or include it in key_risks unless combined with other actual risk signals.
- Noise scores already account for floor level. Do not re-penalise noise if the floor boost is high (>20).
- Bars and restaurants near the property are ALSO convenience assets — do not list them as risks unless they are nightclubs causing genuine late-night issues.
- Only include in key_risks things that are CONFIRMED problems, not absences of data.

Output schema:
{
  "verdict": "<10-15 word headline verdict>",
  "summary": "<3-5 sentence plain language overview>",
  "key_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "key_positives": ["<positive 1>", "<positive 2>", "<positive 3>"],
  "negotiation_angle": "<one concrete actionable sentence>"
}"""

_SYSTEM_COMPARE = """You are a transparent property buying advisor in Spain.
You receive side-by-side data for 2 or 3 properties and produce a concise comparison that tells the buyer which one is better for their profile and why.

Rules:
- Be direct. Give a clear recommendation.
- Reference specific scores and numbers.
- winner_by_dimension keys: "value", "safety", "liveability", "hidden_costs", "airbnb_risk".
  Values are the short address label (e.g. "Property A").
- Output strict JSON only, no code fences, no preamble.

Output schema:
{
  "recommendation": "<one sentence: which property and the single most important reason>",
  "summary": "<3-4 sentences comparing the properties on the dimensions that matter for this buyer>",
  "winner_by_dimension": {
    "value": "<Property A|B|C>",
    "safety": "<Property A|B|C>",
    "liveability": "<Property A|B|C>",
    "hidden_costs": "<Property A|B|C>",
    "airbnb_risk": "<Property A|B|C>"
  }
}"""

# Lazy singleton — initialised on first use so missing API keys don't crash import
_anthropic_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
    return _anthropic_client


# ── Backend: Anthropic API ────────────────────────────────────────────────────

def _call_anthropic(system: str, user: str, max_tokens: int = 1500) -> dict:
    client = _get_client()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        # Prompt caching on the system prompt: static per call type so it can be
        # cached across requests. Minimum threshold is ~2048 tokens for Sonnet 4.6;
        # silently skipped if the prefix is shorter.
        system=[{
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(raw)


# ── Backend: Claude CLI subprocess (local dev only) ───────────────────────────

def _call_cli(system: str, user: str, max_tokens: int = 1500) -> dict:
    combined = (
        f"<system>\n{system}\n</system>\n\n"
        f"<user>\n{user}\n</user>\n\n"
        "Respond with JSON only."
    )
    proc = subprocess.run(
        ["claude", "-p", "--output-format", "json",
         "--model", "sonnet", "--fallback-model", "haiku"],
        input=combined, capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr[:200]}")
    wrapper = json.loads(proc.stdout)
    raw = wrapper.get("result", "") or proc.stdout
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(raw)


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _call_claude(system: str, user: str, max_tokens: int = 1500) -> dict:
    try:
        if os.environ.get("USE_CLAUDE_CLI"):
            return _call_cli(system, user, max_tokens)
        return _call_anthropic(system, user, max_tokens)
    except Exception as e:
        return {"_error": str(e)}


# ── Context builders ──────────────────────────────────────────────────────────

def _build_analysis_context(data: dict) -> str:
    score = data.get("score", {})
    valuation = data.get("valuation", {})
    prop = data.get("property", {})
    safety = data.get("safety", {})
    airbnb = data.get("airbnb_saturation", {})
    school = data.get("school_quality", {})
    noise = data.get("noise", {})
    trajectory = data.get("neighbourhood_trajectory", {})
    hidden = data.get("hidden_costs", {})

    ctx = {
        "composite_score": score.get("composite"),
        "grade": score.get("grade"),
        "dimensions": {d["name"]: d["score"] for d in score.get("dimensions", [])},
        "valuation": {
            "fair_value": valuation.get("fair_value"),
            "listing_vs_fair_pct": valuation.get("vs_listing_pct"),
            "verdict": valuation.get("verdict"),
            "confidence": valuation.get("confidence"),
        },
        "property": {
            "year_built": prop.get("year_built"),
            "surface_m2": prop.get("surface_m2"),
            "energy_cert": prop.get("energy_cert"),
            "ite_status": prop.get("ite_status"),
            "floor": prop.get("floor"),
        },
        "safety": {
            "district": safety.get("district"),
            "theft_index": safety.get("theft_rate_index"),
            "night_safety": safety.get("night_safety_index"),
        },
        "airbnb": {
            "risk": airbnb.get("risk_label"),
            "tourist_pct_building": airbnb.get("tourist_pct_building"),
            "count_500m": airbnb.get("tourist_count_500m"),
        },
        "school": {
            "nearest_m": school.get("nearest_school_m"),
            "type": school.get("school_type"),
            "language": school.get("language"),
            "score": school.get("composite_score"),
        },
        "noise": {
            "day_score": noise.get("day_noise_score"),
            "night_score": noise.get("night_noise_score"),
            "bars_500m": noise.get("bars_clubs_500m"),
        },
        "neighbourhood_trajectory": {
            "trend": trajectory.get("trend"),
            "new_businesses_12m": trajectory.get("new_businesses_12m"),
        },
        "hidden_costs": {
            "total_monthly_eur": hidden.get("total_monthly_eur"),
            "derrama_risk": hidden.get("derrama_risk_label"),
            "energy_upgrade_required": hidden.get("energy_upgrade_required"),
            "energy_upgrade_est_eur": hidden.get("energy_upgrade_estimate_eur"),
        },
    }
    return json.dumps(ctx, ensure_ascii=False, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_narrative(
    analysis_data: dict,
    buyer_profile: str = "balanced",
    language: str = "en",
) -> dict:
    lang = language if language in ("en", "zh") else "en"
    profiles = _BUYER_PROFILE_CONTEXT.get(lang, _BUYER_PROFILE_CONTEXT["en"])
    profile_ctx = profiles.get(buyer_profile, profiles["balanced"])
    lang_instruction = _LANGUAGE_INSTRUCTIONS.get(lang, _LANGUAGE_INSTRUCTIONS["en"])

    user = (
        f"Buyer profile: {profile_ctx}\n\n"
        f"Property: {analysis_data.get('address', 'Unknown')}\n\n"
        f"Analysis data:\n{_build_analysis_context(analysis_data)}\n\n"
        f"{lang_instruction}\n\n"
        "Generate the plain-language verdict JSON."
    )

    result = _call_claude(_SYSTEM, user, max_tokens=1500)

    if "_error" in result:
        if lang == "zh":
            return {
                "verdict": "分析完成——AI叙述暂不可用",
                "summary": "所有数据已成功收集，AI叙述生成失败：" + result["_error"],
                "key_risks": [],
                "key_positives": [],
                "negotiation_angle": "请参考上方各项评分进行议价。",
                "generated_by": "error-fallback",
            }
        return {
            "verdict": "Analysis complete — narrative unavailable",
            "summary": "All data was collected successfully. AI narrative generation failed: " + result["_error"],
            "key_risks": [],
            "key_positives": [],
            "negotiation_angle": "Review the scores above for negotiation leverage.",
            "generated_by": "error-fallback",
        }

    backend = "claude-cli" if os.environ.get("USE_CLAUDE_CLI") else "claude-api"
    result["generated_by"] = backend
    return result


def generate_comparison_narrative(comparison_data: dict) -> dict:
    user = (
        f"Buyer profile: {_BUYER_PROFILE_CONTEXT.get(comparison_data.get('buyer_profile', 'balanced'))}\n\n"
        f"Properties to compare:\n{json.dumps(comparison_data.get('properties', []), ensure_ascii=False, indent=2)}\n\n"
        "Generate the comparison JSON."
    )

    result = _call_claude(_SYSTEM_COMPARE, user, max_tokens=800)

    if "_error" in result:
        return {
            "recommendation": "Unable to generate comparison — review scores above.",
            "summary": "AI comparison narrative failed: " + result["_error"],
            "winner_by_dimension": {},
        }

    return result
