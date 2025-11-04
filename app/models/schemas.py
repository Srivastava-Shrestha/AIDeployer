# app/models/schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum

class AttachmentSchema(BaseModel):
    name: str
    url: str  # Can be data URI or regular URL

class BuildRequestSchema(BaseModel):
    email: EmailStr
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: str
    attachments: Optional[List[AttachmentSchema]] = []

class EvaluationResponseSchema(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str

class BuildResponseSchema(BaseModel):
    status: str = "success"
    message: str = "Build request received and processing"