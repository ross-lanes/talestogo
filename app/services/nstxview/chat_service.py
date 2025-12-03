"""
NSTXView Chat Service - AI-powered chat interface for querying plasma physics data.

Uses Claude with tool use to answer questions about the NSTXView database.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.config import ANTHROPIC_API_KEY
from app.models import NSTXPaper, NSTXShot, NSTXParameter, NSTXPhenomenon, NSTXProcessingStatus

logger = logging.getLogger(__name__)


# Define the tools that Claude can use
NSTXVIEW_TOOLS = [
    {
        "name": "search_papers",
        "description": "Search across papers using text matching. Returns papers that match the search query in title, abstract, or authors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find papers (searches title, abstract, authors)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_paper_details",
        "description": "Get full details of a specific paper including its shots, parameters, and phenomena.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "integer",
                    "description": "The database ID of the paper"
                }
            },
            "required": ["paper_id"]
        }
    },
    {
        "name": "query_shots",
        "description": "Find plasma shots matching specific criteria. Shots are individual plasma experiments identified by 6-digit numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shot_number": {
                    "type": "integer",
                    "description": "Specific shot number to look up (6 digits, 100000-199999)"
                },
                "role": {
                    "type": "string",
                    "enum": ["primary", "comparison", "reference"],
                    "description": "Filter by the role of the shot in the paper"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "get_parameter_statistics",
        "description": "Get aggregate statistics for a plasma parameter across all papers. Returns min, max, average values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parameter_name": {
                    "type": "string",
                    "description": "Name of the parameter (e.g., 'ion_temperature', 'electron_density', 'plasma_current')"
                }
            },
            "required": ["parameter_name"]
        }
    },
    {
        "name": "list_parameters",
        "description": "Get all unique parameter names in the database with their occurrence counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of parameters to return (default 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "list_phenomena",
        "description": "Get all unique phenomenon types in the database with their occurrence counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of phenomena to return (default 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "get_database_stats",
        "description": "Get overall statistics about the NSTXView database including paper counts, shot counts, and processing status.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_by_phenomenon",
        "description": "Find papers and shots that discuss a specific plasma phenomenon.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phenomenon_type": {
                    "type": "string",
                    "description": "Type of phenomenon to search for (e.g., 'H-mode', 'ELM', 'disruption')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 10)",
                    "default": 10
                }
            },
            "required": ["phenomenon_type"]
        }
    }
]


SYSTEM_PROMPT = """You are a research assistant for plasma physicists, specializing in NSTX/NSTX-U spherical tokamak research at Princeton Plasma Physics Laboratory. You have access to a database of scholarly papers about plasma physics experiments.

TONE AND STYLE:
- Be serious, thoughtful, and scientific in all responses
- Avoid hype, enthusiasm, or promotional language
- Write as a colleague would to another scientist
- Be concise and precise; avoid unnecessary elaboration
- Use appropriate plasma physics terminology

CITATION REQUIREMENTS:
- ALWAYS cite the specific paper(s) that information comes from
- Include author names and publication year when available (e.g., "Smith et al., 2015")
- If providing quantitative data, specify which paper reported those values
- If information comes from multiple papers, cite all relevant sources
- If no papers in the database support a claim, clearly state that

You can help researchers:
- Search for papers on specific topics
- Find information about specific plasma shots (experiments)
- Look up plasma parameter values (temperatures, densities, currents, etc.)
- Explore phenomena studied in the papers (H-mode, ELMs, instabilities, etc.)
- Get statistics and summaries from the database

When answering questions:
1. Use the available tools to query the database for accurate information
2. Always cite specific papers with author and year
3. Provide quantitative data with uncertainty when available
4. Be precise about plasma physics terminology
5. Clearly distinguish between what the database shows and what you cannot determine
6. If the database lacks information to answer a question, say so directly

