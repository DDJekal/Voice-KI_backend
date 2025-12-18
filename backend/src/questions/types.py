"""
Type definitions for Question Generator

Port of TypeScript types to Python Pydantic models.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    """Question types"""
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    RANKED_LIST = "ranked_list"


class QuestionGroup(str, Enum):
    """Question groups"""
    MOTIVATION = "Motivation"
    STANDORT = "Standort"
    EINSATZBEREICH = "Einsatzbereich"
    QUALIFIKATION = "Qualifikation"
    PRAEFERENZEN = "Präferenzen"
    RAHMEN = "Rahmen"
    WERDEGANG = "Werdegang"
    VERFUEGBARKEIT = "Verfügbarkeit"
    KONTAKT = "Kontakt"


# Site Models
class SiteSource(BaseModel):
    """Source information for a site"""
    page_id: int


class Site(BaseModel):
    """Site/Location with stations"""
    label: str
    display_name: Optional[str] = None  # NEU: Eleganter Name für Standort-Fragen
    stations: List[str] = Field(default_factory=list)
    source: Optional[SiteSource] = None


# Priority Models
class PrioritySource(BaseModel):
    """Source information for a priority"""
    page_id: int
    prompt_id: Optional[int] = None


class Priority(BaseModel):
    """Priority department/role"""
    label: str
    reason: str
    prio_level: Literal[1, 2, 3] = 2
    source: Optional[PrioritySource] = None


# Constraints Models
class Arbeitszeit(BaseModel):
    """Working time constraints"""
    vollzeit: Optional[Union[str, bool]] = None  # Can be string or boolean
    teilzeit: Optional[Union[str, bool]] = None  # Can be string or boolean


class Constraints(BaseModel):
    """Job constraints"""
    arbeitszeit: Optional[Union[Arbeitszeit, str]] = None  # Can be object or simple string
    gehalt: Optional[Dict[str, Any]] = None  # Salary information (betrag, range, etc.)
    benefits: Optional[List[str]] = None  # List of benefits
    tarif: Optional[str] = None
    schichten: Optional[str] = None


# Verbatim Models
class VerbatimCandidate(BaseModel):
    """Verbatim question candidate from protocol"""
    text: str
    page_id: int
    prompt_id: Optional[int] = None
    is_real_question: bool = False


# Protocol Question Models (NEU für Hybrid-Ansatz)
class ProtocolQuestion(BaseModel):
    """Strukturierte Frage direkt aus dem Protokoll (LLM-extrahiert)"""
    text: str
    page_id: int
    prompt_id: Optional[int] = None
    type: Optional[str] = None  # "boolean", "choice", "string", etc.
    options: Optional[List[str]] = None
    category: Optional[str] = None  # "qualifikation", "erfahrung", "praeferenzen"
    is_required: bool = False
    is_gate: bool = False  # Gate-Question?
    help_text: Optional[str] = None


# Extract Result
class ExtractResult(BaseModel):
    """Result from LLM extract pipeline stage"""
    sites: List[Site]
    roles: List[str] = Field(default_factory=list)
    priorities: List[Priority]
    
    # Qualifikationen - NEU: Unterscheidung Bevorzugt/Alternativ/Optional
    preferred: List[str] = Field(default_factory=list)  # Bevorzugte Haupt-Qualifikation
    must_have: List[str] = Field(default_factory=list)  # Zwingende Qualifikationen (Gate)
    alternatives: List[str] = Field(default_factory=list)  # Alternative Qualifikationen
    optional_qualifications: List[str] = Field(default_factory=list)  # Nice-to-have (z.B. Führerschein)
    
    constraints: Constraints = Field(default_factory=Constraints)
    verbatim_candidates: List[VerbatimCandidate] = Field(default_factory=list)
    all_departments: List[str]
    
    # NEU: Unternehmenskultur und Ansprechpartner
    culture_notes: List[str] = Field(default_factory=list)  # "Gespräch per DU", etc.
    department_contacts: Dict[str, str] = Field(default_factory=dict)  # Fachbereich → AP Name
    
    # NEU: Strukturierte Protokoll-Fragen
    protocol_questions: List[ProtocolQuestion] = Field(default_factory=list)
    
    # NEU: Motivation-Dimensionen für Phase 2
    motivation_dimensions: List[str] = Field(default_factory=list)
    
    # NEU: Werdegang-Anforderungen für Phase 5
    career_questions_needed: bool = Field(default=False)


# Conversation Flow Models
class PreCheck(BaseModel):
    """Pre-check question in conversation flow"""
    question: str
    on_yes: Literal["open_question"] = "open_question"
    on_no: Literal["clustered_options"] = "clustered_options"


class OpenQuestion(BaseModel):
    """Open question in conversation flow"""
    question: str
    allow_fuzzy_match: bool = True
    on_unclear: Literal["clustered_options"] = "clustered_options"


class ClusteredCategory(BaseModel):
    """Category in clustered options"""
    id: str
    label: str
    options: List[str]


class ClusteredOptions(BaseModel):
    """Clustered options presentation"""
    presentation_hint: str
    categories: List[ClusteredCategory]


class ConversationalFlow(BaseModel):
    """Conversation flow for questions with many options"""
    pre_check: PreCheck
    open_question: OpenQuestion
    clustered_options: ClusteredOptions


# Condition Models
class ConditionWhen(BaseModel):
    """When clause in condition"""
    field: str
    op: Literal["eq", "in", "exists"]
    value: Optional[Any] = None


class ConditionThen(BaseModel):
    """Then clause in condition"""
    action: Literal["ask", "skip", "prefill", "reorder"]
    value: Optional[Any] = None


class Condition(BaseModel):
    """Conditional logic for questions"""
    when: ConditionWhen
    then: ConditionThen


# Policy Models - Enhanced for intelligent conversation flow
class SlotConfig(BaseModel):
    """Slot-tracking configuration for questions"""
    fills_slot: str
    required: bool = False
    confidence_threshold: float = 0.8
    validation: Optional[Dict[str, Any]] = None


class KeywordTrigger(BaseModel):
    """Keyword-based conversation triggers"""
    keywords: List[str]
    redirect_to: Optional[str] = None
    priority_boost: int = 0


class GateConfig(BaseModel):
    """Gate configuration for must-have criteria"""
    is_gate: bool = False
    is_alternative: bool = False
    alternative_for: Optional[str] = None
    can_satisfy_gate: bool = False
    final_alternative: bool = False
    end_message_if_all_no: Optional[str] = None
    requires_slots: Optional[List[str]] = None
    condition: Optional[str] = None
    context_triggers: Optional[Dict[str, Any]] = None


class ConversationHints(BaseModel):
    """Hints for natural conversation flow"""
    on_unclear_answer: Optional[str] = None
    on_negative_answer: Optional[str] = None
    confidence_boost_phrases: Optional[List[str]] = None
    diversify_after: Optional[str] = None


# Question Source
class QuestionSource(BaseModel):
    """Source information for a question"""
    page_id: Optional[int] = None
    prompt_id: Optional[int] = None
    verbatim: Optional[bool] = None


# Main Question Model
class Question(BaseModel):
    """A question in the catalog"""
    id: str
    question: str
    type: QuestionType
    phase: Optional[Literal[1, 2, 3, 4, 5, 6]] = None  # NEU: Gesprächsphase (1-6)
    preamble: Optional[str] = None  # NEU: Einführung/Kontext vor der Frage
    options: Optional[List[str]] = None
    conversation_flow: Optional[ConversationalFlow] = None
    required: bool
    priority: Literal[1, 2, 3]
    group: Optional[QuestionGroup] = None
    help_text: Optional[str] = None
    input_hint: Optional[str] = None
    conditions: Optional[List[Condition]] = None
    source: Optional[QuestionSource] = None
    context: Optional[str] = None
    
    # Added by categorizer
    category: Optional[str] = None
    category_order: Optional[int] = None
    
    # Added by policy resolver - Enhanced conversation intelligence
    slot_config: Optional[SlotConfig] = None
    gate_config: Optional[GateConfig] = None
    conversation_hints: Optional[ConversationHints] = None
    
    # Added by structure_v2 - For tracking and debugging
    metadata: Optional[Dict[str, Any]] = None


# Question Catalog
class CatalogMeta(BaseModel):
    """Metadata for question catalog"""
    schema_version: str = "1.0"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    generator: str = "voiceki-python-question-builder@1.0.0"
    policies_applied: Optional[List[str]] = None


class QuestionCatalog(BaseModel):
    """Complete question catalog"""
    meta: CatalogMeta = Field(default_factory=CatalogMeta, alias="_meta")
    questions: List[Question]
    
    model_config = {
        "populate_by_name": True
    }


# Conversation Protocol Models (for input)
class ProtocolPrompt(BaseModel):
    """Prompt in conversation protocol"""
    id: int
    position: int
    question: str
    checked: Optional[Any] = None
    information: Optional[Any] = None
    is_template: Optional[bool] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None


class ProtocolPage(BaseModel):
    """Page in conversation protocol"""
    id: int
    name: str
    position: int
    prompts: List[ProtocolPrompt]
    created_on: Optional[str] = None
    updated_on: Optional[str] = None


class ConversationProtocol(BaseModel):
    """Conversation protocol from API"""
    id: int
    name: str
    pages: List[ProtocolPage]
    created_on: Optional[str] = None
    updated_on: Optional[str] = None

