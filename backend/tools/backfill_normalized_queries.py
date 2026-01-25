"""
Backfill script to update existing UserPlace records with query_normalized values.

This script:
1. Reads all UserPlace records where query_normalized is NULL
2. Normalizes the search_query using QueryNormalizer
3. Updates the record with the normalized query

Run from backend folder:
    python -m tools.backfill_normalized_queries
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models.scrape_history import UserPlace
from sqlalchemy import text
from services.query_normalizer import QueryNormalizer


def backfill_normalized_queries():
    """Backfill query_normalized for existing UserPlace records."""
    normalizer = QueryNormalizer()
    
    with SessionLocal() as db:
        # Count records needing update
        count_query = select(func.count(UserPlace.id)).where(
            UserPlace.query_normalized.is_(None)
        )
        total = db.execute(count_query).scalar()
        print(f"📊 Found {total} UserPlace records with NULL query_normalized")
        
        if total == 0:
            print("✅ All records already have query_normalized set!")
            return
        
        # Fetch records in batches
        batch_size = 500
        updated = 0

        while True:
            query = select(UserPlace).where(
                UserPlace.query_normalized.is_(None)
            ).limit(batch_size)

            results = db.execute(query).scalars().all()
            if not results:
                break

            for place in results:
                normalized_value = None

                # Prefer using an associated ScrapeSession if query_hash is present
                if place.query_hash:
                    # Use raw SQL to avoid relying on optional model columns
                    row = db.execute(
                        text("SELECT query FROM scrape_sessions WHERE query_hash = :qhash LIMIT 1"),
                        {"qhash": place.query_hash}
                    ).fetchone()

                    if row and row[0]:
                        normalized_value = normalizer.normalize(row[0])

                # If we still don't have a normalized value, skip (can't infer safely)
                if normalized_value:
                    place.query_normalized = normalized_value
                    updated += 1

            db.commit()
            print(f"📝 Updated {updated}/{total} records...")

        print(f"✅ Backfill complete! Updated {updated} records.")


def show_stats():
    """Show statistics about query_normalized values."""
    normalizer = QueryNormalizer()
    
    with SessionLocal() as db:
        # Count total
        total = db.execute(select(func.count(UserPlace.id))).scalar()
        
        # Count with normalized
        with_normalized = db.execute(
            select(func.count(UserPlace.id)).where(
                UserPlace.query_normalized.isnot(None)
            )
        ).scalar()
        
        # Count without normalized
        without_normalized = total - with_normalized
        
        # Get unique normalized queries
        unique_normalized = db.execute(
            select(func.count(func.distinct(UserPlace.query_normalized)))
        ).scalar()
        
        # Get unique original queries by query_hash (best available)
        unique_original = db.execute(
            select(func.count(func.distinct(UserPlace.query_hash)))
        ).scalar()
        
        print("=" * 50)
        print("📊 UserPlace Query Normalization Stats")
        print("=" * 50)
        print(f"Total records:           {total}")
        print(f"With query_normalized:   {with_normalized}")
        print(f"Without query_normalized:{without_normalized}")
        print(f"Unique original queries: {unique_original}")
        print(f"Unique normalized queries: {unique_normalized}")
        
        if unique_original and unique_normalized:
            reduction = ((unique_original - unique_normalized) / unique_original) * 100
            print(f"Query consolidation:     {reduction:.1f}% reduction")
        print("=" * 50)
        
        # Show sample mappings (query_hash -> query_normalized)
        print("\n📋 Sample query normalizations (by query_hash):")
        sample = db.execute(
            select(UserPlace.query_hash, UserPlace.query_normalized)
            .where(UserPlace.query_normalized.isnot(None))
            .distinct()
            .limit(10)
        ).all()

        for qhash, norm in sample:
            print(f"  '{qhash}' → '{norm}'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill normalized queries for UserPlace records")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
    elif args.dry_run:
        from services.query_normalizer import QueryNormalizer
        normalizer = QueryNormalizer()
        
        with SessionLocal() as db:
            # Show sample of query_hash values and what we'd infer
            query = select(UserPlace.query_hash).where(
                UserPlace.query_normalized.is_(None)
            ).distinct().limit(20)

            results = db.execute(query).scalars().all()

            print("🔍 Sample normalizations (dry run):")
            for qhash in results:
                if not qhash:
                    print("  <no query_hash> -> skipped")
                    continue

                row = db.execute(
                    text("SELECT query FROM scrape_sessions WHERE query_hash = :qhash LIMIT 1"),
                    {"qhash": qhash}
                ).fetchone()

                if row and row[0]:
                    print(f"  '{qhash}' -> normalized(session.query): '{normalizer.normalize(row[0])}'")
                else:
                    print(f"  '{qhash}' -> no matching ScrapeSession found; would skip")
    else:
        print("🚀 Starting backfill...")
        backfill_normalized_queries()
        print("\n📊 Final stats:")
        show_stats()
