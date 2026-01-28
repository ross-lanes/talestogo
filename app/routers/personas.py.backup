"""
Persona generation routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, PersonaType
from app.schemas import (
    PersonaGeneration, PersonaGenerationCreate, PersonaGenerationWithPersonas,
    Persona as PersonaSchema
)
from app.auth import get_current_user
from app.crud import (
    create_persona_generation, get_persona_generation,
    get_user_persona_generations, get_generation_personas,
    get_active_brand, create_persona,
    update_persona_generation, user_has_brand_access
)
from app.services.persona_generator import PersonaGenerator
from app.services.pptx_generator import PersonaDeckGenerator
from app.config import settings
import os
from datetime import datetime

router = APIRouter(prefix="/personas", tags=["personas"])


async def generate_personas_task(
    generation_id: int,
    db: Session
):
    """Background task to generate personas"""
    try:
        # Get generation request
        generation = get_persona_generation(db, generation_id)
        if not generation:
            return

        # Update status
        update_persona_generation(db, generation_id, "generating")

        # Get brand info
        from app.crud import get_brand
        brand = get_brand(db, generation.brand_id)
        if not brand:
            update_persona_generation(
                db, generation_id, "failed",
                error_message="Brand not found"
            )
            return

        # Prepare brand info dict
        brand_info = {
            "brand_name": brand.brand_name,
            "generic_name": brand.generic_name,
            "therapeutic_area": brand.therapeutic_area,
            "indication": brand.indication,
            "manufacturer": brand.manufacturer,
            "target_audience": brand.target_audience,
            "key_messages": brand.key_messages,
            "primary_color": brand.primary_color,
            "secondary_color": brand.secondary_color,
            "logo_url": brand.logo_url
        }

        # Prepare inputs
        patient_inputs = {
            "patient_occupation": generation.patient_occupation,
            "patient_clinical_scenario": generation.patient_clinical_scenario,
            "patient_gender": generation.patient_gender,
            "patient_symptoms": generation.patient_symptoms,
            "patient_age_range": generation.patient_age_range,
        }

        hcp_inputs = {
            "hcp_doctor_type": generation.hcp_doctor_type,
            "hcp_disease": generation.hcp_disease,
            "hcp_location": generation.hcp_location,
        }

        # Generate personas
        generator = PersonaGenerator(provider=settings.DEFAULT_LLM_PROVIDER)

        # Generate patient personas
        patient_personas = await generator.generate_patient_personas(brand_info, patient_inputs)

        # Generate HCP personas
        hcp_personas = await generator.generate_hcp_personas(brand_info, hcp_inputs)

        # Save personas to database
        all_personas = []

        for i, persona_data in enumerate(patient_personas):
            persona = create_persona(db, PersonaSchema(
                generation_id=generation_id,
                persona_type=PersonaType.PATIENT,
                order_index=i,
                **persona_data
            ))
            all_personas.append(persona)

        for i, persona_data in enumerate(hcp_personas):
            persona = create_persona(db, PersonaSchema(
                generation_id=generation_id,
                persona_type=PersonaType.HCP,
                order_index=i + 4,
                **persona_data
            ))
            all_personas.append(persona)

        # Generate PowerPoint deck
        pptx_gen = PersonaDeckGenerator()

        # Add title slide
        pptx_gen.add_title_slide(
            brand_name=brand.brand_name,
            primary_color=brand.primary_color,
            logo_url=brand.logo_url if brand.logo_url and os.path.exists(brand.logo_url) else None
        )

        # Add patient persona slides
        for persona in all_personas[:4]:
            persona_dict = {
                "name": persona.name,
                "age": persona.age,
                "location": persona.location,
                "quote": persona.quote,
                "family_status": persona.family_status,
                "occupation": persona.occupation,
                "tech_savviness": persona.tech_savviness,
                "clinical_scenario": persona.clinical_scenario,
                "recent_diagnosis": persona.recent_diagnosis,
                "mindset": persona.mindset,
                "goals": persona.goals,
                "fears": persona.fears,
                "information_channels": persona.information_channels,
                "key_question_for_doctor": persona.key_question_for_doctor,
                "marketing_message": persona.marketing_message,
                "marketing_tone": persona.marketing_tone,
                "call_to_action": persona.call_to_action,
                "personality_traits": persona.personality_traits
            }
            pptx_gen.add_patient_persona_slide(
                persona_dict,
                brand.brand_name,
                brand.primary_color,
                brand.secondary_color
            )

        # Add HCP persona slides
        for persona in all_personas[4:]:
            persona_dict = {
                "name": persona.name,
                "age": persona.age,
                "location": persona.location,
                "job_title": persona.job_title,
                "practice_type": persona.practice_type,
                "quote": persona.quote,
                "about": persona.about,
                "motivations": persona.motivations,
                "frustrations": persona.frustrations,
                "how_they_view_brand": persona.how_they_view_brand,
                "marketing_channels": persona.marketing_channels,
                "marketing_messaging": persona.marketing_messaging,
                "marketing_tactics": persona.marketing_tactics,
                "personality_traits": persona.personality_traits
            }
            pptx_gen.add_hcp_persona_slide(
                persona_dict,
                brand.brand_name,
                brand.primary_color,
                brand.secondary_color
            )

        # Save PowerPoint
        output_dir = os.path.join(settings.UPLOAD_DIR, "decks")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"personas_{brand.brand_name}_{timestamp}.pptx"
        filepath = os.path.join(output_dir, filename)

        pptx_gen.save(filepath)

        # Update generation with deck URL
        deck_url = f"/uploads/decks/{filename}"
        update_persona_generation(
            db, generation_id, "completed",
            deck_url=deck_url
        )

    except Exception as e:
        update_persona_generation(
            db, generation_id, "failed",
            error_message=str(e)
        )


@router.post("/generate", response_model=PersonaGeneration, status_code=status.HTTP_201_CREATED)
async def generate_personas(
    request: PersonaGenerationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personas for active brand"""
    # Get active brand
    brand = get_active_brand(db, current_user.id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active brand. Please select a brand first."
        )

    # Create generation request
    generation = create_persona_generation(
        db, request, current_user.id, brand.id, current_user.tenant_id
    )

    # Start background task
    background_tasks.add_task(generate_personas_task, generation.id, db)

    return generation


@router.get("/generations", response_model=List[PersonaGeneration])
async def list_generations(
    brand_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all persona generations for current user"""
    if brand_id:
        # Check access to brand
        if not user_has_brand_access(db, brand_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this brand"
            )

    generations = get_user_persona_generations(db, current_user.id, brand_id)
    return generations


@router.get("/generations/{generation_id}", response_model=PersonaGenerationWithPersonas)
async def get_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific persona generation with all personas"""
    generation = get_persona_generation(db, generation_id)
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )

    # Check access
    if generation.user_id != current_user.id:
        if not user_has_brand_access(db, generation.brand_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this generation"
            )

    # Get personas
    personas = get_generation_personas(db, generation_id)

    return PersonaGenerationWithPersonas(
        **generation.__dict__,
        personas=personas
    )
