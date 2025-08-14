from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Care API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Configuration
MONGODB_URL = "mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net/personal_care_app?retryWrites=true&w=majority"
DATABASE_NAME = "personal_care_app"

# Global MongoDB client - initialized lazily
_client = None
_database = None

async def get_database():
    """Get database connection with lazy initialization"""
    global _client, _database
    
    if _database is None:
        try:
            logger.info("Initializing MongoDB connection...")
            _client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=1
            )
            _database = _client[DATABASE_NAME]
            
            # Test connection
            await _database.command("ping")
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
    
    return _database

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

@app.get("/")
async def root():
    return {
        "message": "Personal Care API is running", 
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = await get_database()
        await db.command("ping")
        logger.info("Health check passed")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "api_version": "1.0.0"
        }

@app.post("/schedules")
async def create_or_update_schedule(schedule: ScheduleModel):
    """Create or update a schedule in MongoDB"""
    try:
        db = await get_database()
        schedule_doc = schedule.dict()
        schedule_doc["updated_at"] = datetime.utcnow().isoformat()
        
        # Preserve original created_at if updating
        existing = await db.schedules.find_one({"id": schedule.id})
        if existing:
            schedule_doc["created_at"] = existing.get("created_at", datetime.utcnow().isoformat())
        else:
            schedule_doc["created_at"] = datetime.utcnow().isoformat()
        
        result = await db.schedules.replace_one(
            {"id": schedule.id},
            schedule_doc,
            upsert=True
        )
        
        logger.info(f"Schedule {schedule.id} synced successfully")
        return {
            "success": True,
            "message": "Schedule synced successfully",
            "schedule_id": schedule.id
        }
    except Exception as e:
        logger.error(f"Schedule sync failed for {schedule.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Schedule sync failed: {str(e)}")

@app.post("/backup")
async def backup_user_data(backup_data: BackupDataModel):
    """Backup user data to MongoDB"""
    try:
        db = await get_database()
        backup_doc = {
            "user_id": backup_data.user.id,
            "user": backup_data.user.dict(),
            "schedules": [schedule.dict() for schedule in backup_data.schedules],
            "backup_date": backup_data.backup_date,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await db.backups.replace_one(
            {"user_id": backup_data.user.id},
            backup_doc,
            upsert=True
        )
        
        logger.info(f"Data backed up for user {backup_data.user.id}")
        return {
            "success": True,
            "message": "Data backed up successfully",
            "backup_id": str(result.upserted_id) if result.upserted_id else "updated",
            "user_id": backup_data.user.id
        }
    except Exception as e:
        logger.error(f"Backup failed for user {backup_data.user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
