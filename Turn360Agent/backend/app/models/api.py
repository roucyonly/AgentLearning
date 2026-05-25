from pydantic import BaseModel, Field

from app.services.decision.pre_opening import PreOpeningEvaluationInput
from app.services.finance.calculator import PreOpeningFinanceInput


class PreOpeningFinanceRequest(BaseModel):
    area_sqm: float | None = None
    monthly_rent: float = Field(gt=0)
    rent_payment_months: int = Field(default=3, ge=1)
    deposit: float = Field(default=0, ge=0)
    transfer_fee: float = Field(default=0, ge=0)
    franchise_or_training_fee: float = Field(default=0, ge=0)
    decoration_and_ads: float = Field(default=0, ge=0)
    equipment: float = Field(default=0, ge=0)
    first_batch_material: float = Field(default=0, ge=0)
    monthly_labor: float = Field(ge=0)
    monthly_utilities: float = Field(ge=0)
    monthly_fixed_operation_cost: float = Field(default=0, ge=0)
    monthly_campaign_cost: float = Field(default=0, ge=0)
    gross_margin_rate: float = Field(gt=0)
    effective_gross_margin_rate: float | None = None
    estimated_average_ticket: float = Field(gt=0)
    target_payback_months: int = Field(default=12, ge=1)
    cash_available: float | None = None
    debt_monthly_payment: float = Field(default=0, ge=0)

    def to_domain(self) -> PreOpeningFinanceInput:
        return PreOpeningFinanceInput(**self.model_dump())


class LocationSignal(BaseModel):
    city: str
    district: str | None = None
    address_text: str
    target_customer_flow_30min: int | None = None
    comparable_store_orders_per_day: int | None = None
    evidence_level: str = "mock"


class CategorySignal(BaseModel):
    category_name: str
    demand_type: str | None = None
    major_type: str | None = None


class PreOpeningEvaluationRequest(BaseModel):
    session_id: str = "demo"
    finance: PreOpeningFinanceRequest
    location: LocationSignal
    category: CategorySignal

    def to_domain(self) -> PreOpeningEvaluationInput:
        return PreOpeningEvaluationInput(
            session_id=self.session_id,
            finance=self.finance.to_domain(),
            location=self.location.model_dump(),
            category=self.category.model_dump(),
        )

