"""
Pre-purchase disclosure generator.

Produces structured, actionable disclosures from analysis data —
the things buyers should know before signing that no portal shows them.

Each disclosure is: what it is + why it matters + what to do about it.
Not a score. Not a rating. A fact with context.
"""

from __future__ import annotations


def generate_disclosures(
    prop_data: dict,
    airbnb_data: dict,
    noise_data: dict,
    hidden_costs_data: dict,
    trajectory_data: dict,
    school_data: dict,
    listing_price: float | None = None,
    buyer_profile: str | None = None,
    language: str = "en",
) -> list[dict]:
    items: list[dict] = []

    items += _transaction_costs(listing_price, prop_data)
    items += _catastro_tax_trap(prop_data, listing_price)
    items += _airbnb_situation(airbnb_data)
    items += _building_era(prop_data)
    items += _community_debt(hidden_costs_data, prop_data)
    items += _ite_status(prop_data)
    items += _nonresident_tax(prop_data, listing_price, buyer_profile)
    items += _noise_reality(noise_data)
    items += _neighbourhood_trajectory(trajectory_data)
    items += _cedula_habitabilidad(prop_data)

    # Sort: red first, then yellow, then green/info
    _ORDER = {"red": 0, "yellow": 1, "green": 2, "info": 3}
    items.sort(key=lambda x: _ORDER.get(x["severity"], 99))

    if language == "zh":
        items = _translate_zh(items, prop_data, airbnb_data, noise_data,
                              hidden_costs_data, listing_price)
    return items


