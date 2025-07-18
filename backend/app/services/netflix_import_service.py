"""
Netflix Viewing History CSV Import Service
"""
import csv
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.content import Movie
from ..schemas.movies import ViewingStatus


class NetflixImportService:
    """Service for importing movies and shows from Netflix viewing history CSV"""
    
    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse Netflix CSV content and return list of viewing data"""
        items = []
        
        # Use StringIO to read CSV content
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Netflix CSV has columns: Title, Date
            title = row.get('Title', '').strip()
            date_str = row.get('Date', '').strip()
            
            if not title:
                continue
                
            # Parse date
            view_date = self._parse_date(date_str)
            
            # Determine if it's a movie or TV show
            # Netflix format: "Show Name: Season X: Episode Title" for TV shows
            # Movies are just the title
            is_tv_show = ': Season ' in title or ': Limited Series:' in title or ': Miniseries:' in title
            
            if is_tv_show:
                # Parse TV show info
                parts = title.split(':')
                show_name = parts[0].strip()
                
                # Extract season and episode info if available
                season_info = None
                episode_info = None
                
                for i, part in enumerate(parts):
                    if 'Season' in part:
                        season_info = part.strip()
                        if i + 1 < len(parts):
                            episode_info = parts[i + 1].strip()
                        break
                
                item_data = {
                    'type': 'tv_show',
                    'title': show_name,
                    'full_title': title,
                    'season_info': season_info,
                    'episode_info': episode_info,
                    'date_watched': view_date,
                }
            else:
                # It's a movie
                item_data = {
                    'type': 'movie',
                    'title': title,
                    'date_watched': view_date,
                }
            
            items.append(item_data)
        
        return items
    
    async def import_viewing_history(
        self, 
        user_id: str, 
        csv_content: str,
        db: Session,
        import_movies: bool = True,
        import_tv_shows: bool = True
    ) -> Dict[str, Any]:
        """Import viewing history from Netflix CSV content"""
        try:
            # Parse CSV
            parsed_items = self.parse_csv_content(csv_content)
            
            if not parsed_items:
                return {
                    'success': False,
                    'message': 'No valid items found in CSV',
                    'movies_imported': 0,
                    'movies_skipped': 0,
                    'tv_shows_imported': 0,
                    'tv_shows_skipped': 0,
                    'errors': 0
                }
            
            movies_imported = 0
            movies_skipped = 0
            tv_shows_imported = 0
            tv_shows_skipped = 0
            errors = 0
            
            # Group TV show episodes by show name to avoid duplicates
            tv_shows_seen = set()
            
            for item_data in parsed_items:
                try:
                    if item_data['type'] == 'movie' and import_movies:
                        # Check if movie already exists for this user
                        existing = db.query(Movie).filter(
                            and_(
                                Movie.user_id == user_id,
                                Movie.title == item_data['title']
                            )
                        ).first()
                        
                        if existing:
                            movies_skipped += 1
                            continue
                        
                        # Create new movie
                        movie = Movie(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            title=item_data['title'],
                            viewing_status=ViewingStatus.WATCHED,
                            date_watched=item_data['date_watched'],
                            source='netflix_import'
                        )
                        
                        db.add(movie)
                        movies_imported += 1
                        
                    elif item_data['type'] == 'tv_show' and import_tv_shows:
                        # For now, we'll track TV shows in the movies table
                        # Later we'll create a separate TV shows table
                        show_title = item_data['title']
                        
                        if show_title in tv_shows_seen:
                            tv_shows_skipped += 1
                            continue
                            
                        tv_shows_seen.add(show_title)
                        
                        # Check if show already exists
                        existing = db.query(Movie).filter(
                            and_(
                                Movie.user_id == user_id,
                                Movie.title == show_title
                            )
                        ).first()
                        
                        if existing:
                            tv_shows_skipped += 1
                            continue
                        
                        # Create entry for the TV show
                        show = Movie(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            title=show_title,
                            viewing_status=ViewingStatus.WATCHED,
                            date_watched=item_data['date_watched'],
                            source='netflix_import',
                            genre='TV Series'  # Mark as TV series
                        )
                        
                        db.add(show)
                        tv_shows_imported += 1
                        
                except Exception as e:
                    print(f"Error importing item '{item_data.get('title', 'Unknown')}': {e}")
                    errors += 1
            
            # Commit all items
            db.commit()
            
            return {
                'success': True,
                'message': f'Successfully imported {movies_imported} movies and {tv_shows_imported} TV shows',
                'movies_imported': movies_imported,
                'movies_skipped': movies_skipped,
                'tv_shows_imported': tv_shows_imported,
                'tv_shows_skipped': tv_shows_skipped,
                'errors': errors,
                'total': len(parsed_items)
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error during Netflix import: {e}")
            return {
                'success': False,
                'message': f'Import failed: {str(e)}',
                'movies_imported': 0,
                'movies_skipped': 0,
                'tv_shows_imported': 0,
                'tv_shows_skipped': 0,
                'errors': 0
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from Netflix format (MM/DD/YY)"""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            # Netflix uses MM/DD/YY format
            return datetime.strptime(date_str.strip(), '%m/%d/%y')
        except:
            try:
                # Try alternative format MM/DD/YYYY
                return datetime.strptime(date_str.strip(), '%m/%d/%Y')
            except:
                return None


# Create singleton instance
netflix_import_service = NetflixImportService()