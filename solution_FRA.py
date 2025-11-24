import streamlit as st
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import pandas as pd

# ============================================================
# 1. Models
# ============================================================

class IncentiveType(str, Enum):
    NATIONAL = "National"
    STATE = "State"
    CITY = "City"
    UTILITY = "Utility"
    LOAN = "Loan"


@dataclass
class BuildingProfile:
    country: str
    city: str
    owner_type: str = "homeowner"
    income_level: str = "medium"
    building_type: str = "single_family"
    year_built: int = 1975
    current_heating: str = "gas"
    target_tech: str = "heat_pump_air"
    total_cost: float = 28000.0
    annual_current_cost: float = 2200.0
    annual_hp_cost: float = 1100.0


@dataclass
class Incentive:
    id: str
    name: str
    source: IncentiveType
    country: str
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
    country: str
    city: str
    supported_tech: List[str]
    rating: float
    reviews: int
    email: str


@dataclass
class Supplier:
    name: str
    country: str
    city: str
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
# 2. Incentive logic
# ============================================================

def match_incentive(i: Incentive, p: BuildingProfile) -> bool:
    if i.country != p.country:
        return False
    if i.city and i.city.lower() != p.city.lower():
        return False
    if i.income_target and i.income_target != p.income_level:
        return False
    if i.eligible_owner_types and p.owner_type not in i.eligible_owner_types:
        return False
    if i.eligible_building_types and p.building_type not in i.eligible_building_types:
        return False
    if i.eligible_current_heat and p.current_heating not in i.eligible_current_heat:
        return False
    if i.eligible_target_tech and p.target_tech not in i.eligible_target_tech:
        return False
    return True


def calc_incentive_amount(i: Incentive, p: BuildingProfile) -> float:
    if i.is_loan:
        return 0.0
    value = p.total_cost * i.coverage_rate
    if i.max_amount:
        value = min(value, i.max_amount)
    return value


def build_stacked_plan(p: BuildingProfile, incentives: List[Incentive]) -> StackedPlan:
    applied: List[IncentiveResult] = []
    for inc in incentives:
        if match_incentive(inc, p):
            amount = calc_incentive_amount(inc, p)
            if amount > 0:
                applied.append(IncentiveResult(inc, amount))

    total = sum(r.amount for r in applied)
    total = min(total, p.total_cost)
    share = total / p.total_cost if p.total_cost > 0 else 0
    remaining = p.total_cost - total

    return StackedPlan(applied, total, share, remaining)


# ============================================================
# 3. Static data: incentives, installers, suppliers (multi-country)
# ============================================================

def incentives_multi(country: str, city: str) -> List[Incentive]:
    """Mock incentives for several countries (demo)."""

    inc: List[Incentive] = []

    if country == "DE":
        inc.extend([
            Incentive(
                id="DE_BEG_WG",
                name="Federal BEG WG Heat Pump Grant",
                source=IncentiveType.NATIONAL,
                country="DE",
                coverage_rate=0.30,
                max_amount=18000,
                eligible_owner_types=["homeowner"],
                eligible_building_types=["single_family"],
                eligible_current_heat=["gas", "oil"],
                eligible_target_tech=["heat_pump_air", "heat_pump_ground"],
            ),
            Incentive(
                id="DE_HESSEN",
                name="Hessen Heat Pump Bonus",
                source=IncentiveType.STATE,
                country="DE",
                coverage_rate=0.10,
                max_amount=4000,
                eligible_owner_types=["homeowner"],
                eligible_current_heat=["gas"],
                eligible_target_tech=["heat_pump_air"],
            ),
            Incentive(
                id="DE_KFW",
                name="KfW Green Heat Loan (0.9%)",
                source=IncentiveType.LOAN,
                country="DE",
                is_loan=True,
                interest_rate=0.009,
                max_loan_share=0.80,
            ),
        ])
        if city.lower() == "frankfurt":
            inc.extend([
                Incentive(
                    id="DE_FFM_TOPUP",
                    name="Frankfurt Climate Upgrade Grant",
                    source=IncentiveType.CITY,
                    country="DE",
                    city="Frankfurt",
                    coverage_rate=0.08,
                    max_amount=3000,
                    eligible_owner_types=["homeowner"],
                    eligible_target_tech=["heat_pump_air"],
                ),
                Incentive(
                    id="DE_MAINOVA",
                    name="Mainova Green Heat Rebate",
                    source=IncentiveType.UTILITY,
                    country="DE",
                    city="Frankfurt",
                    max_amount=500,
                    eligible_owner_types=["homeowner"],
                    eligible_current_heat=["gas"],
                ),
            ])

    elif country == "AT":  # Austria (demo)
        inc.extend([
            Incentive(
                id="AT_NATIONAL",
                name="Austria Renewable Heating Bonus",
                source=IncentiveType.NATIONAL,
                country="AT",
                coverage_rate=0.25,
                max_amount=14000,
                eligible_owner_types=["homeowner"],
                eligible_target_tech=["heat_pump_air", "heat_pump_ground"],
            ),
            Incentive(
                id="AT_CITY",
                name=f"{city} Local Heat Pump Grant",
                source=IncentiveType.CITY,
                country="AT",
                city=city,
                coverage_rate=0.10,
                max_amount=4000,
                eligible_owner_types=["homeowner"],
            ),
        ])

    elif country == "PL":  # Poland (demo)
        inc.extend([
            Incentive(
                id="PL_CLEAN_AIR",
                name="Poland Clean Air Heat Pump Program",
                source=IncentiveType.NATIONAL,
                country="PL",
                coverage_rate=0.30,
                max_amount=12000,
                eligible_owner_types=["homeowner"],
                eligible_current_heat=["coal", "gas", "oil"],
                eligible_target_tech=["heat_pump_air", "heat_pump_ground"],
            ),
        ])

    else:  # generic EU demo
        inc.extend([
            Incentive(
                id="EU_DEMO",
                name="EU Demo Renovation Grant",
                source=IncentiveType.NATIONAL,
                country=country,
                coverage_rate=0.20,
                max_amount=10000,
                eligible_owner_types=["homeowner"],
            ),
        ])

    return inc


