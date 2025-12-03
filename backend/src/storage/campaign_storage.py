"""Campaign Storage - Lokale JSON-Speicherung für Campaign Packages"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class CampaignStorage:
    """
    Verwaltet lokale Speicherung von Campaign Packages als JSON-Dateien.
    
    Packages werden in campaign_packages/ Ordner gespeichert.
    Später migrierbar auf Cloud-Storage (S3, Azure, etc.).
    """
    
    def __init__(self, storage_dir: str = "campaign_packages"):
        """
        Args:
            storage_dir: Verzeichnis für Campaign Packages
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
    
    def save_package(self, campaign_id: str, package: Dict[str, Any]) -> Path:
        """
        Speichert Campaign Package als JSON.
        
        Args:
            campaign_id: Campaign ID
            package: Package Dict
        
        Returns:
            Pfad zur gespeicherten Datei
        
        Raises:
            IOError: Bei Schreibfehler
        """
        path = self.storage_dir / f"{campaign_id}.json"
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(package, f, indent=2, ensure_ascii=False)
            
            print(f"Package gespeichert: {path}")
            return path
            
        except Exception as e:
            raise IOError(f"Fehler beim Speichern von Package {campaign_id}: {e}")
    
    def load_package(self, campaign_id: str) -> Dict[str, Any]:
        """
        Lädt Campaign Package aus JSON.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Package Dict
        
        Raises:
            FileNotFoundError: Wenn Package nicht existiert
            json.JSONDecodeError: Bei ungültigem JSON
        """
        path = self.storage_dir / f"{campaign_id}.json"
        
        if not path.exists():
            raise FileNotFoundError(
                f"Campaign Package nicht gefunden: {path}\n"
                f"Bitte zuerst Setup durchführen: python setup_campaign.py --campaign-id {campaign_id}"
            )
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Ungültiges JSON in Package {campaign_id}: {e.msg}",
                e.doc, e.pos
            )
    
    def package_exists(self, campaign_id: str) -> bool:
        """
        Prüft ob Campaign Package existiert.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            True wenn Package existiert
        """
        path = self.storage_dir / f"{campaign_id}.json"
        return path.exists()
    
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Listet alle gespeicherten Campaign Packages.
        
        Returns:
            Liste mit Campaign-Infos (ID, Name, Datum)
        """
        campaigns = []
        
        for json_file in self.storage_dir.glob("*.json"):
            try:
                campaign_id = json_file.stem
                package = self.load_package(campaign_id)
                
                campaigns.append({
                    "campaign_id": campaign_id,
                    "company_name": package.get('company_name', 'Unknown'),
                    "campaign_name": package.get('campaign_name', 'Unknown'),
                    "created_at": package.get('created_at', 'Unknown'),
                    "file_path": str(json_file)
                })
            except Exception as e:
                print(f"⚠️  Fehler beim Laden von {json_file}: {e}")
                continue
        
        return campaigns
    
    def delete_package(self, campaign_id: str) -> bool:
        """
        Löscht Campaign Package.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            True wenn gelöscht, False wenn nicht existiert
        """
        path = self.storage_dir / f"{campaign_id}.json"
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            print(f"🗑️  Package gelöscht: {path}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Löschen: {e}")
            return False
    
    def get_package_info(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt Basis-Infos über Package ohne vollständiges Laden.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Dict mit Infos oder None
        """
        if not self.package_exists(campaign_id):
            return None
        
        try:
            package = self.load_package(campaign_id)
            
            return {
                "campaign_id": campaign_id,
                "company_name": package.get('company_name', ''),
                "campaign_name": package.get('campaign_name', ''),
                "created_at": package.get('created_at', ''),
                "question_count": len(package.get('questions', {}).get('questions', [])),
                "template_sizes": {
                    phase: len(template) 
                    for phase, template in package.get('kb_templates', {}).items()
                }
            }
        except Exception:
            return None
    
    def upload_to_hoc(
        self,
        package: Dict[str, Any],
        hoc_api_url: str,
        hoc_api_key: str
    ) -> str:
        """
        Uploaded Campaign Package zu HOC Cloud.
        
        Args:
            package: Campaign Package
            hoc_api_url: HOC API Base URL
            hoc_api_key: HOC API Key
        
        Returns:
            Download URL
        
        Raises:
            requests.HTTPError: Bei Upload-Fehler
        """
        import requests
        
        campaign_id = package['campaign_id']
        endpoint = f"{hoc_api_url}/campaigns/{campaign_id}/package"
        
        print(f"📤 Upload Package zu HOC: {endpoint}")
        
        try:
            response = requests.post(
                endpoint,
                json=package,
                headers={
                    'Authorization': f'Bearer {hoc_api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            download_url = result.get('download_url', endpoint)
            
            print(f"   ✅ Upload erfolgreich: {download_url}")
            return download_url
            
        except requests.exceptions.Timeout:
            raise IOError(f"HOC Upload Timeout (>30s): {endpoint}")
        except requests.exceptions.HTTPError as e:
            raise IOError(f"HOC Upload HTTP-Fehler {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise IOError(f"HOC Upload fehlgeschlagen: {e}")

