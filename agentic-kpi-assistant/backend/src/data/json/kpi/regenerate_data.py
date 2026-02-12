#!/usr/bin/env python3
"""
Regenerate all KPI data files with logically consistent values.
This script creates realistic sustainability data for AstraZeneca demo.
"""

import json
import random
from datetime import datetime
from pathlib import Path

random.seed(42)  # For reproducibility

# AstraZeneca sites (realistic pharmaceutical sites)
SITES = [
    "Macclesfield, UK",
    "Gothenburg, Sweden",
    "Gaithersburg, USA",
    "Cambridge, UK",
    "Shanghai, China",
    "Osaka, Japan",
    "Sydney, Australia",
    "Sodertalje, Sweden",
    "Newark, USA",
    "Milan, Italy"
]

# EV Markets and Geographies
MARKETS = ["Europe", "North America", "Asia Pacific", "Latin America", "Middle East & Africa"]
GEOGRAPHIES = {
    "Europe": ["UK", "Sweden", "Germany", "France", "Italy", "Spain"],
    "North America": ["USA", "Canada", "Mexico"],
    "Asia Pacific": ["China", "Japan", "Australia", "India", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Colombia"],
    "Middle East & Africa": ["UAE", "South Africa", "Saudi Arabia"]
}

YEARS = [2022, 2023, 2024, 2025]
QUARTERS = [1, 2, 3, 4]
MONTHS_IN_QUARTER = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}


def get_quarter_for_month(month: int) -> int:
    """Return correct quarter for a given month."""
    if month <= 3:
        return 1
    elif month <= 6:
        return 2
    elif month <= 9:
        return 3
    else:
        return 4


def generate_energy_monthly():
    """
    Generate energy data with logical consistency:
    - Total Energy = Onsite Generated + Imported Energy
    - Renewable Energy <= Total Energy
    - Imported Renewable <= Imported Energy
    """
    data = []

    for site in SITES:
        # Base energy consumption varies by site size (MWh per month)
        base_energy = random.uniform(800, 2500)
        renewable_ratio = random.uniform(0.4, 0.85)  # 40-85% renewable target

        for year in YEARS:
            # Year-over-year improvement in renewable ratio
            year_renewable_ratio = min(0.95, renewable_ratio + (year - 2022) * 0.05)

            for month in range(1, 13):
                quarter = get_quarter_for_month(month)

                # Seasonal variation (higher in winter/summer for HVAC)
                seasonal_factor = 1 + 0.15 * abs(6 - month) / 6

                # Monthly consumption
                total_energy = round(base_energy * seasonal_factor * random.uniform(0.9, 1.1), 2)

                # Onsite generation (solar) - higher in summer months
                solar_factor = max(0, 1 - abs(6 - month) / 6) * 0.3
                onsite_solar = round(total_energy * solar_factor * random.uniform(0.8, 1.0), 2)
                onsite_non_renewable = round(total_energy * random.uniform(0.02, 0.08), 2)

                # Imported energy = Total - Onsite Generated
                imported_total = round(total_energy - onsite_solar - onsite_non_renewable, 2)
                imported_total = max(0, imported_total)

                # Renewable breakdown
                imported_renewable = round(imported_total * year_renewable_ratio * random.uniform(0.9, 1.0), 2)

                # Total renewable = onsite solar + imported renewable
                total_renewable = round(onsite_solar + imported_renewable, 2)

                # Indirect energy (grid-supplied)
                indirect_energy = imported_total
                renewable_indirect = imported_renewable

                data.append({
                    "REPORTING_YEAR_NUMBER": year,
                    "REPORTING_QUARTER_NUMBER": quarter,
                    "REPORTING_MONTH_NUMBER": month,
                    "SHE_SITE_NAME": site,
                    "REPORTING_SCOPE_NAME": "Scope 1 & 2",
                    "ENERGY_SITE_MWH_QUANTITY": total_energy,
                    "ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY": total_renewable,
                    "ENERGY_RENEWABLE_INDIRECT_MWH_QUANTITY": renewable_indirect,
                    "ENERGY_INDIRECT_MWH_QUANTITY": indirect_energy,
                    "ENERGY_ONSITE_GENERATED_RENEWABLE_SOLAR_MWH_QUANTITY": onsite_solar,
                    "ENERGY_ONSITE_GENERATED_NON_RENEWABLE_MWH_QUANTITY": onsite_non_renewable,
                    "ENERGY_IMPORTED_RENEWABLE_MWH_QUANTITY": imported_renewable,
                    "ENERGY_IMPORTED_MWH_QUANTITY": imported_total,
                    "SRC_SYS_NM": "ENABLON"
                })

    return data


