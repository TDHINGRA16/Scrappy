"""
Query Normalizer Service for Scrappy v2.0

Normalizes search queries for cursor matching.
Handles query variations like:
- "dentist amritsar" vs "amritsar dentist"
- Extra spaces, punctuation
- Case differences
- Location indicators ("in", "near", "around")

This is CRITICAL for cursor-based pagination because:
- User might search "dentist in amritsar" first
- Then search "amritsar dentist" later
- Both should match the same cursor!
"""

import hashlib
import re
import logging
from typing import Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class QueryNormalizer:
    """
    Normalize search queries to canonical form for cursor matching.
    
    Normalization steps:
    1. Lowercase
    2. Remove extra punctuation (keep meaningful chars)
    3. Remove extra spaces
    4. Extract and sort tokens
    5. Handle location indicators
    
    Example:
        "Dentist - in Amritsar" → "amritsar dentist in"
        "amritsar dentist"      → "amritsar dentist"
        "DENTIST Amritsar"      → "amritsar dentist"
    """
    
    # Location indicator words - these come at the end
    LOCATION_WORDS = {'in', 'near', 'around', 'at', 'of', 'for'}
    
    # Words to remove completely (articles, conjunctions)
    STOP_WORDS = {'the', 'a', 'an', 'and', 'or'}
    
    @classmethod
    def normalize(cls, query: str) -> str:
        """
        Normalize query to canonical form.
        
        Args:
            query: Raw search query (e.g., "Dentist - in Amritsar")
            
        Returns:
            Normalized query string (e.g., "amritsar dentist in")
        """
        if not query:
            return ""
        
        # Step 1: Lowercase and strip
        q = query.lower().strip()
        
        # Step 2: Remove extra punctuation (keep "-", "&", space)
        # These are meaningful in business names
        q = re.sub(r'[^\w\s\-&]', ' ', q)
        
        # Step 3: Remove extra spaces
        q = re.sub(r'\s+', ' ', q).strip()
        
        # Step 4: Tokenize
        tokens = q.split()
        
        # Step 5: Remove stop words
        tokens = [t for t in tokens if t not in cls.STOP_WORDS]
        
        # Step 6: Separate service words from location indicators
        service_tokens = []
        location_tokens = []
        
        for token in tokens:
            if token in cls.LOCATION_WORDS:
                location_tokens.append(token)
            else:
                service_tokens.append(token)
        
        # Step 7: Sort tokens alphabetically for consistent ordering
        # "dentist amritsar" and "amritsar dentist" both become "amritsar dentist"
        service_tokens.sort()
        location_tokens.sort()
        
        # Step 8: Reconstruct: service words + location words
        normalized = ' '.join(service_tokens + location_tokens)
        
        return normalized
    
    @classmethod
    def get_hash(cls, query: str) -> str:
        """
        Get MD5 hash of normalized query.
        
        Used for fast database lookups with index.
        
        Args:
            query: Raw or normalized query
            
        Returns:
            32-character MD5 hash string
        """
        normalized = cls.normalize(query)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    @classmethod
    def normalize_with_hash(cls, query: str) -> Tuple[str, str]:
        """
        Get both normalized query and its hash.
        
        Args:
            query: Raw search query
            
        Returns:
            Tuple of (normalized_query, hash)
        """
        normalized = cls.normalize(query)
        query_hash = hashlib.md5(normalized.encode('utf-8')).hexdigest()
        return normalized, query_hash
    
    @classmethod
    def are_queries_equivalent(cls, query1: str, query2: str) -> bool:
        """
        Check if two queries are semantically equivalent.
        
        Args:
            query1: First query
            query2: Second query
            
        Returns:
            True if queries normalize to the same form
        """
        return cls.normalize(query1) == cls.normalize(query2)

    @classmethod
    def fuzzy_match(cls, query1: str, query2: str, threshold: float = 0.85) -> bool:
        """
        Fuzzy match two queries using normalized forms and SequenceMatcher.

        Returns True if similarity >= threshold.
        """
        if not query1 or not query2:
            return False

        norm1 = cls.normalize(query1)
        norm2 = cls.normalize(query2)
        if not norm1 or not norm2:
            return False

        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        logger.debug(f"Fuzzy similarity between '{norm1}' and '{norm2}': {similarity:.3f}")
        return similarity >= threshold
    
    @classmethod
    def extract_location(cls, query: str) -> Tuple[str, str]:
        """
        Extract service type and location from query.
        
        Useful for analytics and display.
        
        Args:
            query: Search query (e.g., "dentist in Amritsar")
            
        Returns:
            Tuple of (service_type, location)
            e.g., ("dentist", "amritsar")
        """
        q = query.lower().strip()
        q = re.sub(r'[^\w\s\-&]', ' ', q)
        q = re.sub(r'\s+', ' ', q).strip()
        
        tokens = q.split()
        
        # Find location indicator and split there
        for i, token in enumerate(tokens):
            if token in cls.LOCATION_WORDS and i < len(tokens) - 1:
                service = ' '.join(tokens[:i])
                location = ' '.join(tokens[i+1:])
                return service, location
        
        # No location indicator found - try to guess
        # Usually location is the last token(s)
        if len(tokens) >= 2:
            return tokens[0], ' '.join(tokens[1:])
        
        return query, ""


# Convenience functions for module-level use
def normalize_query(query: str) -> str:
    """Normalize a search query to canonical form."""
    return QueryNormalizer.normalize(query)


def get_query_hash(query: str) -> str:
    """Get MD5 hash of normalized query."""
    return QueryNormalizer.get_hash(query)


def are_queries_equivalent(query1: str, query2: str) -> bool:
    """Check if two queries are semantically equivalent."""
    return QueryNormalizer.are_queries_equivalent(query1, query2)
