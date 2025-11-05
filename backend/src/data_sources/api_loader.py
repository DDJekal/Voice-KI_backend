"""API Data Source - Lädt Daten von der Cloud-API und transformiert sie ins erwartete Format"""

import requests
from typing import Dict, Any, List, Optional
from .base import DataSource


class APIDataSource(DataSource):
    """
    Lädt Bewerber-, Unternehmens- und Kampagnendaten von der API
    und transformiert sie ins Format, das der Rest des Systems erwartet.
    """
    
    def __init__(
        self, 
        api_url: str, 
        api_key: Optional[str] = None,
        status: str = "new",
        filter_test_applicants: bool = True
    ):
        """
        Args:
            api_url: Base URL der API (z.B. https://high-office.hirings.cloud/api/v1)
            api_key: Optional API Key für Authentifizierung
            status: Bewerber-Status ("new" oder "not_reached")
            filter_test_applicants: Filtert Bewerber mit "Test" im Namen
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.status = status
        self.filter_test_applicants = filter_test_applicants
        self.session = requests.Session()
        
        if api_key:
            # WICHTIG: Kein "Bearer" Präfix! HOC API erwartet direkten Token
            self.session.headers.update({'Authorization': f'{api_key}'})
        
        # Cache für API-Daten
        self._api_data = None
    
    def _load_api_data(self) -> Dict[str, Any]:
        """Lädt alle Daten von der API (einmalig pro Session, dann gecacht)"""
        if self._api_data is None:
            try:
                # API Endpoint: /applicants/{status}
                endpoint = f"{self.api_url}/applicants/{self.status}"
                print(f"Lade Daten von: {endpoint}")
                
                response = self.session.get(endpoint)
                response.raise_for_status()
                self._api_data = response.json()
                
                # Filtere Test-Bewerber
                applicants = self._api_data.get('applicants', [])
                original_count = len(applicants)
                
                if self.filter_test_applicants:
                    applicants = [
                        a for a in applicants 
                        if not self._is_test_applicant(a)
                    ]
                    self._api_data['applicants'] = applicants
                    filtered_count = original_count - len(applicants)
                    
                    if filtered_count > 0:
                        print(f"WARNUNG: {filtered_count} Test-Bewerber herausgefiltert")
                
                print(f"API-Daten geladen: {len(applicants)} Bewerber (Status: {self.status})")
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Fehler beim Laden der API-Daten: {e}")
        
        return self._api_data
    
    def _is_test_applicant(self, applicant: Dict[str, Any]) -> bool:
        """
        Prüft ob Bewerber ein Test-Bewerber ist.
        
        Test-Bewerber haben "Test" im Vor- oder Nachnamen.
        
        Args:
            applicant: Bewerber-Dict aus API
        
        Returns:
            True wenn Test-Bewerber, sonst False
        """
        first_name = applicant.get('first_name', '').lower()
        last_name = applicant.get('last_name', '').lower()
        
        return 'test' in first_name or 'test' in last_name
    
    def _find_applicant_by_id(self, applicant_id: str) -> Dict[str, Any]:
        """
        Findet Bewerber anhand ID (Telefonnummer oder Name).
        
        Args:
            applicant_id: Telefonnummer, Name oder andere Kennung
        
        Returns:
            Bewerber-Dict aus API
        """
        data = self._load_api_data()
        
        for applicant in data.get('applicants', []):
            # Match über verschiedene Kriterien
            phone = applicant.get('telephone', '')
            name = f"{applicant.get('first_name', '')} {applicant.get('last_name', '')}"
            
            if (phone == applicant_id or 
                name.lower() == applicant_id.lower() or
                applicant.get('first_name', '').lower() == applicant_id.lower()):
                return applicant
        
        raise ValueError(f"Bewerber '{applicant_id}' nicht in API gefunden")
    
    def _find_campaign_by_id(self, campaign_id: int) -> Dict[str, Any]:
        """
        Findet Kampagne anhand campaign_id.
        
        Args:
            campaign_id: Campaign ID vom Bewerber
        
        Returns:
            Campaign-Dict aus API
        """
        data = self._load_api_data()
        campaigns = data.get('campaigns', [])
        
        # Suche Campaign mit passender ID
        for campaign in campaigns:
            if campaign.get('id') == campaign_id:
                return campaign
        
        raise ValueError(f"Campaign {campaign_id} nicht gefunden. Verfügbare Campaigns: {len(campaigns)}")
    
    def _find_company_by_id(self, company_id: int) -> Dict[str, Any]:
        """Findet Unternehmen anhand company_id"""
        data = self._load_api_data()
        
        for company in data.get('companies', []):
            if company.get('id') == company_id:
                return company
        
        raise ValueError(f"Company {company_id} nicht gefunden")
    
    def get_applicant_profile(self, applicant_id: str) -> Dict[str, Any]:
        """
        Transformiert API-Bewerber ins erwartete Format.
        
        Erwartet vom System:
        {
            "first_name": "Max",
            "last_name": "Mustermann",
            "telephone": "+49...",
            "email": "max@example.com",
            ...
        }
        
        Args:
            applicant_id: Bewerber-Kennung
        
        Returns:
            Transformiertes Bewerber-Dict
        """
        api_applicant = self._find_applicant_by_id(applicant_id)
        
        # Transformation ins erwartete Format
        return {
            "first_name": api_applicant.get('first_name', ''),
            "last_name": api_applicant.get('last_name', ''),
            "telephone": api_applicant.get('telephone', ''),
            "email": api_applicant.get('email', ''),
            "campaign_id": api_applicant.get('campaign_id')
        }
    
    def get_applicant_address(self, applicant_id: str) -> Dict[str, Any]:
        """
        Holt Bewerber-Adresse.
        
        WICHTIG: Adresse ist NICHT in der API-Antwort!
        Sie wird im Gespräch (Phase 1) erfragt, wenn im Protokoll gefordert.
        
        Args:
            applicant_id: Bewerber-Kennung
        
        Returns:
            Leeres Adress-Dict (wird im Gespräch erfasst)
        """
        return {
            "street": "",
            "house_number": "",
            "postal_code": "",
            "city": "",
            "country": "Deutschland"
        }
    
    def get_company_profile(self, campaign_id: str) -> Dict[str, Any]:
        """
        Transformiert Unternehmens-Daten ins erwartete Format.
        
        Erwartet vom System:
        {
            "name": "Robert Bosch Krankenhaus",
            "size": "3420",
            "address": "Auerbachstraße 110...",
            "benefits": "attraktive Vergütung...",
            ...
        }
        
        Args:
            campaign_id: Campaign ID (wird zu company_id aufgelöst)
        
        Returns:
            Transformiertes Company-Dict
        """
        # 1. Finde Campaign
        campaign = self._find_campaign_by_id(int(campaign_id))
        
        # 2. Finde Company über company_id
        company = self._find_company_by_id(campaign['company_id'])
        
        # 3. Parse Onboarding-Prompts
        onboarding = company.get('onboarding', {})
        prompts = self._flatten_prompts(onboarding.get('pages', []))
        
        # 4. Transformation ins erwartete Format
        company_data = {
            "name": company.get('name', ''),
            "size": self._extract_answer(prompts, "Wie viele Mitarbeitende"),
            "address": self._extract_answer(prompts, "Wie lautet die Adresse"),
            "benefits": self._extract_answer(prompts, "Was unterscheidet"),
            "target_group": self._extract_answer(prompts, "Zielgruppe"),
            "website": self._extract_answer(prompts, "Link zur Organisation"),
            "career_page": self._extract_answer(prompts, "Link zur Karriereseite"),
            "privacy_url": self._extract_answer(prompts, "Link zur Datenschutzerklärung"),
            "impressum": self._extract_answer(prompts, "Link zum Impressum"),
        }
        
        return company_data
    
    def get_conversation_protocol(self, campaign_id: str) -> Dict[str, Any]:
        """
        Transformiert Campaign-Transcript ins erwartete Format.
        
        Erwartet vom System:
        {
            "id": 60,
            "name": "Pflegefachkräfte",
            "pages": [
                {
                    "id": 79,
                    "name": "Der Bewerber erfüllt folgende Kriterien:",
                    "prompts": [
                        {
                            "id": 190,
                            "question": "zwingend: Pflegefachmann /-frau",
                            ...
                        }
                    ]
                }
            ]
        }
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Transformiertes Protokoll-Dict im erwarteten Format
        """
        campaign = self._find_campaign_by_id(int(campaign_id))
        transcript = campaign.get('transcript', {})
        
        # Transformation: API-Format → Erwartetes Format
        return {
            "id": transcript.get('id', 0),
            "name": transcript.get('name', campaign.get('name', '')),
            "pages": transcript.get('pages', [])
        }
    
    def _flatten_prompts(self, pages: List[Dict]) -> List[Dict]:
        """Flacht Prompts aus Pages in eine Liste"""
        prompts = []
        for page in pages:
            prompts.extend(page.get('prompts', []))
        return prompts
    
    def _extract_answer(self, prompts: List[Dict], keyword: str) -> str:
        """
        Extrahiert Antwort basierend auf Keyword in der Frage.
        
        Args:
            prompts: Liste aller Prompts
            keyword: Suchbegriff (case-insensitive)
        
        Returns:
            Antwort oder leerer String
        """
        keyword_lower = keyword.lower()
        
        for prompt in prompts:
            question = prompt.get('question', '').lower()
            if keyword_lower in question:
                return prompt.get('answer', '')
        
        return ''
    
    def list_pending_applicants(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Bewerber mit konfiguriertem Status zurück.
        
        Nützlich für Batch-Verarbeitung.
        Test-Bewerber werden automatisch herausgefiltert (falls aktiviert).
        
        Returns:
            Liste aller Bewerber aus der API (ohne Test-Bewerber)
        """
        data = self._load_api_data()
        return data.get('applicants', [])

