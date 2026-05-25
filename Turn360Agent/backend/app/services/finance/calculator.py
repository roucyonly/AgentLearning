from dataclasses import asdict, dataclass, field
from math import isfinite


@dataclass(frozen=True)
class PreOpeningFinanceInput:
    monthly_rent: float
    monthly_labor: float
    monthly_utilities: float
    gross_margin_rate: float
    estimated_average_ticket: float
    area_sqm: float | None = None
    rent_payment_months: int = 3
    deposit: float = 0
    transfer_fee: float = 0
    franchise_or_training_fee: float = 0
    decoration_and_ads: float = 0
    equipment: float = 0
    first_batch_material: float = 0
    monthly_fixed_operation_cost: float = 0
    monthly_campaign_cost: float = 0
    effective_gross_margin_rate: float | None = None
    target_payback_months: int = 12
    cash_available: float | None = None
    debt_monthly_payment: float = 0


@dataclass(frozen=True)
class PreOpeningFinanceResult:
    mode: str
    build_cost: float
    monthly_fixed_cost: float
    daily_fixed_cost: float
    effective_gross_margin_rate: float
    daily_breakeven: float
    target_daily_revenue: float
    target_order_count: float
    minimum_cash_reserve_3m: float
    minimum_cash_reserve_6m: float
    cash_gap_3m: float | None
    cash_gap_6m: float | None
    finance_status: str
    pre_opening_verdict: str
    risk_flags: list[str] = field(default_factory=list)
    positive_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_rate(rate: float) -> float:
    if rate <= 0:
        raise ValueError("gross margin rate must be positive")
    value = rate / 100 if rate > 1 else rate
    if value <= 0 or value >= 1:
        raise ValueError("gross margin rate must be between 0 and 1, or 0 and 100 percent")
    return value


def round_money(value: float) -> float:
    if not isfinite(value):
        raise ValueError("calculation produced a non-finite number")
    return round(value + 1e-9, 2)


def calculate_pre_opening_finance(payload: PreOpeningFinanceInput) -> PreOpeningFinanceResult:
    margin = normalize_rate(payload.effective_gross_margin_rate or payload.gross_margin_rate)
    if payload.estimated_average_ticket <= 0:
        raise ValueError("estimated average ticket must be positive")
    if payload.target_payback_months <= 0:
        raise ValueError("target payback months must be positive")

    build_cost = (
        payload.monthly_rent * payload.rent_payment_months
        + payload.deposit
        + payload.transfer_fee
        + payload.franchise_or_training_fee
        + payload.decoration_and_ads
        + payload.equipment
        + payload.first_batch_material
    )
    monthly_fixed_cost = (
        payload.monthly_rent
        + payload.monthly_labor
        + payload.monthly_utilities
        + payload.monthly_fixed_operation_cost
    )
    daily_fixed_cost = monthly_fixed_cost / 30
    daily_breakeven = daily_fixed_cost / margin
    target_daily_revenue = (
        monthly_fixed_cost
        + build_cost / payload.target_payback_months
        + payload.monthly_campaign_cost
    ) / margin / 30
    target_order_count = target_daily_revenue / payload.estimated_average_ticket
    minimum_cash_reserve_3m = build_cost + monthly_fixed_cost * 3 + payload.debt_monthly_payment * 3
    minimum_cash_reserve_6m = build_cost + monthly_fixed_cost * 6 + payload.debt_monthly_payment * 6
    cash_gap_3m = None if payload.cash_available is None else payload.cash_available - minimum_cash_reserve_3m
    cash_gap_6m = None if payload.cash_available is None else payload.cash_available - minimum_cash_reserve_6m

    risk_flags: list[str] = []
    positive_flags: list[str] = []

    if margin < 0.35:
        risk_flags.append("effective_margin_below_35_percent")
    if payload.cash_available is None:
        risk_flags.append("cash_available_missing")
    elif payload.cash_available < build_cost:
        risk_flags.append("cash_below_build_cost")
    elif payload.cash_available < minimum_cash_reserve_3m:
        risk_flags.append("cash_below_3m_reserve")
    else:
        positive_flags.append("cash_covers_build_cost_and_3m_fixed_cost")

    if target_order_count > 180:
        risk_flags.append("target_order_count_extremely_high")
    elif target_order_count > 100:
        risk_flags.append("target_order_count_needs_strong_location_evidence")
    else:
        positive_flags.append("target_order_count_not_extreme")

    if payload.debt_monthly_payment > 0:
        risk_flags.append("has_monthly_debt_payment")
    if build_cost <= 150000:
        positive_flags.append("build_cost_light_or_moderate")

    if "cash_below_build_cost" in risk_flags or margin < 0.25:
        status = "finance_do_not_open"
        verdict = "do_not_open"
    elif "cash_below_3m_reserve" in risk_flags or "target_order_count_extremely_high" in risk_flags:
        status = "finance_do_not_open"
        verdict = "do_not_open"
    elif "cash_available_missing" in risk_flags or "target_order_count_needs_strong_location_evidence" in risk_flags:
        status = "finance_validate_first"
        verdict = "validate_first"
    else:
        status = "finance_can_open"
        verdict = "can_open"

    return PreOpeningFinanceResult(
        mode="pre_opening",
        build_cost=round_money(build_cost),
        monthly_fixed_cost=round_money(monthly_fixed_cost),
        daily_fixed_cost=round_money(daily_fixed_cost),
        effective_gross_margin_rate=round(margin, 4),
        daily_breakeven=round_money(daily_breakeven),
        target_daily_revenue=round_money(target_daily_revenue),
        target_order_count=round_money(target_order_count),
        minimum_cash_reserve_3m=round_money(minimum_cash_reserve_3m),
        minimum_cash_reserve_6m=round_money(minimum_cash_reserve_6m),
        cash_gap_3m=None if cash_gap_3m is None else round_money(cash_gap_3m),
        cash_gap_6m=None if cash_gap_6m is None else round_money(cash_gap_6m),
        finance_status=status,
        pre_opening_verdict=verdict,
        risk_flags=risk_flags,
        positive_flags=positive_flags,
    )

