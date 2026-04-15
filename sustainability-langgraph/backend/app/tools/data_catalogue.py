"""
Sustainability KPI Catalogue
Defines available KPIs for semantic matching and SQL generation.
"""

# KPI Catalogue for simple KPI lookups
KPI_CATALOGUE = {
    # ============ ENERGY KPIs ============
    "total_energy_consumption": {
        "name": "Total Energy Consumption",
        "description": "Total energy consumed at site level in MWh, including all sources",
        "table": "ENERGY_MONTHLY_SUMMARY",
        "column": "ENERGY_SITE_MWH_QUANTITY",
        "unit": " MWh",
        "target": None,
        "aliases": ["energy consumption", "energy usage", "total energy", "energy", "power consumption"],
        "sample_queries": [
            "What is our total energy consumption?",
            "How much energy did we use?",
            "Monthly energy usage",
            "Energy consumption last year"
        ]
    },

    "renewable_energy": {
        "name": "Renewable Energy",
        "description": "Renewable electricity and heat consumption in MWh",
        "table": "ENERGY_MONTHLY_SUMMARY",
        "column": "ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY",
        "unit": " MWh",
        "target": None,
        "aliases": ["renewable", "green energy", "clean energy", "renewable electricity"],
        "sample_queries": [
            "How much renewable energy do we use?",
            "Renewable energy consumption",
            "Green energy usage",
            "Solar and renewable energy"
        ]
    },

    "solar_energy": {
        "name": "Solar Energy Generated",
        "description": "On-site generated renewable solar energy in MWh",
        "table": "ENERGY_MONTHLY_SUMMARY",
        "column": "ENERGY_ONSITE_GENERATED_RENEWABLE_SOLAR_MWH_QUANTITY",
        "unit": " MWh",
        "target": None,
        "aliases": ["solar", "solar power", "solar generation", "photovoltaic"],
        "sample_queries": [
            "How much solar energy did we generate?",
            "Solar power generation",
            "On-site solar production"
        ]
    },

    # ============ GHG EMISSIONS KPIs ============
    "total_ghg_emissions": {
        "name": "Total GHG Emissions",
        "description": "Total Scope 1 and Scope 2 greenhouse gas emissions in tonnes CO2",
        "table": "GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY",
        "column": "SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY",
        "unit": " tCO2",
        "target": None,
        "aliases": ["emissions", "ghg", "greenhouse gas", "carbon emissions", "CO2", "carbon footprint"],
        "sample_queries": [
            "What are our total emissions?",
            "GHG emissions last quarter",
            "Carbon footprint",
            "Show me emissions data"
        ]
    },

    "scope1_emissions": {
        "name": "Scope 1 Emissions",
        "description": "Direct emissions from owned or controlled sources in tonnes CO2",
        "table": "GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY",
        "column": "SCOPE1_SITE_ENERGY_TCO2_QUANTITY",
        "unit": " tCO2",
        "target": None,
        "aliases": ["scope 1", "direct emissions", "scope one"],
        "sample_queries": [
            "What are our Scope 1 emissions?",
            "Direct emissions",
            "Scope 1 breakdown"
        ]
    },

    "scope2_emissions": {
        "name": "Scope 2 Emissions",
        "description": "Indirect emissions from purchased electricity/heat in tonnes CO2 (market-based)",
        "table": "GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY",
        "column": "SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY",
        "unit": " tCO2",
        "target": None,
        "aliases": ["scope 2", "indirect emissions", "scope two", "market based"],
        "sample_queries": [
            "What are our Scope 2 emissions?",
            "Indirect emissions",
            "Market-based emissions"
        ]
    },

    "f_gases_emissions": {
        "name": "F-Gas Emissions",
        "description": "Fluorinated gas emissions (refrigerants, etc.) in tonnes CO2",
        "table": "GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY",
        "column": "SCOPE1_F_GASES_TCO2_QUANTITY",
        "unit": " tCO2",
        "target": None,
        "aliases": ["f-gases", "fluorinated gases", "refrigerant emissions", "HFC"],
        "sample_queries": [
            "F-gas emissions",
            "Refrigerant emissions",
            "Fluorinated gas leakage"
        ]
    },

    # ============ WATER KPIs ============
    "total_water_withdrawn": {
        "name": "Total Water Withdrawn",
        "description": "Total water withdrawn from all sources in million cubic meters",
        "table": "WATER_MONTHLY_SUMMARY",
        "column": "TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY",
        "unit": " million m³",
        "target": None,
        "aliases": ["water", "water usage", "water consumption", "water withdrawn"],
        "sample_queries": [
            "How much water did we use?",
            "Water consumption",
            "Total water usage",
            "Water usage last month"
        ]
    },

    "municipal_water": {
        "name": "Municipal Water Supply",
        "description": "Water from municipal supply in million cubic meters",
        "table": "WATER_MONTHLY_SUMMARY",
        "column": "MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY",
        "unit": " million m³",
        "target": None,
        "aliases": ["municipal water", "city water", "tap water", "mains water"],
        "sample_queries": [
            "Municipal water usage",
            "City water consumption"
        ]
    },

    "groundwater": {
        "name": "Groundwater Usage",
        "description": "Groundwater withdrawn in million cubic meters",
        "table": "WATER_MONTHLY_SUMMARY",
        "column": "GROUNDWATER_MILLION_M3_QUANTITY",
        "unit": " million m³",
        "target": None,
        "aliases": ["groundwater", "well water", "aquifer"],
        "sample_queries": [
            "Groundwater usage",
            "Well water consumption"
        ]
    },

    "rainwater_harvesting": {
        "name": "Rainwater Harvesting",
        "description": "Rainwater collected and used in million cubic meters",
        "table": "WATER_MONTHLY_SUMMARY",
        "column": "RAINWATER_HARVESTING_MILLION_M3_QUANTITY",
        "unit": " million m³",
        "target": None,
        "aliases": ["rainwater", "harvested water", "rain collection"],
        "sample_queries": [
            "Rainwater harvesting",
            "How much rainwater do we collect?"
        ]
    },

    # ============ WASTE KPIs ============
    "total_waste": {
        "name": "Total Waste Generated",
        "description": "Total waste generated across all categories",
        "table": "WASTE_MONTHLY_SUMMARY",
        "column": "WASTE_TOTAL_TONNES_QUANTITY",
        "unit": " tonnes",
        "target": None,
        "aliases": ["waste", "total waste", "waste generated", "waste production"],
        "sample_queries": [
            "How much waste did we generate?",
            "Total waste",
            "Monthly waste generation",
            "Waste generated last year"
        ]
    },

    "hazardous_waste": {
        "name": "Hazardous Waste",
        "description": "Hazardous waste generated in tonnes",
        "table": "WASTE_MONTHLY_SUMMARY",
        "column": "WASTE_HAZARDOUS_TONNES_QUANTITY",
        "unit": " tonnes",
        "target": None,
        "aliases": ["hazardous waste", "dangerous waste", "toxic waste"],
        "sample_queries": [
            "Hazardous waste generated",
            "How much hazardous waste?"
        ]
    },

    "recycled_waste": {
        "name": "Recycled Waste",
        "description": "Waste sent for recycling in tonnes",
        "table": "WASTE_MONTHLY_SUMMARY",
        "column": "WASTE_RECYCLED_TONNES_QUANTITY",
        "unit": " tonnes",
        "target": None,
        "aliases": ["recycled", "recycling", "waste recycled"],
        "sample_queries": [
            "How much waste was recycled?",
            "Recycling rate",
            "Waste sent for recycling"
        ]
    },

    # ============ EV FLEET KPIs ============
    "ev_count": {
        "name": "Electric Vehicle Count",
        "description": "Total number of battery electric vehicles (BEV) in fleet",
        "table": "ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY",
        "column": "TOTAL_BEV_COUNT",
        "unit": " vehicles",
        "target": None,
        "aliases": ["ev", "electric vehicles", "BEV", "electric cars", "EV fleet"],
        "sample_queries": [
            "How many electric vehicles do we have?",
            "EV count",
            "Electric vehicle fleet size",
            "BEV count by market"
        ]
    },

    "total_fleet_count": {
        "name": "Total Fleet Count",
        "description": "Total number of vehicles in fleet",
        "table": "ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY",
        "column": "TOTAL_FLEET_ASSET_COUNT",
        "unit": " vehicles",
        "target": None,
        "aliases": ["fleet size", "total vehicles", "fleet count", "vehicle count"],
        "sample_queries": [
            "Total fleet size",
            "How many vehicles in our fleet?",
            "Fleet count by region"
        ]
    },

    "ev_transition_rate": {
        "name": "EV Transition Rate",
        "description": "Percentage of fleet that is electric (calculated as BEV/Total Fleet)",
        "table": "ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY",
        "column": "EV_PERCENTAGE",  # Will need to calculate this
        "unit": "%",
        "target": 100,
        "aliases": ["ev percentage", "ev ratio", "electrification rate", "ev transition"],
        "sample_queries": [
            "What is our EV transition rate?",
            "Percentage of electric vehicles",
            "EV adoption rate",
            "How far are we in EV transition?"
        ]
    }
}


