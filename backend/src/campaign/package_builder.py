"""Campaign Package Builder - Orchestriert Template-Erstellung und Package-Zusammenstellung"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..data_sources.api_loader import APIDataSource
from .template_builder import TemplateBuilder
from ..questions.builder import build_question_catalog


class CampaignPackageBuilder:
    """
    Erstellt Campaign Packages aus Cloud-API-Daten.
    
    Ein Campaign Package enthält:
    - KB Templates für alle 4 Phasen
    - Questions.json (automatisch generiert mit OpenAI)
    - Company Metadata
    """
    
    def __init__(
        self, 
        prompts_dir: Optional[Path] = None,
        policy_config: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            prompts_dir: Pfad zu VoiceKI _prompts/
            policy_config: Optional policy configuration
        """
        self.template_builder = TemplateBuilder(prompts_dir)
        self.policy_config = policy_config or {"enabled": True, "level": "standard"}
    
    async def build_package(
        self, 
        campaign_id: str, 
        api_source: APIDataSource
    ) -> Dict[str, Any]:
        """
        Erstellt vollständiges Campaign Package.
        
        ACHTUNG: Jetzt ASYNC weil questions.json automatisch generiert wird!
        
        Args:
            campaign_id: Campaign ID
            api_source: API Data Source für Cloud-Daten
        
        Returns:
            Campaign Package Dict
        
        Raises:
            ValueError: Wenn Campaign-Daten ungültig
        """
        print(f"\nErstelle Campaign Package fuer Campaign {campaign_id}")
        
        # 1. Lade Company + Campaign Daten von API
        print("1. Lade Company & Campaign Daten von API...")
        company = api_source.get_company_profile(campaign_id)
        protocol = api_source.get_conversation_protocol(campaign_id)
        
        print(f"   Company: {company.get('name', 'Unknown')}")
        print(f"   Campaign: {protocol.get('name', 'Unknown')}")
        
        # 2. Generiere questions.json automatisch mit OpenAI!
        print("2. Generiere questions.json automatisch (OpenAI)...")
        
        # Context für Question-Builder (mit Policy-Config)
        build_context = {}
        if self.policy_config.get("enabled", True):
            build_context["policy_level"] = self.policy_config.get("level", "standard")
            print(f"   Policies aktiviert (Level: {build_context['policy_level']})")
        else:
            print("   Policies deaktiviert (A/B-Testing)")
        
        questions_catalog = await build_question_catalog(protocol, build_context)
        print(f"   {len(questions_catalog.questions)} Fragen generiert")
        
        # Convert to dict for backward compatibility
        questions = questions_catalog.model_dump()
        
        # 3. Extrahiere Prioritäten
        print("3. Extrahiere Prioritaeten...")
        priorities = self._extract_priorities(company, questions)
        if priorities:
            print(f"   Prioritaeten: {', '.join(priorities)}")
        else:
            print("   Keine Prioritaeten gefunden")
        
        # 4. Package zusammenstellen (KB Templates entfernt - werden in ElevenLabs Dashboard verwaltet)
        print("4. Stelle Package zusammen...")
        package = {
            # Unternehmensinformationen ZUERST (besser für Lesbarkeit)
            "company_name": company.get('name', ''),
            "campaign_id": campaign_id,
            "campaign_name": protocol.get('name', ''),
            "created_at": datetime.utcnow().isoformat() + "Z",
            
            # Company Metadata
            "company_info": {
                "size": company.get('size', ''),
                "address": company.get('address', ''),
                "benefits": company.get('benefits', ''),
                "website": company.get('website', ''),
                "privacy_url": company.get('privacy_url', ''),
                "career_page": company.get('career_page', ''),
            },
            
            # Questions Catalog (für ElevenLabs Conversational AI)
            "questions": questions,
            
            # Metadata
            "meta": {
                "priority_areas": priorities,
                "generated_with": "python-question-generator",
                "note": "KB Templates werden nicht mehr generiert - sie werden direkt im ElevenLabs Dashboard als Prompts konfiguriert"
            }
        }
        
        # 5. Validierung
        self._validate_package(package)
        print("   Package validiert")
        
        return package
    
    def _extract_priorities(
        self, 
        company: Dict[str, Any], 
        questions: Dict[str, Any]
    ) -> list:
        """
        Extrahiert Prioritäts-Bereiche aus Company-Daten.
        
        Sucht nach Keywords wie "Priorität", "besonders", "dringend"
        in Benefits/Pitch.
        
        Args:
            company: Company-Profil
            questions: Questions.json
        
        Returns:
            Liste von Prioritäts-Bereichen
        """
        priorities = []
        
        # Suche in Benefits/Pitch
        benefits = company.get('benefits', '').lower()
        pitch = company.get('company_pitch', '').lower()
        text = benefits + " " + pitch
        
        # Keywords für Prioritäten
        priority_keywords = ['priorität', 'besonders', 'dringend', 'aktuell', 'hoher bedarf']
        
        # Wenn Keywords gefunden, extrahiere Kontext
        for keyword in priority_keywords:
            if keyword in text:
                # Einfache Extraktion - in Produktion mit NLP verbessern
                # Für jetzt: Gebe generischen Hinweis
                priorities.append("Siehe Unternehmensprofil für Details")
                break
        
        return priorities
    
    def _validate_package(self, package: Dict[str, Any]) -> None:
        """
        Validiert Campaign Package.
        
        Args:
            package: Package Dict
        
        Raises:
            ValueError: Wenn Package ungültig
        """
        required_keys = ['campaign_id', 'company_name', 'questions']
        
        for key in required_keys:
            if key not in package:
                raise ValueError(f"Package fehlt required key: {key}")
        
        # Questions muss "questions" Array enthalten
        if 'questions' not in package['questions']:
            raise ValueError("questions.json fehlt 'questions' Array")
