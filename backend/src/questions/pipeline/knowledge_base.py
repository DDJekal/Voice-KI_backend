"""
Knowledge Base Builder

Strukturiert Information-Items aus dem Protokoll in eine Knowledge-Base,
die von VoiceKI/Agent als Context genutzt werden kann.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_knowledge_base(
    information_items: List[Dict], 
    constraints: Any = None,
    priority_items: List[Dict] = None,
    internal_note_items: List[Dict] = None,
    metadata_items: List[Dict] = None
) -> Dict[str, Any]:
    """
    Baut Knowledge-Base aus Information-Items und Constraints.
    
    Args:
        information_items: Klassifizierte Information Items vom Classifier
        constraints: Optional - ExtractResult.constraints für zusätzliche Info
        priority_items: Optional - PRIORITY Items vom Classifier
        internal_note_items: Optional - INTERNAL_NOTE Items vom Classifier
        metadata_items: Optional - METADATA Items vom Classifier
        
    Returns:
        {
            'company_benefits': [...],
            'salary_info': {...},
            'special_benefits': [...],
            'location_priorities': [...],
            'work_conditions': [...],
            'company_culture': [...],
            'general_info': [...],
            'internal_notes': [...],
            'job_context': {...}
        }
    """
    logger.info("🏗️  Building Knowledge Base...")
    
    kb = {
        'company_benefits': [],
        'salary_info': {},
        'special_benefits': [],
        'location_priorities': [],
        'work_conditions': [],
        'company_culture': [],
        'general_info': [],
        'internal_notes': [],  # NEU
        'job_context': {}      # NEU
    }
    
    # 1. Verarbeite Information Items
    for item in information_items:
        text = item.get('text', '').strip()
        if not text:
            continue
        
        # Kategorisiere basierend auf Keywords
        categorized = False
        
        # Benefits
        if _is_benefit(text):
            kb['company_benefits'].append({
                'text': text,
                'source': 'protocol_information'
            })
            categorized = True
        
        # Gehalt/Salary
        if _is_salary_info(text):
            salary_data = _extract_salary_info(text)
            if salary_data:
                kb['salary_info'].update(salary_data)
                categorized = True
        
        # Arbeitszeit/Conditions
        if _is_work_condition(text):
            kb['work_conditions'].append({
                'text': text,
                'source': 'protocol_information'
            })
            categorized = True
        
        # Unternehmenskultur
        if _is_culture_info(text):
            kb['company_culture'].append({
                'text': text,
                'source': 'protocol_information'
            })
            categorized = True
        
        # Fallback: General Info
        if not categorized:
            kb['general_info'].append({
                'text': text,
                'source': 'protocol_information'
            })
    
    # 2. Ergänze aus Constraints (falls vorhanden)
    if constraints:
        _add_constraints_to_kb(kb, constraints)
    
    # 3. Verarbeite Priority Items
    if priority_items:
        for item in priority_items:
            text = item.get('text', '').strip()
            if text:
                kb['location_priorities'].append({
                    'location': text,
                    'level': _extract_priority_level(item),
                    'reason': item.get('reason', ''),
                    'source': 'protocol'
                })
    
    # 4. Verarbeite Internal Note Items
    if internal_note_items:
        for item in internal_note_items:
            text = item.get('text', '').strip()
            if text:
                kb['internal_notes'].append({
                    'text': text,
                    'category': _detect_note_category(text),
                    'source': 'protocol'
                })
    
    # 5. Verarbeite Metadata Items
    if metadata_items:
        for item in metadata_items:
            text = item.get('text', '').strip()
            if text:
                # Job ID extrahieren
                if job_id := _extract_job_id(text):
                    kb['job_context']['job_id'] = job_id
                # Raw metadata speichern
                if 'raw' not in kb['job_context']:
                    kb['job_context']['raw'] = []
                kb['job_context']['raw'].append(text)
    
    # 6. Log Results
    logger.info(f"  ✓ Knowledge Base built:")
    logger.info(f"    - Benefits: {len(kb['company_benefits'])}")
    logger.info(f"    - Salary Info: {bool(kb['salary_info'])}")
    logger.info(f"    - Work Conditions: {len(kb['work_conditions'])}")
    logger.info(f"    - Company Culture: {len(kb['company_culture'])}")
    logger.info(f"    - General Info: {len(kb['general_info'])}")
    logger.info(f"    - Internal Notes: {len(kb['internal_notes'])}")
    logger.info(f"    - Job Context: {bool(kb['job_context'])}")
    
    return kb


def _is_benefit(text: str) -> bool:
    """
    Prüft, ob Text ein Benefit beschreibt.
    """
    benefit_keywords = [
        'urlaub', 'urlaubstage', 'weiterbildung', 'fortbildung',
        'prämie', 'bonus', 'vergünstig', 'kostenlos', 'gratis',
        'zuschuss', 'zusatz', 'benefit', 'vorteil', 'sonderzahlung',
        'weihnachtsgeld', 'urlaubsgeld', 'akademie', 'schulung'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in benefit_keywords)


def _is_salary_info(text: str) -> bool:
    """
    Prüft, ob Text Gehaltsinformationen enthält.
    """
    salary_keywords = [
        'gehalt', 'verdienst', 'entgelt', 'vergütung',
        'tv-öd', 'tvöd', 'tarif', '€', 'euro'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in salary_keywords)


def _is_work_condition(text: str) -> bool:
    """
    Prüft, ob Text Arbeitsbedingungen beschreibt.
    """
    condition_keywords = [
        'vollzeit', 'teilzeit', 'stunden', 'wochenstunden',
        'schicht', 'nachtdienst', 'frühdienst', 'spätdienst',
        'arbeitszeit', 'unbefristet', 'befristet'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in condition_keywords)


def _is_culture_info(text: str) -> bool:
    """
    Prüft, ob Text Unternehmenskultur beschreibt.
    """
    culture_keywords = [
        'kultur', 'atmosphäre', 'team', 'kollegial',
        'wertschätzung', 'tradition', 'familienunternehmen',
        'startup', 'innovation', 'flache hierarchien',
        'dresscode', 'kommunikation', 'du-kultur', 'sie-kultur'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in culture_keywords)


def _extract_salary_info(text: str) -> Dict[str, Any]:
    """
    Extrahiert strukturierte Gehaltsinformationen aus Text.
    
    Returns:
        {
            'amount': 3500,
            'range': {'min': 3000, 'max': 4000},
            'tariff': 'TV-ÖD',
            'notes': [...]
        }
    """
    salary_info = {}
    
    # Suche nach Beträgen
    amount_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*€'
    amounts = re.findall(amount_pattern, text)
    
    if amounts:
        # Parse Amounts
        parsed_amounts = []
        for amount_str in amounts:
            # Normalisiere: 3.500,00 oder 3500.00 -> 3500
            normalized = amount_str.replace('.', '').replace(',', '.')
            try:
                parsed_amounts.append(float(normalized))
            except ValueError:
                continue
        
        if parsed_amounts:
            if len(parsed_amounts) == 1:
                salary_info['amount'] = int(parsed_amounts[0])
            elif len(parsed_amounts) == 2:
                salary_info['range'] = {
                    'min': int(min(parsed_amounts)),
                    'max': int(max(parsed_amounts))
                }
    
    # Suche nach Tarifen
    tariff_pattern = r'(TV-?ÖD|TVÖD|Tarifvertrag|TV-L|TVöD)'
    tariff_match = re.search(tariff_pattern, text, re.IGNORECASE)
    if tariff_match:
        salary_info['tariff'] = tariff_match.group(1)
    
    # Original Text als Note
    if salary_info:
        salary_info['notes'] = [text]
    
    return salary_info


def _add_constraints_to_kb(kb: Dict, constraints: Any) -> None:
    """
    Fügt Informationen aus Constraints zur Knowledge-Base hinzu.
    """
    # Benefits aus Constraints
    if hasattr(constraints, 'benefits') and constraints.benefits:
        for benefit in constraints.benefits:
            if benefit and benefit not in [b.get('text') for b in kb['company_benefits']]:
                kb['company_benefits'].append({
                    'text': benefit,
                    'source': 'extracted_constraints'
                })
    
    # Gehalt aus Constraints
    if hasattr(constraints, 'gehalt') and constraints.gehalt:
        if 'notes' not in kb['salary_info']:
            kb['salary_info']['notes'] = []
        kb['salary_info']['notes'].append(constraints.gehalt)
    
    # Arbeitszeit aus Constraints
    if hasattr(constraints, 'arbeitszeit') and constraints.arbeitszeit:
        arbeitszeit = constraints.arbeitszeit
        if isinstance(arbeitszeit, str):
            text = arbeitszeit
        elif hasattr(arbeitszeit, 'vollzeit') or hasattr(arbeitszeit, 'teilzeit'):
            parts = []
            if hasattr(arbeitszeit, 'vollzeit') and arbeitszeit.vollzeit:
                parts.append(f"Vollzeit: {arbeitszeit.vollzeit}")
            if hasattr(arbeitszeit, 'teilzeit') and arbeitszeit.teilzeit:
                parts.append(f"Teilzeit: {arbeitszeit.teilzeit}")
            text = ", ".join(parts)
        else:
            text = str(arbeitszeit)
        
        if text and text not in [w.get('text') for w in kb['work_conditions']]:
            kb['work_conditions'].append({
                'text': text,
                'source': 'extracted_constraints'
            })


def _extract_priority_level(item: Dict) -> int:
    """
    Extrahiert das Priority-Level aus einem Item.
    
    Returns:
        1 (hoch), 2 (mittel), oder 3 (niedrig)
    """
    text = item.get('text', '').lower()
    
    if any(kw in text for kw in ['dringend', 'priorität 1', 'sehr wichtig', 'sofort']):
        return 1
    elif any(kw in text for kw in ['bevorzugt', 'priorität 2', 'wichtig']):
        return 2
    else:
        return 3


def _detect_note_category(text: str) -> str:
    """
    Erkennt die Kategorie einer Internal Note.
    
    Returns:
        'contact', 'process', 'hint' oder 'general'
    """
    text_lower = text.lower()
    
    # Kontakt-Information (E-Mail, Telefon, Ansprechpartner)
    if any(kw in text_lower for kw in ['ap:', 'ansprechpartner', '@', 'tel:', 'telefon', 'mail']):
        return 'contact'
    
    # Prozess-Notiz
    if any(kw in text_lower for kw in ['prozess', 'ablauf', 'hinweis', 'beachten', 'wichtig']):
        return 'process'
    
    # Recruiter-Hint
    if any(kw in text_lower for kw in ['tipp', 'achtung', 'info']):
        return 'hint'
    
    return 'general'


def _extract_job_id(text: str) -> str:
    """
    Extrahiert eine Job-ID aus einem Text.
    
    Returns:
        Job-ID als String oder None
    """
    # Pattern: JOB-123, Job-ID: 456, etc.
    patterns = [
        r'JOB-?(\d+)',
        r'Job-?ID:?\s*(\d+)',
        r'Stellen-?ID:?\s*(\d+)',
        r'Position-?ID:?\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

