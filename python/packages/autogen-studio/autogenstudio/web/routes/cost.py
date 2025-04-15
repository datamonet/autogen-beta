
from fastapi import APIRouter, Request, Depends
import os
import httpx
from uuid import UUID
from typing import Dict
from ...datamodel import Message, MessageConfig, Run, RunStatus, Session, Team
from ..deps import get_db, get_team_manager, get_websocket_manager
from fastapi.responses import Response as FastAPIResponse
from loguru import logger
from pydantic import BaseModel


router = APIRouter()

# cookie name for authjs v5
cookie_name= "__Secure-authjs.session-token" if os.getenv("DEPLOY_ENV") == "production" else "authjs.session-token"

class CostRequest(BaseModel):
    """Request body model for cost calculation"""
    # Add your required fields here, for example:
    model: str
    run_id: int

@router.post("/")
async def cost(request: Request,cost_data: CostRequest, db=Depends(get_db)) -> Dict:
    """takin code:Calculate cost based on run details and user information
    
    Args:
        run_id (UUID): The ID of the run to calculate cost for
        cost_data (CostRequest): The request body containing cost calculation data
        request (Request): The FastAPI request object
        db: Database dependency
        
    Returns:
        Dict: Response containing credit information or error details
    """

    # Validate and get run details
    run = db.get(Run, filters={"id": cost_data.run_id}, return_json=False)
    if not run.status or not run.data:
        return {"status": False, "message": "Run not found"}
    run_result = run.data[0].team_result

    # Get pricing service URL
    pricing_url = os.getenv('TAKIN_API_URL')
    
    pricing_url = f"{pricing_url}/api/external/autogen/pricing"
    
    # Get authentication token
    token = request.cookies.get(cookie_name)
    if not token:
        return {"status": False, "message": "No authentication token found"}
    
    # Send request to pricing service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                pricing_url,
                json={"run_id":cost_data.run_id,"run_result": run_result,"model":cost_data.model},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
            )
            
            result = response.json()
            
        except httpx.TimeoutException:
            return {"status": False, "message": "Pricing service request timed out"}
        except httpx.HTTPStatusError as e:
            return {"status": False, "message": f"Pricing service error: {e.response.text}"}
    
    return {
        "status": True,
        "data": {
            "extra_credits": result.get("extraCredits", 0),
            "subscription_credits": result.get("subscriptionCredits", 0),
            "subscription_purchased_credits": result.get("subscriptionPurchasedCredits", 0)
        }
    }

