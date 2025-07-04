from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import csv
from io import StringIO
from app.services.google_sheets import import_from_sheets
from app.database import get_db
from app.models import SearchJob, OutreachMessage
from app.schemas import GoogleSheetImportRequest
from app.utils.loggers import logger

router = APIRouter()

@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    contents = await file.read()
    csv_data = StringIO(contents.decode("utf-8"))
    reader = csv.DictReader(csv_data)
    
    # Create a new "import" job record
    job = SearchJob(
        query="CSV Import",
        mode="scrape_and_contact",  # Default mode for imports
        status="processing"
    )
    db.add(job)
    await db.commit()
    
    for row in reader:
        # Add each row as an outreach target
        if "phone" in row or "email" in row:
            message = "Custom message"  # Use default or template
            
            if row.get("phone"):
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="whatsapp",
                    recipient=row["phone"],
                    message=message
                )
                db.add(outreach)
                
            if row.get("email"):
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="email",
                    recipient=row["email"],
                    message=message
                )
                db.add(outreach)
    
    job.status = "import_completed"
    await db.commit()
    return {"job_id": job.id, "count": reader.line_num}

@router.post("/import/google-sheets")
async def import_google_sheets(request: GoogleSheetImportRequest, db: AsyncSession = Depends(get_db)):
    """Import contacts from Google Sheets"""
    try:
        # Import data from Google Sheets
        contacts = await import_from_sheets(request.sheet_id, request.range)
        
        if not contacts:
            raise HTTPException(status_code=400, detail="No valid contacts found in sheet")
        
        # Create a new "import" job record
        job = SearchJob(
            query=f"Google Sheets Import - {request.sheet_id}",
            mode="scrape_and_contact",
            status="processing"
        )
        db.add(job)
        await db.commit()
        
        # Process each contact
        imported_count = 0
        for contact in contacts:
            message = request.message_template or "Custom message from Google Sheets import"
            
            # Format message with contact info
            formatted_message = message.format(
                name=contact.get('name', 'valued customer'),
                business_name=contact.get('name', 'your business'),
                email=contact.get('email', ''),
                phone=contact.get('phone', ''),
                website=contact.get('website', '')
            )
            
            # Add WhatsApp message if phone exists
            if contact.get('phone'):
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="whatsapp",
                    recipient=contact['phone'],
                    message=formatted_message
                )
                db.add(outreach)
                imported_count += 1
            
            # Add email message if email exists
            if contact.get('email'):
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="email",
                    recipient=contact['email'],
                    message=formatted_message
                )
                db.add(outreach)
                imported_count += 1
        
        job.status = "import_completed"
        await db.commit()
        
        return {
            "job_id": job.id,
            "contacts_found": len(contacts),
            "messages_created": imported_count,
            "status": "import_completed"
        }
        
    except Exception as e:
        logger.error(f"Google Sheets import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/bulk-message")
async def send_bulk_messages(
    contacts: list,
    message_template: str,
    contact_method: str = "both",
    subject: str = "Business Inquiry",
    db: AsyncSession = Depends(get_db)
):
    """Send bulk messages to a list of contacts"""
    try:
        # Create job for bulk messaging
        job = SearchJob(
            query="Bulk Message Campaign",
            mode="scrape_and_contact",
            message_type=contact_method,
            prewritten_message=message_template,
            status="processing"
        )
        db.add(job)
        await db.commit()
        
        message_count = 0
        for contact in contacts:
            name = contact.get('name', 'valued customer')
            email = contact.get('email')
            phone = contact.get('phone')
            
            # Format message
            formatted_message = message_template.format(
                name=name,
                business_name=name,
                email=email or '',
                phone=phone or ''
            )
            
            # Send WhatsApp if requested and phone available
            if contact_method in ["whatsapp", "both"] and phone:
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="whatsapp",
                    recipient=phone,
                    message=formatted_message
                )
                db.add(outreach)
                message_count += 1
            
            # Send email if requested and email available
            if contact_method in ["email", "both"] and email:
                outreach = OutreachMessage(
                    job_id=job.id,
                    contact_method="email",
                    recipient=email,
                    message=formatted_message
                )
                db.add(outreach)
                message_count += 1
        
        job.status = "bulk_message_queued"
        await db.commit()
        
        return {
            "job_id": job.id,
            "contacts_processed": len(contacts),
            "messages_queued": message_count,
            "status": "bulk_message_queued"
        }
        
    except Exception as e:
        logger.error(f"Bulk message creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk message failed: {str(e)}")