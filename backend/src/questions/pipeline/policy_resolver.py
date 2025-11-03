"""
Policy Resolver Pipeline Stage

Applies conversation policies to question catalog for intelligent flow control.
Implements slot-tracking, keyword triggers, and context-aware rules.
"""

import logging
from typing import List, Dict, Any, Tuple
from copy import deepcopy

from ..types import (
    Question, 
    SlotConfig, 
    GateConfig, 
    ConversationHints,
    KeywordTrigger
)

logger = logging.getLogger(__name__)


class PolicyResolver:
    """
    Applies conversation policies to question catalog.
    
    Policies enhance questions with:
    - Slot-tracking for required information
    - Keyword-based triggers for context-aware responses
    - Gate sequencing for must-have criteria
    - Diversification to avoid repetitive questioning
    - Confidence checks for unclear answers
    """
    
    def __init__(self):
        """Initialize policy resolver"""
        self.audit_log: Dict[str, Any] = {"policies_applied": []}
    
    def apply_policies(
        self, 
        questions: List[Question],
        policy_level: str = "standard"
    ) -> Tuple[List[Question], Dict[str, Any]]:
        """
        Apply all policies to question catalog.
        
        Args:
            questions: List of questions to enhance
            policy_level: "basic", "standard", or "advanced"
            
        Returns:
            Tuple of (enhanced questions, audit log)
        """
        logger.info(f"Applying policies at level: {policy_level}")
        
        # Reset audit log
        self.audit_log = {"policies_applied": []}
        
        # Deep copy to avoid mutations
        questions = deepcopy(questions)
        
        # Basic policies (always applied)
        questions = self._consent_first_policy(questions)
        questions = self._slot_dependency_policy(questions)
        questions = self._gate_sequence_policy(questions)
        
        # Standard and Advanced policies
        if policy_level in ["standard", "advanced"]:
            questions = self._keyword_trigger_policy(questions)
            questions = self._diversification_policy(questions)
            questions = self._confidence_check_policy(questions)
        
        # Advanced only policies
        if policy_level == "advanced":
            questions = self._empathy_enhancement_policy(questions)
        
        logger.info(f"Applied {len(self.audit_log['policies_applied'])} policies")
        
        return questions, self.audit_log
    
    def _consent_first_policy(self, questions: List[Question]) -> List[Question]:
        """
        Ensures DSGVO/consent questions come first.
        
        Policy: Any question related to consent, DSGVO, or data protection
        must have highest priority and come before other questions.
        """
        logger.debug("Applying consent-first policy...")
        
        consent_keywords = ["dsgvo", "einwilligung", "consent", "datenschutz", "speichern"]
        
        for q in questions:
            q_lower = q.question.lower() + q.id.lower()
            
            if any(kw in q_lower for kw in consent_keywords):
                # Set highest priority
                q.priority = 1
                q.category_order = 0
                
                # Add slot config
                if not q.slot_config:
                    q.slot_config = SlotConfig(
                        fills_slot="consent_given",
                        required=True,
                        confidence_threshold=0.95
                    )
                
                logger.debug(f"  Consent question prioritized: {q.id}")
                self.audit_log["policies_applied"].append(f"consent_first: {q.id}")
        
        return questions
    
    def _slot_dependency_policy(self, questions: List[Question]) -> List[Question]:
        """
        Adds slot-tracking configuration to questions.
        
        Policy: Required questions must fill slots. Slots define what
        information needs to be collected for successful completion.
        """
        logger.debug("Applying slot-dependency policy...")
        
        slot_mapping = {
            # Identification & Contact
            "name": ["name", "spreche ich mit"],
            "address": ["adresse"],
            "email": ["e-mail", "email"],
            "phone": ["telefon", "erreichbar"],
            
            # Qualification
            "qualifikation": ["examen", "pflegefach", "qualifikation", "ausbildung"],
            
            # Preferences
            "standort": ["standort", "einsatzort"],
            "einsatzbereich": ["abteilung", "bereich", "station", "fachabteilung"],
            "dienstmodell": ["vollzeit", "teilzeit", "arbeitszeit"],
            "verfuegbarkeit": ["verfügbar", "anfangen", "starten", "beginn"],
            
            # Shifts & Schedule
            "schichtmodell": ["schicht", "nacht", "früh", "spät"],
        }
        
        for q in questions:
            if q.required and not q.slot_config:
                q_lower = q.question.lower()
                
                # Find matching slot
                for slot_name, keywords in slot_mapping.items():
                    if any(kw in q_lower for kw in keywords):
                        q.slot_config = SlotConfig(
                            fills_slot=slot_name,
                            required=True,
                            confidence_threshold=0.8
                        )
                        
                        logger.debug(f"  Slot '{slot_name}' assigned to: {q.id}")
                        self.audit_log["policies_applied"].append(
                            f"slot_dependency: {q.id} -> {slot_name}"
                        )
                        break
        
        return questions
    
    def _gate_sequence_policy(self, questions: List[Question]) -> List[Question]:
        """
        Ensures gate questions are asked in correct sequence.
        
        Policy: Gate questions (must-have criteria) must be asked before
        preference questions. Failed gates end conversation early.
        """
        logger.debug("Applying gate-sequence policy...")
        
        gate_questions = [q for q in questions if q.gate_config and q.gate_config.is_gate]
        
        for q in gate_questions:
            # Ensure gates have high priority
            if q.priority > 1:
                q.priority = 1
            
            # Ensure gates are in standardqualifikationen category
            if not q.category or q.category != "standardqualifikationen":
                q.category = "standardqualifikationen"
                q.category_order = 3
            
            # Add slot requirements if not present
            if not q.gate_config.requires_slots:
                q.gate_config.requires_slots = []
            
            # Add slot for gate question itself
            slot_name = f"gate_{q.id}"
            if q.slot_config:
                slot_name = q.slot_config.fills_slot
            else:
                q.slot_config = SlotConfig(
                    fills_slot=slot_name,
                    required=True,
                    confidence_threshold=0.9
                )
            
            q.gate_config.requires_slots.append(slot_name)
            
            logger.debug(f"  Gate question sequenced: {q.id}")
            self.audit_log["policies_applied"].append(f"gate_sequence: {q.id}")
        
        return questions
    
    def _keyword_trigger_policy(self, questions: List[Question]) -> List[Question]:
        """
        Adds keyword-based conversation triggers.
        
        Policy: Certain keywords in candidate responses should trigger
        specific follow-up questions or topic switches.
        """
        logger.debug("Applying keyword-trigger policy...")
        
        # Domain-specific keyword mappings
        keyword_triggers = {
            "Intensiv": ["IMC", "Intensiv", "ITS", "Intensivstation"],
            "OP": ["OP", "Operation", "Operationssaal"],
            "Notaufnahme": ["Notaufnahme", "ZNA", "Rettungsstelle"],
            "Palliativ": ["Palliativ", "Hospiz"],
            "Teilzeit": ["Teilzeit", "Stunden"],
            "Nachtdienst": ["Nacht", "Nachtdienst", "Schicht"],
        }
        
        for q in questions:
            q_lower = q.question.lower()
            
            # Check if question relates to keyword-sensitive topics
            for topic, keywords in keyword_triggers.items():
                if any(kw.lower() in q_lower for kw in keywords):
                    # Add context triggers to gate config
                    if not q.gate_config:
                        q.gate_config = GateConfig()
                    
                    if not q.gate_config.context_triggers:
                        q.gate_config.context_triggers = {}
                    
                    q.gate_config.context_triggers["keywords_to_follow_up"] = keywords
                    
                    logger.debug(f"  Keyword triggers added to: {q.id} ({topic})")
                    self.audit_log["policies_applied"].append(
                        f"keyword_trigger: {q.id} -> {topic}"
                    )
                    break
        
        return questions
    
    def _diversification_policy(self, questions: List[Question]) -> List[Question]:
        """
        Prevents repetitive question patterns.
        
        Policy: Avoid asking multiple yes/no questions in a row.
        Mix question types for natural conversation flow.
        """
        logger.debug("Applying diversification policy...")
        
        # Group questions by category order
        categorized = {}
        for q in questions:
            order = q.category_order or 99
            if order not in categorized:
                categorized[order] = []
            categorized[order].append(q)
        
        # Check for boolean clusters
        for order, qs in categorized.items():
            boolean_count = 0
            
            for q in qs:
                if q.type.value == "boolean":
                    boolean_count += 1
                    
                    # Add diversification hint after 2 booleans
                    if boolean_count >= 2:
                        if not q.conversation_hints:
                            q.conversation_hints = ConversationHints()
                        
                        q.conversation_hints.diversify_after = "boolean"
                        
                        logger.debug(f"  Diversification hint added: {q.id}")
                        self.audit_log["policies_applied"].append(
                            f"diversification: {q.id}"
                        )
                else:
                    boolean_count = 0  # Reset counter
        
        return questions
    
    def _confidence_check_policy(self, questions: List[Question]) -> List[Question]:
        """
        Adds confidence checks and clarification prompts.
        
        Policy: For important questions, add hints for handling
        unclear or uncertain answers.
        """
        logger.debug("Applying confidence-check policy...")
        
        for q in questions:
            # Add confidence checks to required questions
            if q.required and not q.conversation_hints:
                q.conversation_hints = ConversationHints()
            
            if q.required and q.conversation_hints:
                # Add clarification prompts
                if not q.conversation_hints.on_unclear_answer:
                    q.conversation_hints.on_unclear_answer = (
                        "Verstehe ich richtig, dass Sie {interpretation}? "
                        "Bitte korrigieren Sie mich, falls das nicht stimmt."
                    )
                
                # Add confidence boost phrases based on question type
                if q.type.value == "boolean" and not q.conversation_hints.confidence_boost_phrases:
                    q.conversation_hints.confidence_boost_phrases = [
                        "ja", "definitiv", "sicher", "korrekt", "genau",
                        "nein", "nicht", "keineswegs"
                    ]
                
                logger.debug(f"  Confidence check added: {q.id}")
                self.audit_log["policies_applied"].append(f"confidence_check: {q.id}")
        
        return questions
    
    def _empathy_enhancement_policy(self, questions: List[Question]) -> List[Question]:
        """
        Adds empathetic responses for negative answers.
        
        Policy: When candidates give negative answers (especially to gates),
        respond with empathy before moving to alternatives or ending.
        """
        logger.debug("Applying empathy-enhancement policy...")
        
        empathy_phrases = {
            "gate_no": "Vielen Dank für Ihre Offenheit. Lassen Sie uns eine Alternative prüfen.",
            "preference_no": "Kein Problem, das verstehe ich gut.",
            "availability_later": "Das ist völlig in Ordnung. Wir können gerne einen späteren Zeitpunkt besprechen.",
        }
        
        for q in questions:
            # Add empathy to gate questions
            if q.gate_config and q.gate_config.is_gate:
                if not q.conversation_hints:
                    q.conversation_hints = ConversationHints()
                
                if not q.conversation_hints.on_negative_answer:
                    q.conversation_hints.on_negative_answer = empathy_phrases["gate_no"]
                    
                    logger.debug(f"  Empathy phrase added: {q.id}")
                    self.audit_log["policies_applied"].append(f"empathy: {q.id}")
        
        return questions

