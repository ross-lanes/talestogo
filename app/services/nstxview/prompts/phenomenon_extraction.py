"""
Prompt for extracting plasma phenomena from NSTX/NSTX-U research papers.
"""

PHENOMENON_EXTRACTION_PROMPT = """You are an expert at analyzing scientific papers about plasma physics experiments on the NSTX and NSTX-U fusion reactors at Princeton Plasma Physics Laboratory.

Given the following text extracted from a research paper, identify all plasma physics phenomena discussed.

<paper_text>
{paper_text}
</paper_text>

Identify phenomena from these categories:

INSTABILITIES:
- ELM: Edge Localized Modes (Type I, II, III, grassy)
- kink_mode: Kink instabilities
- tearing_mode: Tearing modes, neoclassical tearing modes (NTM)
- ballooning_mode: Ballooning instabilities
- alfven_eigenmode: Toroidal Alfvén Eigenmodes (TAE), other AEs
- energetic_particle_mode: Energetic particle-driven modes
- resistive_wall_mode: RWMs
- locked_mode: Locked modes
- sawtooth: Sawtooth oscillations
- fishbone: Fishbone instabilities

CONFINEMENT:
- H-mode: High confinement mode
- L-mode: Low confinement mode
- I-mode: Improved confinement mode
- enhanced_confinement: Any enhanced confinement regime
- internal_transport_barrier: ITBs
- edge_transport_barrier: ETBs, pedestals
- QH-mode: Quiescent H-mode
- EDA_H-mode: Enhanced D-alpha H-mode

TRANSPORT:
- energy_transport: Anomalous/turbulent energy transport
- particle_transport: Particle transport
- momentum_transport: Momentum/rotation transport
- impurity_transport: Impurity transport
- turbulence: Turbulent transport, fluctuations

HEATING:
- NBI_heating: Neutral beam heating effects
- RF_heating: ICRF, HHFW, ECH effects
- current_drive: Non-inductive current drive
- rotation_drive: Torque and rotation effects

DISRUPTION:
- disruption: Plasma disruption
- vertical_displacement_event: VDE
- runaway_electrons: Runaway electron generation
- thermal_quench: Thermal quench
- current_quench: Current quench
- disruption_mitigation: MGI, SPI

DIVERTOR:
- detachment: Divertor detachment
- snowflake_divertor: Snowflake divertor configuration
- heat_flux: Divertor heat flux studies
- SOL_physics: Scrape-off layer physics
- lithium_conditioning: Lithium wall conditioning

Return your findings as valid JSON:

{{
    "phenomena": [
        {{
            "type": "H-mode",
            "category": "confinement",
            "description": "Achieved H-mode with pedestal pressure of 8 kPa",
            "is_primary_focus": true,
            "shot_numbers": [141234, 141235]
        }},
        {{
            "type": "ELM",
            "category": "instability",
            "description": "Type I ELMs observed with frequency of 50 Hz",
            "is_primary_focus": false,
            "shot_numbers": [141234]
        }}
    ]
}}

Rules:
1. Use standardized type names from the lists above
2. Category must be: "instability", "confinement", "transport", "heating", "disruption", or "divertor"
3. Set is_primary_focus=true if this phenomenon is a main topic of the paper
4. Include shot_numbers if the phenomenon is associated with specific shots
5. Description should briefly explain what was observed/studied
6. Include phenomena even if they're just mentioned for context
7. If no phenomena found, return {{"phenomena": []}}
8. Return ONLY valid JSON, no additional text

Return the JSON:"""