def _translate_zh(
    items: list[dict],
    prop_data: dict,
    airbnb_data: dict,
    noise_data: dict,
    hidden_costs_data: dict,
    listing_price: float | None,
) -> list[dict]:
    """Replace English disclosure text with Chinese equivalents."""
    year = prop_data.get("year_built")
    ite  = prop_data.get("ite_status", "UNKNOWN")
    derrama = hidden_costs_data.get("derrama_risk_label", "low")
    pct = airbnb_data.get("tourist_pct_building")
    count_100m = airbnb_data.get("tourist_count_100m") or 0
    count_500m = airbnb_data.get("tourist_count_500m") or 0
    risk = airbnb_data.get("risk_label") or "low"
    bars  = noise_data.get("bars_clubs_500m", 0)
    nightclubs = noise_data.get("nightclubs_500m", 0)
    night = noise_data.get("night_noise_score", 100)

    cadastral = prop_data.get("cadastral_value")
    price = listing_price or (cadastral / 0.35 if cadastral else None)
    itp = int(price * 0.10) if price else None
    notary = int(price * 0.015) if price else None
    lawyer = int(price * 0.01) if price else None
    total_low = itp + notary if (itp and notary) else None
    total_high = total_low + lawyer if (total_low and lawyer) else None

    # IRNR: imputed income = cadastral × 1.1%; tax = imputed income × 19% (EU residents) ≈ 0.2% cadastral
    annual_irnr = round(cadastral * 0.011 * 0.19) if cadastral else None

    cadastral_value = prop_data.get("cadastral_value")
    ref_estimate = int(cadastral_value / 0.35) if cadastral_value else None
    catastro_gap = int(ref_estimate - listing_price) if (ref_estimate and listing_price and ref_estimate > listing_price) else None
    catastro_extra_tax = int(catastro_gap * 0.10) if catastro_gap else None
    catastro_tax_detail = (
        f"该房产的Catastro参考价估算约为 €{ref_estimate:,}（估算值，巴塞罗那老楼地籍估值通常为市场价的25–40%），"
        + (f"高于挂牌价 €{int(listing_price):,} 约 €{catastro_gap:,}。" if catastro_gap and listing_price else "")
        + "西班牙税务局有权按实际成交价与官方Catastro参考价中的较高者征收ITP（加泰罗尼亚税率10%）。"
        + (f"若按参考价计算，你可能需要额外缴纳约 €{catastro_extra_tax:,} 的税款。" if catastro_extra_tax else "")
        if ref_estimate is not None
        else (
            "当前公开数据未返回该房产的Catastro参考价估算。"
            "西班牙税务局有权按实际成交价与官方Catastro参考价中的较高者征收ITP（加泰罗尼亚税率10%），"
            "因此仍需在签约前单独核实官方valor de referencia。"
        )
    )

    zh_map: dict[str, dict] = {
        "catastro_tax_trap": {
            "title": "Catastro参考价可能高于成交价，税务局按高者征收ITP",
            "detail": catastro_tax_detail,
            "action": (
                "签约前请在Catastro官网（sede.catastro.gob.es）查询精确的valor de referencia。"
                "若高于成交价，建议咨询税务律师，评估是否提出异议或将额外税款纳入预算。"
            ),
        },
        "transaction_costs": {
            "title": (
                f"购房税费约 €{total_low:,}–€{total_high:,}，需额外准备"
                if total_low and total_high
                else "购房税费约为房价的12–14%，需额外准备"
            ),
            "detail": (
                f"在加泰罗尼亚购买二手房，买家须支付：10% 产权转让税（ITP）"
                + (f"约 €{itp:,}" if itp else "")
                + f"、公证及土地登记费约 1.5%"
                + (f"（€{notary:,}）" if notary else "")
                + "、律师费约 1%（建议聘请）。"
                "大多数外籍买家低估了这部分费用，往往多付 €2–4万。"
            ),
            "action": "报价前确认总预算已包含这部分税费，而非事后补充。",
        },
        "airbnb_saturation": {
            "title": (
                f"本楼约 {pct:.0f}% 的单元为注册旅游公寓"
                if pct and pct > 0
                else (
                    "本楼未发现注册旅游公寓"
                    if pct == 0
                    else f"100米内有 {count_100m} 套 Airbnb 房源"
                )
            ),
            "detail": (
                f"500米范围内共有 {count_500m} 套旅游公寓。"
                "巴塞罗那已通过法规，所有旅游公寓牌照须于2028年11月前归还。"
                "在此之前：短租邻居频繁更换、楼宇损耗加速、业主大会决议难以形成多数。"
                "2028年后：旅游公寓将全面停止，居住品质有望提升，但短租收益也将消失。"
            ),
            "action": (
                "签约前确认楼栋业主大会是否已通过禁止旅游出租的决议（楼规高于个人牌照）。"
                if pct and pct > 5 else None
            ),
        },
        "building_era_risk": (
            {
                "title": f"建于 {year} 年：铝水泥高风险 + 社区大修费可能达 €15,000–€40,000/户",
                "detail": (
                    "1960–1975年间的巴塞罗那建筑大量使用铝水泥（aluminosis），"
                    "该材料随时间降解并削弱结构柱和楼板，外观无法判断。"
                    "修缮时社区议定的大修摊派（derrama）实际案例中每户费用从 €15,000 到 €40,000 不等。"
                    "卖方无主动披露义务。"
                ),
                "action": (
                    "签约前：（1）委托独立结构工程师出具ITE报告，不依赖卖方检测；"
                    "（2）索取近3年业主大会记录（actas de junta）——已知结构问题必须在此记录；"
                    "（3）询问是否已有正在讨论或议定的结构修缮摊派计划。"
                ),
            }
            if year and 1960 <= year <= 1975
            else {
                "title": f"建于 {year} 年：1960年前老建筑——请核实结构状况",
                "detail": (
                    "1960年前的建筑可能存在老旧电路、铅管，缺乏隔热设施。"
                    "部分为文保建筑，翻新有限制。请核实当前ITE（建筑技术检查）状态。"
                ),
                "action": "向卖方或楼栋管理员索取最新的ITE报告。",
            }
            if year and year < 1960
            else {
                "title": f"建于 {year} 年：可能含石棉材料",
                "detail": (
                    "1975–1990年建筑可能在隔热层、地板砖或管道中含有石棉。"
                    "稳定状态下的石棉不构成健康风险，翻新施工时才需处理。"
                ),
                "action": "如计划翻新，施工前请委托专业机构进行石棉检测。",
            }
            if year and 1975 < year < 1990
            else {
                "title": f"建于 {year} 年：1990年后建筑，结构风险较低",
                "detail": (
                    "1990年后的建筑符合现代抗震标准，不受铝水泥或石棉问题影响。"
                    "请确认物业管理费中包含维修储备金（fondo de reserva）。"
                ),
                "action": None,
            }
        ),
        "community_debt": {
            "title": "前业主欠缴的费用，法律上由你承担",
            "detail": (
                "西班牙法律规定，前业主未缴的IBI房产税和物业管理费，"
                "在产权过户后由新买家承担——最多追溯4年IBI税和当年物业费。"
                + {
                    "high": "本楼的维修摊派风险评级为【高】，可能面临较大金额的业主大会临时摊派（€5,000–€40,000/户）。",
                    "medium": "本楼维修摊派风险为中等，未来几年内可能出现临时摊派。",
                    "low": "根据现有数据，维修摊派风险较低。",
                }.get(derrama, "")
            ),
            "action": (
                "签约前向楼栋管理员索取债务证明（certificado de deudas de la comunidad），"
                "并要求查看最近一期已缴清的IBI收据。"
            ),
        },
        "ite_status": (
            {
                "title": "本楼建筑技术检查（ITE）结果为【不合格】",
                "detail": (
                    "本楼的ITE（建筑技术检查）已发现存在问题，"
                    "可能面临强制整改施工——费用由全体业主分摊。"
                    "购房后你将共同承担这笔费用。"
                ),
                "action": (
                    "索取完整的ITE报告，了解具体整改内容、估算费用及截止日期，"
                    "再决定是否出价。"
                ),
            }
            if ite == "DESFAVORABLE"
            else {
                "title": "本楼ITE检查状态无法确认",
                "detail": (
                    f"该{year}年楼龄的建筑应定期接受ITE检查，"
                    "但无法从公开数据确认当前状态。"
                ),
                "action": "向卖方或楼栋管理员询问最近一次ITE报告。",
            }
        ),
        "nonresident_tax": {
            "title": (
                f"非居民税：即使空置也需每年缴纳约 €{annual_irnr:,}"
                if annual_irnr
                else "非居民须每年缴纳IRNR税，即使房产空置"
            ),
            "detail": (
                (
                    f"根据地籍估值（€{int(cadastral):,}），预计IRNR = "
                    f"€{annual_irnr:,}/年（地籍估值 × 1.1% 推算收入 × 19% 欧盟税率，实际税率约为地籍估值的0.2%）。"
                )
                if annual_irnr
                else ""
            ) + (
                "此税适用于所有非西班牙税务居民，无论房产出租还是空置均须缴纳，"
                "且与IBI房产税分开计算，常被外籍买家忽视。"
            ),
            "action": "购房前咨询西班牙税务顾问了解年度税务义务。购房后30天内注册税务代理人（representante fiscal）。",
        },
        "noise_reality": {
            "title": (
                f"噪音风险高：500米内有 {bars} 家酒吧/夜店，其中 {nightclubs} 家夜总会"
                if night < 40 or bars > 10 or nightclubs > 2
                else f"噪音环境中等：500米内有 {bars} 家酒吧"
            ),
            "detail": (
                "该区域深夜活动频繁。房源描述从不披露噪音状况，"
                "但它是买家后悔的首要原因之一。白天看房无法感受到夜间的声音穿透情况。"
                if night < 40 or bars > 10 or nightclubs > 2
                else (
                    "该区域有一定夜生活活动，是否影响居住体验取决于楼层、"
                    "建筑隔音质量和个人承受能力，白天看房无法判断。"
                )
            ),
            "action": (
                "承诺购买前，务必在周五或周六晚22:00后实地察看，"
                "重点了解双层玻璃和隔音情况。"
                if night < 40 or bars > 10 or nightclubs > 2
                else "建议夜间实地考察后再做决定。"
            ),
        },
        "neighbourhood_trajectory": {
            "title": (
                "街区商业活动呈下行趋势"
                if airbnb_data.get("risk_label") == "very_high"  # placeholder, use trend
                else "街区呈活跃增长态势"
            ),
            "detail": "",  # filled dynamically below
            "action": None,
        },
        "cedula_habitabilidad": {
            "title": "签约前请核实居住证（cèdula d'habitabilitat）是否有效",
            "detail": (
                "居住证（cèdula d'habitabilitat）在加泰罗尼亚是接通水电气、"
                "合法出租房产的必要文件。"
                f"该{year}年建筑早于现行认证体系，证书可能已过期或从未更新。"
                "申请新证需 €300–€800 并需技术检查，部分房产可能无法通过。"
            ) if year else "",
            "action": "要求卖方提供有效的居住证，已过期须计入成本和风险。",
        },
    }

    # Special case: neighbourhood_trajectory needs trajectory data passed in
    # We handle it differently based on severity/title
    out = []
    for item in items:
        disc_id = item.get("id", "")
        zh = zh_map.get(disc_id)
        if zh:
            new_item = dict(item)
            new_item["title"]  = zh.get("title", item["title"])
            new_item["action"] = zh.get("action", item["action"])
            # For neighbourhood_trajectory, rebuild detail from trajectory data embedded in title
            if disc_id == "neighbourhood_trajectory":
                # Extract numbers from original English detail
                if item["severity"] == "green":
                    new_item["title"]  = "街区呈活跃增长态势"
                    new_item["detail"] = item["detail"]  # keep original numbers, readable
                    new_item["action"] = None
                else:
                    new_item["title"]  = "街区商业活动呈下行趋势"
                    new_item["detail"] = item["detail"]
                    new_item["action"] = "研究下行原因后再做决定——是开发计划、居民外迁还是季节性因素？"
            else:
                new_item["detail"] = zh.get("detail", item["detail"])
            out.append(new_item)
        else:
            out.append(item)
    return out