# Foundation Data Products for Analyst Agent (complex queries)
FOUNDATION_DATA_PRODUCTS = {
    "energy_analysis": {
        "name": "Energy Consumption Analysis",
        "description": "Detailed energy consumption data by site, source type, and time period",
        "tables": ["energy_monthly_summary", "energy_quarterly_summary", "energy_consumption"],
        "sample_queries": [
            "Compare energy consumption across sites",
            "Energy consumption by site",
            "Why is our energy consumption high?",
            "How can we reduce energy usage?"
        ]
    },

    "emissions_analysis": {
        "name": "GHG Emissions Analysis",
        "description": "Comprehensive emissions data across scopes, sources, and locations",
        "tables": ["greenhouse_gas_emissions_monthly_summary", "greenhouse_gas_emissions_quarterly_summary", "greenhouse_gas_emissions"],
        "sample_queries": [
            "Compare emissions across sites",
            "CO2 emissions by site",
            "Why are our emissions high?",
            "How can we reduce carbon footprint?"
        ]
    },

    "water_analysis": {
        "name": "Water Usage Analysis",
        "description": "Water consumption patterns, sources, and efficiency metrics",
        "tables": ["water_monthly_summary", "water_usage"],
        "sample_queries": [
            "Compare water usage across facilities",
            "Water withdrawn by site",
            "How can we reduce water usage?",
            "Water sources breakdown"
        ]
    },

    "waste_analysis": {
        "name": "Waste Management Analysis",
        "description": "Waste generation, disposal methods, and recycling rates",
        "tables": ["waste_monthly_summary", "waste_record"],
        "sample_queries": [
            "Compare waste across sites",
            "Waste by site",
            "How can we improve recycling?",
            "Waste reduction opportunities"
        ]
    },

    "fleet_analysis": {
        "name": "Fleet Transition Analysis",
        "description": "EV transition progress, fleet composition, and electrification roadmap",
        "tables": ["electric_vehicle_transition_quarterly_summary", "fleet_asset_inventory", "fleet_fuel_consumption", "fleet_mileage"],
        "sample_queries": [
            "Analyze our EV transition progress",
            "How can we accelerate EV adoption?",
            "Fleet electrification roadmap",
            "Recommend actions for EV transition"
        ]
    },

    "site_sustainability": {
        "name": "Site Sustainability Overview",
        "description": "Comprehensive sustainability metrics for specific sites",
        "tables": ["she_site", "she_site_dimension"],
        "sample_queries": [
            "Sustainability performance by site",
            "Which sites need improvement?",
            "Best performing sites"
        ]
    }
}