def generate_energy_quarterly():
    """Generate quarterly energy summary."""
    monthly_data = generate_energy_monthly()
    quarterly = {}

    for record in monthly_data:
        key = (record["REPORTING_YEAR_NUMBER"], record["REPORTING_QUARTER_NUMBER"], record["SHE_SITE_NAME"])
        if key not in quarterly:
            quarterly[key] = {
                "REPORTING_YEAR_NUMBER": record["REPORTING_YEAR_NUMBER"],
                "REPORTING_QUARTER_NUMBER": record["REPORTING_QUARTER_NUMBER"],
                "SHE_SITE_NAME": record["SHE_SITE_NAME"],
                "ENERGY_FLEET_MWH_QUANTITY": 0,
                "ENERGY_TOTAL_MWH_QUANTITY": 0,
                "SRC_SYS_NM": "ENABLON"
            }
        quarterly[key]["ENERGY_TOTAL_MWH_QUANTITY"] += record["ENERGY_SITE_MWH_QUANTITY"]
        quarterly[key]["ENERGY_FLEET_MWH_QUANTITY"] += record["ENERGY_SITE_MWH_QUANTITY"] * 0.05  # 5% fleet energy

    result = []
    for v in quarterly.values():
        v["ENERGY_TOTAL_MWH_QUANTITY"] = round(v["ENERGY_TOTAL_MWH_QUANTITY"], 2)
        v["ENERGY_FLEET_MWH_QUANTITY"] = round(v["ENERGY_FLEET_MWH_QUANTITY"], 2)
        result.append(v)

    return result, monthly_data


def generate_ghg_emissions_quarterly():
    """
    Generate GHG emissions with logical consistency:
    - Scope 1 Total = F-Gases + Road Fleet + Site Energy + Solvents + Non-Energy
    - Scope 2 has Market-based and Location-based (usually Location > Market)
    """
    data = []

    for site in SITES:
        # Base emissions vary by site
        base_scope1 = random.uniform(50, 200)  # tCO2 per quarter
        base_scope2 = random.uniform(100, 400)

        for year in YEARS:
            # Year-over-year reduction targets
            reduction_factor = 1 - (year - 2022) * 0.08

            for quarter in QUARTERS:
                # Scope 1 breakdown
                f_gases = round(base_scope1 * 0.15 * reduction_factor * random.uniform(0.8, 1.2), 2)
                road_fleet = round(base_scope1 * 0.55 * reduction_factor * random.uniform(0.8, 1.2), 2)
                site_energy = round(base_scope1 * 0.20 * reduction_factor * random.uniform(0.8, 1.2), 2)
                solvents = round(base_scope1 * 0.05 * reduction_factor * random.uniform(0.8, 1.2), 2)
                non_energy = round(base_scope1 * 0.05 * reduction_factor * random.uniform(0.8, 1.2), 2)

                scope1_total = round(f_gases + road_fleet + site_energy + solvents + non_energy, 2)

                # Scope 2 breakdown
                # Market-based is typically lower (due to renewable energy certificates)
                scope2_location = round(base_scope2 * reduction_factor * random.uniform(0.8, 1.2), 2)
                scope2_market = round(scope2_location * random.uniform(0.1, 0.4), 2)  # 10-40% of location-based
                ev_charging = round(scope2_market * random.uniform(0.05, 0.15), 2)

                gross_total = round(scope1_total + scope2_market, 2)

                data.append({
                    "REPORTING_YEAR_NUMBER": year,
                    "REPORTING_QUARTER_NUMBER": quarter,
                    "SHE_SITE_NAME": site,
                    "REPORTING_SCOPE_NAME": "Scope 1 & 2",
                    "SCOPE1_ROAD_FLEET_TCO2_QUANTITY": road_fleet,
                    "SCOPE1_F_GASES_TCO2_QUANTITY": f_gases,
                    "SCOPE1_SOLVENTS_TCO2_QUANTITY": solvents,
                    "SCOPE1_SITE_ENERGY_TCO2_QUANTITY": site_energy,
                    "SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY": non_energy,
                    "SCOPE1_TOTAL_TCO2_QUANTITY": scope1_total,
                    "SCOPE2_MARKET_BASED_EV_CHARGING_TCO2_QUANTITY": ev_charging,
                    "SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY": scope2_market,
                    "GROSS_SCOPE1_SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY": gross_total,
                    "SCOPE1_SCOPE2_TOTAL_SITE_ENERGY_TCO2_QUANTITY": round(site_energy + scope2_market * 0.8, 2),
                    "SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY": round(scope1_total + scope2_market, 2),
                    "SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY": scope2_location,
                    "SRC_SYS_NM": "ENABLON"
                })

    return data