# ─── individual generators ───────────────────────────────────────────────────

def _transaction_costs(listing_price: float | None, prop_data: dict) -> list[dict]:
    cadastral = prop_data.get("cadastral_value")
    price = listing_price or (cadastral / 0.35 if cadastral else None)
    if not price:
        return [{
            "id": "transaction_costs",
            "severity": "info",
            "category": "costs",
            "title": "Add 12–14% on top of purchase price for transaction costs",
            "detail": (
                "In Catalonia, resale property buyers pay: 10% transfer tax (ITP), "
                "~1.5% notary + Land Registry, ~1% lawyer. "
                "This surprises most non-Spanish buyers who expect 5–7%."
            ),
            "action": "Budget for total transaction cost before making an offer, not after.",
        }]

    itp = price * 0.10
    notary_registry = price * 0.015
    lawyer = price * 0.01
    total_low = itp + notary_registry
    total_high = itp + notary_registry + lawyer
    pct_low = round(total_low / price * 100, 1)
    pct_high = round(total_high / price * 100, 1)

    return [{
        "id": "transaction_costs",
        "severity": "yellow",
        "category": "costs",
        "title": f"Transaction costs: ~€{int(total_low):,}–€{int(total_high):,} on top of asking price",
        "detail": (
            f"For a €{int(price):,} resale property in Catalonia: "
            f"10% ITP (€{int(itp):,}) + notary/registry (~€{int(notary_registry):,}) "
            f"+ optional but recommended lawyer (~€{int(lawyer):,}). "
            f"Total {pct_low}–{pct_high}% of purchase price. "
            "Most non-Spanish buyers underestimate this by €20,000–€40,000."
        ),
        "action": "Confirm your total budget covers purchase price + these costs before making an offer.",
    }]


