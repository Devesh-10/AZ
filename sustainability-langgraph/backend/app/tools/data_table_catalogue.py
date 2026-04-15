"""
Data Table Catalogue for Sustainability Insight Agent
Defines all available data tables for semantic search and data loading.
"""

DATA_TABLE_CATALOGUE = {
    # ============ KPI / SUMMARY DATA ============
    "energy_monthly_summary": {
        "name": "Energy Monthly Summary",
        "description": "Monthly aggregated energy consumption data by site. Includes total energy, "
                      "renewable energy, solar generation, imported energy, and indirect energy. "
                      "Use for energy consumption questions, renewable energy tracking, and efficiency analysis.",
        "file_path": "KPI/energy_monthly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "REPORTING_MONTH_NUMBER",
                   "SHE_SITE_NAME", "REPORTING_SCOPE_NAME", "ENERGY_SITE_MWH_QUANTITY",
                   "ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY", "ENERGY_RENEWABLE_INDIRECT_MWH_QUANTITY",
                   "ENERGY_INDIRECT_MWH_QUANTITY", "ENERGY_ONSITE_GENERATED_RENEWABLE_SOLAR_MWH_QUANTITY",
                   "ENERGY_ONSITE_GENERATED_NON_RENEWABLE_MWH_QUANTITY", "ENERGY_IMPORTED_RENEWABLE_MWH_QUANTITY",
                   "ENERGY_IMPORTED_MWH_QUANTITY", "SRC_SYS_NM"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "SHE_SITE_NAME",
                       "ENERGY_SITE_MWH_QUANTITY", "ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY"],
        "sample_values": {
            "SHE_SITE_NAME": ["Macclesfield, UK", "Gaithersburg, US", "Sodertalje, Sweden"],
            "REPORTING_SCOPE_NAME": ["Scope 1 & 2"]
        },
        "sample_queries": [
            "What is our total energy consumption?",
            "Energy usage by site",
            "Renewable energy percentage",
            "Solar energy generated",
            "Monthly energy trends"
        ],
        "aliases": ["energy", "energy consumption", "power usage", "electricity", "MWh"]
    },

    "energy_quarterly_summary": {
        "name": "Energy Quarterly Summary",
        "description": "Quarterly aggregated energy data for trend analysis and reporting.",
        "file_path": "KPI/energy_quarterly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_SITE_NAME",
                   "REPORTING_SCOPE_NAME", "ENERGY_SITE_MWH_QUANTITY"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_SITE_NAME"],
        "sample_values": {},
        "sample_queries": ["Quarterly energy trends", "Q1 vs Q2 energy comparison"],
        "aliases": ["quarterly energy", "energy by quarter"]
    },

    "greenhouse_gas_emissions_monthly_summary": {
        "name": "GHG Emissions Monthly Summary",
        "description": "Monthly greenhouse gas emissions data by site and scope. Includes Scope 1 (direct), "
                      "Scope 2 (indirect), F-gases, solvents, and total emissions. Use for emissions tracking, "
                      "carbon footprint analysis, and environmental reporting.",
        "file_path": "KPI/greenhouse_gas_emissions_monthly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "REPORTING_QUARTER_NUMBER",
                   "SHE_SITE_NAME", "REPORTING_SCOPE_NAME", "SCOPE1_F_GASES_TCO2_QUANTITY",
                   "SCOPE1_SOLVENTS_TCO2_QUANTITY", "SCOPE1_SITE_ENERGY_TCO2_QUANTITY",
                   "SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY", "SCOPE2_MARKET_BASED_EV_CHARGING_TCO2_QUANTITY",
                   "SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY", "SCOPE1_SCOPE2_TOTAL_SITE_ENERGY_TCO2_QUANTITY",
                   "SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY", "SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "SHE_SITE_NAME",
                       "SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY"],
        "sample_values": {
            "SHE_SITE_NAME": ["Macclesfield, UK", "Gaithersburg, US"],
            "REPORTING_SCOPE_NAME": ["Scope 1 & 2"]
        },
        "sample_queries": [
            "What are our total emissions?",
            "GHG emissions breakdown",
            "Scope 1 vs Scope 2 emissions",
            "Carbon footprint by site",
            "F-gas emissions"
        ],
        "aliases": ["emissions", "GHG", "greenhouse gas", "carbon", "CO2", "tCO2", "carbon footprint"]
    },

    "greenhouse_gas_emissions_quarterly_summary": {
        "name": "GHG Emissions Quarterly Summary",
        "description": "Quarterly aggregated emissions data for trend analysis.",
        "file_path": "KPI/greenhouse_gas_emissions_quarterly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_SITE_NAME"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_SITE_NAME"],
        "sample_values": {},
        "sample_queries": ["Quarterly emissions trends", "Year-over-year emissions comparison"],
        "aliases": ["quarterly emissions", "emissions by quarter"]
    },

    "water_monthly_summary": {
        "name": "Water Monthly Summary",
        "description": "Monthly water consumption data by site and source. Includes groundwater, "
                      "municipal supply, rainwater harvesting, and total water withdrawn. "
                      "Use for water usage tracking and efficiency analysis.",
        "file_path": "KPI/water_monthly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "REPORTING_QUARTER_NUMBER",
                   "SHE_SITE_NAME", "GROUNDWATER_MILLION_M3_QUANTITY", "MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY",
                   "RAINWATER_HARVESTING_MILLION_M3_QUANTITY", "TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY",
                   "DIRECT_FROM_FRESH_SURFACE_MILLION_M3_QUANTITY", "CHEMICAL_OXYGEN_DEMAND_EFFLUENT_TONNES_QUANTITY"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "SHE_SITE_NAME",
                       "TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY"],
        "sample_values": {
            "SHE_SITE_NAME": ["Macclesfield, UK", "Gaithersburg, US"]
        },
        "sample_queries": [
            "How much water did we use?",
            "Water consumption by site",
            "Groundwater vs municipal water",
            "Rainwater harvesting volume"
        ],
        "aliases": ["water", "water usage", "water consumption", "water withdrawn", "m3"]
    },

    "waste_monthly_summary": {
        "name": "Waste Monthly Summary",
        "description": "Monthly waste generation data by site. Includes total waste, hazardous waste, "
                      "recycled waste, and disposal methods. Use for waste management tracking and recycling analysis.",
        "file_path": "KPI/waste_monthly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "REPORTING_QUARTER_NUMBER",
                   "SHE_SITE_NAME", "WASTE_TOTAL_TONNES_QUANTITY", "WASTE_HAZARDOUS_TONNES_QUANTITY",
                   "WASTE_NON_HAZARDOUS_TONNES_QUANTITY", "WASTE_RECYCLED_TONNES_QUANTITY",
                   "WASTE_LANDFILL_TONNES_QUANTITY", "WASTE_INCINERATED_TONNES_QUANTITY"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "SHE_SITE_NAME",
                       "WASTE_TOTAL_TONNES_QUANTITY"],
        "sample_values": {
            "SHE_SITE_NAME": ["Macclesfield, UK"]
        },
        "sample_queries": [
            "Total waste generated",
            "Hazardous waste by site",
            "Recycling rate",
            "Waste sent to landfill"
        ],
        "aliases": ["waste", "waste management", "garbage", "recycling", "hazardous waste"]
    },

    "electric_vehicle_transition_quarterly_summary": {
        "name": "EV Transition Quarterly Summary",
        "description": "Quarterly electric vehicle fleet transition data by market and geography. "
                      "Tracks BEV count vs total fleet for EV adoption monitoring.",
        "file_path": "KPI/electric_vehicle_transition_quarterly_summary.csv",
        "category": "KPI",
        "columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_MARKET_NAME",
                   "SHE_GEOGRAPHY_NAME", "TOTAL_BEV_COUNT", "TOTAL_FLEET_ASSET_COUNT", "SRC_SYS_NM"],
        "key_columns": ["REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_MARKET_NAME",
                       "SHE_GEOGRAPHY_NAME", "TOTAL_BEV_COUNT", "TOTAL_FLEET_ASSET_COUNT"],
        "sample_values": {
            "SHE_MARKET_NAME": ["Europe", "Americas", "Asia Pacific"],
            "SHE_GEOGRAPHY_NAME": ["UK", "US", "Germany", "Japan"]
        },
        "sample_queries": [
            "How many EVs do we have?",
            "EV transition progress",
            "Electric vehicle count by region",
            "Fleet electrification rate"
        ],
        "aliases": ["EV", "electric vehicle", "BEV", "fleet", "electrification", "EV transition"]
    },

    # ============ TRANSACTIONAL DATA ============
    "energy_consumption": {
        "name": "Energy Consumption Records",
        "description": "Detailed energy consumption transaction records.",
        "file_path": "Transactional/energy_consumption.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Detailed energy records"],
        "aliases": ["energy transactions", "energy details"]
    },

    "fleet_asset_inventory": {
        "name": "Fleet Asset Inventory",
        "description": "Complete fleet vehicle inventory with vehicle counts by powertrain type (Diesel, Petrol, BEV, Hybrid), geography, market, and year. Use this for diesel car count, petrol car count, BEV count trends, and vehicle breakdown by fuel type.",
        "file_path": "Transactional/fleet_asset_inventory.csv",
        "category": "Transactional",
        "columns": ["FLEET_ASSET_COUNT", "FLEET_ASSET_TYPE_NAME", "FLEET_FUEL_POWERTRAIN_TYPE_NAME", "REPORTING_YEAR_NUMBER", "REPORTING_QUARTER_NUMBER", "SHE_GEOGRAPHY_NAME", "SHE_MARKET_NAME"],
        "key_columns": ["FLEET_ASSET_COUNT", "FLEET_FUEL_POWERTRAIN_TYPE_NAME", "REPORTING_YEAR_NUMBER"],
        "sample_values": {"FLEET_FUEL_POWERTRAIN_TYPE_NAME": ["Diesel", "Petrol", "Battery Electric Car (BEV)", "Hybrid"]},
        "sample_queries": ["Diesel car count trend by year", "Fleet asset count by powertrain type", "How many petrol cars?", "BEV adoption by market"],
        "aliases": ["fleet inventory", "vehicle list", "fleet assets", "diesel car", "petrol car", "diesel count", "petrol count", "powertrain", "car count", "vehicle count", "by powertrain type"]
    },

    "fleet_fuel_consumption": {
        "name": "Fleet Fuel Consumption",
        "description": "Fuel consumption records for fleet vehicles.",
        "file_path": "Transactional/fleet_fuel_consumption.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Fleet fuel usage", "Vehicle fuel consumption"],
        "aliases": ["fuel consumption", "fleet fuel"]
    },

    "fleet_mileage": {
        "name": "Fleet Mileage",
        "description": "Mileage records for fleet vehicles.",
        "file_path": "Transactional/fleet_mileage.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Fleet mileage", "Vehicle kilometers"],
        "aliases": ["mileage", "kilometers", "vehicle distance"]
    },

    "greenhouse_gas_emissions": {
        "name": "GHG Emissions Records",
        "description": "Detailed greenhouse gas emission transaction records.",
        "file_path": "Transactional/greenhouse_gas_emissions.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Detailed emissions records"],
        "aliases": ["emissions records", "GHG details"]
    },

    "water_usage": {
        "name": "Water Usage Records",
        "description": "Detailed water usage transaction records.",
        "file_path": "Transactional/water_usage.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Detailed water records"],
        "aliases": ["water records", "water details"]
    },

    "waste_record": {
        "name": "Waste Records",
        "description": "Detailed waste generation and disposal records.",
        "file_path": "Transactional/waste_record.csv",
        "category": "Transactional",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["Detailed waste records"],
        "aliases": ["waste records", "waste details"]
    },

    # ============ MASTER DATA ============
    "she_site": {
        "name": "SHE Site Master",
        "description": "Master data for all Safety, Health, Environment (SHE) sites with location details.",
        "file_path": "Master/she_site.csv",
        "category": "Master",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["List all sites", "Site information", "How many sites?"],
        "aliases": ["sites", "locations", "facilities"]
    },

    "she_indicator": {
        "name": "SHE Indicators",
        "description": "Master list of sustainability indicators and metrics definitions.",
        "file_path": "Master/she_indicator.csv",
        "category": "Master",
        "columns": [],
        "key_columns": [],
        "sample_values": {},
        "sample_queries": ["What indicators do we track?", "Sustainability metrics list"],
        "aliases": ["indicators", "metrics", "KPI definitions"]
    }
}


def get_all_table_descriptions() -> list[dict]:
    """Get table descriptions for embedding generation"""
    descriptions = []
    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        # Build semantic description
        text_parts = [
            meta["name"],
            meta["description"],
            ", ".join(meta.get("aliases", [])),
            " | ".join(meta.get("sample_queries", []))
        ]
        descriptions.append({
            "table_id": table_id,
            "text": " ".join(text_parts)
        })
    return descriptions