def generate_ghg_emissions_monthly():
    """Generate monthly GHG emissions (different field structure from quarterly)."""
    data = []

    for site in SITES:
        base_scope1 = random.uniform(15, 60)  # tCO2 per month
        base_scope2 = random.uniform(30, 120)

        for year in YEARS:
            reduction_factor = 1 - (year - 2022) * 0.08

            for month in range(1, 13):
                quarter = get_quarter_for_month(month)

                # Scope 1 (no road fleet in monthly - that's in quarterly only)
                f_gases = round(base_scope1 * 0.25 * reduction_factor * random.uniform(0.8, 1.2), 2)
                solvents = round(base_scope1 * 0.15 * reduction_factor * random.uniform(0.8, 1.2), 2)
                site_energy = round(base_scope1 * 0.45 * reduction_factor * random.uniform(0.8, 1.2), 2)
                non_energy = round(base_scope1 * 0.15 * reduction_factor * random.uniform(0.8, 1.2), 2)

                # Scope 2
                scope2_location = round(base_scope2 * reduction_factor * random.uniform(0.8, 1.2), 2)
                scope2_market = round(scope2_location * random.uniform(0.1, 0.4), 2)
                ev_charging = round(scope2_market * random.uniform(0.05, 0.15), 2)

                site_total = round(f_gases + solvents + site_energy + non_energy + scope2_market, 2)

                data.append({
                    "REPORTING_YEAR_NUMBER": year,
                    "REPORTING_MONTH_NUMBER": month,
                    "REPORTING_QUARTER_NUMBER": quarter,
                    "SHE_SITE_NAME": site,
                    "REPORTING_SCOPE_NAME": "Scope 1 & 2",
                    "SCOPE1_F_GASES_TCO2_QUANTITY": f_gases,
                    "SCOPE1_SOLVENTS_TCO2_QUANTITY": solvents,
                    "SCOPE1_SITE_ENERGY_TCO2_QUANTITY": site_energy,
                    "SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY": non_energy,
                    "SCOPE2_MARKET_BASED_EV_CHARGING_TCO2_QUANTITY": ev_charging,
                    "SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY": scope2_market,
                    "SCOPE1_SCOPE2_TOTAL_SITE_ENERGY_TCO2_QUANTITY": round(site_energy + scope2_market * 0.8, 2),
                    "SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY": site_total,
                    "SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY": scope2_location,
                    "SRC_SYS_NM": "ENABLON"
                })

    return data


