"""
Prompt for extracting plasma parameters from NSTX/NSTX-U research papers.
"""

PARAMETER_EXTRACTION_PROMPT = """You are an expert at analyzing scientific papers about plasma physics experiments on the NSTX and NSTX-U fusion reactors at Princeton Plasma Physics Laboratory.

Given the following text extracted from a research paper, extract all plasma parameters mentioned with their values and units.

<paper_text>
{paper_text}
</paper_text>

Extract parameters from these categories:

PLASMA PARAMETERS:
- ion_temperature (Ti): Ion temperature, typically in keV or eV
- electron_temperature (Te): Electron temperature, typically in keV or eV
- electron_density (ne): Electron density, typically in m^-3 or cm^-3
- ion_density (ni): Ion density
- pressure: Plasma pressure, typically in kPa or Pa
- beta: Plasma beta (ratio of plasma pressure to magnetic pressure), dimensionless
- beta_N: Normalized beta
- stored_energy: Stored energy, typically in kJ or MJ
- confinement_time: Energy confinement time, typically in ms or s

OPERATIONAL PARAMETERS:
- plasma_current (Ip): Plasma current, typically in MA or kA
- toroidal_field (Bt): Toroidal magnetic field, typically in T
- nbi_power: Neutral beam injection power, typically in MW
- rf_power: RF heating power, typically in MW
- total_heating_power: Total auxiliary heating power
- gas_species: Main gas species (D, H, He, etc.)
- line_averaged_density: Line-averaged electron density

PERFORMANCE METRICS:
- H_factor (H98): Confinement quality factor relative to H-mode scaling
- fusion_power: Fusion power if mentioned
- neutron_rate: Neutron production rate
- q95: Safety factor at 95% flux surface
- li: Internal inductance
- kappa: Plasma elongation
- triangularity: Plasma triangularity

Return your findings as valid JSON:

{{
    "parameters": [
        {{
            "name": "ion_temperature",
            "category": "plasma",
            "value": 2.5,
            "value_min": null,
            "value_max": null,
            "unit": "keV",
            "uncertainty": 0.2,
            "shot_number": 141234,
            "context": "Central ion temperature measured by CHERS"
        }},
        {{
            "name": "plasma_current",
            "category": "operational",
            "value": null,
            "value_min": 0.8,
            "value_max": 1.2,
            "unit": "MA",
            "uncertainty": null,
            "shot_number": null,
            "context": "Range of plasma currents studied"
        }}
    ]
}}

Rules:
1. Extract exact numerical values when given
2. For ranges, use value_min and value_max
3. Include uncertainty if provided (e.g., "2.5 ± 0.2 keV")
4. Link to shot number if the value is specific to a shot
5. Use standardized parameter names from the lists above
6. Category must be: "plasma", "operational", or "performance"
7. Preserve original units (we'll normalize later)
8. If no parameters found, return {{"parameters": []}}
9. Return ONLY valid JSON, no additional text

Return the JSON:"""