def installers_multi(country: str, city: str) -> List[Installer]:
    data = [
        Installer("HeatPump Frankfurt GmbH", "DE", "Frankfurt",
                  ["heat_pump_air"], 4.9, 211, "service@hp-ffm.de"),
        Installer("MainHeat Solutions", "DE", "Frankfurt",
                  ["heat_pump_air", "heat_pump_ground"], 4.7, 143, "contact@mainheat.de"),
        Installer("Green Therm Frankfurt", "DE", "Frankfurt",
                  ["heat_pump_air"], 4.6, 94, "hello@greentherm.de"),

        Installer("Vienna Green Heating GmbH", "AT", "Vienna",
                  ["heat_pump_air", "heat_pump_ground"], 4.8, 175, "office@vgh.at"),
        Installer("Warsaw Heat Experts", "PL", "Warsaw",
                  ["heat_pump_air"], 4.5, 98, "info@whe.pl"),

        Installer("EU Demo Heating", "EU", "Capital",
                  ["heat_pump_air"], 4.3, 35, "hello@eudemo.eu"),
    ]
    return [i for i in data if i.country == country and i.city.lower() == city.lower()]


def suppliers_multi(country: str, city: str) -> List[Supplier]:
    data = [
        Supplier("Mainova GreenHeat", "100% renewable electricity", 0.286, 100,
                 "mainova.de", country="DE", city="Frankfurt"),
        Supplier("Naturstrom AG", "Premium Ökostrom", 0.295, 100,
                 "naturstrom.de", country="DE", city="Frankfurt"),

        Supplier("Wien Energie Naturstrom", "100% Ökostrom", 0.290, 100,
                 "wienenergie.at", country="AT", city="Vienna"),
        Supplier("Polenergia Green", "Green electricity tariff", 0.280, 100,
                 "polenergia.pl", country="PL", city="Warsaw"),

        Supplier("EU Green Power", "Generic demo green tariff", 0.300, 100,
                 "eugreen.eu", country="EU", city="Capital"),
    ]
    res = [s for s in data if s.country == country and s.city.lower() == city.lower()]
    if not res:
        # Fallback generic supplier per country
        res = [Supplier(
            name=f"{country} Green Supplier",
            country=country,
            city=city,
            tariff="Renewable mix (demo)",
            price_kwh=0.30,
            renewable_share=100,
            contact="example.com",
        )]
    return res


# ============================================================
# 4. Additional calculations (energy, CO₂, taxes, loans)
# ============================================================

