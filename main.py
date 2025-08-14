from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Care API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net")
DATABASE_NAME = "personal_care_app"

# Global MongoDB client
client = None
database = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL, maxPoolSize=10, minPoolSize=1)
        database = client[DATABASE_NAME]
        # Test connection
        await database.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

async def get_database():
    """Get database connection"""
    global database
    if database is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return database

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

# API Routes
@app.get("/")
async def root():
    return {"message": "Personal Care API is running", "version": "1.0.0"}

@app.post("/backup")
async def backup_user_data(
    backup_data: BackupDataModel
):
    """Backup user data to MongoDB"""
    try:
        db = await get_database()
        # Create backup document
        backup_doc = {
            "user_id": backup_data.user.id,
            "user": backup_data.user.dict(),
            "schedules": [schedule.dict() for schedule in backup_data.schedules],
            "backup_date": backup_data.backup_date,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert or update backup
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

@app.get("/restore/{user_id}", response_model=RestoreDataResponse)
async def restore_user_data(
    user_id: str
):
    """Restore user data from MongoDB"""
    try:
        db = await get_database()
        backup_doc = await db.backups.find_one({"user_id": user_id})
        
        if not backup_doc:
            logger.warning(f"No backup found for user {user_id}")
            raise HTTPException(status_code=404, detail="No backup found for this user")
        
        logger.info(f"Data restored for user {user_id}")
        return RestoreDataResponse(
            user=UserModel(**backup_doc["user"]),
            schedules=[ScheduleModel(**schedule) for schedule in backup_doc["schedules"]],
            backup_date=backup_doc["backup_date"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@app.post("/schedules")
async def create_or_update_schedule(
    schedule: ScheduleModel
):
    """Create or update a schedule in MongoDB"""
    try:
        db = await get_database()
        schedule_doc = schedule.dict()
        schedule_doc["updated_at"] = datetime.utcnow().isoformat()
        
        # Ensure we don't lose the original created_at if updating
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

@app.get("/schedules/{user_id}")
async def get_user_schedules(
    user_id: str
):
    """Get all schedules for a user from MongoDB"""
    try:
        db = await get_database()
        schedules_cursor = db.schedules.find({"user_id": user_id})
        schedules = await schedules_cursor.to_list(length=None)
        
        # Convert MongoDB documents to ScheduleModel format
        schedule_models = []
        for schedule in schedules:
            schedule.pop("_id", None)  # Remove MongoDB _id field
            try:
                schedule_models.append(ScheduleModel(**schedule))
            except Exception as e:
                logger.warning(f"Skipping invalid schedule document: {e}")
                continue
        
        logger.info(f"Retrieved {len(schedule_models)} schedules for user {user_id}")
        return schedule_models
    except Exception as e:
        logger.error(f"Failed to get schedules for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str
):
    """Delete a schedule from MongoDB"""
    try:
        db = await get_database()
        result = await db.schedules.delete_one({"id": schedule_id})
        
        if result.deleted_count == 0:
            logger.warning(f"Schedule {schedule_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        logger.info(f"Schedule {schedule_id} deleted successfully")
        return {
            "success": True,
            "message": "Schedule deleted successfully",
            "schedule_id": schedule_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = await get_database()
        await db.command("ping")
        logger.info("Health check passed")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
