"""Variable Injector - Ersetzt {{variables}} in questions.json mit Bewerberdaten"""

import copy
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VariableInjector:
    """
    Ersetzt {{variable}} Platzhalter in questions.json mit echten Bewerberdaten.
    
    Diese Klasse ist verantwortlich für die Trennung von:
    - Kampagnen-Template (einmalig generiert, ohne PII)
    - Bewerber-spezifische Daten (zur Laufzeit injiziert)
    """
    
    def inject_applicant_data(
        self,
        template: Dict[str, Any],
        profile: Dict[str, Any],
        address: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ersetzt alle {{variable}} Platzhalter mit echten Bewerberdaten.
        
        Args:
            template: questions.json Template mit {{variables}}
            profile: Bewerberprofil JSON (Vorname, Nachname, etc.)
            address: Optional - Bewerberadresse JSON (Straße, PLZ, etc.)
            
        Returns:
            Resolved questions.json mit eingesetzten Werten
            
        Example:
            >>> injector = VariableInjector()
            >>> template = {"questions": [{"question": "Spreche ich mit {{candidatefirst_name}}?"}]}
            >>> profile = {"Vorname": "Max"}
            >>> result = injector.inject_applicant_data(template, profile)
            >>> result["questions"][0]["question"]
            "Spreche ich mit Max?"
        """
        resolved = copy.deepcopy(template)
        
        # Mapping von Variablen zu Datenquellen
        mappings = self._build_mappings(profile, address)
        
        # Statistik für Logging
        total_replacements = 0
        
        # Alle Fragen durchgehen und Platzhalter ersetzen
        if "questions" in resolved:
            for question in resolved["questions"]:
                if "question" in question:
                    original = question["question"]
                    question["question"], count = self._replace_vars(
                        question["question"], 
                        mappings
                    )
                    total_replacements += count
                    
                    if count > 0:
                        logger.debug(
                            f"Replaced {count} variable(s) in question '{question.get('id', 'unknown')}': "
                            f"{original} -> {question['question']}"
                        )
                
                # Auch help_text und context ersetzen, falls vorhanden
                if "help_text" in question:
                    question["help_text"], _ = self._replace_vars(
                        question["help_text"], 
                        mappings
                    )
                
                if "context" in question:
                    question["context"], _ = self._replace_vars(
                        question["context"], 
                        mappings
                    )
                
                # Conversation Flow prüfen
                if "conversation_flow" in question:
                    self._replace_in_conversation_flow(
                        question["conversation_flow"], 
                        mappings
                    )
        
        logger.info(
            f"Variable injection complete: {total_replacements} replacement(s) made"
        )
        
        return resolved
    
    def _build_mappings(
        self, 
        profile: Dict[str, Any], 
        address: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Erstellt Mapping von Variablennamen zu tatsächlichen Werten.
        
        Args:
            profile: Bewerberprofil
            address: Bewerberadresse (optional)
            
        Returns:
            Dictionary mit variable -> value mapping
        """
        mappings = {
            # Aus Profil - unterstütze beide Formate
            "candidatefirst_name": (
                profile.get("Vorname") or 
                profile.get("first_name") or 
                ""
            ),
            "candidatelast_name": (
                profile.get("Nachname") or 
                profile.get("last_name") or 
                ""
            ),
            "telephone": (
                profile.get("Telefonnummer") or 
                profile.get("telephone") or 
                ""
            ),
            "email": (
                profile.get("Email") or 
                profile.get("email") or 
                ""
            ),
        }
        
        # Aus Adresse (falls vorhanden) - unterstütze beide Formate
        if address:
            mappings.update({
                "street": (
                    address.get("Straße") or 
                    address.get("street") or 
                    ""
                ),
                "house_number": (
                    address.get("Hausnummer") or 
                    address.get("house_number") or 
                    ""
                ),
                "postal_code": (
                    address.get("PLZ") or 
                    address.get("postal_code") or 
                    ""
                ),
                "city": (
                    address.get("Ort") or 
                    address.get("city") or 
                    ""
                ),
            })
            
            # Vollständige Adresse (fallback)
            street_val = mappings.get("street", "")
            house_val = mappings.get("house_number", "")
            postal_val = mappings.get("postal_code", "")
            city_val = mappings.get("city", "")
            
            if all([street_val, house_val, postal_val, city_val]):
                mappings["address_full"] = (
                    f"{street_val} {house_val}, {postal_val} {city_val}"
                )
        
        # Entferne None-Werte und leere Strings
        return {k: str(v) for k, v in mappings.items() if v}
    
    def _replace_vars(self, text: str, mappings: Dict[str, str]) -> tuple[str, int]:
        """
        Ersetzt {{var}} Platzhalter im Text.
        
        Args:
            text: Text mit {{variables}}
            mappings: Variable -> Wert Mapping
            
        Returns:
            (replaced_text, replacement_count)
        """
        if not text:
            return text, 0
        
        original = text
        count = 0
        
        # Finde alle {{variable}} Patterns
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, text)
        
        for var in matches:
            if var in mappings:
                text = text.replace(f"{{{{{var}}}}}", mappings[var])
                count += 1
            else:
                logger.warning(
                    f"Variable '{var}' not found in mappings. "
                    f"Available: {list(mappings.keys())}"
                )
        
        return text, count
    
    def _replace_in_conversation_flow(
        self, 
        flow: Dict[str, Any], 
        mappings: Dict[str, str]
    ) -> None:
        """
        Ersetzt Variablen in conversation_flow (rekursiv).
        
        Args:
            flow: Conversation flow dictionary
            mappings: Variable -> Wert Mapping
        """
        for key, value in flow.items():
            if isinstance(value, str):
                flow[key], _ = self._replace_vars(value, mappings)
            elif isinstance(value, dict):
                self._replace_in_conversation_flow(value, mappings)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        value[i], _ = self._replace_vars(item, mappings)
                    elif isinstance(item, dict):
                        self._replace_in_conversation_flow(item, mappings)
    
    def validate_template(self, template: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validiert ob Template alle erwarteten {{variables}} enthält.
        
        Args:
            template: questions.json Template
            
        Returns:
            (is_valid, list_of_found_variables)
        """
        found_vars = set()
        
        def extract_vars(text: str):
            if text:
                matches = re.findall(r'\{\{(\w+)\}\}', text)
                found_vars.update(matches)
        
        if "questions" in template:
            for q in template["questions"]:
                extract_vars(q.get("question", ""))
                extract_vars(q.get("help_text", ""))
                extract_vars(q.get("context", ""))
        
        expected_vars = {
            "candidatefirst_name", "candidatelast_name",
            "street", "house_number", "postal_code", "city"
        }
        
        is_valid = bool(found_vars.intersection(expected_vars))
        
        return is_valid, sorted(list(found_vars))