def generate_water_monthly():
    """
    Generate water usage with logical consistency:
    - Total Water = Groundwater + Municipal + Rainwater + Surface
    """
    data = []

    for site in SITES:
        # Base water usage varies by site (million m3 per month)
        base_water = random.uniform(0.001, 0.01)
        groundwater_ratio = random.uniform(0.2, 0.5)
        municipal_ratio = random.uniform(0.4, 0.7)

        for year in YEARS:
            # Year-over-year reduction
            reduction_factor = 1 - (year - 2022) * 0.03

            for month in range(1, 13):
                quarter = get_quarter_for_month(month)

                # Seasonal variation
                seasonal_factor = 1 + 0.1 * (month in [6, 7, 8])

                total_base = base_water * seasonal_factor * reduction_factor * random.uniform(0.9, 1.1)

                groundwater = round(total_base * groundwater_ratio, 6)
                municipal = round(total_base * municipal_ratio, 6)
                rainwater = round(total_base * random.uniform(0.02, 0.1), 6)
                surface = round(total_base * random.uniform(0.01, 0.05), 6)

                total_withdrawn = round(groundwater + municipal + rainwater + surface, 6)

                # Chemical oxygen demand (effluent quality)
                cod = round(total_withdrawn * random.uniform(50, 150), 4)

                data.append({
                    "REPORTING_YEAR_NUMBER": year,
                    "REPORTING_MONTH_NUMBER": month,
                    "REPORTING_QUARTER_NUMBER": quarter,
                    "SHE_SITE_NAME": site,
                    "GROUNDWATER_MILLION_M3_QUANTITY": groundwater,
                    "MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY": municipal,
                    "RAINWATER_HARVESTING_MILLION_M3_QUANTITY": rainwater,
                    "TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY": total_withdrawn,
                    "DIRECT_FROM_FRESH_SURFACE_MILLION_M3_QUANTITY": surface,
                    "CHEMICAL_OXYGEN_DEMAND_EFFLUENT_TONNES_QUANTITY": cod,
                    "SRC_SYS_NM": "ENABLON"
                })

    return data


