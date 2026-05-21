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
    city: str = "barcelona",
    user_answers: dict | None = None,
) -> list[dict]:
    items: list[dict] = []

    items += _transaction_costs(listing_price, prop_data, city=city)
    items += _catastro_tax_trap(prop_data, listing_price, city=city)
    items += _airbnb_situation(airbnb_data, city=city)
    items += _building_era(prop_data, city=city)
    items += _community_debt(hidden_costs_data, prop_data)
    items += _ite_status(prop_data, city=city)
    items += _nonresident_tax(prop_data, listing_price, buyer_profile, city=city)
    items += _noise_reality(noise_data)
    items += _neighbourhood_trajectory(trajectory_data)
    # Cédula de habitabilitat only applies in Catalonia — abolished in Madrid (Decreto 111/2018)
    if city != "madrid":
        items += _cedula_habitabilidad(prop_data)
    # Madrid-specific: Plan RESIDE + LPH VUT compliance (fires for STR investors too)
    if city == "madrid":
        items += _madrid_vut_compliance(airbnb_data, prop_data, buyer_profile=buyer_profile, user_answers=user_answers)
    # Madrid-specific: elevator derrama risk for old buildings on high floors
    if city == "madrid":
        items += _madrid_elevator_risk(prop_data)

    # Sort: red first, then yellow, then green/info
    _ORDER = {"red": 0, "yellow": 1, "green": 2, "info": 3}
    items.sort(key=lambda x: _ORDER.get(x["severity"], 99))

    if language == "zh":
        items = _translate_zh(items, prop_data, airbnb_data, noise_data,
                              hidden_costs_data, listing_price, city=city)
    return items


