"""Abstract Base Class für Data Sources"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class DataSource(ABC):
    """
    Abstract interface für verschiedene Datenquellen.
    Ermöglicht einfachen Austausch zwischen FileLoader, API Client, etc.
    """

    @abstractmethod
    def get_applicant_profile(self, applicant_id: str) -> Dict[str, Any]:
        """
        Lädt Bewerberprofil für gegebene ID.
        
        Args:
            applicant_id: Eindeutige Bewerber-ID
            
        Returns:
            Dict mit Bewerberdaten (first_name, last_name, email, etc.)
        """
        pass

    @abstractmethod
    def get_applicant_address(self, applicant_id: str) -> Dict[str, Any]:
        """
        Lädt Adressdaten für Bewerber.
        
        Args:
            applicant_id: Eindeutige Bewerber-ID
            
        Returns:
            Dict mit Adressdaten (street, house_number, city, postal_code)
        """
        pass

    @abstractmethod
    def get_company_profile(self, company_id: str) -> Dict[str, Any]:
        """
        Lädt Unternehmensprofil.
        
        Args:
            company_id: Eindeutige Unternehmens-ID
            
        Returns:
            Dict mit Firmendaten
        """
        pass

    @abstractmethod
    def get_conversation_protocol(self, campaign_id: str) -> Dict[str, Any]:
        """
        Lädt Gesprächsprotokoll für Kampagne.
        
        Args:
            campaign_id: Eindeutige Kampagnen-ID
            
        Returns:
            Dict mit Protokoll-Struktur (pages, prompts)
        """
        pass

