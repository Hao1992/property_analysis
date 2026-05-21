from pydantic import BaseModel, field_validator
from typing import Optional

from models.user_profile import UserAnswers

_SUPPORTED_CITIES = {"barcelona", "madrid"}


class AnalyzeRequest(BaseModel):
    address: str
    city: str = "barcelona"               # "barcelona" | "madrid"

    @field_validator("city")
    @classmethod
    def normalize_city(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in _SUPPORTED_CITIES:
            raise ValueError(f"Unsupported city '{v}'. Supported: {sorted(_SUPPORTED_CITIES)}")
        return normalized
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
    city: str = "barcelona"               # "barcelona" | "madrid"

    @field_validator("city")
    @classmethod
    def normalize_city_compare(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in _SUPPORTED_CITIES:
            raise ValueError(f"Unsupported city '{v}'.")
        return normalized