def _airbnb_situation(airbnb_data: dict) -> list[dict]:
    pct = airbnb_data.get("tourist_pct_building")
    count_100m = airbnb_data.get("tourist_count_100m") or 0
    count_500m = airbnb_data.get("tourist_count_500m") or 0
    risk = airbnb_data.get("risk_label") or "low"

    severity = "red" if risk in ("high", "very_high") else "yellow" if risk == "medium" else "green"

    if pct is not None:
        building_detail = (
            f"{pct:.0f}% of units in this building are registered tourist apartments"
            if pct > 0
            else "No registered tourist apartments found in this building"
        )
    else:
        building_detail = f"{count_100m} Airbnb listings within 100m"

    return [{
        "id": "airbnb_saturation",
        "severity": severity,
        "category": "neighborhood",
        "title": building_detail,
        "detail": (
            f"{count_500m} total tourist apartments within 500m. "
            "Barcelona's Constitutional Court upheld a full ban on tourist apartment licenses — "
            "all existing licenses must be relinquished by November 2028. "
            "Until then: rotating short-term neighbors, increased building wear, and potential "
            "community disputes. After 2028: this ends, which may improve residential quality "
            "but eliminates any rental income potential from tourist lets."
        ),
        "action": (
            "Before signing: verify whether the building's community has already voted to "
            "prohibit tourist rentals (building rules override individual licenses)."
            if pct and pct > 5 else None
        ),
    }]


