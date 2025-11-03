export interface CategoryMapping {
  category: string;
  order: number;
  description: string;
}

export function categorizeQuestion(
  prompt: any,
  page: any
): CategoryMapping {
  const question = prompt.question.toLowerCase();
  const pageName = page.name.toLowerCase();
  const isRequired = prompt.type === 'yes_no' && question.includes('zwingend');
  
  // Standardqualifikationen (Gate-Questions) - PRÜFE ZUERST!
  // Muss vor Identifikation geprüft werden
  if (isRequired || question.includes('zwingend') || 
      question.includes('pflicht') || question.includes('voraussetzung') ||
      question.includes('examen') || question.includes('abschluss') ||
      question.includes('pflegefach') || question.includes('qualifikation') ||
      pageName.includes('kriterien') || pageName.includes('qualifikation')) {
    return {
      category: 'standardqualifikationen',
      order: 3,
      description: 'Standardqualifikationen (Gate)'
    };
  }
  
  // Identifikation (Bestätigungsfragen: Name, Adresse)
  if (question.includes('spreche ich mit') ||
      (question.includes('adresse') && question.includes('korrekt')) ||
      (question.includes('adresse') && question.includes('bestät'))) {
    return {
      category: 'identifikation',
      order: 1,
      description: 'Identifikation & Bestätigung'
    };
  }
  
  // Kontaktinformationen (Erfassung)
  if ((question.includes('adresse') && !question.includes('korrekt')) ||
      question.includes('telefon') || question.includes('erreichbar') ||
      question.includes('e-mail')) {
    return {
      category: 'kontaktinformationen',
      order: 2,
      description: 'Kontaktdaten'
    };
  }
  
  // Info (Unternehmensvorstellung + Stelleninfos)
  if (prompt.type === 'info' || question.startsWith('!!!') ||
      pageName.includes('weitere informationen')) {
    return {
      category: 'info',
      order: 4,
      description: 'Unternehmensvorstellung & Stelleninfos'
    };
  }
  
  // Standort
  if (question.includes('standort') || question.includes('einsatzort')) {
    return {
      category: 'standort',
      order: 5,
      description: 'Standorte'
    };
  }
  
  // Einsatzbereiche
  if (question.includes('abteilung') || question.includes('bereich') || 
      question.includes('station') || question.includes('fachabteilung')) {
    return {
      category: 'einsatzbereiche',
      order: 6,
      description: 'Einsatzbereiche & Abteilungen'
    };
  }
  
  // Rahmenbedingungen
  if (pageName.includes('rahmenbedingungen') || 
      question.includes('arbeitszeit') || question.includes('schicht') ||
      question.includes('urlaub') || question.includes('vollzeit') ||
      question.includes('teilzeit') || question.includes('vergütung')) {
    return {
      category: 'rahmenbedingungen',
      order: 7,
      description: 'Rahmenbedingungen'
    };
  }
  
  // Default: Zusätzliche Informationen
  return {
    category: 'zusaetzliche_informationen',
    order: 8,
    description: 'Zusätzliche Informationen'
  };
}

