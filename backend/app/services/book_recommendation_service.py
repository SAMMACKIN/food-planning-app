"""
Book Recommendation Service with AI-powered suggestions and learning feedback system
"""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ai_service import ai_service

from ..models.content import Book, BookRecommendationFeedback
from ..schemas.books import (
    BookRecommendation, 
    BookRecommendationRequest, 
    BookRecommendationResponse,
    FeedbackType
)


class BookRecommendationService:
    def __init__(self):
        self.ai = ai_service
        self.cache_ttl = timedelta(hours=6)  # Cache recommendations for 6 hours
    
    async def get_recommendations(
        self, 
        user_id: str, 
        db: Session, 
        request: BookRecommendationRequest
    ) -> BookRecommendationResponse:
        """
        Generate AI-powered book recommendations based on user's reading history and feedback
        """
        # Build user context from their books and feedback history
        context = await self._build_user_context(user_id, db)
        
        # Generate session ID for tracking feedback
        session_id = f"rec_{user_id[:8]}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Create AI prompt with learned preferences
        prompt = self._create_recommendation_prompt(context, request)
        
        try:
            # Log context details
            print(f"🔍 Book recommendation context: {context['total_books']} total books, {len(context['read_books'])} read")
            print(f"🔍 Preferred genres: {context['preferred_genres']}")
            print(f"🔍 Existing books to exclude: {len(context['existing_books'])}")
            
            # Get AI recommendations
            print(f"🤖 Calling AI service for recommendations...")
            print(f"🤖 AI service available: {self.ai is not None}")
            print(f"🤖 Prompt length: {len(prompt)} characters")
            
            # Check if AI providers are available
            if hasattr(self.ai, 'groq_client'):
                print(f"🤖 Groq client available: {self.ai.groq_client is not None}")
            if hasattr(self.ai, 'claude_client'):
                print(f"🤖 Claude client available: {self.ai.claude_client is not None}")
            if hasattr(self.ai, 'perplexity_api_key'):
                print(f"🤖 Perplexity available: {self.ai.perplexity_api_key is not None}")
            
            ai_response = await self.ai.get_ai_response(prompt)
            print(f"✅ AI response received, length: {len(ai_response)}")
            
            # Parse AI response
            recommendations = self._parse_ai_recommendations(ai_response, session_id)
            print(f"📚 Parsed {len(recommendations)} recommendations from AI")
            
            # Filter out books user already has
            filtered_recommendations = self._filter_existing_books(
                recommendations, context['existing_books']
            )
            print(f"📚 After filtering existing: {len(filtered_recommendations)} recommendations")
            
            # Apply user preferences and exclusions
            final_recommendations = self._apply_user_filters(
                filtered_recommendations, request, context
            )
            print(f"📚 After applying filters: {len(final_recommendations)} recommendations")
            
            # Limit to requested count
            final_recommendations = final_recommendations[:request.max_recommendations]
            
            return BookRecommendationResponse(
                recommendations=final_recommendations,
                session_id=session_id,
                context_summary=self._generate_context_summary(context),
                total_recommendations=len(final_recommendations)
            )
            
        except Exception as e:
            print(f"❌ Error generating book recommendations: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            print(f"❌ Error details: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return empty recommendations with error message
            return BookRecommendationResponse(
                recommendations=[],
                session_id=session_id,
                context_summary=f"Unable to generate recommendations: {str(e)}",
                total_recommendations=0
            )
    
    async def process_feedback(
        self,
        user_id: str,
        db: Session,
        session_id: str,
        recommendation_title: str,
        recommendation_author: str,
        feedback_type: FeedbackType,
        feedback_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback and optionally generate new recommendations
        """
        try:
            # Get context that led to this recommendation
            context = await self._build_user_context(user_id, db)
            
            # Create feedback record
            feedback = BookRecommendationFeedback(
                id=uuid.uuid4(),
                user_id=user_id,
                recommendation_session_id=session_id,
                recommended_title=recommendation_title,
                recommended_author=recommendation_author,
                feedback_type=feedback_type.value,
                feedback_notes=feedback_notes,
                context_books=[book['title'] for book in context['read_books'][-5:]],  # Last 5 books
                context_genres=context['preferred_genres'],
                context_feedback_history=context['feedback_patterns']
            )
            
            db.add(feedback)
            
            # If user wants to read the book, add it to their list
            if feedback_type == FeedbackType.WANT_TO_READ:
                existing_book = db.query(Book).filter(
                    and_(
                        Book.user_id == user_id,
                        Book.title.ilike(f"%{recommendation_title}%"),
                        Book.author.ilike(f"%{recommendation_author}%")
                    )
                ).first()
                
                if not existing_book:
                    new_book = Book(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        title=recommendation_title,
                        author=recommendation_author,
                        reading_status="want_to_read",
                        source="ai_recommendation"
                    )
                    db.add(new_book)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Feedback recorded: {feedback_type.value}",
                "should_regenerate": feedback_type in [FeedbackType.NOT_INTERESTED]
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error processing feedback: {e}")
            return {
                "success": False,
                "message": "Failed to process feedback",
                "should_regenerate": False
            }
    
    async def regenerate_recommendations(
        self,
        user_id: str,
        db: Session,
        request: BookRecommendationRequest
    ) -> BookRecommendationResponse:
        """
        Generate new recommendations incorporating latest feedback
        """
        return await self.get_recommendations(user_id, db, request)
    
    async def _build_user_context(self, user_id: str, db: Session) -> Dict[str, Any]:
        """
        Build comprehensive user context from reading history and feedback
        """
        # Get user's books
        books = db.query(Book).filter(Book.user_id == user_id).all()
        
        # Get user's ratings
        from ..models.content import ContentRating
        ratings = db.query(ContentRating).filter(
            ContentRating.user_id == user_id,
            ContentRating.book_id.isnot(None)
        ).all()
        
        # Create rating lookup
        rating_lookup = {str(rating.book_id): rating.rating for rating in ratings}
        
        # Get feedback history
        feedback_history = db.query(BookRecommendationFeedback).filter(
            BookRecommendationFeedback.user_id == user_id
        ).order_by(desc(BookRecommendationFeedback.created_at)).limit(50).all()
        
        # Categorize books with ratings
        read_books = []
        reading_books = []
        want_to_read_books = []
        favorite_books = []
        highly_rated_books = []
        poorly_rated_books = []
        
        for book in books:
            book_dict = self._book_to_dict(book)
            book_dict['rating'] = rating_lookup.get(str(book.id))
            
            if book.reading_status == "read":
                read_books.append(book_dict)
                # Track highly rated and poorly rated books
                if book_dict['rating']:
                    if book_dict['rating'] >= 4:
                        highly_rated_books.append(book_dict)
                    elif book_dict['rating'] <= 2:
                        poorly_rated_books.append(book_dict)
            elif book.reading_status == "reading":
                reading_books.append(book_dict)
            elif book.reading_status == "want_to_read":
                want_to_read_books.append(book_dict)
                
            if book.is_favorite:
                favorite_books.append(book_dict)
        
        # Analyze genres
        all_genres = [book.genre for book in books if book.genre]
        genre_counts = {}
        for genre in all_genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        preferred_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        preferred_genres = [genre[0] for genre in preferred_genres]
        
        # Analyze feedback patterns
        feedback_patterns = {
            "recent_positive": [],
            "recent_negative": [],
            "preferred_characteristics": [],
            "avoided_characteristics": []
        }
        
        for feedback in feedback_history[-20:]:  # Last 20 feedback items
            if feedback.feedback_type == "want_to_read":
                feedback_patterns["recent_positive"].append({
                    "title": feedback.recommended_title,
                    "author": feedback.recommended_author
                })
            elif feedback.feedback_type == "not_interested":
                feedback_patterns["recent_negative"].append({
                    "title": feedback.recommended_title,
                    "author": feedback.recommended_author
                })
        
        return {
            "total_books": len(books),
            "read_books": read_books,
            "reading_books": reading_books,
            "want_to_read_books": want_to_read_books,
            "favorite_books": favorite_books,
            "highly_rated_books": highly_rated_books,
            "poorly_rated_books": poorly_rated_books,
            "preferred_genres": preferred_genres,
            "genre_distribution": genre_counts,
            "feedback_patterns": feedback_patterns,
            "existing_books": [f"{book.title} by {book.author}" for book in books],
            "reading_level": self._estimate_reading_level(books),
            "recent_activity": self._get_recent_activity(books, feedback_history),
            "average_rating": self._calculate_average_rating(rating_lookup)
        }
    
    def _create_recommendation_prompt(
        self, 
        context: Dict[str, Any], 
        request: BookRecommendationRequest
    ) -> str:
        """
        Create intelligent AI prompt based on user context and feedback history
        """
        prompt = f"""
You are a highly intelligent book recommendation engine. Based on the user's reading history and feedback patterns, recommend {request.max_recommendations} books they would love to read.

USER READING PROFILE:
- Total books in collection: {context['total_books']}
- Books read: {len(context['read_books'])}
- Currently reading: {len(context['reading_books'])}
- Want to read: {len(context['want_to_read_books'])}
- Favorite books: {len(context['favorite_books'])}

PREFERRED GENRES (in order of preference):
{chr(10).join([f"- {genre}" for genre in context['preferred_genres'][:5]])}

HIGHLY RATED BOOKS (4-5 stars):
{chr(10).join([f"- {book['title']} by {book['author']} ({book['rating']}⭐)" for book in context['highly_rated_books'][:10]])}

POORLY RATED BOOKS (1-2 stars - AVOID similar):
{chr(10).join([f"- {book['title']} by {book['author']} ({book['rating']}⭐)" for book in context['poorly_rated_books'][:5]])}

FAVORITE BOOKS:
{chr(10).join([f"- {book['title']} by {book['author']}{f' ({book["rating"]}⭐)' if book.get('rating') else ''}" for book in context['favorite_books'][:5]])}

RECENTLY READ BOOKS:
{chr(10).join([f"- {book['title']} by {book['author']} ({book.get('genre', 'Unknown genre')}){f' - {book["rating"]}⭐' if book.get('rating') else ''}" for book in context['read_books'][-5:]])}

USER RATING PROFILE:
- Average rating: {context.get('average_rating', 'N/A')}
- Tends to rate highly: {len(context['highly_rated_books'])} books rated 4-5 stars
- Tends to rate poorly: {len(context['poorly_rated_books'])} books rated 1-2 stars

RECENT POSITIVE FEEDBACK (books they wanted to read):
{chr(10).join([f"- {item['title']} by {item['author']}" for item in context['feedback_patterns']['recent_positive'][-5:]])}

RECENT NEGATIVE FEEDBACK (books they weren't interested in):
{chr(10).join([f"- {item['title']} by {item['author']}" for item in context['feedback_patterns']['recent_negative'][-5:]])}

BOOKS TO EXCLUDE (already in their collection):
{chr(10).join(context['existing_books'])}

SPECIFIC PREFERENCES:
- Preferred genres: {', '.join(request.preferred_genres) if request.preferred_genres else 'None specified'}
- Exclude genres: {', '.join(request.exclude_genres) if request.exclude_genres else 'None specified'}
- Reading level: {context['reading_level']}

INSTRUCTIONS:
1. Recommend books that align with their demonstrated preferences
2. Learn from their positive/negative feedback patterns
3. CRITICAL: Do NOT recommend any books from the "BOOKS TO EXCLUDE" list above - they already own these
4. STRONGLY prioritize recommending books similar to their HIGHLY RATED books (4-5 stars)
5. AVOID recommending books similar to their POORLY RATED books (1-2 stars)
6. Consider their reading level and genre preferences
7. Provide variety while staying within their interests
8. Include both popular and lesser-known gems
9. Double-check each recommendation against the exclusion list
10. Weight recommendations towards books similar to those rated 4-5 stars

For each recommendation, provide:
- Title
- Author
- Genre
- Brief description (2-3 sentences)
- Why you think they'll like it (based on their reading history)
- Publication year (if known)
- Approximate page count (if known)

Format your response as JSON:
{{
  "recommendations": [
    {{
      "title": "Book Title",
      "author": "Author Name",
      "genre": "Genre",
      "description": "Brief description...",
      "reasoning": "Why this matches their preferences...",
      "publication_year": 2020,
      "pages": 300,
      "confidence_score": 0.85
    }}
  ]
}}
"""
        return prompt
    
    def _parse_ai_recommendations(
        self, 
        ai_response: str, 
        session_id: str
    ) -> List[BookRecommendation]:
        """
        Parse AI response into structured recommendations
        """
        try:
            print(f"🔍 AI Response preview: {ai_response[:200]}...")
            
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                print(f"❌ No JSON found in AI response")
                raise ValueError("No JSON found in response")
            
            json_str = ai_response[start_idx:end_idx]
            print(f"🔍 Extracted JSON length: {len(json_str)}")
            
            data = json.loads(json_str)
            print(f"✅ Successfully parsed JSON with {len(data.get('recommendations', []))} recommendations")
            
            recommendations = []
            for item in data.get('recommendations', []):
                recommendation = BookRecommendation(
                    title=item.get('title', ''),
                    author=item.get('author', ''),
                    genre=item.get('genre'),
                    description=item.get('description'),
                    publication_year=item.get('publication_year'),
                    pages=item.get('pages'),
                    reasoning=item.get('reasoning'),
                    confidence_score=item.get('confidence_score', 0.5)
                )
                recommendations.append(recommendation)
                print(f"  📖 Added: {recommendation.title} by {recommendation.author}")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error parsing AI recommendations: {e}")
            print(f"❌ Full AI response: {ai_response}")
            return []
    
    def _filter_existing_books(
        self, 
        recommendations: List[BookRecommendation], 
        existing_books: List[str]
    ) -> List[BookRecommendation]:
        """
        Remove books that user already has - more aggressive filtering
        """
        filtered = []
        existing_lower = [book.lower() for book in existing_books]
        
        for rec in recommendations:
            rec_title_lower = rec.title.lower()
            rec_author_lower = rec.author.lower()
            book_identifier = f"{rec_title_lower} by {rec_author_lower}"
            
            # Check multiple matching patterns
            is_duplicate = False
            
            for existing in existing_lower:
                # Check exact match
                if existing == book_identifier:
                    is_duplicate = True
                    break
                
                # Check if title and author match separately (handles different formatting)
                if rec_title_lower in existing and rec_author_lower in existing:
                    is_duplicate = True
                    break
                
                # Check if existing contains the full identifier
                if book_identifier in existing:
                    is_duplicate = True
                    break
                
                # Check if title matches exactly (sometimes author might be formatted differently)
                existing_parts = existing.split(' by ')
                if len(existing_parts) > 0 and existing_parts[0] == rec_title_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(rec)
            else:
                print(f"Filtered out duplicate: {rec.title} by {rec.author}")
                
        return filtered
    
    def _apply_user_filters(
        self,
        recommendations: List[BookRecommendation],
        request: BookRecommendationRequest,
        context: Dict[str, Any]
    ) -> List[BookRecommendation]:
        """
        Apply user preferences and exclusions
        """
        filtered = []
        
        for rec in recommendations:
            # Skip if genre is explicitly excluded
            if request.exclude_genres and rec.genre and rec.genre.lower() in [g.lower() for g in request.exclude_genres]:
                continue
            
            # Prefer books in preferred genres
            if request.preferred_genres and rec.genre:
                if rec.genre.lower() not in [g.lower() for g in request.preferred_genres]:
                    # Lower confidence for books outside preferred genres
                    if rec.confidence_score:
                        rec.confidence_score *= 0.7
            
            filtered.append(rec)
        
        # Sort by confidence score
        filtered.sort(key=lambda x: x.confidence_score or 0, reverse=True)
        return filtered
    
    def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of what influenced recommendations
        """
        summary_parts = []
        
        if context['preferred_genres']:
            summary_parts.append(f"Based on your preference for {', '.join(context['preferred_genres'][:3])}")
        
        if context['favorite_books']:
            summary_parts.append(f"Similar to your favorites like '{context['favorite_books'][0]['title']}'")
        
        if context['feedback_patterns']['recent_positive']:
            summary_parts.append("Incorporating your recent positive feedback")
        
        if context['feedback_patterns']['recent_negative']:
            summary_parts.append("Avoiding patterns you've shown less interest in")
        
        return ". ".join(summary_parts) + "."
    
    
    def _book_to_dict(self, book: Book) -> Dict[str, Any]:
        """
        Convert book model to dictionary
        """
        return {
            "id": str(book.id),
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "description": book.description,
            "pages": book.pages,
            "publication_year": book.publication_year,
            "reading_status": book.reading_status,
            "is_favorite": book.is_favorite,
            "date_started": book.date_started,
            "date_finished": book.date_finished
        }
    
    def _estimate_reading_level(self, books: List[Book]) -> str:
        """
        Estimate user's reading level based on their book collection
        """
        if not books:
            return "Unknown"
        
        # Simple heuristic based on average page count and genres
        avg_pages = sum(book.pages for book in books if book.pages) / len([book for book in books if book.pages])
        
        complex_genres = ['Philosophy', 'Science', 'Academic', 'Technical', 'Classic Literature']
        complex_count = sum(1 for book in books if book.genre and book.genre in complex_genres)
        
        if avg_pages > 400 or complex_count > len(books) * 0.3:
            return "Advanced"
        elif avg_pages > 250:
            return "Intermediate"
        else:
            return "Light/Popular"
    
    def _get_recent_activity(self, books: List[Book], feedback_history: List[BookRecommendationFeedback]) -> Dict[str, Any]:
        """
        Analyze recent reading activity
        """
        recent_books = [book for book in books if book.updated_at and book.updated_at > datetime.now(timezone.utc) - timedelta(days=30)]
        recent_feedback = [f for f in feedback_history if f.created_at > datetime.now(timezone.utc) - timedelta(days=30)]
        
        return {
            "books_added_recently": len(recent_books),
            "feedback_given_recently": len(recent_feedback),
            "active_reader": len(recent_books) > 2 or len(recent_feedback) > 5
        }
    
    def _calculate_average_rating(self, rating_lookup: Dict[str, int]) -> float:
        """
        Calculate average rating from rating lookup
        """
        if not rating_lookup:
            return 0.0
        
        ratings = list(rating_lookup.values())
        return round(sum(ratings) / len(ratings), 1)


# Create singleton instance
book_recommendation_service = BookRecommendationService()