def _building_era(prop_data: dict) -> list[dict]:
    year = prop_data.get("year_built")
    if not year:
        return []

    if 1960 <= year <= 1975:
        return [{
            "id": "building_era_risk",
            "severity": "red",
            "category": "building",
            "title": f"Built {year}: aluminosis + potential community repair cost €15,000–€40,000/unit",
            "detail": (
                "Barcelona buildings from 1960–1975 were frequently built with aluminium cement (aluminosis), "
                "which degrades over time and weakens structural columns and slabs. "
                "This cannot be detected visually — several buildings in this era required major rehabilitation "
                "or demolition. When remediation is required, community-agreed structural repair costs "
                "have ranged from €15,000 to €40,000 per unit (real cases documented in Galicia and BCN). "
                "The seller is not required to disclose this proactively."
            ),
            "action": (
                "Before signing: (1) Commission an independent structural engineer's ITE report — "
                "do not rely on the seller's inspection. "
                "(2) Request the last 3 years of community meeting minutes (actas de junta) — "
                "any known structural issues must be discussed there. "
                "(3) Ask if a derrama for structural works has been agreed or is under discussion."
            ),
        }]
    elif year < 1960:
        return [{
            "id": "building_era_risk",
            "severity": "yellow",
            "category": "building",
            "title": f"Built {year}: pre-1960 building — verify structural condition",
            "detail": (
                "Pre-1960 buildings may have outdated electrical wiring, lead pipes, and lack "
                "thermal insulation. Some are protected heritage buildings with restrictions "
                "on renovations. Verify the current ITE (technical building inspection) status."
            ),
            "action": "Request the building's most recent ITE report from the seller or community administrator.",
        }]
    elif 1975 < year < 1990:
        return [{
            "id": "building_era_risk",
            "severity": "yellow",
            "category": "building",
            "title": f"Built {year}: possible asbestos-containing materials",
            "detail": (
                "Buildings from 1975–1990 may contain asbestos in insulation, floor tiles, "
                "or pipes. This is only a concern during renovation work — stable asbestos "
                "is not a health risk. Budget for professional removal if you plan to renovate."
            ),
            "action": "If planning renovations, request an asbestos survey before work begins.",
        }]
    else:
        return [{
            "id": "building_era_risk",
            "severity": "green",
            "category": "building",
            "title": f"Built {year}: post-1990 construction — lower structural risk",
            "detail": (
                "Post-1990 buildings comply with modern seismic standards and are not "
                "affected by aluminosis or asbestos risks. Check the community fee includes "
                "a reserve fund (fondo de reserva) for future maintenance."
            ),
            "action": None,
        }]


def _community_debt(hidden_costs_data: dict, prop_data: dict) -> list[dict]:
    derrama = hidden_costs_data.get("derrama_risk_label", "low")
    severity = "red" if derrama == "high" else "yellow"
    derrama_detail = {
        "high": (
            "The building's derrama risk is rated HIGH based on age and condition. "
            "A large one-time community levy (derrama) may be imminent — "
            "past examples in Barcelona range from €5,000 to €40,000 per unit."
        ),
        "medium": "The building shows moderate derrama risk — a community levy is possible within the next few years.",
        "low": "Derrama risk appears low based on available data.",
    }.get(derrama, "")

    return [{
        "id": "community_debt",
        "severity": severity,
        "category": "legal",
        "title": "Unpaid community debts and levies transfer to you by law",
        "detail": (
            "In Spain, any unpaid IBI taxes and community fees (comunidad) owed by the "
            "previous owner legally become the new buyer's responsibility upon transfer — "
            "up to 4 years of IBI and the current year's community fees. "
            f"{derrama_detail}"
        ),
        "action": (
            "Before signing: (1) Request the certificado de deudas de la comunidad "
            "(community debt certificate) from the building administrator. "
            "(2) Request the last IBI receipt proving it was paid. "
            "(3) Request the last 2 years of community meeting minutes (actas de junta) "
            "— approved derrama levies must be disclosed there."
        ),
    }]


