import streamlit as st
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ============================================================
# 1. Models (Diia-style Clean)
# ============================================================

class IncentiveType(str, Enum):
    NATIONAL = "National"
    STATE = "State"
    CITY = "City"
    UTILITY = "Utility"
    LOAN = "Loan"


@dataclass
class BuildingProfile:
    country: str = "DE"
    city: str = "Frankfurt"
    owner_type: str = "homeowner"
    income_level: str = "medium"
    building_type: str = "single_family"
    year_built: int = 1975
    current_heating: str = "gas"
    target_tech: str = "heat_pump_air"
    total_cost: float = 28000.0
    annual_gas_cost: float = 2200.0
    annual_electricity_cost_hp: float = 1100.0


@dataclass
class Incentive:
    id: str
    name: str
    source: IncentiveType
    city: Optional[str] = None
    description: str = ""
    coverage_rate: float = 0.0
    max_amount: float = 0.0

    eligible_owner_types: List[str] = field(default_factory=list)
    eligible_building_types: List[str] = field(default_factory=list)
    eligible_current_heat: List[str] = field(default_factory=list)
    eligible_target_tech: List[str] = field(default_factory=list)
    income_target: Optional[str] = None

    is_loan: bool = False
    interest_rate: Optional[float] = None
    max_loan_share: Optional[float] = None


@dataclass
class IncentiveResult:
    incentive: Incentive
    amount: float


@dataclass
class Installer:
    name: str
    city: str
    supported_tech: List[str]
    rating: float
    reviews: int
    email: str


@dataclass
class Supplier:
    name: str
    tariff: str
    price_kwh: float
    renewable_share: int
    contact: str


@dataclass
class StackedPlan:
    incentives: List[IncentiveResult]
    total: float
    share: float
    remaining: float


# ============================================================
# 2. Calculation Logic
# ============================================================

def matches_profile(
    incentive_item: Incentive,
    profile: BuildingProfile,
) -> bool:
    """Check if a given incentive applies to this building profile."""
    if incentive_item.city and (
        incentive_item.city.lower() != profile.city.lower()
    ):
        return False

    if (
        incentive_item.income_target
        and incentive_item.income_target != profile.income_level
    ):
        return False

    if (
        incentive_item.eligible_owner_types
        and profile.owner_type not in incentive_item.eligible_owner_types
    ):
        return False

    if (
        incentive_item.eligible_building_types
        and profile.building_type not in incentive_item.eligible_building_types
    ):
        return False

    if (
        incentive_item.eligible_current_heat
        and profile.current_heating
        not in incentive_item.eligible_current_heat
    ):
        return False

    if (
        incentive_item.eligible_target_tech
        and profile.target_tech
        not in incentive_item.eligible_target_tech
    ):
        return False

    return True


def calculate_amount(
    incentive_item: Incentive,
    profile: BuildingProfile,
) -> float:
    """Grant amount for a given incentive and building profile."""
    if incentive_item.is_loan:
        return 0.0

    amount = profile.total_cost * incentive_item.coverage_rate

    if incentive_item.max_amount:
        amount = min(amount, incentive_item.max_amount)

    return amount


def build_stack(
    profile: BuildingProfile,
    all_incentives: List[Incentive],
) -> StackedPlan:
    """Create stacked incentive plan for the profile."""
    applied_results: List[IncentiveResult] = []

    for incentive_item in all_incentives:
        if matches_profile(incentive_item, profile):
            amount = calculate_amount(incentive_item, profile)
            if amount > 0:
                applied_results.append(
                    IncentiveResult(incentive=incentive_item, amount=amount)
                )

    total_grants = sum(result.amount for result in applied_results)
    total_grants = min(total_grants, profile.total_cost)

    share = total_grants / profile.total_cost if profile.total_cost > 0 else 0.0
    remaining_cost = profile.total_cost - total_grants

    return StackedPlan(
        incentives=applied_results,
        total=total_grants,
        share=share,
        remaining=remaining_cost,
    )


# ============================================================
# 3. Frankfurt Incentives
# ============================================================

