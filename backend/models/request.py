from pydantic import BaseModel
from typing import Optional

from models.user_profile import UserAnswers


class AnalyzeRequest(BaseModel):
    address: str
    listing_price: Optional[float] = None
    # Legacy profile string (kept for /compare backward compat)
    buyer_profile: str = "balanced"
    # Questionnaire answers — override buyer_profile when provided
    user_answers: Optional[UserAnswers] = None
    # Optional overrides when Catastro data is missing or wrong.
    # Typically found on Idealista listings.
    year_built: Optional[int] = None
    floor: Optional[int] = None            # 0 = ground, 1 = first, etc. Affects noise score.
    surface_m2: Optional[float] = None     # Advertised surface area from listing
    energy_cert: Optional[str] = None      # A–G energy rating from listing
    condition: Optional[str] = None        # "renovated" | "good" | "needs_work"
    has_parking: Optional[bool] = None
    has_terrace: Optional[bool] = None
    has_views:   Optional[bool] = None
    language: str = "en"                   # "en" | "zh" — report output language


class CompareRequest(BaseModel):
    addresses: list[str]
    listing_prices: Optional[list[float]] = None
    buyer_profile: str = "balanced"