def _ite_status(prop_data: dict) -> list[dict]:
    ite = prop_data.get("ite_status", "UNKNOWN")
    year = prop_data.get("year_built")
    if ite == "DESFAVORABLE":
        return [{
            "id": "ite_status",
            "severity": "red",
            "category": "building",
            "title": "Building has a UNFAVORABLE technical inspection (ITE)",
            "detail": (
                "The building's ITE (Inspecció Tècnica d'Edificis) has flagged deficiencies. "
                "This may mean mandatory rehabilitation works are pending — costs are shared "
                "among owners. You would inherit responsibility for these works upon purchase."
            ),
            "action": (
                "Request the full ITE report and understand exactly what works are required, "
                "their estimated cost, and the compliance deadline before making any offer."
            ),
        }]
    elif ite == "UNKNOWN" and year and year < 1980:
        return [{
            "id": "ite_status",
            "severity": "yellow",
            "category": "building",
            "title": "Building inspection (ITE) status could not be confirmed",
            "detail": (
                f"This {year} building is old enough to require periodic ITE inspections. "
                "We could not confirm the current inspection status from available data."
            ),
            "action": "Ask the seller or building administrator for the most recent ITE report.",
        }]
    return []


def _nonresident_tax(
    prop_data: dict,
    listing_price: float | None,
    buyer_profile: str | None,
) -> list[dict]:
    is_expat = buyer_profile in ("expat", None)  # default to showing for unknown profile
    if not is_expat:
        return []

    cadastral = prop_data.get("cadastral_value")
    if not cadastral and listing_price:
        cadastral = listing_price * 0.5  # rough proxy

    if not cadastral:
        return [{
            "id": "nonresident_tax",
            "severity": "info",
            "category": "costs",
            "title": "Non-resident owners pay annual income tax even with no rental income",
            "detail": (
                "If you are not a Spanish tax resident, you must file and pay IRNR "
                "(Impuesto sobre la Renta de No Residentes) annually — approximately 0.2% "
                "of the cadastral value for EU residents (1.1% imputed income × 19% tax rate), "
                "even if the property sits empty. "
                "This is separate from IBI and is frequently overlooked by foreign buyers."
            ),
            "action": "Consult a Spanish gestor or tax advisor before purchase to understand your annual tax obligation.",
        }]

    # IRNR formula: imputed income = cadastral × 1.1%; tax = imputed income × 19% (EU residents)
    # Effective rate ≈ 0.209% of cadastral value
    annual_irnr = round(cadastral * 0.011 * 0.19)
    return [{
        "id": "nonresident_tax",
        "severity": "yellow",
        "category": "costs",
        "title": f"Non-resident tax: ~€{annual_irnr:,}/year even if property sits empty",
        "detail": (
            f"Based on cadastral value (€{int(cadastral):,}), estimated IRNR = "
            f"€{annual_irnr:,}/year (cadastral value × 1.1% imputed income × 19% EU tax rate ≈ 0.2% of cadastral). "
            "This applies to all non-Spanish tax residents and is due regardless of "
            "whether you rent the property or leave it vacant. "
            "Plus IBI on top."
        ),
        "action": "Factor this into your annual holding cost. Register with a Spanish tax representative (representante fiscal) within 30 days of purchase.",
    }]


def _noise_reality(noise_data: dict) -> list[dict]:
    night = noise_data.get("night_noise_score", 100)
    bars = noise_data.get("bars_clubs_500m", 0)
    nightclubs = noise_data.get("nightclubs_500m", 0)

    if night < 40 or bars > 10 or nightclubs > 2:
        return [{
            "id": "noise_reality",
            "severity": "red",
            "category": "neighborhood",
            "title": f"High noise risk: {bars} bars/clubs within 500m, {nightclubs} nightclubs",
            "detail": (
                "This area has significant late-night activity. "
                "Property listings never disclose noise levels — but it's one of the top "
                "causes of buyer regret. Noise through walls and windows is not apparent "
                "during a daytime viewing."
            ),
            "action": (
                "Visit the property on a Friday or Saturday night after 22:00 before committing. "
                "Ask specifically about double-glazing and insulation quality."
            ),
        }]
    elif night < 65 or bars > 5:
        return [{
            "id": "noise_reality",
            "severity": "yellow",
            "category": "neighborhood",
            "title": f"Moderate noise environment: {bars} bars/clubs within 500m",
            "detail": (
                "The area has moderate nightlife activity. Whether this is a problem "
                "depends heavily on your floor, the building's insulation, and your tolerance. "
                "It is not visible from a daytime viewing."
            ),
            "action": "Visit at night before making an offer.",
        }]
    return []