def incentives_frankfurt() -> List[Incentive]:
    """Static list of incentives for Frankfurt."""
    return [
        Incentive(
            id="BEG_WG",
            name="Federal BEG WG Heat Pump Grant",
            source=IncentiveType.NATIONAL,
            coverage_rate=0.30,
            max_amount=18000,
            eligible_owner_types=["homeowner"],
            eligible_building_types=["single_family"],
            eligible_current_heat=["gas", "oil"],
            eligible_target_tech=[
                "heat_pump_air",
                "heat_pump_ground",
            ],
        ),
        Incentive(
            id="HESSEN_BONUS",
            name="Hessen Heat Pump Bonus",
            source=IncentiveType.STATE,
            coverage_rate=0.10,
            max_amount=4000,
            eligible_owner_types=["homeowner"],
            eligible_current_heat=["gas"],
            eligible_target_tech=["heat_pump_air"],
        ),
        Incentive(
            id="FRANKFURT_TOPUP",
            name="Frankfurt Climate Upgrade Grant",
            source=IncentiveType.CITY,
            coverage_rate=0.08,
            max_amount=3000,
            city="Frankfurt",
            eligible_owner_types=["homeowner"],
            eligible_target_tech=["heat_pump_air"],
        ),
        Incentive(
            id="MAINOVA_GREEN",
            name="Mainova Green Heat Rebate",
            source=IncentiveType.UTILITY,
            max_amount=500,
            city="Frankfurt",
            eligible_owner_types=["homeowner"],
            eligible_current_heat=["gas"],
        ),
        Incentive(
            id="KFW_LOAN",
            name="KfW Green Heat Loan (0.9%)",
            source=IncentiveType.LOAN,
            is_loan=True,
            interest_rate=0.009,
            max_loan_share=0.80,
        ),
    ]


# ============================================================
# 4. Installers + Suppliers
# ============================================================

def installers_ffm() -> List[Installer]:
    """Predefined list of certified installers in Frankfurt."""
    return [
        Installer(
            name="HeatPump Frankfurt GmbH",
            city="Frankfurt",
            supported_tech=["heat_pump_air"],
            rating=4.9,
            reviews=211,
            email="service@hp-ffm.de",
        ),
        Installer(
            name="MainHeat Solutions",
            city="Frankfurt",
            supported_tech=["heat_pump_air", "heat_pump_ground"],
            rating=4.7,
            reviews=143,
            email="contact@mainheat.de",
        ),
        Installer(
            name="Green Therm Frankfurt",
            city="Frankfurt",
            supported_tech=["heat_pump_air"],
            rating=4.6,
            reviews=94,
            email="hello@greentherm.de",
        ),
    ]


def suppliers_ffm() -> List[Supplier]:
    """Predefined list of green electricity suppliers."""
    return [
        Supplier(
            name="Mainova GreenHeat",
            tariff="100% renewable",
            price_kwh=0.286,
            renewable_share=100,
            contact="mainova.de",
        ),
        Supplier(
            name="Naturstrom AG",
            tariff="Premium Ökostrom",
            price_kwh=0.295,
            renewable_share=100,
            contact="naturstrom.de",
        ),
        Supplier(
            name="E.ON Ökostrom",
            tariff="Green electricity",
            price_kwh=0.299,
            renewable_share=100,
            contact="eon.de",
        ),
    ]


# ============================================================
# 5. Additional Savings Calculations
# ============================================================

def calc_tax_savings(profile: BuildingProfile) -> float:
    """Environmental tax savings from avoided fossil CO₂ price."""
    co2_price = 45.0  # €/ton (2025 Germany)
    gas_emission_factor = 0.202  # ton CO₂ / MWh
    gas_kwh = profile.annual_gas_cost / 0.12  # assume €0.12/kWh
    tons_co2 = gas_kwh * gas_emission_factor / 1000.0
    return tons_co2 * co2_price


def calc_energy_savings(profile: BuildingProfile) -> float:
    """Annual fuel bill savings."""
    return profile.annual_gas_cost - profile.annual_electricity_cost_hp


def calc_co2_impact(profile: BuildingProfile) -> float:
    """Annual CO₂ avoided (tons)."""
    gas_emission_factor = 0.202  # ton CO₂ per MWh
    gas_kwh = profile.annual_gas_cost / 0.12
    tons = gas_kwh * gas_emission_factor / 1000.0
    return tons


def calc_green_loan_savings(profile: BuildingProfile) -> float:
    """Interest savings from using subsidised green loan."""
    normal_rate = 0.05
    green_rate = 0.009
    loan_amount = profile.total_cost * 0.80
    years = 10
    normal_cost = loan_amount * normal_rate * years
    green_cost = loan_amount * green_rate * years
    return normal_cost - green_cost


