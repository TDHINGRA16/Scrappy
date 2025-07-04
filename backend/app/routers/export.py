from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
from app.database import get_db
from app.models import SearchJob, ScrapeResult, OutreachMessage
from app.schemas import ExportRequest
from app.dependencies import get_search_job
from app.utils.loggers import logger

router = APIRouter()

@router.post("/csv/{job_id}")
async def export_to_csv(
    job_id: int,
    include_messages: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Export search results to CSV format"""
    try:
        # Get job with results
        result = await db.execute(
            select(SearchJob)
            .options(selectinload(SearchJob.results))
            .where(SearchJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create CSV content
        output = StringIO()
        fieldnames = ['name', 'website', 'email', 'phone', 'address', 'source']
        
        if include_messages:
            # Get messages for this job
            messages_result = await db.execute(
                select(OutreachMessage).where(OutreachMessage.job_id == job_id)
            )
            messages = messages_result.scalars().all()
            fieldnames.extend(['message_sent', 'message_status', 'contact_method'])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in job.results:
            row = {
                'name': result.name,
                'website': result.website,
                'email': result.email or '',
                'phone': result.phone or '',
                'address': result.address or '',
                'source': result.source
            }
            
            if include_messages:
                # Find corresponding message
                message = next(
                    (m for m in messages if m.recipient in [result.email, result.phone]), 
                    None
                )
                row.update({
                    'message_sent': 'Yes' if message else 'No',
                    'message_status': message.status if message else '',
                    'contact_method': message.contact_method if message else ''
                })
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_results.csv"}
        )
        
    except Exception as e:
        logger.error(f"CSV export failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/excel/{job_id}")
async def export_to_excel(
    job_id: int,
    include_messages: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Export search results to Excel format"""
    try:
        # Get job with results
        result = await db.execute(
            select(SearchJob)
            .options(selectinload(SearchJob.results))
            .where(SearchJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Prepare data for DataFrame
        data = []
        for result in job.results:
            row = {
                'Name': result.name,
                'Website': result.website,
                'Email': result.email or '',
                'Phone': result.phone or '',
                'Address': result.address or '',
                'Source': result.source
            }
            data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # If including messages, add message data
        if include_messages:
            messages_result = await db.execute(
                select(OutreachMessage).where(OutreachMessage.job_id == job_id)
            )
            messages = messages_result.scalars().all()
            
            # Add message columns
            df['Message_Sent'] = df.apply(
                lambda row: 'Yes' if any(
                    m.recipient in [row['Email'], row['Phone']] for m in messages
                ) else 'No',
                axis=1
            )
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Add job info sheet
            job_info = pd.DataFrame([{
                'Job_ID': job.id,
                'Query': job.query,
                'Mode': job.mode,
                'Status': job.status,
                'Created_At': job.created_at,
                'Total_Results': len(job.results)
            }])
            job_info.to_excel(writer, sheet_name='Job_Info', index=False)
        
        excel_content = output.getvalue()
        output.close()
        
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_results.xlsx"}
        )
        
    except Exception as e:
        logger.error(f"Excel export failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/json/{job_id}")
async def export_to_json(
    job_id: int,
    include_messages: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Export search results to JSON format"""
    try:
        # Get job with results and optionally messages
        query = select(SearchJob).options(selectinload(SearchJob.results))
        
        if include_messages:
            query = query.options(selectinload(SearchJob.messages))
        
        result = await db.execute(query.where(SearchJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Build JSON response
        export_data = {
            "job_info": {
                "id": job.id,
                "query": job.query,
                "mode": job.mode,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "total_results": len(job.results)
            },
            "results": [
                {
                    "id": result.id,
                    "name": result.name,
                    "website": result.website,
                    "email": result.email,
                    "phone": result.phone,
                    "address": result.address,
                    "source": result.source
                }
                for result in job.results
            ]
        }
        
        if include_messages:
            export_data["messages"] = [
                {
                    "id": msg.id,
                    "contact_method": msg.contact_method,
                    "recipient": msg.recipient,
                    "message": msg.message,
                    "status": msg.status,
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                    "error": msg.error
                }
                for msg in job.messages
            ]
        
        json_content = json.dumps(export_data, indent=2)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_results.json"}
        )
        
    except Exception as e:
        logger.error(f"JSON export failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/json/{job_id}")
async def get_job_data_json(
    job_id: int,
    include_messages: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get job results in JSON format (for frontend display)"""
    try:
        # Get job with results and optionally messages
        query = select(SearchJob).options(selectinload(SearchJob.results))
        
        if include_messages:
            query = query.options(selectinload(SearchJob.messages))
        
        result = await db.execute(query.where(SearchJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Build JSON response for frontend consumption
        response_data = {
            "job_info": {
                "id": job.id,
                "query": job.query,
                "mode": job.mode,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "total_results": len(job.results)
            },
            "results": [
                {
                    "id": result.id,
                    "name": result.name,
                    "website": result.website,
                    "email": result.email,
                    "phone": result.phone,
                    "address": result.address,
                    "source": result.source
                }
                for result in job.results
            ]
        }
        
        if include_messages:
            response_data["messages"] = [
                {
                    "id": msg.id,
                    "contact_method": msg.contact_method,
                    "recipient": msg.recipient,
                    "message": msg.message,
                    "status": msg.status,
                    "sent_at": msg.sent_at.isoformat() if msg.sent_at else None
                }
                for msg in job.messages
            ]
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to get job data for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job data: {str(e)}")

@router.get("/jobs")
async def list_jobs(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List all search jobs with pagination"""
    try:
        offset = (page - 1) * size
        
        # Get total count
        count_result = await db.execute(select(SearchJob))
        total_jobs = len(count_result.scalars().all())
        
        # Get paginated jobs
        result = await db.execute(
            select(SearchJob)
            .offset(offset)
            .limit(size)
            .order_by(SearchJob.created_at.desc())
        )
        jobs = result.scalars().all()
        
        return {
            "jobs": [
                {
                    "id": job.id,
                    "query": job.query,
                    "mode": job.mode,
                    "status": job.status,
                    "created_at": job.created_at.isoformat()
                }
                for job in jobs
            ],
            "pagination": {
                "page": page,
                "size": size,
                "total": total_jobs,
                "pages": (total_jobs + size - 1) // size
            }
        }
        
    except Exception as e:
        logger.error(f"Job listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed status of a specific job"""
    try:
        result = await db.execute(
            select(SearchJob)
            .options(
                selectinload(SearchJob.results),
                selectinload(SearchJob.messages)
            )
            .where(SearchJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Count message statuses
        message_stats = {}
        for message in job.messages:
            status = message.status
            message_stats[status] = message_stats.get(status, 0) + 1
        
        return {
            "job_id": job.id,
            "query": job.query,
            "mode": job.mode,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "results_count": len(job.results),
            "messages_count": len(job.messages),
            "message_stats": message_stats,
            "has_results": len(job.results) > 0,
            "can_export": job.status in ["completed", "scraping_completed"]
        }
        
    except Exception as e:
        logger.error(f"Status check failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Status check failed")
