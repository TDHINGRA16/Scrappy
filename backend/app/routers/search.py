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

router = APIRouter()

@router.post("/", response_model=SearchJobResponse)
async def start_search(
    request: SearchRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        job = SearchJob(
            query=request.query,
            limit=request.limit,
            source=request.source,
            mode=request.mode,
            message_type=request.message_type,
            prewritten_message=request.prewritten_message
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        background_tasks.add_task(process_search_job, job.id, request)
        return {"job_id": job.id, "status": "processing_started"}
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create search job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create search job: {str(e)}")

async def process_search_job(job_id: int, request: SearchRequest):
    """Process a search job using Google Maps scraping"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SearchJob).where(SearchJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Preprocess query for better business results
            processed_query = preprocess_business_query(request.query)
            logger.info(f"Searching for: '{processed_query}'")
              # Use Google Maps scraping
            results = await scrape_google_maps(processed_query, max_results=request.limit)
            
            if not results:
                logger.warning(f"No Google Maps results found for query: '{processed_query}'")
                job.status = f"completed - no results found for '{request.query}'"
                await db.commit()
                return            # Save results to database with deduplication
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
                        source="Google Maps"                    )
                    
                    db.add(scrape_result)
                    saved_results += 1
                      # Add small delay between saves                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
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
                    # Convert results to the format expected by Google Sheets
                    sheet_results = []
                    for business in results:
                        sheet_results.append({
                            'Name': business.get('name', 'Unknown Business'),
                            'Website': business.get('website', ''),
                            'Email': business.get('email', ''),
                            'Phone': business.get('phone', ''),
                            'Address': business.get('address', ''),
                            'Reviews Count': business.get('reviews_count', 0),
                            'Reviews Average': business.get('reviews_average', 0.0),
                            'Store Shopping': business.get('store_shopping', 'No'),
                            'In Store Pickup': business.get('in_store_pickup', 'No'),
                            'Store Delivery': business.get('store_delivery', 'No'),
                            'Place Type': business.get('place_type', ''),
                            'Opening Hours': business.get('opening_hours', ''),
                            'Introduction': business.get('introduction', ''),
                            'Source': 'Google Maps'
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
async def get_search_job(job_id: int, db: AsyncSession = Depends(get_db)):
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
        "prewritten_message": job.prewritten_message,        "created_at": job.created_at,
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