def calc_co2_profile(p: BuildingProfile, supplier: Supplier):
    """
    Returns (CO2_before, CO2_after, CO2_saved) in tons/year.
    Very simplified demo.
    """
    # Assume current system based on fossil fuel (gas/oil/coal)
    fossil_price = 0.12      # €/kWh equivalent
    fossil_ef = 0.202        # ton CO2 / MWh
    grid_ef = 0.35           # ton CO2 / MWh for normal grid

    # before: fossil or inefficient electric
    kwh_before = p.annual_current_cost / fossil_price
    co2_before = kwh_before * fossil_ef / 1000

    # after: heat pump on (partly) green electricity
    hp_kwh = p.annual_hp_cost / supplier.price_kwh
    effective_grid_ef = grid_ef * (1 - supplier.renewable_share / 100)
    co2_after = hp_kwh * effective_grid_ef / 1000

    co2_saved = co2_before - co2_after
    return co2_before, max(co2_after, 0), max(co2_saved, 0)


def calc_tax_savings(co2_saved_tons: float) -> float:
    co2_price = 45  # €/ton (illustrative)
    return co2_saved_tons * co2_price


def calc_energy_savings(p: BuildingProfile) -> float:
    return p.annual_current_cost - p.annual_hp_cost


def calc_green_loan_savings(p: BuildingProfile) -> float:
    normal_rate = 0.05
    green_rate = 0.009
    loan_amount = p.total_cost * 0.80
    years = 10
    normal_cost = loan_amount * normal_rate * years
    green_cost = loan_amount * green_rate * years
    return normal_cost - green_cost


# ============================================================
# 5. Streamlit UI
# ============================================================

st.set_page_config(
    page_title="HeatShift — Multi-country",
    page_icon="🔥",
    layout="centered"
)