def generate_waste_monthly():
    """
    Generate waste data with logical consistency:
    - Total Waste = Hazardous + Non-Hazardous
    - Total Waste = Recycled + Landfill + Other
    """
    data = []

    for site in SITES:
        # Base waste generation (tonnes per month)
        base_waste = random.uniform(50, 200)
        hazardous_ratio = random.uniform(0.1, 0.3)  # 10-30% hazardous
        recycle_rate = random.uniform(0.5, 0.8)  # 50-80% recycling target

        for year in YEARS:
            # Improving recycling rate over time
            year_recycle_rate = min(0.95, recycle_rate + (year - 2022) * 0.05)

            for month in range(1, 13):
                quarter = get_quarter_for_month(month)

                # Variation
                variation = random.uniform(0.85, 1.15)

                # Site waste vs product waste
                site_waste = round(base_waste * 0.4 * variation, 2)
                product_waste = round(base_waste * 0.6 * variation, 2)
                total_waste = round(site_waste + product_waste, 2)

                # Recycled waste
                recycled_site = round(site_waste * year_recycle_rate * random.uniform(0.9, 1.0), 2)
                recycled_product = round(product_waste * year_recycle_rate * random.uniform(0.9, 1.0), 2)
                total_recycled = round(recycled_site + recycled_product, 2)

                # Landfill (what's not recycled, minus some incineration)
                landfill_rate = random.uniform(0.3, 0.6)  # Of non-recycled
                landfill_site = round((site_waste - recycled_site) * landfill_rate, 2)
                landfill_product = round((product_waste - recycled_product) * landfill_rate, 2)
                total_landfill = round(landfill_site + landfill_product, 2)

                # Hazardous breakdown
                haz_site = round(site_waste * hazardous_ratio, 2)
                haz_product = round(product_waste * hazardous_ratio, 2)
                total_haz = round(haz_site + haz_product, 2)

                haz_recycled_site = round(haz_site * year_recycle_rate * 0.7, 2)  # Lower recycling for hazardous
                haz_recycled_product = round(haz_product * year_recycle_rate * 0.7, 2)
                total_haz_recycled = round(haz_recycled_site + haz_recycled_product, 2)

                haz_landfill_site = round((haz_site - haz_recycled_site) * 0.2, 2)  # Very little hazardous to landfill
                haz_landfill_product = round((haz_product - haz_recycled_product) * 0.2, 2)
                total_haz_landfill = round(haz_landfill_site + haz_landfill_product, 2)

                # Non-hazardous
                nonhaz_site = round(site_waste - haz_site, 2)
                nonhaz_product = round(product_waste - haz_product, 2)
                total_nonhaz = round(nonhaz_site + nonhaz_product, 2)

                nonhaz_recycled_site = round(recycled_site - haz_recycled_site, 2)
                nonhaz_recycled_product = round(recycled_product - haz_recycled_product, 2)
                total_nonhaz_recycled = round(nonhaz_recycled_site + nonhaz_recycled_product, 2)

                nonhaz_landfill_site = round(landfill_site - haz_landfill_site, 2)
                nonhaz_landfill_product = round(landfill_product - haz_landfill_product, 2)
                total_nonhaz_landfill = round(nonhaz_landfill_site + nonhaz_landfill_product, 2)

                # External waste avoided
                external_avoided = round(total_recycled * random.uniform(0.1, 0.2), 2)

                data.append({
                    "REPORTING_YEAR_NUMBER": year,
                    "REPORTING_MONTH_NUMBER": month,
                    "REPORTING_QUARTER_NUMBER": quarter,
                    "SHE_SITE_NAME": site,
                    "WASTE_TONNES_SITE_QUANTITY": site_waste,
                    "WASTE_TONNES_PRODUCT_QUANTITY": product_waste,
                    "TOTAL_WASTE_TONNES_QUANTITY": total_waste,
                    "RECYCLED_WASTE_TONNES_SITE_QUANTITY": recycled_site,
                    "RECYCLED_WASTE_TONNES_PRODUCT_QUANTITY": recycled_product,
                    "TOTAL_RECYCLED_WASTE_TONNES_QUANTITY": total_recycled,
                    "WASTE_TO_LANDFILL_TONNES_SITE_QUANTITY": landfill_site,
                    "WASTE_TO_LANDFILL_TONNES_PRODUCT_QUANTITY": landfill_product,
                    "TOTAL_WASTE_TO_LANDFILL_TONNES_QUANTITY": total_landfill,
                    "EXTERNAL_WASTE_AVOIDED_REUSE_AND_BYPRODUCT_2022_ONWARDS_TONNES_QUANTITY": external_avoided,
                    "NON_HAZARDOUS_WASTE_TONNES_SITE_QUANTITY": nonhaz_site,
                    "NON_HAZARDOUS_WASTE_TONNES_PRODUCT_QUANTITY": nonhaz_product,
                    "TOTAL_NON_HAZARDOUS_WASTE_TONNES_QUANTITY": total_nonhaz,
                    "NON_HAZARDOUS_WASTE_RECYCLED_TONNES_SITE_QUANTITY": nonhaz_recycled_site,
                    "NON_HAZARDOUS_WASTE_RECYCLED_TONNES_PRODUCT_QUANTITY": nonhaz_recycled_product,
                    "TOTAL_NON_HAZARDOUS_WASTE_RECYCLED_TONNES_QUANTITY": total_nonhaz_recycled,
                    "NON_HAZARDOUS_WASTE_TO_LANDFILL_TONNES_SITE_QUANTITY": nonhaz_landfill_site,
                    "NON_HAZARDOUS_WASTE_TO_LANDFILL_TONNES_PRODUCT_QUANTITY": nonhaz_landfill_product,
                    "TOTAL_NON_HAZARDOUS_WASTE_TO_LANDFILL_TONNES_QUANTITY": total_nonhaz_landfill,
                    "HAZARDOUS_WASTE_TONNES_SITE_QUANTITY": haz_site,
                    "HAZARDOUS_WASTE_TONNES_PRODUCT_QUANTITY": haz_product,
                    "TOTAL_HAZARDOUS_WASTE_TONNES_QUANTITY": total_haz,
                    "HAZARDOUS_WASTE_RECYCLED_TONNES_SITE_QUANTITY": haz_recycled_site,
                    "HAZARDOUS_WASTE_RECYCLED_TONNES_PRODUCT_QUANTITY": haz_recycled_product,
                    "TOTAL_HAZARDOUS_WASTE_RECYCLED_TONNES_QUANTITY": total_haz_recycled,
                    "HAZARDOUS_WASTE_TO_LANDFILL_TONNES_SITE_QUANTITY": haz_landfill_site,
                    "HAZARDOUS_WASTE_TO_LANDFILL_TONNES_PRODUCT_QUANTITY": haz_landfill_product,
                    "TOTAL_HAZARDOUS_WASTE_TO_LANDFILL_TONNES_QUANTITY": total_haz_landfill,
                    "SRC_SYS_NM": "ENABLON"
                })

    return data


