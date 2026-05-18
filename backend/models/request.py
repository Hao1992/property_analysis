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
    # Optional override when Catastro data is missing or wrong.
    # Typically found on Idealista listings as "año de construcción".
    year_built: Optional[int] = None


class CompareRequest(BaseModel):
    addresses: list[str]
    listing_prices: Optional[list[float]] = None
    buyer_profile: str = "balanced"
