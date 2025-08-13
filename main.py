from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI(title="Personal Care API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net")
DATABASE_NAME = "personal_care_app"

# Global MongoDB client
client = None
database = None

@app.on_event("startup")
async def startup_event():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    print("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    if client:
        client.close()
        print("Disconnected from MongoDB")

# Pydantic Models
class UserModel(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

class ScheduleModel(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    scheduled_time: str
    frequency: str
    notification_tone: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    end_date: Optional[str] = None
    completed_dates: str
    is_completed: bool

class BackupDataModel(BaseModel):
    user: UserModel
    schedules: List[ScheduleModel]
    backup_date: str

class RestoreDataResponse(BaseModel):
    user: UserModel
    schedules: List[ScheduleModel]
    backup_date: str

# Helper Functions
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify API token. In production, implement proper JWT validation.
    For now, we'll use a simple API key check.
    """
    expected_token = os.getenv("API_KEY", "pcare_api_key_2024")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# API Routes
@app.get("/")
async def root():
    return {"message": "Personal Care API is running", "version": "1.0.0"}

@app.post("/backup")
async def backup_user_data(
    backup_data: BackupDataModel,
    token: str = Depends(verify_token)
):
    """Backup user data to MongoDB"""
    try:
        # Create backup document
        backup_doc = {
            "user_id": backup_data.user.id,
            "user": backup_data.user.dict(),
            "schedules": [schedule.dict() for schedule in backup_data.schedules],
            "backup_date": backup_data.backup_date,
            "created_at": datetime.utcnow()
        }
        
        # Insert or update backup
        result = await database.backups.replace_one(
            {"user_id": backup_data.user.id},
            backup_doc,
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Data backed up successfully",
            "backup_id": str(result.upserted_id) if result.upserted_id else "updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@app.get("/restore/{user_id}", response_model=RestoreDataResponse)
async def restore_user_data(
    user_id: str,
    token: str = Depends(verify_token)
):
    """Restore user data from MongoDB"""
    try:
        backup_doc = await database.backups.find_one({"user_id": user_id})
        
        if not backup_doc:
            raise HTTPException(status_code=404, detail="No backup found for this user")
        
        return RestoreDataResponse(
            user=UserModel(**backup_doc["user"]),
            schedules=[ScheduleModel(**schedule) for schedule in backup_doc["schedules"]],
            backup_date=backup_doc["backup_date"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@app.post("/schedules")
async def create_or_update_schedule(
    schedule: ScheduleModel,
    token: str = Depends(verify_token)
):
    """Create or update a schedule in MongoDB"""
    try:
        schedule_doc = schedule.dict()
        schedule_doc["created_at"] = datetime.utcnow()
        
        result = await database.schedules.replace_one(
            {"id": schedule.id},
            schedule_doc,
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Schedule synced successfully",
            "schedule_id": schedule.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schedule sync failed: {str(e)}")

@app.get("/schedules/{user_id}")
async def get_user_schedules(
    user_id: str,
    token: str = Depends(verify_token)
):
    """Get all schedules for a user from MongoDB"""
    try:
        schedules_cursor = database.schedules.find({"user_id": user_id})
        schedules = await schedules_cursor.to_list(length=None)
        
        # Convert MongoDB documents to ScheduleModel format
        schedule_models = []
        for schedule in schedules:
            schedule.pop("_id", None)  # Remove MongoDB _id field
            schedule_models.append(ScheduleModel(**schedule))
        
        return schedule_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    token: str = Depends(verify_token)
):
    """Delete a schedule from MongoDB"""
    try:
        result = await database.schedules.delete_one({"id": schedule_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule deleted successfully",
            "schedule_id": schedule_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await database.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