# ============================================================
# 6. Streamlit UI (Diia-style)
# ============================================================

st.set_page_config(
    page_title="HeatShift — Frankfurt",
    page_icon="🔥",
    layout="centered",
)

st.title("🔥 HeatShift Frankfurt")
st.caption("Renewable Heating. Made simple.")

st.header("🏠 Your Building")

year_built = st.slider("Year built", 1900, 2023, 1975)
current_heating = st.selectbox(
    "Current heating",
    ["gas", "oil", "electric"],
)
target_tech = st.selectbox(
    "Target technology",
    ["heat_pump_air", "heat_pump_ground"],
)
total_project_cost = st.number_input(
    "Total project cost (€)",
    min_value=5000,
    max_value=60000,
    value=28000,
    step=1000,
)
income_level = st.selectbox(
    "Income level",
    ["low", "medium", "high"],
)
annual_gas_cost = st.number_input(
    "Your annual gas/oil bill (€)",
    min_value=500,
    max_value=5000,
    value=2200,
    step=100,
)
annual_hp_cost = st.number_input(
    "Expected annual heat pump electricity cost (€)",
    min_value=300,
    max_value=3000,
    value=1100,
    step=50,
)

user_profile = BuildingProfile(
    year_built=year_built,
    current_heating=current_heating,
    target_tech=target_tech,
    total_cost=total_project_cost,
    income_level=income_level,
    annual_gas_cost=annual_gas_cost,
    annual_electricity_cost_hp=annual_hp_cost,
)

st.markdown("---")

# ============================================================
# Compute everything
# ============================================================

available_incentives = incentives_frankfurt()
stacked_plan = build_stack(user_profile, available_incentives)

tax_savings = calc_tax_savings(user_profile)
energy_savings = calc_energy_savings(user_profile)
co2_saved = calc_co2_impact(user_profile)
loan_savings = calc_green_loan_savings(user_profile)

total_annual_benefit = tax_savings + energy_savings

# ============================================================
# 7. UI Output
# ============================================================

st.header("💰 Financial Benefits")

col1, col2, col3 = st.columns(3)
col1.metric(
    "Annual savings",
    f"€{total_annual_benefit:,.0f}",
)
col2.metric(
    "Energy bill savings",
    f"€{energy_savings:,.0f}",
)
col3.metric(
    "Env. tax savings",
    f"€{tax_savings:,.0f}",
)

col4, col5 = st.columns(2)
col4.metric(
    "CO₂ avoided / year",
    f"{co2_saved:.2f} t",
)
col5.metric(
    "Loan interest saved",
    f"€{loan_savings:,.0f}",
)

st.markdown("---")

st.header("🎁 Incentives You Receive")

if stacked_plan.incentives:
    for result in stacked_plan.incentives:
        st.write(
            f"**{result.incentive.name}** — "
            f"€{result.amount:,.0f}"
        )
else:
    st.info(
        "No matching incentives found for this profile. "
        "Try adjusting inputs."
    )

st.success(
    "Total grants: **€{total:,.0f}** "
    "({share:.0%} of the project)\n"
    "You pay: **€{remaining:,.0f}**".format(
        total=stacked_plan.total,
        share=stacked_plan.share,
        remaining=stacked_plan.remaining,
    )
)

st.markdown("---")

st.header("🛠 Certified Installers")

for installer in installers_ffm():
    st.write(
        "**{name}** — ⭐ {rating} "
        "({reviews} reviews) — {email}".format(
            name=installer.name,
            rating=installer.rating,
            reviews=installer.reviews,
            email=installer.email,
        )
    )

st.markdown("---")

st.header("⚡ Licensed Green Energy Suppliers")

for supplier in suppliers_ffm():
    st.write(
        "**{name}** — {tariff}\n"
        "Price: €{price:.3f}/kWh | "
        "Renewable share: {share}%\n"
        "🌐 {contact}".format(
            name=supplier.name,
            tariff=supplier.tariff,
            price=supplier.price_kwh,
            share=supplier.renewable_share,
            contact=supplier.contact,
        )
    )

st.markdown("---")
st.caption("HeatShift — Full Renewable Heating Transition Assistant")