Shot numbers are 6-digit integers starting with 1 (e.g., 141234).
Common plasma parameters include: ion_temperature, electron_temperature, electron_density, plasma_current, magnetic_field, beta, confinement_time.
Common phenomena include: H-mode, L-mode, ELM, disruption, kink_mode, tearing_mode, ITB (internal transport barrier)."""


class NSTXViewChatService:
    """Chat service for NSTXView using Claude with tool use."""

    # Use Claude Sonnet 4 for current API compatibility
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096

    def __init__(self, db: Session, api_key: Optional[str] = None):
        """
        Initialize the chat service.

        Args:
            db: SQLAlchemy database session
            api_key: Anthropic API key (uses env var if not provided)
        """
        self.db = db
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        self.client = Anthropic(api_key=self.api_key)

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool and return the result as a string."""
        try:
            if tool_name == "search_papers":
                return self._search_papers(
                    tool_input.get("query", ""),
                    tool_input.get("limit", 10)
                )
            elif tool_name == "get_paper_details":
                return self._get_paper_details(tool_input.get("paper_id"))
            elif tool_name == "query_shots":
                return self._query_shots(
                    tool_input.get("shot_number"),
                    tool_input.get("role"),
                    tool_input.get("limit", 20)
                )
            elif tool_name == "get_parameter_statistics":
                return self._get_parameter_statistics(tool_input.get("parameter_name"))
            elif tool_name == "list_parameters":
                return self._list_parameters(tool_input.get("limit", 20))
            elif tool_name == "list_phenomena":
                return self._list_phenomena(tool_input.get("limit", 20))
            elif tool_name == "get_database_stats":
                return self._get_database_stats()
            elif tool_name == "search_by_phenomenon":
                return self._search_by_phenomenon(
                    tool_input.get("phenomenon_type", ""),
                    tool_input.get("limit", 10)
                )
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return json.dumps({"error": str(e)})

    def _search_papers(self, query: str, limit: int) -> str:
        """Search papers by title, abstract, or authors."""
        search_term = f"%{query}%"
        papers = self.db.query(NSTXPaper).filter(
            NSTXPaper.status == NSTXProcessingStatus.COMPLETED.value,
            or_(
                NSTXPaper.title.ilike(search_term),
                NSTXPaper.abstract.ilike(search_term),
                NSTXPaper.authors.ilike(search_term)
            )
        ).limit(limit).all()

        results = []
        for paper in papers:
            results.append({
                "id": paper.id,
                "title": paper.title,
                "authors": json.loads(paper.authors) if paper.authors else None,
                "journal": paper.journal,
                "abstract": paper.abstract[:500] + "..." if paper.abstract and len(paper.abstract) > 500 else paper.abstract,
                "doi": paper.doi
            })

        return json.dumps({"papers": results, "count": len(results)})

    def _get_paper_details(self, paper_id: int) -> str:
        """Get full details of a paper."""
        paper = self.db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
        if not paper:
            return json.dumps({"error": f"Paper {paper_id} not found"})

        # Get associated shots
        shots = self.db.query(NSTXShot).filter(NSTXShot.paper_id == paper_id).all()

        # Get associated parameters
        params = self.db.query(NSTXParameter).filter(NSTXParameter.paper_id == paper_id).all()

        # Get associated phenomena
        phenomena = self.db.query(NSTXPhenomenon).filter(NSTXPhenomenon.paper_id == paper_id).all()

        result = {
            "id": paper.id,
            "title": paper.title,
            "authors": json.loads(paper.authors) if paper.authors else None,
            "journal": paper.journal,
            "abstract": paper.abstract,
            "key_findings": json.loads(paper.key_findings) if paper.key_findings else None,
            "doi": paper.doi,
            "shots": [
                {"shot_number": s.shot_number, "role": s.role, "context": s.context}
                for s in shots
            ],
            "parameters": [
                {
                    "name": p.parameter_name,
                    "value": p.value,
                    "unit": p.unit,
                    "context": p.context
                }
                for p in params[:20]  # Limit to avoid huge responses
            ],
            "phenomena": [
                {
                    "type": ph.phenomenon_type,
                    "description": ph.description,
                    "is_primary_focus": ph.is_primary_focus
                }
                for ph in phenomena
            ]
        }

        return json.dumps(result)

    def _query_shots(self, shot_number: Optional[int], role: Optional[str], limit: int) -> str:
        """Query shots by number or role."""
        query = self.db.query(NSTXShot).join(NSTXPaper)

        if shot_number:
            query = query.filter(NSTXShot.shot_number == shot_number)
        if role:
            query = query.filter(NSTXShot.role == role)

        shots = query.limit(limit).all()

        results = []
        for shot in shots:
            results.append({
                "shot_number": shot.shot_number,
                "role": shot.role,
                "context": shot.context,
                "paper_id": shot.paper_id,
                "paper_title": shot.paper.title if shot.paper else None
            })

        return json.dumps({"shots": results, "count": len(results)})

    def _get_parameter_statistics(self, parameter_name: str) -> str:
        """Get statistics for a parameter."""
        params = self.db.query(NSTXParameter).filter(
            NSTXParameter.parameter_name.ilike(f"%{parameter_name}%")
        ).all()

        if not params:
            return json.dumps({"error": f"No data found for parameter: {parameter_name}"})

        values = [p.value for p in params if p.value is not None]
        paper_ids = set(p.paper_id for p in params)

        # Get most common unit
        units = [p.unit for p in params if p.unit]
        unit = max(set(units), key=units.count) if units else None

        result = {
            "parameter_name": parameter_name,
            "count": len(params),
            "min_value": min(values) if values else None,
            "max_value": max(values) if values else None,
            "avg_value": sum(values) / len(values) if values else None,
            "unit": unit,
            "paper_count": len(paper_ids)
        }

        return json.dumps(result)

    def _list_parameters(self, limit: int) -> str:
        """List all unique parameter names."""
        results = self.db.query(
            NSTXParameter.parameter_name,
            NSTXParameter.parameter_category,
            func.count(NSTXParameter.id).label('count')
        ).group_by(
            NSTXParameter.parameter_name,
            NSTXParameter.parameter_category
        ).order_by(func.count(NSTXParameter.id).desc()).limit(limit).all()

        return json.dumps({
            "parameters": [
                {"name": r.parameter_name, "category": r.parameter_category, "count": r.count}
                for r in results
            ]
        })

    def _list_phenomena(self, limit: int) -> str:
        """List all unique phenomenon types."""
        results = self.db.query(
            NSTXPhenomenon.phenomenon_type,
            NSTXPhenomenon.phenomenon_category,
            func.count(NSTXPhenomenon.id).label('count')
        ).group_by(
            NSTXPhenomenon.phenomenon_type,
            NSTXPhenomenon.phenomenon_category
        ).order_by(func.count(NSTXPhenomenon.id).desc()).limit(limit).all()

        return json.dumps({
            "phenomena": [
                {"type": r.phenomenon_type, "category": r.phenomenon_category, "count": r.count}
                for r in results
            ]
        })

    def _get_database_stats(self) -> str:
        """Get overall database statistics."""
        total_papers = self.db.query(func.count(NSTXPaper.id)).scalar()
        completed_papers = self.db.query(func.count(NSTXPaper.id)).filter(
            NSTXPaper.status == NSTXProcessingStatus.COMPLETED.value
        ).scalar()
        total_shots = self.db.query(func.count(NSTXShot.id)).scalar()
        unique_shots = self.db.query(func.count(func.distinct(NSTXShot.shot_number))).scalar()
        total_parameters = self.db.query(func.count(NSTXParameter.id)).scalar()
        total_phenomena = self.db.query(func.count(NSTXPhenomenon.id)).scalar()

        return json.dumps({
            "papers": {"total": total_papers, "completed": completed_papers},
            "shots": {"total": total_shots, "unique": unique_shots},
            "parameters": {"total": total_parameters},
            "phenomena": {"total": total_phenomena}
        })

    def _search_by_phenomenon(self, phenomenon_type: str, limit: int) -> str:
        """Search for papers/shots by phenomenon type."""
        phenomena = self.db.query(NSTXPhenomenon).join(NSTXPaper).filter(
            NSTXPhenomenon.phenomenon_type.ilike(f"%{phenomenon_type}%")
        ).limit(limit).all()

        results = []
        for ph in phenomena:
            shot_number = None
            if ph.shot_id:
                shot = self.db.query(NSTXShot).filter(NSTXShot.id == ph.shot_id).first()
                shot_number = shot.shot_number if shot else None

            results.append({
                "phenomenon_type": ph.phenomenon_type,
                "category": ph.phenomenon_category,
                "description": ph.description,
                "is_primary_focus": ph.is_primary_focus,
                "paper_id": ph.paper_id,
                "paper_title": ph.paper.title if ph.paper else None,
                "shot_number": shot_number
            })

        return json.dumps({"phenomena": results, "count": len(results)})

    def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a chat message and return the response.

        Args:
            user_message: The user's question or message
            conversation_history: Previous messages in the conversation (optional)

        Returns:
            Dict with 'response' (text) and 'tool_calls' (list of tools used)
        """
        # Build messages list
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []

        try:
            # Initial API call
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=NSTXVIEW_TOOLS,
                messages=messages
            )

            # Handle tool use in a loop until we get a final response
            while response.stop_reason == "tool_use":
                # Extract tool use blocks
                tool_results = []
                assistant_content = response.content

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = block.id

                        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
                        tool_calls_made.append({"name": tool_name, "input": tool_input})

                        # Execute the tool
                        result = self._execute_tool(tool_name, tool_input)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                # Add assistant message and tool results to messages
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})

                # Continue the conversation
                response = self.client.messages.create(
                    model=self.MODEL,
                    max_tokens=self.MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=NSTXVIEW_TOOLS,
                    messages=messages
                )

            # Extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_text += block.text

            return {
                "response": final_text,
                "tool_calls": tool_calls_made
            }

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "tool_calls": tool_calls_made,
                "error": str(e)
            }

    def generate_conversation_title(self, first_user_message: str) -> str:
        """
        Generate a short title for the conversation based on the first user message.

        Args:
            first_user_message: The first message from the user

        Returns:
            A short (3-6 word) title summarizing the conversation topic
        """
        prompt = f"""Generate a short (3-6 words) title summarizing this plasma physics research question.

Question: {first_user_message[:500]}

Return ONLY the title, no quotes or punctuation at the end. Examples of good titles:
- H-mode Transition Analysis
- Lithium Wall Conditioning Effects
- Ion Temperature in NSTX-U
- ELM Stability Studies"""

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            title = response.content[0].text.strip()
            # Clean up common issues
            title = title.strip('"\'')
            if title.endswith('.'):
                title = title[:-1]
            return title[:255]  # Ensure within DB limit
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return None

    def generate_conversation_summary(self, messages: List[Dict]) -> str:
        """
        Generate a 1-2 sentence summary of the conversation for list view.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            A brief summary (max 150 chars) of the conversation
        """
        # Format messages for summarization (limit to first 6 messages to keep prompt small)
        formatted = "\n".join([
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in messages[:6]
        ])

        prompt = f"""Summarize this plasma physics research conversation in 1-2 sentences (max 150 characters).

{formatted}

Return ONLY the summary, nothing else."""

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.content[0].text.strip()
            return summary[:150]  # Ensure within limit
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
