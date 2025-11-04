# app/api/endpoints.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request
from app.models.schemas import BuildRequestSchema, BuildResponseSchema, EvaluationResponseSchema
from app.services.code_generator import CodeGenerator
from app.services.github.github_service import GitHubService
from app.services.deployment import DeploymentService
from app.utils.attachments import AttachmentHandler
from app.config import settings
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

async def process_build_request(request: BuildRequestSchema):
    """Process build request in the background."""
    try:
        logger.info(f"Processing build request for task: {request.task}, round: {request.round}")
        
        # Process attachments
        processed_attachments = []
        for attachment in request.attachments:
            processed = await AttachmentHandler.process_attachment(attachment.model_dump())
            processed_attachments.append(processed)
        
        # Initialize services
        code_generator = CodeGenerator()
        github_service = GitHubService()
        
        # Generate or update application
        repo_name = f"{request.task}-{request.email.split('@')[0]}".replace('.', '-').replace('_', '-')
        repo = github_service.get_repository(repo_name)
        
        if request.round == 1 or repo is None:
            # Generate new application
            files = await code_generator.generate_application(request, processed_attachments)
            
            # Create repository if it doesn't exist
            if repo is None:
                repo = github_service.create_repository(
                    repo_name,
                    f"Application for task: {request.task}"
                )
        else:
            # Update existing application
            existing_files = github_service.get_files(repo)
            files = await code_generator.update_application(
                request,
                existing_files,
                processed_attachments
            )
        
        # Add round metadata
        files['round'] = str(request.round)
        
        # Push files to GitHub
        commit_sha = github_service.push_files(repo, files)
        
        # Enable GitHub Pages
        pages_url = github_service.enable_pages(repo)
        
        # Wait a bit for GitHub Pages to deploy
        await asyncio.sleep(10)
        
        # Prepare evaluation response
        eval_response = EvaluationResponseSchema(
            email=request.email,
            task=request.task,
            round=request.round,
            nonce=request.nonce,
            repo_url=f"https://github.com/{repo.full_name}",
            commit_sha=commit_sha,
            pages_url=pages_url
        )
        
        # Notify evaluation API
        async with DeploymentService() as deployment:
            # Wait for pages to be accessible
            await deployment.wait_for_pages_deployment(pages_url, max_wait=120)
            
            # Send evaluation response
            await deployment.notify_evaluation(request.evaluation_url, eval_response)
        
        logger.info(f"Successfully completed build for task: {request.task}, round: {request.round}")
        
    except Exception as e:
        logger.error(f"Error processing build request: {str(e)}", exc_info=True)

@router.post("/build", response_model=BuildResponseSchema)
async def build_endpoint(
    request: BuildRequestSchema,
    background_tasks: BackgroundTasks
):
    """Handle build/update requests."""
    
    # Verify secret
    if request.secret != settings.secret_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret"
        )
    
    # Add task to background
    background_tasks.add_task(process_build_request, request)
    
    # Return immediate response
    return BuildResponseSchema(
        status="success",
        message=f"Build request received for task {request.task}, round {request.round}. Processing in background."
    )

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LLM Code Deployment"
    }

@router.post("/evaluate")
async def test(request: Request):
    data = await request.json()
    logger.info(data)
    return {"status": "ok"}