# Simple “green Diia” styling
st.markdown(
    """
    <style>
    .main {
        background-color: #071b2f;
        color: #f5f7fb;
    }
    .stMetric {
        background-color: #0d253a !important;
        border-radius: 12px;
        padding: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔥 HeatShift")
st.caption("Interactive green heating assistant — multi-country demo.")

# -------- Sidebar: country + basic inputs --------
with st.sidebar:
    st.header("🌍 Location")

    country_name = st.selectbox(
        "Country",
        ["Germany", "Austria", "Poland", "Other EU demo"],
        index=0
    )
    country_code = {"Germany": "DE", "Austria": "AT", "Poland": "PL", "Other EU demo": "EU"}[country_name]

    if country_code == "DE":
        city = st.selectbox("City", ["Frankfurt", "Berlin", "Munich", "Other"], index=0)
    elif country_code == "AT":
        city = st.selectbox("City", ["Vienna", "Graz", "Other"], index=0)
    elif country_code == "PL":
        city = st.selectbox("City", ["Warsaw", "Krakow", "Other"], index=0)
    else:
        city = st.text_input("City", "Capital")

    st.markdown("---")
    st.header("🏠 Building")

    year = st.slider("Year built", 1900, 2023, 1975)
    current_heating_display = st.selectbox("Current heating system", ["Gas / oil", "Electric (old)", "District / other"])
    current_heating_code = {
        "Gas / oil": "gas",
        "Electric (old)": "electric",
        "District / other": "district"
    }[current_heating_display]

    tech_display = st.selectbox("Target technology", ["Air-source heat pump", "Ground-source heat pump (geothermal)"])
    target_tech_code = "heat_pump_air" if "Air" in tech_display else "heat_pump_ground"

    total_cost = st.number_input("Total project cost (€)", 5000, 100000, 30000, step=1000)
    income = st.selectbox("Income level", ["low", "medium", "high"])

    st.markdown("---")
    st.header("💡 Energy costs (per year)")
    current_cost = st.number_input("Current annual heating cost (€)", 500, 8000, 4000, step=100)
    hp_cost = st.number_input("Expected annual heat-pump electricity cost (€)", 200, 6000, 2000, step=100)

    st.markdown("---")

# suppliers & profile
suppliers = suppliers_multi(country_code, city)
supplier_names = [s.name for s in suppliers]
chosen_supplier_name = st.selectbox("Choose certified green electricity supplier", supplier_names)
chosen_supplier = next(s for s in suppliers if s.name == chosen_supplier_name)

profile = BuildingProfile(
    country=country_code,
    city=city,
    year_built=year,
    current_heating=current_heating_code,
    target_tech=target_tech_code,
    total_cost=total_cost,
    income_level=income,
    annual_current_cost=current_cost,
    annual_hp_cost=hp_cost,
)

# Calculations
inc_list = incentives_multi(country_code, city)
stack = build_stacked_plan(profile, inc_list)
co2_before, co2_after, co2_saved = calc_co2_profile(profile, chosen_supplier)
tax_savings = calc_tax_savings(co2_saved)
energy_savings = calc_energy_savings(profile)
loan_savings = calc_green_loan_savings(profile)
total_annual_benefit = energy_savings + tax_savings

# ============================================================
# Tabs for overview / charts / suppliers & installers
# ============================================================

tab_overview, tab_charts, tab_suppliers = st.tabs(["Overview", "Charts", "Suppliers & Installers"])

# -------- Overview tab --------
with tab_overview:
    st.header("💰 Financial & climate benefits")

    col1, col2, col3 = st.columns(3)
    col1.metric("Annual savings", f"€{total_annual_benefit:,.0f}")
    col2.metric("Energy bill savings", f"€{energy_savings:,.0f}")
    col3.metric("CO₂ avoided / year", f"{co2_saved:.2f} t")

    col4, col5 = st.columns(2)
    col4.metric("Environmental tax savings*", f"€{tax_savings:,.0f}")
    col5.metric("Loan interest saved†", f"€{loan_savings:,.0f}")
    st.caption("*Approximate CO₂-price savings.  †Demo vs 5% standard loan over 10 years.")

    st.markdown("---")
    st.header("🎁 Incentives you receive")

    if stack.incentives:
        for r in stack.incentives:
            st.write(f"**{r.incentive.name}** — €{r.amount:,.0f} ({r.incentive.source.value})")
    else:
        st.info("No incentives matched this profile. Try another country/city or heating type.")

    st.success(
        f"Total grants: **€{stack.total:,.0f}** "
        f"({stack.share:.0%} of your project).  "
        f"You pay: **€{stack.remaining:,.0f}**."
    )

# -------- Charts tab --------
with tab_charts:
    st.header("📊 Cost & CO₂ comparison")

    # Cost comparison
    cost_df = pd.DataFrame({
        "Scenario": ["Before (current system)", "After (heat pump)"],
        "Annual cost (€)": [profile.annual_current_cost, profile.annual_hp_cost],
    }).set_index("Scenario")
    st.subheader("Annual heating cost")
    st.bar_chart(cost_df)

    # CO2 comparison
    co2_df = pd.DataFrame({
        "Scenario": ["Before (current system)", "After (heat pump)"],
        "CO₂ (t/year)": [co2_before, co2_after],
    }).set_index("Scenario")
    st.subheader("Annual CO₂ emissions")
    st.bar_chart(co2_df)

    # 10-year cumulative
    years = list(range(1, 11))
    cum_before = [profile.annual_current_cost * y for y in years]
    cum_after = [profile.annual_hp_cost * y for y in years]

    cum_df = pd.DataFrame({
        "Year": years,
        "Current heating (€)": cum_before,
        "Heat pump (€)": cum_after,
    }).set_index("Year")

    st.subheader("Cumulative heating cost over 10 years")
    st.line_chart(cum_df)

# -------- Suppliers & installers tab --------
with tab_suppliers:
    st.header("⚡ Certified green electricity suppliers")

    st.write(f"**Selected supplier:** {chosen_supplier.name}")
    st.write(
        f"- Tariff: {chosen_supplier.tariff}\n"
        f"- Price: €{chosen_supplier.price_kwh:.3f}/kWh\n"
        f"- Renewable share: {chosen_supplier.renewable_share}%\n"
        f"- Website: {chosen_supplier.contact}"
    )

    st.markdown("---")
    st.subheader(f"All available green suppliers in {city}")
    for s in suppliers:
        st.write(
            f"**{s.name}** — {s.tariff}  \n"
            f"Price: €{s.price_kwh:.3f}/kWh | Renewable: {s.renewable_share}%  \n"
            f"🌐 {s.contact}"
        )

    st.markdown("---")
    st.header("🛠 Certified installers")

    installers = installers_multi(country_code, city)
    if not installers:
        st.info("No installers in this demo city yet — using generic data.")
        installers = installers_multi("EU", "Capital")

    for inst in installers:
        if profile.target_tech in inst.supported_tech:
            st.write(
                f"**{inst.name}** — ⭐ {inst.rating} ({inst.reviews} reviews)  \n"
                f"Tech: {', '.join(inst.supported_tech)}  \n"
                f"📧 {inst.email}"
            )

st.markdown("---")
st.caption("HeatShift — multi-country, interactive, Diia-style prototype for renewable heating.")
