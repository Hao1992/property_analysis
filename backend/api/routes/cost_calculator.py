"""
Spanish property purchase cost calculator.

Computes all buyer-side costs for a property purchase in Spain:
- ITP (resale) or AJD/VAT (new build)
- Notary + Land Registry
- Lawyer (optional but recommended)
- Mortgage arrangement fees (if applicable)
- Non-resident surcharge notes

Data: static tax rates (correct as of 2025). No external API required.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class CostCalcRequest(BaseModel):
    purchase_price: float
    is_new_build: bool = False
    buyer_type: str = "resident"   # "resident" | "non_resident" | "company"
    region: str = "catalonia"      # "catalonia" | "madrid" | "valencia" | "other"
    mortgage_amount: float | None = None
    include_lawyer: bool = True


class CostLine(BaseModel):
    label: str
    label_zh: str
    amount: float
    rate_pct: float | None = None
    note: str = ""
    note_zh: str = ""


class CostCalcResponse(BaseModel):
    purchase_price: float
    lines: list[CostLine]
    subtotal_taxes: float
    subtotal_services: float
    total_costs: float
    total_pct_of_price: float
    minimum_cash_required: float  # down_payment (price - mortgage) + total_costs
    warnings: list[str]
    warnings_zh: list[str]


# ITP rates by region (resale property transfer tax)
_ITP_RATES = {
    "catalonia": 0.10,
    "madrid":    0.06,
    "valencia":  0.10,
    "other":     0.08,
}

# AJD rate on new builds (stamp duty on mortgage deed)
_AJD_RATES = {
    "catalonia": 0.015,
    "madrid":    0.0075,
    "valencia":  0.015,
    "other":     0.010,
}


@router.post("/cost-calculator", response_model=CostCalcResponse)
async def calculate_costs(req: CostCalcRequest) -> CostCalcResponse:
    if req.purchase_price <= 0:
        raise HTTPException(status_code=422, detail="purchase_price must be positive")
    if req.mortgage_amount and req.mortgage_amount > req.purchase_price:
        raise HTTPException(status_code=422, detail="mortgage_amount cannot exceed purchase_price")

    price = req.purchase_price
    lines: list[CostLine] = []
    warnings: list[str] = []
    warnings_zh: list[str] = []

    if req.is_new_build:
        # New build: VAT (21% commercial, 10% residential) + AJD
        vat_rate = 0.10
        vat = price * vat_rate
        lines.append(CostLine(
            label="VAT (IVA) — new build",
            label_zh="增值税（IVA）— 新建房",
            amount=vat,
            rate_pct=vat_rate * 100,
            note="10% residential rate. 21% applies to commercial or parking-only purchases.",
            note_zh="住宅税率10%。商业或独立车位适用21%。",
        ))
        ajd_rate = _AJD_RATES.get(req.region, _AJD_RATES["other"])
        ajd = price * ajd_rate
        lines.append(CostLine(
            label=f"AJD stamp duty — new build ({req.region.title()})",
            label_zh=f"印花税（AJD）— {req.region}",
            amount=ajd,
            rate_pct=round(ajd_rate * 100, 2),
            note="Actos Jurídicos Documentados — on the purchase deed.",
            note_zh="法律文件印花税 — 适用于购房公证书。",
        ))
    else:
        # Resale: ITP
        if req.region == "catalonia":
            itp, effective_rate_pct = _calc_itp_catalonia(price)
            lines.append(CostLine(
                label="ITP transfer tax — Catalonia (progressive 10/11/12%)",
                label_zh="产权转让税（ITP）— 加泰罗尼亚（累进税率10/11/12%）",
                amount=itp,
                rate_pct=round(effective_rate_pct, 2),
                note="Progressive rate: 10% up to €600k, 11% €600k–€1M, 12% above €1M.",
                note_zh="累进税率：60万以内10%，60–100万11%，100万以上12%。",
            ))
        else:
            itp_rate = _ITP_RATES.get(req.region, _ITP_RATES["other"])
            itp = price * itp_rate
            lines.append(CostLine(
                label=f"ITP transfer tax — resale ({req.region.title()})",
                label_zh=f"产权转让税（ITP）— {req.region}",
                amount=itp,
                rate_pct=round(itp_rate * 100, 2),
                note="Impuesto de Transmisiones Patrimoniales. Rate varies by region.",
                note_zh="产权转让税，税率因自治区不同而有所差异。",
            ))

    # Notary fees (sliding scale — approximate)
    notary = _estimate_notary(price)
    lines.append(CostLine(
        label="Notary fees",
        label_zh="公证费",
        amount=notary,
        note="Statutory sliding scale. Estimate only — exact amount confirmed at signing.",
        note_zh="法定阶梯费率，此为估算，实际金额以签约时为准。",
    ))

    # Land Registry (Registro de la Propiedad)
    registry = _estimate_registry(price)
    lines.append(CostLine(
        label="Land Registry (Registro de la Propiedad)",
        label_zh="土地登记费（Registro de la Propiedad）",
        amount=registry,
        note="Registering the title deed. Statutory fee.",
        note_zh="产权证书登记，法定费用。",
    ))

    # Lawyer (recommended, not mandatory)
    if req.include_lawyer:
        lawyer = max(1500.0, price * 0.01)
        lines.append(CostLine(
            label="Independent lawyer (recommended)",
            label_zh="独立律师费（强烈建议）",
            amount=lawyer,
            rate_pct=1.0,
            note="Not legally required but strongly recommended for foreign buyers. Reviews title, debts, permits.",
            note_zh="法律上非强制，但外籍买家强烈建议聘请。核查产权清晰、债务及许可证情况。",
        ))
        warnings.append(
            "Foreign buyers: always hire an independent lawyer who works for YOU, not the agent or developer. "
            "Cost is €1,000–€3,000 and could save tens of thousands."
        )
        warnings_zh.append(
            "外籍买家：务必聘请代表您自身利益的独立律师（而非中介或开发商的律师）。"
            "费用约 €1,000–€3,000，可帮您避免潜在的重大损失。"
        )

    # Mortgage arrangement costs (if applicable)
    if req.mortgage_amount and req.mortgage_amount > 0:
        appraisal = 400.0
        lines.append(CostLine(
            label="Property appraisal (tasación)",
            label_zh="房产评估费（tasación）",
            amount=appraisal,
            note="Required by Spanish banks before granting a mortgage. Typically €300–€600.",
            note_zh="西班牙银行批贷前的强制房产评估，通常 €300–€600。",
        ))
        # Since 2019, banks pay AJD on mortgage deeds — buyers pay notary/registry for mortgage
        mortgage_notary = _estimate_notary(req.mortgage_amount) * 0.4
        lines.append(CostLine(
            label="Mortgage deed notary + registry",
            label_zh="贷款公证及登记费",
            amount=mortgage_notary,
            note="Notary and registry for the mortgage deed (buyer's portion). Bank pays AJD since 2019.",
            note_zh="贷款公证书的公证及登记费（买家部分）。2019年起印花税由银行承担。",
        ))

    # Non-resident notes
    if req.buyer_type == "non_resident":
        warnings.append(
            "Non-residents: you will need an NIE (tax ID) before signing. "
            "Also consider annual IRNR tax (non-resident income tax) if you don't rent the property — "
            "approximately 0.2% of cadastral value per year (EU residents: 1.1% imputed income × 19% tax rate), "
            "due even if the flat is empty."
        )
        warnings_zh.append(
            "非居民买家：签约前须办理NIE（税务识别号）。"
            "若房产不出租，每年仍需缴纳IRNR非居民所得税，"
            "欧盟居民约为地籍估值的0.2%（1.1%推算收入 × 19%税率），即便房屋空置也须申报。"
        )

    tax_labels = {"ITP", "AJD", "VAT", "IVA"}
    taxes = sum(l.amount for l in lines if any(t in l.label for t in tax_labels))
    services = sum(l.amount for l in lines) - taxes
    total = taxes + services
    total_pct = round(total / price * 100, 1)
    down_payment = (price - req.mortgage_amount) if req.mortgage_amount else price
    min_cash = down_payment + total

    return CostCalcResponse(
        purchase_price=price,
        lines=lines,
        subtotal_taxes=round(taxes),
        subtotal_services=round(services),
        total_costs=round(total),
        total_pct_of_price=total_pct,
        minimum_cash_required=round(min_cash),
        warnings=warnings,
        warnings_zh=warnings_zh,
    )


def _calc_itp_catalonia(price: float) -> tuple[float, float]:
    """Returns (tax_amount, effective_rate_pct) for Catalonia progressive ITP.
    Brackets per Decreto Ley 5/2025 (effective June 27, 2025):
      ≤€600k: 10% | €600k–€900k: 11% | €900k–€1.5M: 12% | >€1.5M: 13%
    """
    if price <= 600_000:
        tax = price * 0.10
    elif price <= 900_000:
        tax = 60_000 + (price - 600_000) * 0.11
    elif price <= 1_500_000:
        tax = 60_000 + 33_000 + (price - 900_000) * 0.12
    else:
        tax = 60_000 + 33_000 + 72_000 + (price - 1_500_000) * 0.13
    return tax, round(tax / price * 100, 2)


def _estimate_notary(price: float) -> float:
    """Spanish notary fee sliding scale (Royal Decree 1426/1989, updated)."""
    if price <= 6_010:     return 90.15
    if price <= 30_050:    return 90.15 + (price - 6_010)    * 0.0045
    if price <= 60_101:    return 198.18 + (price - 30_050)  * 0.00150
    if price <= 150_253:   return 243.25 + (price - 60_101)  * 0.00100
    if price <= 601_012:   return 333.41 + (price - 150_253) * 0.00050
    return 558.79 + (price - 601_012) * 0.00030


def _estimate_registry(price: float) -> float:
    """Land Registry fee — roughly 60-70% of notary fee."""
    return round(_estimate_notary(price) * 0.65)