def _translate_zh(
    items: list[dict],
    prop_data: dict,
    airbnb_data: dict,
    noise_data: dict,
    hidden_costs_data: dict,
    listing_price: float | None,
    city: str = "barcelona",
) -> list[dict]:
    """Replace English disclosure text with Chinese equivalents."""
    is_madrid = city == "madrid"
    year = prop_data.get("year_built")
    ite  = prop_data.get("ite_status", "UNKNOWN")
    derrama = hidden_costs_data.get("derrama_risk_label", "low")
    pct = airbnb_data.get("tourist_pct_building")
    count_100m = airbnb_data.get("tourist_count_100m", 0)
    count_500m = airbnb_data.get("tourist_count_500m") or 0
    bars  = noise_data.get("bars_clubs_500m", 0)
    nightclubs = noise_data.get("nightclubs_500m", 0)
    night = noise_data.get("night_noise_score", 100)

    cadastral = prop_data.get("cadastral_value")
    # City-specific ITP rate and cadastral ratio
    itp_rate = 0.06 if is_madrid else 0.10
    cadastral_ratio = 0.20 if is_madrid else 0.35
    region_zh = "马德里" if is_madrid else "加泰罗尼亚"
    pct_range_zh = "8–10%" if is_madrid else "12–14%"

    price = listing_price or (cadastral / cadastral_ratio if cadastral else None)
    itp = int(price * itp_rate) if price else None
    notary = int(price * 0.015) if price else None
    lawyer = int(price * 0.01) if price else None
    total_low = itp + notary if (itp and notary) else None
    total_high = total_low + lawyer if (total_low and lawyer) else None

    # IRNR: Madrid properties use 2% imputed rate (pre-1994 catastral values)
    # BCN: 1.1%. Both use 19% (EU) — note non-EU should be 24% but we show a note
    irnr_rate = 0.02 if is_madrid else 0.011
    annual_irnr = round(cadastral * irnr_rate * 0.19) if cadastral else None

    cadastral_value = prop_data.get("cadastral_value")
    ref_estimate = int(cadastral_value / cadastral_ratio) if cadastral_value else None
    catastro_gap = int(ref_estimate - listing_price) if (ref_estimate and listing_price and ref_estimate > listing_price) else None
    catastro_extra_tax = int(catastro_gap * itp_rate) if catastro_gap else None

    zh_map: dict[str, dict] = {
        "catastro_tax_trap": {
            "title": "Catastro参考价可能高于成交价，税务局按高者征收ITP",
            "detail": (
                f"该房产的Catastro参考价估算约为 €{ref_estimate:,}（估算值，{region_zh}地籍估值通常为市场价的{'10–25%' if is_madrid else '25–40%'}），"
                + (f"高于挂牌价 €{int(listing_price):,} 约 €{catastro_gap:,}。" if catastro_gap and listing_price else "")
                + f"西班牙税务局有权按实际成交价与官方Catastro参考价中的较高者征收ITP（{region_zh}税率{int(itp_rate*100)}%）。"
                + (f"若按参考价计算，你可能需要额外缴纳约 €{catastro_extra_tax:,} 的税款。" if catastro_extra_tax else "")
            ),
            "action": (
                "签约前请在Catastro官网（sede.catastro.gob.es）查询精确的valor de referencia。"
                "若高于成交价，建议咨询税务律师，评估是否提出异议或将额外税款纳入预算。"
            ),
        },
        "transaction_costs": {
            "title": (
                f"购房税费约 €{total_low:,}–€{total_high:,}，需额外准备"
                if total_low and total_high
                else f"购房税费约为房价的{pct_range_zh}，需额外准备"
            ),
            "detail": (
                f"在{region_zh}购买二手房，买家须支付：{int(itp_rate*100)}% 产权转让税（ITP）"
                + (f"约 €{itp:,}" if itp else "")
                + "、公证及土地登记费约 1.5%"
                + (f"（€{notary:,}）" if notary else "")
                + "、律师费约 1%（建议聘请）。"
                "大多数外籍买家低估了这部分费用，往往多付 €2–4万。"
                + ("马德里ITP税率（6%）是全西班牙最低之一，比加泰罗尼亚低4个百分点。" if is_madrid else "")
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
                + (
                    "Plan RESIDE（2025年9月生效）禁止在住宅混合楼栋开设新VUT许可证。"
                    "《水平产权法》2025年改革：短租现在默认禁止，需社区3/5票数表决同意才能开放。"
                    "马德里约91%的在营短租房源无合法有效许可证，经营者面临€30,001–€100,001罚款风险。"
                    if is_madrid else
                    "巴塞罗那已通过法规，所有旅游公寓牌照须于2028年11月前归还。"
                    "在此之前：短租邻居频繁更换、楼宇损耗加速、业主大会决议难以形成多数。"
                    "2028年后：旅游公寓将全面停止，居住品质有望提升，但短租收益也将消失。"
                )
            ),
            "action": (
                ("签约前核实该楼栋是否持有Comunidad de Madrid颁发的合法VUT牌照，"
                 "以及业主大会是否已表决同意短租。无牌照+无表决则无法合法运营。"
                 if is_madrid else
                 "签约前确认楼栋业主大会是否已通过禁止旅游出租的决议（楼规高于个人牌照）。")
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
                    f"€{annual_irnr:,}/年（欧盟居民）或更高（非欧盟按24%）。"
                    f"计算方式：地籍估值 × {irnr_rate*100:.1f}%（推算收入） × 19%（欧盟税率）。"
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
        # Madrid-specific disclosures
        "madrid_vut_compliance": {
            "title": "Plan RESIDE：约91%的马德里短租房无合法有效许可证",
            "detail": (
                f"该地区500米内有 {count_500m} 套短租房源。"
                "Plan RESIDE（2025年9月生效）禁止在住宅楼栋开设新VUT许可证。"
                "《水平产权法》2025年4月改革：短租默认禁止，需社区3/5投票同意才能允许。"
                "Comunidad de Madrid审计发现仅约9%的在营VUT持有合法现行许可证。"
                "违规运营罚款：首次€30,001，二次€60,001，三次€100,001。"
            ),
            "action": (
                "投资购房前：（1）核实是否持有Comunidad de Madrid颁发的合法VUT注册号；"
                "（2）确认楼栋业主大会已通过表决允许短租。两者缺一不可。"
            ),
        },
        "madrid_elevator_risk": {
            "title": f"{year}年建造 · 高楼层 · 无电梯 — 潜在电梯改造摊派风险",
            "detail": (
                "根据修订后的《水平产权法》，楼内任何70岁以上或残障业主均可依法要求安装电梯，"
                "无需征得所有业主同意。马德里住宅楼安装电梯费用约4万–30万欧元以上（取决于楼型），"
                "政府补贴40–75%后，个人承担部分仍可能达€5,000–€25,000。"
            ),
            "action": (
                "购房前询问楼内是否有老年或残障业主，是否讨论过电梯安装计划，"
                "将此风险纳入未来持有成本预算。"
            ),
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

def _transaction_costs(listing_price: float | None, prop_data: dict, city: str = "barcelona") -> list[dict]:
    cadastral = prop_data.get("cadastral_value")
    price = listing_price or (cadastral / 0.35 if cadastral else None)
    is_madrid = city == "madrid"
    itp_rate = 0.06 if is_madrid else 0.10
    region_label = "Madrid (Comunidad de Madrid)" if is_madrid else "Catalonia"
    pct_range = "8–10%" if is_madrid else "12–14%"

    if not price:
        return [{
            "id": "transaction_costs",
            "severity": "info",
            "category": "costs",
            "title": f"Add {pct_range} on top of purchase price for transaction costs",
            "detail": (
                f"In {region_label}, resale property buyers pay: {int(itp_rate*100)}% transfer tax (ITP), "
                "~1.5% notary + Land Registry, ~1% lawyer. "
                "This surprises most non-Spanish buyers who expect 5–7%."
            ),
            "action": "Budget for total transaction cost before making an offer, not after.",
        }]

    itp = price * itp_rate
    notary_registry = price * 0.015
    lawyer = price * 0.01
    total_low = itp + notary_registry
    total_high = itp + notary_registry + lawyer
    pct_low = round(total_low / price * 100, 1)
    pct_high = round(total_high / price * 100, 1)

    madrid_note = (
        " Madrid's ITP rate (6%) is one of Spain's lowest — 4 percentage points below Catalonia's 10%."
        if is_madrid else ""
    )

    return [{
        "id": "transaction_costs",
        "severity": "yellow",
        "category": "costs",
        "title": f"Transaction costs: ~€{int(total_low):,}–€{int(total_high):,} on top of asking price",
        "detail": (
            f"For a €{int(price):,} resale property in {region_label}: "
            f"{int(itp_rate*100)}% ITP (€{int(itp):,}) + notary/registry (~€{int(notary_registry):,}) "
            f"+ optional but recommended lawyer (~€{int(lawyer):,}). "
            f"Total {pct_low}–{pct_high}% of purchase price.{madrid_note}"
        ),
        "action": "Confirm your total budget covers purchase price + these costs before making an offer.",
    }]


def _airbnb_situation(airbnb_data: dict, city: str = "barcelona") -> list[dict]:
    pct = airbnb_data.get("tourist_pct_building")
    count_100m = airbnb_data.get("tourist_count_100m", 0)
    count_500m = airbnb_data.get("tourist_count_500m", 0)
    risk = airbnb_data.get("risk_label", "low")

    severity = "red" if risk in ("high", "very_high") else "yellow" if risk == "medium" else "green"

    count_500m_display = count_500m or 0
    count_100m_display = count_100m or 0

    if pct is not None:
        building_detail = (
            f"{pct:.0f}% of units in this building are registered tourist apartments"
            if pct > 0
            else "No registered tourist apartments found in this building"
        )
    else:
        building_detail = f"{count_100m_display} Airbnb listings within 100m"

    if city == "madrid":
        # Keep saturation facts here; VUT compliance details are in _madrid_vut_compliance
        detail = (
            f"{count_500m_display} total tourist apartments within 500m. "
            "Plan RESIDE (Sep 2025) restricts new tourist rental licenses. "
            "~91% of active Madrid VUTs operate without a currently valid municipal license."
        )
        action = (
            "See the Plan RESIDE compliance disclosure below for detailed licence requirements and fines."
            if pct and pct > 0 else
            "If you plan to rent short-term: see the Plan RESIDE disclosure for licence requirements."
        )
    else:
        detail = (
            f"{count_500m_display} total tourist apartments within 500m. "
            "Barcelona's Constitutional Court upheld a full ban on tourist apartment licenses — "
            "all existing licenses must be relinquished by November 2028. "
            "Until then: rotating short-term neighbors, increased building wear, and potential "
            "community disputes. After 2028: this ends, which may improve residential quality "
            "but eliminates any rental income potential from tourist lets."
        )
        action = (
            "Before signing: verify whether the building's community has already voted to "
            "prohibit tourist rentals (building rules override individual licenses)."
            if pct and pct > 5 else None
        )

    return [{
        "id": "airbnb_saturation",
        "severity": severity,
        "category": "neighborhood",
        "title": building_detail,
        "detail": detail,
        "action": action,
    }]


def _building_era(prop_data: dict, city: str = "barcelona") -> list[dict]:
    year = prop_data.get("year_built")
    if not year:
        return []

    if 1960 <= year <= 1975:
        if city == "madrid":
            return [{
                "id": "building_era_risk",
                "severity": "yellow",
                "category": "building",
                "title": f"Built {year}: verify structural condition and ITE inspection status",
                "detail": (
                    "Madrid buildings from 1960–1975 used standard concrete construction. "
                    "Aluminosis risk is minimal in Madrid due to the dry climate. "
                    "However, this age building may have outdated electrical wiring, original plumbing, "
                    "and no thermal insulation. Buildings over 50 years old must have completed an ITE inspection. "
                    "Request the ITE report and last 2 years of community meeting minutes."
                ),
                "action": (
                    "Request the building's most recent ITE report from the seller or community administrator. "
                    "Check community meeting minutes for any agreed or upcoming works (derramas)."
                ),
            }]
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
            "documented Spanish cases range from €5,000 to €40,000 per unit."
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


def _ite_status(prop_data: dict, city: str = "barcelona") -> list[dict]:
    ite = prop_data.get("ite_status", "UNKNOWN")
    year = prop_data.get("year_built")
    ite_name = "Inspección Técnica de Edificios" if city == "madrid" else "Inspecció Tècnica d'Edificis"
    if ite == "DESFAVORABLE":
        return [{
            "id": "ite_status",
            "severity": "red",
            "category": "building",
            "title": "Building has an UNFAVORABLE technical inspection (ITE)",
            "detail": (
                f"The building's ITE ({ite_name}) has flagged deficiencies. "
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
    city: str = "barcelona",
) -> list[dict]:
    is_expat = buyer_profile in ("expat", None)  # default to showing for unknown profile
    if not is_expat:
        return []

    cadastral = prop_data.get("cadastral_value")
    # Madrid: most properties have pre-1994 catastral values → 2% imputed rate
    # BCN: typically post-1994 update → 1.1% rate
    # Tax rate: 19% for EU/EEA residents; 24% for non-EU
    # We use 19% (EU) as the displayed base but flag non-EU
    imputed_rate = 0.02 if city == "madrid" else 0.011
    eu_tax_rate = 0.19

    # Cadastral proxy when Catastro didn't return it
    cadastral_proxy_ratio = 0.15 if city == "madrid" else 0.50
    if not cadastral and listing_price:
        cadastral = listing_price * cadastral_proxy_ratio

    if not cadastral:
        return [{
            "id": "nonresident_tax",
            "severity": "info",
            "category": "costs",
            "title": "Non-resident owners pay annual income tax even with no rental income",
            "detail": (
                "If you are not a Spanish tax resident, you must file and pay IRNR "
                "(Impuesto sobre la Renta de No Residentes) annually, "
                f"even if the property sits empty. For {'Madrid' if city == 'madrid' else 'Barcelona'} properties: "
                f"estimated rate ≈ {imputed_rate*100:.1f}% imputed income × 19% (EU) or 24% (non-EU) tax. "
                "This is separate from IBI and is frequently overlooked by foreign buyers."
            ),
            "action": "Consult a Spanish gestor or tax advisor before purchase to understand your annual tax obligation.",
        }]

    annual_irnr_eu = round(cadastral * imputed_rate * eu_tax_rate)
    annual_irnr_noneu = round(cadastral * imputed_rate * 0.24)
    return [{
        "id": "nonresident_tax",
        "severity": "yellow",
        "category": "costs",
        "title": f"Non-resident tax: ~€{annual_irnr_eu:,}–€{annual_irnr_noneu:,}/year even if property sits empty",
        "detail": (
            f"Based on estimated cadastral value (€{int(cadastral):,}), annual IRNR: "
            f"EU/EEA residents: ~€{annual_irnr_eu:,}/year ({imputed_rate*100:.1f}% imputed × 19%); "
            f"Non-EU residents (USA, China, UK): ~€{annual_irnr_noneu:,}/year ({imputed_rate*100:.1f}% imputed × 24%). "
            "This applies regardless of whether you rent the property or leave it vacant. "
            "Plus IBI on top. Non-EU buyers pay the higher rate."
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


def _catastro_tax_trap(prop_data: dict, listing_price: float | None, city: str = "barcelona") -> list[dict]:
    """Warn when Catastro value could be higher than listing price — buyer pays ITP on the higher value."""
    cadastral_value = prop_data.get("cadastral_value")
    if not cadastral_value or not listing_price:
        return []
    # Madrid: valor catastral is based on 1990-era valuations — much lower ratio to market.
    # BCN: typically 25–40% of market value; Madrid: often 10–25%.
    ratio = 0.20 if city == "madrid" else 0.35
    itp_rate = 0.06 if city == "madrid" else 0.10
    region = "Madrid" if city == "madrid" else "Catalonia"

    reference_estimate = cadastral_value / ratio
    if listing_price >= reference_estimate * 0.95:
        return []  # listing price is at or above reference — no trap likely
    gap = reference_estimate - listing_price
    extra_tax = round(gap * itp_rate)
    return [{
        "id": "catastro_tax_trap",
        "severity": "yellow",
        "category": "costs",
        "title": "ITP tax may be calculated on Catastro reference value, not purchase price",
        "detail": (
            f"The Catastro valor de referencia for this property is estimated at ~€{int(reference_estimate):,} "
            f"(approximation — {region} cadastral values are typically {int(ratio*100)}% of market value). "
            f"This is {round((reference_estimate - listing_price) / listing_price * 100)}% above the asking price of €{int(listing_price):,}. "
            f"In Spain, Hacienda can charge ITP ({int(itp_rate*100)}% in {region}) on the higher of: "
            "your actual purchase price OR the official Catastro reference value. "
            f"If that applies here, you could owe an extra ~€{extra_tax:,} in tax beyond what you budgeted."
        ),
        "action": (
            "Before signing, check the exact valor de referencia at the Catastro website "
            "(sede.catastro.gob.es). If it exceeds your purchase price, get a tax lawyer's opinion "
            "on whether to challenge it or factor the extra ITP into your budget."
        ),
    }]


def _madrid_vut_compliance(airbnb_data: dict, prop_data: dict, buyer_profile: str | None = None, user_answers: dict | None = None) -> list[dict]:
    """Madrid-specific: Plan RESIDE + LPH 2025 VUT compliance warning.
    Fires for: high/very_high Airbnb saturation OR buyer intends short-term rental.
    """
    risk = airbnb_data.get("risk_label", "low")
    rental_intent = (user_answers or {}).get("rental_intent")
    # Show for high-saturation areas OR any STR investor regardless of area saturation
    is_str_investor = rental_intent == "short_term"
    if risk not in ("high", "very_high") and not is_str_investor:
        return []
    count_500m = airbnb_data.get("tourist_count_500m") or 0
    return [{
        "id": "madrid_vut_compliance",
        "severity": "red",
        "category": "legal",
        "title": "Plan RESIDE: ~91% of Madrid VUTs operate without valid license",
        "detail": (
            f"This area has {count_500m} short-term rental listings within 500m. "
            "Plan RESIDE (Sep 2025) bans new VUT licenses in residential buildings. "
            "LPH reform (Apr 2025) means tourist lets are BANNED by default — a 3/5 community "
            "vote is needed to allow them. A Comunidad de Madrid audit found only ~9% of "
            "active VUTs hold a valid current license. "
            "Fines for unlicensed operation: €30,001 (1st offence), €60,001 (2nd), €100,001 (3rd)."
        ),
        "action": (
            "If buying as investment: obtain the official VUT registry number from the Comunidad "
            "de Madrid and verify the building community has voted to permit tourist lets. "
            "Without a valid license AND community approval, you cannot legally operate on Airbnb."
        ),
    }]


def _madrid_elevator_risk(prop_data: dict) -> list[dict]:
    """Madrid-specific: elevator installation derrama risk for pre-1975 buildings on high floors."""
    year = prop_data.get("year_built")
    floor = prop_data.get("floor")
    has_lift = prop_data.get("has_lift")
    if not year or year >= 1975:
        return []
    if floor is None or floor < 3:
        return []
    if has_lift is True:
        return []
    return [{
        "id": "madrid_elevator_risk",
        "severity": "yellow",
        "category": "building",
        "title": f"Pre-1975 building, floor {floor}, no elevator — hidden derrama risk",
        "detail": (
            f"This {year} building on floor {floor} has no elevator. "
            "Under the reformed Ley de Propiedad Horizontal, any owner over 70 or with a disability "
            "can legally demand elevator installation, forcing a community vote. "
            "Installing an elevator in a Madrid building costs €40,000–€300,000+ "
            "(€40–120K standard shaft, €100–180K exterior installation, €200K+ for complex structural modifications) "
            "split among all owners. Subsidies cover 40–75% but the owner's share can still reach €5,000–€25,000+ per unit."
        ),
        "action": (
            "Before signing: ask whether the community has discussed elevator installation. "
            "If any elderly or disabled owners are present, budget for this as a potential future derrama."
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
