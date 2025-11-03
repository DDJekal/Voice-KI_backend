"""File-basierte Data Source - lädt JSON-Dateien aus lokalem Verzeichnis"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .base import DataSource


class FileDataSource(DataSource):
    """
    Lädt Daten aus lokalen JSON-Dateien.
    Für Entwicklung und Tests ohne Cloud-Abhängigkeit.
    """

    def __init__(self, data_dir: str):
        """
        Initialisiert FileDataSource.
        
        Args:
            data_dir: Pfad zum Verzeichnis mit JSON-Dateien
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def get_applicant_profile(self, applicant_id: str) -> Dict[str, Any]:
        """
        Lädt Bewerberprofil - flexibel für beide Strukturen.
        
        Unterstützt:
        - Neue Struktur: Bewerberprofil.json (eine Datei)
        - Alte Struktur: Bewerberprofil_Teil1.json + Teil2.json
        
        Args:
            applicant_id: Wird für Logging verwendet (File-basiert ignoriert ID)
            
        Returns:
            Dict mit Bewerberdaten
        """
        # Variante 1: Neue Struktur (eine Datei)
        profile_path = self.data_dir / "Bewerberprofil.json"
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Variante 2: Alte Struktur (Teil 1 + Teil 2)
        teil1_path = self.data_dir / "Bewerberprofil_Teil1.json"
        if teil1_path.exists():
            with open(teil1_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)

            # Teil 2 laden (optional)
            teil2_path = self.data_dir / "Bewerberprofil_Teil2.json"
            if teil2_path.exists():
                with open(teil2_path, 'r', encoding='utf-8') as f:
                    teil2 = json.load(f)
                    # Merge Teil 2 in Profile
                    profile.update(teil2)

            return profile
        
        raise FileNotFoundError(
            f"Kein Bewerberprofil gefunden in {self.data_dir}. "
            "Erwartet: 'Bewerberprofil.json' oder 'Bewerberprofil_Teil1.json'"
        )

    def get_applicant_address(self, applicant_id: str) -> Dict[str, Any]:
        """
        Lädt Adresse - flexibel für beide Strukturen.
        
        Unterstützt:
        - Neue Struktur: "Adresse des Bewerbers.json" (separate Datei)
        - Alte Struktur: Bewerberprofil_Teil2.json
        
        Args:
            applicant_id: Wird für Logging verwendet
            
        Returns:
            Dict mit Adressdaten oder leeres Dict
        """
        # Variante 1: Separate Adress-Datei (neu)
        address_path = self.data_dir / "Adresse des Bewerbers.json"
        if address_path.exists():
            with open(address_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Variante 2: In Teil2 integriert (alt)
        teil2_path = self.data_dir / "Bewerberprofil_Teil2.json"
        if teil2_path.exists():
            with open(teil2_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}  # Fallback: leeres Dict

    def get_company_profile(self, company_id: str) -> Dict[str, Any]:
        """
        Lädt Unternehmensprofil (Q&A Format für Onboarding).
        
        Unterscheidet zwischen:
        - Neues Format: question/answer Paare (Onboarding-Daten)
        - Altes Format: Nur questions (Gesprächsprotokoll)
        
        Args:
            company_id: Wird für Logging verwendet
            
        Returns:
            Dict mit Firmendaten
        """
        # Versuche zuerst Unternehmensprofil.json
        profile_path = self.data_dir / "Unternehmensprofil.json"
        if not profile_path.exists():
            # Fallback auf Unternehmensprofil2.json
            profile_path = self.data_dir / "Unternehmensprofil2.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(
                f"Kein Unternehmensprofil gefunden in {self.data_dir}"
            )

        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_conversation_protocol(self, campaign_id: str) -> Dict[str, Any]:
        """
        Lädt Gesprächsprotokoll - flexibel für beide Strukturen.
        
        Unterstützt:
        - Neue Struktur: Separate Gesprächsprotokoll*.json Datei
        - Alte Struktur: Im Unternehmensprofil.json enthalten
        
        Args:
            campaign_id: Wird für Logging verwendet
            
        Returns:
            Dict mit Protokoll-Struktur
        """
        # Variante 1: Separate Gesprächsprotokoll-Dateien (neu)
        protocol_patterns = [
            "Gesprächsprotokoll.json",
            "Gesprächsprotokoll_Beispiel.json",
            "Gesprächsprotokoll_Beispiel1.json",
            "Gesprächsprotokoll_Beispiel2.json"
        ]
        
        for pattern in protocol_patterns:
            protocol_path = self.data_dir / pattern
            if protocol_path.exists():
                with open(protocol_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Variante 2: Im Unternehmensprofil enthalten (alt)
        # Prüfe ob Unternehmensprofil das alte Format hat (= Gesprächsprotokoll)
        company_profile = self.get_company_profile(campaign_id)
        
        # Wenn es das alte Format ist (kein answer Feld), ist es das Gesprächsprotokoll
        if not self._is_qa_format(company_profile):
            return company_profile
        
        # Neues Format ohne separates Protokoll → leeres Protokoll
        return {"pages": []}
    
    def _is_qa_format(self, data: Dict) -> bool:
        """
        Prüft ob neues Q&A Format (mit answer Feld).
        
        Args:
            data: Zu prüfendes Dict
            
        Returns:
            True wenn Q&A Format, False sonst
        """
        if "pages" in data and len(data["pages"]) > 0:
            first_page = data["pages"][0]
            if "prompts" in first_page and len(first_page["prompts"]) > 0:
                first_prompt = first_page["prompts"][0]
                return "answer" in first_prompt
        return False

