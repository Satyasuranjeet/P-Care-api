#!/usr/bin/env python3
"""
Local development server for Personal Care API
"""
import uvicorn
import os

if __name__ == "__main__":
    # Set environment variables for local development
    os.environ["MONGODB_URL"] = "mongodb+srv://satya:satya@cluster0.8thgg4a.mongodb.net"
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
