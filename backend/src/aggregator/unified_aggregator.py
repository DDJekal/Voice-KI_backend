"""Unified Aggregator - Zentrale Datenaggregation für alle Phasen"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class UnifiedAggregator:
    """
    Aggregiert Daten aus verschiedenen Quellen und bereitet sie
    für die verschiedenen Voice-Phasen auf.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialisiert Aggregator.
        
        Args:
            prompts_dir: Pfad zum Verzeichnis mit Phase-Prompts (optional)
        """
        self.prompts_dir = prompts_dir

    def aggregate_phase_1(
        self, 
        applicant: Dict[str, Any], 
        address: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregiert Daten für Phase 1: Begrüßung & persönliche Daten.
        
        Args:
            applicant: Bewerberprofil
            address: Adressdaten
            
        Returns:
            Dict mit allen Variablen für Phase 1
        """
        return {
            "candidatefirst_name": applicant.get("first_name", ""),
            "candidatelast_name": applicant.get("last_name", ""),
            "street": address.get("street", ""),
            "house_number": address.get("house_number", ""),
            "postal_code": address.get("postal_code", ""),
            "city": address.get("city", ""),
            "telephone": applicant.get("telephone", ""),
            "email": applicant.get("email", ""),
            # Rolle aus campaign (wird später aus campaign_id gemapped)
            "rolle": "Pflegefachkraft",  # Placeholder
            "privacy_text": self._get_privacy_text(),
            "handoffwindow": "innerhalb von 48 Stunden"
        }

    def aggregate_phase_2(
        self, 
        company: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregiert Daten für Phase 2: Unternehmensvorstellung.
        
        Unterstützt beide Formate:
        - Neues Format: Q&A mit answer Feldern (Onboarding-Daten)
        - Altes Format: Nur questions (Gesprächsprotokoll)
        
        Args:
            company: Unternehmensprofil
            
        Returns:
            Dict mit allen Variablen für Phase 2
        """
        # Prüfe Format und wähle passenden Parser
        if self._is_qa_format(company):
            return self._aggregate_phase_2_from_qa(company)
        else:
            return self._aggregate_phase_2_from_protocol(company)
    
    def _is_qa_format(self, company: Dict) -> bool:
        """Prüft ob Q&A Format (mit answer Feld)"""
        if "pages" in company and len(company["pages"]) > 0:
            first_prompt = company["pages"][0].get("prompts", [{}])[0]
            return "answer" in first_prompt
        return False
    
    def _aggregate_phase_2_from_qa(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrahiert Daten aus Q&A Format (neues Unternehmensprofil).
        
        Args:
            company: Unternehmensprofil mit question/answer Paaren
            
        Returns:
            Dict mit Phase 2 Variablen
        """
        qa_map = self._build_qa_map(company)
        
        # Extrahiere Firmendaten aus Q&A
        company_name = (
            qa_map.get("Wie lautet der vollständige Name Ihrer Organisation?") or
            qa_map.get("Wie lautet der vollständige Name") or
            company.get("name", "")
        )
        
        company_size_str = (
            qa_map.get("Wie viele Mitarbeitende beschäftigen Sie insgesamt?") or
            qa_map.get("Wie viele Mitarbeitende") or
            "300"
        )
        
        # Parse Mitarbeiterzahl
        try:
            company_size = int(company_size_str.strip())
        except (ValueError, AttributeError):
            company_size = 300
        
        company_pitch = (
            qa_map.get("Was unterscheidet Ihre Organisation von Ihren Marktbegleitern?") or
            qa_map.get("Was unterscheidet Ihre Organisation") or
            ""
        )
        
        location = (
            qa_map.get("Wie lautet die Adresse der Organisation?") or
            qa_map.get("Wie lautet die Adresse") or
            ""
        )
        
        target_group = (
            qa_map.get("Wer ist die Zielgruppe Ihres Angebots") or
            ""
        )
        
        return {
            "companyname": company_name,
            "companysize": company_size,
            "companypitch": self._shorten_pitch(company_pitch),
            "companypriorities": self._extract_priorities_from_text(company_pitch),
            "campaignrole_title": target_group or company_name,
            "campaignlocation_label": location
        }
    
    def _aggregate_phase_2_from_protocol(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrahiert Daten aus altem Format (Gesprächsprotokoll).
        Backward compatibility mit bestehenden Test-Daten.
        
        Args:
            company: Gesprächsprotokoll-Struktur
            
        Returns:
            Dict mit Phase 2 Variablen
        """
        company_name = company.get("name", "")
        pages = company.get("pages", [])
        
        # Extrahiere Rahmenbedingungen
        constraints = self._extract_constraints(pages)
        
        # Extrahiere zusätzliche Infos
        additional_info = self._extract_additional_info(pages)
        
        return {
            "companyname": company_name,
            "companysize": 300,  # Default
            "companypitch": self._build_company_pitch(additional_info),
            "companypriorities": self._extract_priorities(pages),
            "campaignrole_title": company_name,
            "campaignlocation_label": self._extract_main_location(pages)
        }

    def aggregate_phase_3(
        self, 
        questions_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregiert Daten für Phase 3: Fragenkatalog.
        
        Args:
            questions_json: Das generierte questions.json vom TypeScript Tool
            
        Returns:
            Dict mit questions.json und Context
        """
        return {
            "questions": questions_json,
            "total_questions": len(questions_json.get("questions", [])),
            "groups": self._extract_question_groups(questions_json),
            "priority_questions": self._filter_priority_questions(questions_json)
        }

    def aggregate_phase_4(
        self, 
        applicant: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregiert Daten für Phase 4: Beruflicher Werdegang.
        
        Args:
            applicant: Bewerberprofil
            
        Returns:
            Dict mit Variablen für Phase 4
        """
        return {
            "candidatefirst_name": applicant.get("first_name", ""),
            "candidatelast_name": applicant.get("last_name", ""),
            "information": applicant.get("information", ""),
            "transcript": applicant.get("transcript", "")
        }

    def _get_privacy_text(self) -> str:
        """Gibt Datenschutz-Einwilligungstext zurück"""
        return (
            "Sind Sie damit einverstanden, dass wir Ihre Daten im Rahmen "
            "dieses Bewerbungsgesprächs verarbeiten und speichern?"
        )
    
    def _build_qa_map(self, company: Dict[str, Any]) -> Dict[str, str]:
        """
        Erstellt question → answer Mapping aus Unternehmensprofil.
        
        Args:
            company: Unternehmensprofil mit Q&A Format
            
        Returns:
            Dict mit question als Key und answer als Value
        """
        qa_map = {}
        
        for page in company.get("pages", []):
            for prompt in page.get("prompts", []):
                question = prompt.get("question", "")
                answer = prompt.get("answer", "")
                if question and answer:
                    qa_map[question] = answer
        
        return qa_map
    
    def _shorten_pitch(self, pitch: str, max_points: int = 3) -> str:
        """
        Kürzt Company Pitch auf wichtigste Punkte.
        
        Args:
            pitch: Vollständiger Pitch-Text
            max_points: Maximale Anzahl Punkte
            
        Returns:
            Gekürzter Pitch
        """
        if not pitch or len(pitch) < 200:
            return pitch
        
        # Split by common delimiters
        points = [p.strip() for p in pitch.split("-") if p.strip()]
        
        if len(points) <= max_points:
            return pitch
        
        # Take first max_points
        return " - ".join(points[:max_points])
    
    def _extract_priorities_from_text(self, text: str) -> str:
        """
        Extrahiert Prioritäten aus Freitext via Keywords.
        
        Args:
            text: Text zum Durchsuchen
            
        Returns:
            Komma-separierte Liste von gefundenen Prioritäten
        """
        keywords = [
            "Palliativ", "Herzkatheter", "Herzkatheterlabor", 
            "Intensiv", "OP", "Geriatrie", "Anästhesie",
            "Onkologie", "Notfall"
        ]
        
        found = [kw for kw in keywords if kw.lower() in text.lower()]
        
        return ", ".join(found) if found else "Alle Bereiche"

    def _extract_constraints(self, pages: list) -> Dict[str, Any]:
        """Extrahiert Rahmenbedingungen aus Protokoll-Pages"""
        constraints = {}
        
        for page in pages:
            if "Rahmenbedingungen" in page.get("name", ""):
                for prompt in page.get("prompts", []):
                    question = prompt.get("question", "")
                    if "Vollzeit" in question:
                        constraints["vollzeit"] = question
                    elif "Teilzeit" in question:
                        constraints["teilzeit"] = question
                    elif "Tarif" in question or "TV" in question:
                        constraints["tarif"] = question
                    elif "Schicht" in question:
                        constraints["schichten"] = question
        
        return constraints

    def _extract_additional_info(self, pages: list) -> list:
        """Extrahiert zusätzliche Infos aus Protokoll"""
        info = []
        
        for page in pages:
            if "Weitere Informationen" in page.get("name", ""):
                for prompt in page.get("prompts", []):
                    info.append(prompt.get("question", ""))
        
        return info

    def _build_company_pitch(self, additional_info: list) -> str:
        """Baut Company Pitch aus zusätzlichen Infos"""
        # Filtere relevante Benefits raus
        benefits = [
            info for info in additional_info
            if any(keyword in info for keyword in [
                "Wohnung", "JobRad", "Tarif", "Weiterbildung", "Kita"
            ])
        ]
        return " ".join(benefits[:3])  # Top 3 Benefits

    def _extract_priorities(self, pages: list) -> str:
        """Extrahiert Prioritäten aus Protokoll"""
        priorities = []
        
        for page in pages:
            for prompt in page.get("prompts", []):
                question = prompt.get("question", "")
                if "Prio" in question or "akut" in question.lower() or "wichtig" in question.lower():
                    # Extrahiere den wichtigen Teil
                    if "Palliativ" in question:
                        priorities.append("Palliativmedizin")
                    elif "Herzkatheter" in question:
                        priorities.append("Herzkatheterlabor")
        
        return ", ".join(priorities) if priorities else "Alle Bereiche"

    def _extract_main_location(self, pages: list) -> str:
        """Extrahiert Hauptstandort aus Protokoll"""
        for page in pages:
            if "Standort" in page.get("name", ""):
                for prompt in page.get("prompts", []):
                    question = prompt.get("question", "")
                    # Suche nach Adresse
                    if any(char.isdigit() for char in question) and "Straße" in question:
                        return question.split(",")[0] if "," in question else question
        
        return "Hauptstandort"

    def _extract_question_groups(self, questions_json: Dict[str, Any]) -> list:
        """Extrahiert alle Gruppen aus questions.json"""
        groups = set()
        questions = questions_json.get("questions", [])
        # Handle case where questions might be a list of strings (fallback)
        if questions and isinstance(questions[0], dict):
            for q in questions:
                if "group" in q and q["group"]:
                    groups.add(q["group"])
        return sorted(list(groups))

    def _filter_priority_questions(self, questions_json: Dict[str, Any]) -> list:
        """Filtert Fragen mit priority=1"""
        return [
            q for q in questions_json.get("questions", [])
            if q.get("priority") == 1 and q.get("required", False)
        ]

