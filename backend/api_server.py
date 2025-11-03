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
    Führt Campaign Setup aus (async wrapper).
    
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
    
    # Neues Package erstellen in Thread Pool
    loop = asyncio.get_event_loop()
    
    def _setup():
        """Synchroner Setup-Code"""
        api = APIDataSource(
            api_url=settings.api_url,
            api_key=settings.api_key,
            status="new",
            filter_test_applicants=True
        )
        
        builder = CampaignPackageBuilder(
            prompts_dir=settings.get_prompts_dir_path(),
            questions_json_path=settings.get_questions_json_path()
        )
        
        package = builder.build_package(campaign_id, api)
        storage.save_package(campaign_id, package)
        
        return package
    
    return await loop.run_in_executor(None, _setup)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

