# Personal Care API

A FastAPI-based REST API for the Personal Care Flutter application that provides MongoDB integration for data backup and synchronization.

## Features

- **Data Backup**: Backup user data and schedules to MongoDB
- **Data Restore**: Restore user data from MongoDB
- **Schedule Management**: CRUD operations for schedules
- **Authentication**: API key-based authentication
- **Health Check**: Monitor API and database status

## Setup

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB instance)
- pip (Python package manager)

### Installation

1. **Clone or navigate to the API directory:**
   ```bash
   cd d:/Projects/PCare/api
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables (optional):**
   Create a `.env` file in the api directory:
   ```
   MONGODB_URL=mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net
   API_KEY=your_secure_api_key_here
   HOST=0.0.0.0
   PORT=8000
   ```

### Running the API

1. **Start the server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
All endpoints require an API key in the Authorization header:
```
Authorization: Bearer your_api_key_here
```

### Endpoints

#### 1. Health Check
- **GET** `/health`
- **Description**: Check API and database health
- **Response**: Status information

#### 2. Backup Data
- **POST** `/backup`
- **Description**: Backup user data and schedules
- **Body**: JSON containing user and schedules data
- **Response**: Success confirmation

#### 3. Restore Data
- **GET** `/restore/{user_id}`
- **Description**: Restore user data from backup
- **Parameters**: `user_id` - User ID to restore data for
- **Response**: User data and schedules

#### 4. Create/Update Schedule
- **POST** `/schedules`
- **Description**: Create or update a schedule
- **Body**: Schedule data in JSON format
- **Response**: Success confirmation

#### 5. Get User Schedules
- **GET** `/schedules/{user_id}`
- **Description**: Get all schedules for a user
- **Parameters**: `user_id` - User ID
- **Response**: List of schedules

#### 6. Delete Schedule
- **DELETE** `/schedules/{schedule_id}`
- **Description**: Delete a specific schedule
- **Parameters**: `schedule_id` - Schedule ID to delete
- **Response**: Success confirmation

## Flutter App Integration

Update your Flutter app's MongoDB service to use this API:

```dart
class MongoDBService {
  static const String baseUrl = 'http://localhost:8000'; // Update with your API URL
  static const String apiKey = 'your_api_key_here'; // Update with your API key
  
  // ... rest of your service methods
}
```

## Database Structure

### Collections

1. **backups**: User data backups
   ```json
   {
     "user_id": "string",
     "user": {...},
     "schedules": [...],
     "backup_date": "ISO date string",
     "created_at": "MongoDB timestamp"
   }
   ```

2. **schedules**: Individual schedule documents
   ```json
   {
     "id": "string",
     "user_id": "string",
     "title": "string",
     "description": "string",
     "scheduled_time": "ISO date string",
     "frequency": "string",
     "notification_tone": "string",
     "is_active": "boolean",
     "created_at": "MongoDB timestamp",
     // ... other fields
   }
   ```

## Production Deployment

### Environment Variables
Set these environment variables for production:

- `MONGODB_URL`: Your MongoDB connection string
- `API_KEY`: A secure API key
- `HOST`: Server host (usually 0.0.0.0)
- `PORT`: Server port
- `SECRET_KEY`: For JWT tokens (future use)

### Security Considerations

1. **API Key**: Use a strong, unique API key
2. **CORS**: Update CORS origins to only allow your Flutter app's domain
3. **HTTPS**: Use HTTPS in production
4. **Database**: Ensure MongoDB has proper authentication and encryption
5. **Rate Limiting**: Consider adding rate limiting for production use

## Development

### Project Structure
```
api/
├── main.py           # FastAPI application
├── config.py         # Configuration settings
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

### Adding New Features

1. Add new Pydantic models for data validation
2. Create new endpoint functions in `main.py`
3. Update the database schema if needed
4. Test the endpoints using the interactive docs at `/docs`

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check your MongoDB URL and credentials
   - Ensure your IP is whitelisted in MongoDB Atlas

2. **Authentication Failed**
   - Verify the API key in your requests
   - Check the Authorization header format

3. **CORS Errors**
   - Update CORS origins in the configuration
   - Ensure your Flutter app URL is allowed

### Logs
Check the console output for detailed error messages and logs.