def _neighbourhood_trajectory(trajectory_data: dict) -> list[dict]:
    trend = trajectory_data.get("trend", "stable")
    new_biz = trajectory_data.get("new_businesses_12m", 0)
    permits = trajectory_data.get("renovation_permits_12m", 0)

    if trend == "declining":
        return [{
            "id": "neighbourhood_trajectory",
            "severity": "yellow",
            "category": "neighborhood",
            "title": "Neighbourhood showing declining business activity",
            "detail": (
                f"Over the past 12 months: {new_biz} new business licences, "
                f"{permits} renovation permits — indicators of a cooling or declining area. "
                "This affects future resale liquidity and quality of local services."
            ),
            "action": "Research why the area is declining before committing — development plans, tenant pressures, or seasonal patterns?",
        }]
    elif trend == "rising":
        return [{
            "id": "neighbourhood_trajectory",
            "severity": "green",
            "category": "neighborhood",
            "title": "Neighbourhood showing active growth",
            "detail": (
                f"{new_biz} new business licences and {permits} renovation permits in 12 months "
                "signal a rising area. This is a positive indicator for long-term value."
            ),
            "action": None,
        }]
    return []


def _catastro_tax_trap(prop_data: dict, listing_price: float | None) -> list[dict]:
    """Warn when Catastro value could be higher than listing price — buyer pays ITP on the higher value."""
    cadastral_value = prop_data.get("cadastral_value")
    if not cadastral_value or not listing_price:
        return []
    # For BCN old stock, valor catastral is typically 25-40% of market value.
    # Using 0.35 as a central estimate gives better coverage than 0.5.
    # Verify the exact valor de referencia at sede.catastro.gob.es before signing.
    reference_estimate = cadastral_value / 0.35
    if listing_price >= reference_estimate * 0.95:
        return []  # listing price is at or above reference — no trap likely
    gap = reference_estimate - listing_price
    extra_tax = round(gap * 0.10)
    return [{
        "id": "catastro_tax_trap",
        "severity": "yellow",
        "category": "costs",
        "title": f"ITP tax may be calculated on Catastro reference value, not purchase price",
        "detail": (
            f"The Catastro valor de referencia for this property is estimated at ~€{int(reference_estimate):,} "
            "(approximation — BCN old stock cadastral values are typically 25–40% of market value). "
            f"This is {round((reference_estimate - listing_price) / listing_price * 100)}% above the asking price of €{int(listing_price):,}. "
            "In Spain, Hacienda can charge ITP (10% in Catalonia) on the higher of: "
            "your actual purchase price OR the official Catastro reference value. "
            f"If that applies here, you could owe an extra ~€{extra_tax:,} in tax beyond what you budgeted."
        ),
        "action": (
            "Before signing, check the exact valor de referencia at the Catastro website "
            "(sede.catastro.gob.es). If it exceeds your purchase price, get a tax lawyer's opinion "
            "on whether to challenge it or factor the extra ITP into your budget."
        ),
    }]


def _cedula_habitabilidad(prop_data: dict) -> list[dict]:
    year = prop_data.get("year_built")
    if year and year < 1995:
        return [{
            "id": "cedula_habitabilidad",
            "severity": "yellow",
            "category": "legal",
            "title": "Verify cèdula d'habitabilitat is current before signing",
            "detail": (
                "The cèdula d'habitabilitat (habitation certificate) is required in Catalonia "
                "to connect utilities (electricity, water, gas) and to legally rent the property. "
                f"This {year} building predates the current certification system — the certificate "
                "may have expired or never been renewed. Obtaining a new one costs €300–€800 "
                "and requires a technical inspection; some properties fail."
            ),
            "action": (
                "Ask the seller to provide a valid cèdula d'habitabilitat — it must be current. "
                "If it expired, factor in the renewal cost and risk."
            ),
        }]
    return []
