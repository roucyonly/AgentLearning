from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryProfile:
    name: str
    major_type: str
    demand_type: str
    operation_complexity: str
    default_gross_margin_rate: float
    notes: list[str]


CATALOG: dict[str, CategoryProfile] = {
    "咖啡": CategoryProfile(
        name="咖啡",
        major_type="drinks",
        demand_type="light_social",
        operation_complexity="medium_high",
        default_gross_margin_rate=0.55,
        notes=["品牌、便利性、复购和位置强相关。"],
    ),
    "泡菜": CategoryProfile(
        name="泡菜",
        major_type="snack_or_side_dish",
        demand_type="scene_dependent",
        operation_complexity="medium",
        default_gross_margin_rate=0.60,
        notes=["个人喜好不等于需求，需要验证佐餐、社区复购或外卖场景。"],
    ),
    "融合菜": CategoryProfile(
        name="融合菜",
        major_type="meal",
        demand_type="social_or_light_social",
        operation_complexity="high",
        default_gross_margin_rate=0.60,
        notes=["大面积融合菜高度依赖运营、内容种草、服务和复购。"],
    ),
    "米饭快餐": CategoryProfile(
        name="米饭快餐",
        major_type="meal",
        demand_type="rigid",
        operation_complexity="medium",
        default_gross_margin_rate=0.55,
        notes=["刚需强，但选址、出餐效率和午晚高峰承接能力关键。"],
    ),
}


def get_category_profile(category_name: str) -> CategoryProfile:
    return CATALOG.get(
        category_name,
        CategoryProfile(
            name=category_name,
            major_type="unknown",
            demand_type="unknown_need_confirm",
            operation_complexity="unknown",
            default_gross_margin_rate=0.55,
            notes=["品类未命中基础库，需要补充地域和需求证据。"],
        ),
    )

