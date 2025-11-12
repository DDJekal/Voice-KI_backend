"""
FastAPI Webhook Server für VoiceKI Campaign Setup

Provides webhook endpoint for HOC to trigger campaign package creation
and automatic upload back to cloud.
"""

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import asyncio
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.data_sources.api_loader import APIDataSource
from src.campaign.package_builder import CampaignPackageBuilder
from src.storage.campaign_storage import CampaignStorage

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="VoiceKI Campaign Setup API",
    version="1.0.0",
    description="Webhook API für Campaign Package Setup via HOC"
)

# CORS Middleware für HOC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Später einschränken auf HOC Domain
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# Request/Response Models
class SetupCampaignRequest(BaseModel):
    campaign_id: str
    force_rebuild: bool = False


class SetupCampaignResponse(BaseModel):
    status: str
    package_id: str
    created_at: str
    download_url: str
    question_count: int
    company_name: str


class CampaignListItem(BaseModel):
    campaign_id: str
    company_name: str
    campaign_name: str
    created_at: str
    question_count: int


class CampaignListResponse(BaseModel):
    count: int
    campaigns: list[CampaignListItem]


# Logging Middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Logs alle eingehenden Requests und Responses"""
    start_time = datetime.utcnow()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} ({duration:.2f}s)")
    
    return response


# Helper Functions
def verify_webhook_auth(authorization: Optional[str] = None) -> bool:
    """
    Verifiziert Webhook Authorization Header.
    
    Args:
        authorization: Authorization Header
    
    Returns:
        True wenn valide
    
    Raises:
        HTTPException: Bei ungültigem Auth
    """
    settings = get_settings()
    
    # Kein Secret konfiguriert - für Dev OK
    if not settings.webhook_secret:
        logger.warning("Webhook Secret nicht konfiguriert - Auth deaktiviert (nur für Dev!)")
        return True
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    expected = f"Bearer {settings.webhook_secret}"
    
    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token"
        )
    
    return True


async def run_campaign_setup(campaign_id: str, force: bool = False):
    """
    Führt Campaign Setup aus (jetzt richtig async!).
    
    Args:
        campaign_id: Campaign ID
        force: Überschreibt existierendes Package
    
    Returns:
        Campaign Package Dict
    """
    settings = get_settings()
    storage = CampaignStorage()
    
    # Existierendes Package nutzen wenn vorhanden
    if storage.package_exists(campaign_id) and not force:
        logger.info(f"Using existing package for campaign {campaign_id}")
        return storage.load_package(campaign_id)
    
    # Neues Package erstellen - jetzt richtig async!
    api = APIDataSource(
        api_url=settings.api_url,
        api_key=settings.api_key,
        status="new",
        filter_test_applicants=True
    )
    
    builder = CampaignPackageBuilder(
        prompts_dir=settings.get_prompts_dir_path()
        # questions_json_path REMOVED - wird jetzt automatisch generiert!
    )
    
    # build_package ist jetzt async!
    package = await builder.build_package(campaign_id, api)
    storage.save_package(campaign_id, package)
    
    return package


async def upload_to_hoc(package: dict) -> str:
    """
    Uploaded Campaign Package zu HOC Cloud (async wrapper).
    
    Args:
        package: Campaign Package
    
    Returns:
        Download URL
    """
    settings = get_settings()
    
    # Prüfe ob Upload aktiviert
    if not settings.hoc_upload_enabled:
        logger.warning("HOC Upload deaktiviert - Package nur lokal gespeichert")
        return f"local://campaign_packages/{package['campaign_id']}.json"
    
    storage = CampaignStorage()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        storage.upload_to_hoc,
        package,
        settings.hoc_api_url,
        settings.api_key
    )


# Endpoints
@app.get("/health")
async def health_check():
    """Health Check Endpoint für Render.com"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook/setup-campaign", response_model=SetupCampaignResponse)
async def setup_campaign_webhook(
    request: SetupCampaignRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None)
):
    """
    Webhook-Endpoint für Campaign Setup.
    
    Wird von HOC Button getriggert.
    
    Args:
        request: Setup Request mit campaign_id
        authorization: Bearer Token
    
    Returns:
        Setup Response mit Package-Info
    
    Raises:
        HTTPException: Bei Fehlern (401, 404, 400, 500)
    """
    
    # 1. Auth prüfen
    verify_webhook_auth(authorization)
    
    logger.info(f"Setup triggered for campaign {request.campaign_id} (force={request.force_rebuild})")
    
    try:
        # 2. Setup ausführen
        package = await run_campaign_setup(
            campaign_id=request.campaign_id,
            force=request.force_rebuild
        )
        
        logger.info(f"Package created for campaign {request.campaign_id}")
        
        # 3. Zu HOC uploaden
        download_url = await upload_to_hoc(package)
        
        logger.info(f"Package uploaded: {download_url}")
        
        # 4. Response
        return SetupCampaignResponse(
            status="success",
            package_id=package['campaign_id'],
            created_at=package['created_at'],
            download_url=download_url,
            question_count=len(package['questions'].get('questions', [])),
            company_name=package['company_name']
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/campaigns/{campaign_id}/package")
async def get_campaign_package(
    campaign_id: str,
    authorization: str = Header(None)
):
    """
    Gibt ein spezifisches Campaign Package zurück.
    
    Nutzen:
    - HOC kann Package jederzeit abrufen
    - Fallback bei fehlgeschlagenem Upload
    - Für Testing/Debugging
    
    Args:
        campaign_id: Campaign ID
        authorization: Bearer Token
    
    Returns:
        Campaign Package JSON
    
    Raises:
        HTTPException: 401 (Unauthorized), 404 (Not Found)
    """
    
    # Auth prüfen
    verify_webhook_auth(authorization)
    
    logger.info(f"Package retrieval requested for campaign {campaign_id}")
    
    try:
        storage = CampaignStorage()
        
        if not storage.package_exists(campaign_id):
            raise HTTPException(
                status_code=404,
                detail=f"Campaign Package {campaign_id} nicht gefunden. Bitte zuerst Setup durchführen."
            )
        
        package = storage.load_package(campaign_id)
        
        logger.info(f"Package {campaign_id} successfully retrieved")
        return package
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving package {campaign_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden des Packages: {str(e)}"
        )


@app.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    authorization: str = Header(None)
):
    """
    Listet alle verfügbaren Campaign Packages.
    
    Nutzen:
    - Übersicht über alle erstellten Packages
    - Für Debugging/Monitoring
    
    Args:
        authorization: Bearer Token
    
    Returns:
        Liste mit Campaign-Infos
    
    Raises:
        HTTPException: 401 (Unauthorized)
    """
    
    # Auth prüfen
    verify_webhook_auth(authorization)
    
    logger.info("Campaign list requested")
    
    try:
        storage = CampaignStorage()
        campaigns = storage.list_campaigns()
        
        # Konvertiere zu Response-Format
        campaign_items = []
        for campaign in campaigns:
            # Lade Package für question_count
            try:
                pkg = storage.load_package(campaign['campaign_id'])
                question_count = len(pkg.get('questions', {}).get('questions', []))
            except Exception:
                question_count = 0
            
            campaign_items.append(CampaignListItem(
                campaign_id=campaign['campaign_id'],
                company_name=campaign['company_name'],
                campaign_name=campaign['campaign_name'],
                created_at=campaign['created_at'],
                question_count=question_count
            ))
        
        logger.info(f"Returning {len(campaign_items)} campaigns")
        
        return CampaignListResponse(
            count=len(campaign_items),
            campaigns=campaign_items
        )
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden der Campaign-Liste: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