def generate_ev_transition_quarterly():
    """
    Generate EV transition data with logical consistency:
    - BEV Count <= Total Fleet
    - BEV % increasing over time
    """
    data = []

    for market in MARKETS:
        for geography in GEOGRAPHIES[market]:
            # Base fleet size varies by geography
            base_fleet = random.randint(100, 500)
            initial_bev_ratio = random.uniform(0.05, 0.15)  # Starting EV ratio

            for year in YEARS:
                # Fleet size relatively stable
                fleet_growth = 1 + (year - 2022) * 0.02

                # BEV ratio increasing significantly
                bev_ratio = min(0.8, initial_bev_ratio + (year - 2022) * 0.12)

                for quarter in QUARTERS:
                    # Quarterly variation
                    q_variation = random.uniform(0.95, 1.05)

                    total_fleet = round(base_fleet * fleet_growth * q_variation)
                    bev_count = round(total_fleet * bev_ratio * random.uniform(0.95, 1.05))
                    bev_count = min(bev_count, total_fleet)  # Can't exceed total

                    data.append({
                        "REPORTING_YEAR_NUMBER": year,
                        "REPORTING_QUARTER_NUMBER": quarter,
                        "SHE_MARKET_NAME": market,
                        "SHE_GEOGRAPHY_NAME": geography,
                        "TOTAL_BEV_COUNT": bev_count,
                        "TOTAL_FLEET_ASSET_COUNT": total_fleet,
                        "SRC_SYS_NM": "ENABLON"
                    })

    return data


def main():
    """Generate all data files."""
    output_dir = Path(__file__).parent

    print("Generating Energy data...")
    energy_quarterly, energy_monthly = generate_energy_quarterly()

    print("Generating GHG Emissions data...")
    ghg_quarterly = generate_ghg_emissions_quarterly()
    ghg_monthly = generate_ghg_emissions_monthly()

    print("Generating Water data...")
    water_monthly = generate_water_monthly()

    print("Generating Waste data...")
    waste_monthly = generate_waste_monthly()

    print("Generating EV Transition data...")
    ev_quarterly = generate_ev_transition_quarterly()

    # Write files
    files = {
        "energy_monthly_summary.json": energy_monthly,
        "energy_quarterly_summary.json": energy_quarterly,
        "greenhouse_gas_emissions_monthly_summary.json": ghg_monthly,
        "greenhouse_gas_emissions_quarterly_summary.json": ghg_quarterly,
        "water_monthly_summary.json": water_monthly,
        "waste_monthly_summary.json": waste_monthly,
        "electric_vehicle_transition_quarterly_summary.json": ev_quarterly
    }

    for filename, data in files.items():
        filepath = output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Written {filename}: {len(data)} records")

    print("\nData generation complete!")

    # Verification
    print("\n=== Verification ===")

    # Energy check
    sample = energy_monthly[0]
    total = sample["ENERGY_SITE_MWH_QUANTITY"]
    renewable = sample["ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY"]
    imported = sample["ENERGY_IMPORTED_MWH_QUANTITY"]
    print(f"Energy sample: Total={total}, Renewable={renewable} ({renewable/total*100:.1f}%), Imported={imported}")
    assert renewable <= total * 1.01, "Renewable should not exceed total"

    # GHG check
    sample = ghg_quarterly[0]
    scope1_total = sample["SCOPE1_TOTAL_TCO2_QUANTITY"]
    scope1_sum = (sample["SCOPE1_F_GASES_TCO2_QUANTITY"] +
                  sample["SCOPE1_ROAD_FLEET_TCO2_QUANTITY"] +
                  sample["SCOPE1_SOLVENTS_TCO2_QUANTITY"] +
                  sample["SCOPE1_SITE_ENERGY_TCO2_QUANTITY"] +
                  sample["SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY"])
    print(f"GHG sample: Scope1 Total={scope1_total}, Sum of components={scope1_sum:.2f}")
    assert abs(scope1_total - scope1_sum) < 0.1, "Scope 1 total should equal sum of components"

    # Quarter/Month check
    for record in energy_monthly:
        expected_q = get_quarter_for_month(record["REPORTING_MONTH_NUMBER"])
        assert record["REPORTING_QUARTER_NUMBER"] == expected_q, f"Quarter mismatch: month {record['REPORTING_MONTH_NUMBER']} should be Q{expected_q}"
    print("Quarter/Month alignment: OK")

    # EV check
    for record in ev_quarterly:
        assert record["TOTAL_BEV_COUNT"] <= record["TOTAL_FLEET_ASSET_COUNT"], "BEV count exceeds fleet"
    print("EV BEV <= Fleet: OK")

    print("\nAll verifications passed!")


if __name__ == "__main__":
    main()
