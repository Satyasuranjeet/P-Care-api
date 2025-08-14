#!/usr/bin/env python3
"""
Test script for Personal Care API
"""
import asyncio
import httpx
import json

async def test_api():
    """Test the API endpoints"""
    base_url = "https://p-care-api.vercel.app"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test root endpoint
            print("Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            print(f"Root status: {response.status_code}")
            print(f"Root response: {response.json()}")
            
            # Test health endpoint
            print("\nTesting health endpoint...")
            response = await client.get(f"{base_url}/health")
            print(f"Health status: {response.status_code}")
            print(f"Health response: {response.json()}")
            
        except Exception as e:
            print(f"API test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
