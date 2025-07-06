from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
import random
from app.schemas import SearchRequest, SearchJobResponse
from app.database import get_db, AsyncSessionLocal
from app.services.scraper import scrape_google_maps, scrape_website
from app.services.google_sheets import sheets_service
from app.models import SearchJob, ScrapeResult
from app.utils.loggers import logger
from app.utils.rate_limiter import wait_for_rate_limit
from app.dependencies import require_auth
from datetime import datetime

router = APIRouter()

@router.post("", response_model=SearchJobResponse)
async def start_search(
    request: SearchRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth)
):
    try:
        job = SearchJob(
            query=request.query,
            limit=request.limit,
            source=request.source,
            mode=request.mode,
            message_type=request.message_type,
            prewritten_message=request.prewritten_message,
            status="processing"  # Set initial status
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        # Start the background task but don't wait for it
        background_tasks.add_task(process_search_job, job.id, request)
        
        # Return immediately with job ID and processing status
        logger.info(f"Started search job {job.id} for query: '{request.query}'")
        return {"job_id": job.id, "status": "processing_started"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create search job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create search job: {str(e)}")

async def process_search_job(job_id: int, request: SearchRequest):
    """Process a search job using Google Maps scraping"""
    async with AsyncSessionLocal() as db:
        try:
            # Get the job and update status to processing immediately
            result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update status to processing
            job.status = "processing"
            await db.commit()
            logger.info(f"Started processing job {job_id}")
            
            # Preprocess query for better business results
            processed_query = preprocess_business_query(request.query)
            logger.info(f"Searching for: '{processed_query}'")
            
            # Use Google Maps scraping
            results = await scrape_google_maps(processed_query, max_results=request.limit)
            
            if not results:
                logger.warning(f"No Google Maps results found for query: '{processed_query}'")
                job.status = f"completed - no results found for '{request.query}'"
                await db.commit()
                return
                
            # Save results to database with deduplication
            saved_results = 0
            seen_entries = set()
            
            for business in results:
                try:
                    # Create a unique key for deduplication
                    name = business.get('name', 'Unknown Business').strip()
                    address = business.get('address', '').strip()
                    phone = business.get('phone', '').strip()
                    
                    # Skip if name is empty or generic
                    if not name or name.lower() in ['unknown business', '']:
                        continue
                    
                    # Create unique identifier
                    unique_key = (name.lower(), address.lower(), phone)
                    
                    if unique_key in seen_entries:
                        logger.info(f"Skipping duplicate entry: {name}")
                        continue
                    
                    seen_entries.add(unique_key)
                    
                    # Check if this business already exists in the database for this job
                    existing_check = await db.execute(
                        select(ScrapeResult).where(
                            ScrapeResult.job_id == job.id,
                            ScrapeResult.name == name,
                            ScrapeResult.address == address
                        )
                    )
                    if existing_check.scalar_one_or_none():
                        logger.info(f"Business already exists in database: {name}")
                        continue
                    
                    # Extract email if website is available
                    email = business.get('email', '')
                    website = business.get('website', '')
                    
                    # If we have a website but no email, try to scrape the website for contact info
                    if website and not email:
                        try:
                            contact_info = await scrape_website(website)
                            if contact_info.get('emails'):
                                email = contact_info['emails'][0]
                        except Exception as e:
                            logger.warning(f"Failed to scrape website {website}: {str(e)}")
                    
                    scrape_result = ScrapeResult(
                        job_id=job.id,
                        name=business.get('name', 'Unknown Business'),
                        website=website,
                        email=email,
                        phone=business.get('phone', ''),
                        address=business.get('address', ''),
                        
                        # Review information
                        reviews_count=business.get('reviews_count', 0),
                        reviews_average=business.get('reviews_average', 0.0),
                        
                        # Business features
                        store_shopping=business.get('store_shopping', 'No'),
                        in_store_pickup=business.get('in_store_pickup', 'No'),
                        store_delivery=business.get('store_delivery', 'No'),
                        
                        # Additional details
                        place_type=business.get('place_type', ''),
                        opening_hours=business.get('opening_hours', ''),
                        introduction=business.get('introduction', ''),
                        
                        # Metadata
                        source="Google Maps"
                    )
                    
                    db.add(scrape_result)
                    saved_results += 1
                    
                    # Add small delay between saves
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    # Check if it's a unique constraint violation (duplicate)
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.info(f"Skipping duplicate business: {business.get('name', 'Unknown')}")
                    else:
                        logger.error(f"Error saving result: {str(e)}")
                    continue
            
            job.status = "completed"
            try:
                await db.commit()
                logger.info(f"Job {job_id} completed with {saved_results} unique results (out of {len(results)} scraped)")
                
                # Save results to Google Sheets
                try:
                    # Get the final results from database (which include emails)
                    final_results_query = await db.execute(
                        select(ScrapeResult).where(ScrapeResult.job_id == job_id)
                    )
                    final_results = final_results_query.scalars().all()
                    
                    # Convert database results to the format expected by Google Sheets
                    sheet_results = []
                    for result in final_results:
                        sheet_results.append({
                            'Name': result.name,
                            'Website': result.website,
                            'Email': result.email,  # This will now include the extracted emails
                            'Phone': result.phone,
                            'Address': result.address,
                            'Reviews Count': result.reviews_count,
                            'Reviews Average': result.reviews_average,
                            'Store Shopping': result.store_shopping,
                            'In Store Pickup': result.in_store_pickup,
                            'Store Delivery': result.store_delivery,
                            'Place Type': result.place_type,
                            'Opening Hours': result.opening_hours,
                            'Introduction': result.introduction,
                            'Source': result.source
                        })
                    
                    # Save to Google Sheets
                    sheets_saved = sheets_service.save_scraper_results_sync(
                        results=sheet_results,
                        job_id=job_id,
                        query=request.query
                    )
                    
                    if sheets_saved:
                        logger.info(f"Successfully saved {len(sheet_results)} results to Google Sheets for job {job_id}")
                    else:
                        logger.warning(f"Failed to save results to Google Sheets for job {job_id}")
                        
                except Exception as sheets_error:
                    logger.error(f"Error saving to Google Sheets for job {job_id}: {str(sheets_error)}")
                    # Don't fail the job if Google Sheets saving fails
                
            except Exception as commit_error:
                logger.error(f"Error committing job completion: {str(commit_error)}")
                await db.rollback()
                try:
                    await db.refresh(job)
                    job.status = "completed"
                    await db.commit()
                    logger.info(f"Job {job_id} completed with {saved_results} results (after rollback)")
                except Exception as retry_error:
                    logger.error(f"Failed to commit after rollback: {str(retry_error)}")
            
        except Exception as e:
            logger.exception(f"Job {job_id} failed")
            try:
                job.status = f"failed: {str(e)}"
                await db.commit()
            except Exception as commit_error:
                logger.error(f"Error committing job failure: {str(commit_error)}")
                await db.rollback()

def preprocess_business_query(query: str) -> str:
    """Preprocess search query to improve business search results"""
    query = query.strip()
    
    # Add business context for short queries
    words = query.split()
    if len(words) <= 2:
        if not any(word.lower() in ['restaurant', 'hotel', 'store', 'shop'] for word in words):
            query = f"{query} business"
    
    return query

@router.get("/{job_id}")
async def get_search_job(job_id: int, db: AsyncSession = Depends(get_db), _: dict = Depends(require_auth)):
    """Get details of a search job including results"""
    result = await db.execute(
        select(SearchJob).where(SearchJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    
    # Get results
    results_query = await db.execute(
        select(ScrapeResult).where(ScrapeResult.job_id == job_id)
    )
    results = results_query.scalars().all()
    
    return {
        "id": job.id,
        "query": job.query,
        "limit": job.limit,
        "source": job.source,
        "mode": job.mode,
        "message_type": job.message_type,
        "prewritten_message": job.prewritten_message,
        "created_at": job.created_at,
        "status": job.status,
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "website": r.website,
                "email": r.email,
                "phone": r.phone,
                "address": r.address,
                "reviews_count": r.reviews_count,
                "reviews_average": r.reviews_average,
                "store_shopping": r.store_shopping,
                "in_store_pickup": r.in_store_pickup,
                "store_delivery": r.store_delivery,
                "place_type": r.place_type,
                "opening_hours": r.opening_hours,
                "introduction": r.introduction,
                "source": r.source
            }
            for r in results
        ]
    }

@router.get("/{job_id}/progress")
async def get_job_progress(job_id: int, db: AsyncSession = Depends(get_db), _: dict = Depends(require_auth)):
    """Get detailed progress information for a job"""
    result = await db.execute(
        select(SearchJob).where(SearchJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    
    # Get current results count
    results_count_query = await db.execute(
        select(ScrapeResult).where(ScrapeResult.job_id == job_id)
    )
    results_count = len(results_count_query.scalars().all())
    
    # Calculate progress based on status and results
    progress_percentage = 0
    current_step = "Initializing"
    
    if job.status == "completed":
        progress_percentage = 100
        current_step = "Completed"
    elif job.status == "processing":
        # More accurate progress calculation
        if job.limit > 0:
            # Base progress on results found, but cap at 95% until truly complete
            base_progress = min(95, int((results_count / job.limit) * 100))
            # Add some progress for being in processing state
            progress_percentage = max(10, base_progress)
        else:
            progress_percentage = 50
        current_step = f"Scraping... ({results_count} results found)"
    elif job.status == "pending":
        progress_percentage = 5
        current_step = "Queued"
    elif "failed" in job.status.lower():
        progress_percentage = 0
        current_step = "Failed"
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percentage": progress_percentage,
        "current_step": current_step,
        "results_count": results_count,
        "target_results": job.limit,
        "query": job.query,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if hasattr(job, 'updated_at') and job.updated_at else None,
        "estimated_time_remaining": calculate_estimated_time(job, results_count)
    }

def calculate_estimated_time(job: SearchJob, current_results: int) -> str:
    """Calculate estimated time remaining based on current progress and elapsed time"""
    if job.status == "completed":
        return "Completed"
    
    if current_results == 0:
        return "Calculating..."
    
    # Calculate elapsed time since job started
    elapsed_time = (datetime.utcnow() - job.created_at).total_seconds()
    
    if elapsed_time < 30:  # Still in initial phase
        return "Starting up..."
    
    # Calculate rate based on actual performance
    if current_results > 0 and elapsed_time > 0:
        results_per_second = current_results / elapsed_time
        remaining_results = max(0, job.limit - current_results)
        
        if results_per_second > 0:
            estimated_seconds = remaining_results / results_per_second
        else:
            # Fallback estimate: 3-5 seconds per result
            estimated_seconds = remaining_results * 4
    else:
        # Fallback estimate
        estimated_seconds = max(0, job.limit - current_results) * 4
    
    # Add some buffer time for processing
    estimated_seconds += 30
    
    # Format time remaining
    if estimated_seconds < 60:
        return f"{int(estimated_seconds)} seconds"
    elif estimated_seconds < 3600:
        minutes = int(estimated_seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        hours = int(estimated_seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''}"