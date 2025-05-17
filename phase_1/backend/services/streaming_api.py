from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import json
import asyncio
from threading import Thread
import sys
import uvicorn
import os

# Import the background scraper module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.append(os.path.abspath("C:/Work/Internship/Web Scraper Caprae/LeadGenAI/phase_1/backend"))

# Import the start_background_scraping function
from background import start_background_scraping

app = FastAPI()

# Add CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def scraper_stream(industry: str, location: str):
    """Generate SSE stream from the background scraper results"""
    # SSE headers and initialization message
    yield "retry: 1000\n"  # Retry interval if connection is lost
    yield "event: init\n"
    yield f"data: {json.dumps({'message': 'Scraper started'})}\n\n"
    
    # Start the background scraper
    get_results = start_background_scraping(industry, location)
    
    # Track the last amount of data we've seen
    last_data_count = 0
    
    # Keep checking for new results until scraping is complete
    while True:
        results = get_results()
        
        # Get the processed data
        processed_data = results.get("processed_data", [])
        current_data_count = len(processed_data)
        
        # If we have new data since last check, send it
        if current_data_count > last_data_count:
            # Send only the new data items
            new_items = processed_data[last_data_count:current_data_count]
            
            batch_data = {
                "batch": last_data_count // 10 + 1,  # Batch number (just for tracking)
                "new_items": new_items,
                "total_scraped": results.get("total_scraped", 0),
                "elapsed_time": results.get("elapsed_time", 0),
                "processed_count": current_data_count
            }
            
            yield f"event: batch\n"
            yield f"data: {json.dumps(batch_data)}\n\n"
            
            # Update last data count
            last_data_count = current_data_count
        
        # If scraping is complete, send final message and end stream
        if results.get("is_complete", False):
            # Send a final summary
            final_data = {
                "message": "Scraping completed",
                "total_scraped": results.get("total_scraped", 0),
                "total_processed": len(processed_data),
                "elapsed_time": results.get("elapsed_time", 0)
            }
            yield f"event: done\n"
            yield f"data: {json.dumps(final_data)}\n\n"
            break
        
        # Wait a bit before checking for new results
        await asyncio.sleep(2)

@app.get("/scrape-stream")
async def stream(industry: str, location: str):
    """Endpoint to stream scraper results for a given industry and location"""
    return StreamingResponse(
        scraper_stream(industry, location),
        media_type="text/event-stream"
    )

# Endpoint to check server status
@app.get("/status")
async def status():
    return {"status": "online"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
