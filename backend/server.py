from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
import uuid
import asyncio
import os
from datetime import datetime
import random
import math
import json
import logging
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
# Import SQLAlchemy components
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_, or_
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_db_session, init_database, engine,
    Player as DBPlayer, Category as DBCategory, 
    Match as DBMatch, Session as DBSession, Club as DBClub
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database will use SQLite through dependency injection

# Initialize FastAPI app
app = FastAPI(title="CourtChime API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class MatchStatus(str, Enum):
    pending = "pending"
    active = "active" 
    buffer = "buffer"
    done = "done"
    saved = "saved"  # Add saved status for completed matches

class MatchType(str, Enum):
    singles = "singles"
    doubles = "doubles"

class SessionPhase(str, Enum):
    idle = "idle"
    ready = "ready"  # New phase: matches generated, waiting for timer start
    play = "play"
    buffer = "buffer"
    ended = "ended"

class Format(str, Enum):
    singles = "singles"
    doubles = "doubles"
    auto = "auto"

# Data Models
class Club(BaseModel):
    name: str  # Primary key - club identifier
    display_name: str
    description: Optional[str] = None
    access_code: Optional[str] = None  # For club access control
    created_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())

class ClubCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    access_code: str  # Required for club creation

class ClubLogin(BaseModel):
    club_name: str
    access_code: str

class ClubSession(BaseModel):
    club_name: str
    display_name: str
    authenticated: bool = True

class PlayerStats(BaseModel):
    wins: int = 0
    losses: int = 0
    pointDiff: int = 0

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    sitNextRound: bool = False
    sitCount: int = 0
    missDueToCourtLimit: int = 0
    isActive: bool = True  # Can be toggled for daily sessions
    # DUPR-style rating fields
    rating: float = 3.0  # Starting rating (typical DUPR range 2.0-8.0)
    matchesPlayed: int = 0
    wins: int = 0
    losses: int = 0
    recentForm: List[str] = []  # Last 10 results: 'W' or 'L'
    ratingHistory: List[dict] = []  # Track rating changes over time
    lastUpdated: str = Field(default_factory=lambda: datetime.now().isoformat())
    stats: PlayerStats = Field(default_factory=PlayerStats)

class PlayerCreate(BaseModel):
    name: str
    category: str

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    sitNextRound: Optional[bool] = None

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    roundIndex: int
    courtIndex: int
    category: str
    teamA: List[str]  # Player IDs
    teamB: List[str]  # Player IDs
    status: MatchStatus = MatchStatus.pending
    matchType: MatchType
    scoreA: Optional[int] = None
    scoreB: Optional[int] = None
    matchDate: str = Field(default_factory=lambda: datetime.now().isoformat())  # Date when match was created

class MatchScoreUpdate(BaseModel):
    scoreA: int
    scoreB: int

class SessionConfig(BaseModel):
    numCourts: int = 4
    playSeconds: int = 720  # 12 minutes
    bufferSeconds: int = 30  # 30 seconds
    allowSingles: bool = True
    allowDoubles: bool = True
    allowCrossCategory: bool = False
    maximizeCourtUsage: bool = False  # New option for court optimization
    rotationModel: str = 'legacy'  # 'legacy' or 'top_court'

class SessionState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    currentRound: int = 0
    phase: SessionPhase = SessionPhase.idle
    timeRemaining: int = 0
    paused: bool = False
    sessionDate: Optional[str] = None  # ISO format date string (YYYY-MM-DD)
    config: SessionConfig = Field(default_factory=SessionConfig)
    histories: Dict[str, Any] = Field(default_factory=dict)  # partners and opponents histories

# Scheduling Algorithm Functions
def shuffle_list(items: List[Any]) -> List[Any]:
    """Shuffle a list for randomization"""
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled

def calculate_rating_change(player_rating: float, opponent_avg_rating: float, game_result: str, 
                          score_margin: int = 0, k_factor: float = 32.0) -> float:
    """
    DUPR-style rating calculation
    
    Args:
        player_rating: Current rating of the player
        opponent_avg_rating: Average rating of opponents in the match
        game_result: 'W' for win, 'L' for loss
        score_margin: Point difference (positive for wins, negative for losses)
        k_factor: How much ratings can change (higher = more volatile)
    
    Returns:
        Rating change (can be positive or negative)
    """
    # Expected score based on rating difference (ELO-style)
    rating_diff = opponent_avg_rating - player_rating
    expected_score = 1 / (1 + 10 ** (rating_diff / 400))
    
    # Actual score (1 for win, 0 for loss)
    actual_score = 1.0 if game_result == 'W' else 0.0
    
    # Base rating change
    base_change = k_factor * (actual_score - expected_score)
    
    # Margin multiplier (DUPR considers score margins)
    # Closer games have less impact, blowout wins/losses have more impact
    margin_multiplier = 1.0
    if score_margin > 0:  # Win
        margin_multiplier = min(1.5, 1.0 + (abs(score_margin) / 20.0))  # Cap at 1.5x
    elif score_margin < 0:  # Loss  
        margin_multiplier = min(1.5, 1.0 + (abs(score_margin) / 20.0))  # Same for losses
    
    # Apply diminishing returns for very high/low ratings
    if player_rating > 6.0:  # High-rated players change less
        base_change *= 0.8
    elif player_rating < 3.0:  # Low-rated players can improve faster
        base_change *= 1.2
    
    final_change = base_change * margin_multiplier
    
    # Ensure rating stays within reasonable bounds
    new_rating = player_rating + final_change
    if new_rating > 8.0:
        final_change = 8.0 - player_rating
    elif new_rating < 2.0:
        final_change = 2.0 - player_rating
    
    return final_change

async def update_player_ratings(match: dict, teamA_score: int, teamB_score: int, db_session: AsyncSession):
    """
    Update player ratings based on match result (DUPR-style) - SQLite version
    """
    try:
        # Get all players in the match
        all_player_ids = match['teamA'] + match['teamB']
        players = []
        
        for player_id in all_player_ids:
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id))
            db_player = result.scalar_one_or_none()
            if db_player:
                # Convert to dict format for compatibility
                player_dict = {
                    'id': db_player.id,
                    'rating': db_player.rating,
                    'matchesPlayed': db_player.matches_played,
                    'wins': db_player.wins,
                    'losses': db_player.losses,
                    'recentForm': json.loads(db_player.recent_form) if db_player.recent_form else [],
                    'ratingHistory': json.loads(db_player.rating_history) if db_player.rating_history else []
                }
                players.append((db_player, player_dict))
        
        if len(players) != len(all_player_ids):
            return  # Some players not found
        
        # Split into teams
        teamA_players = [(db_p, p_dict) for db_p, p_dict in players if p_dict['id'] in match['teamA']]
        teamB_players = [(db_p, p_dict) for db_p, p_dict in players if p_dict['id'] in match['teamB']]
        
        # Calculate average ratings for each team
        teamA_avg = sum(p_dict['rating'] for _, p_dict in teamA_players) / len(teamA_players)
        teamB_avg = sum(p_dict['rating'] for _, p_dict in teamB_players) / len(teamB_players)
        
        # Determine winner and score margin
        teamA_won = teamA_score > teamB_score
        score_margin = abs(teamA_score - teamB_score)
        
        # Update ratings for all players
        for db_player, player_dict in teamA_players:
            result = 'W' if teamA_won else 'L'
            margin = score_margin if teamA_won else -score_margin
            rating_change = calculate_rating_change(
                player_dict['rating'], teamB_avg, result, margin
            )
            
            new_rating = round(player_dict['rating'] + rating_change, 2)
            new_matches = player_dict['matchesPlayed'] + 1
            new_wins = player_dict['wins'] + (1 if teamA_won else 0)
            new_losses = player_dict['losses'] + (0 if teamA_won else 1)
            
            # Update recent form (last 10 games)
            recent_form = player_dict['recentForm'].copy()
            recent_form.append(result)
            if len(recent_form) > 10:
                recent_form = recent_form[-10:]
            
            # Add to rating history
            rating_history = player_dict['ratingHistory'].copy()
            rating_history.append({
                'date': datetime.now().isoformat(),
                'oldRating': player_dict['rating'],
                'newRating': new_rating,
                'change': rating_change,
                'matchId': match['id'],
                'result': result
            })
            if len(rating_history) > 50:
                rating_history = rating_history[-50:]  # Keep last 50 rating changes
            
            # Update player in SQLite database
            db_player.rating = new_rating
            db_player.matches_played = new_matches
            db_player.wins = new_wins
            db_player.losses = new_losses
            db_player.recent_form = json.dumps(recent_form)
            db_player.rating_history = json.dumps(rating_history)
            db_player.last_updated = datetime.now()
        
        # Update ratings for Team B
        for db_player, player_dict in teamB_players:
            result = 'L' if teamA_won else 'W'
            margin = -score_margin if teamA_won else score_margin
            rating_change = calculate_rating_change(
                player_dict['rating'], teamA_avg, result, margin
            )
            
            new_rating = round(player_dict['rating'] + rating_change, 2)
            new_matches = player_dict['matchesPlayed'] + 1
            new_wins = player_dict['wins'] + (0 if teamA_won else 1)
            new_losses = player_dict['losses'] + (1 if teamA_won else 0)
            
            # Update recent form
            recent_form = player_dict['recentForm'].copy()
            recent_form.append(result)
            if len(recent_form) > 10:
                recent_form = recent_form[-10:]
            
            # Add to rating history
            rating_history = player_dict['ratingHistory'].copy()
            rating_history.append({
                'date': datetime.now().isoformat(),
                'oldRating': player_dict['rating'],
                'newRating': new_rating,
                'change': rating_change,
                'matchId': match['id'],
                'result': result
            })
            if len(rating_history) > 50:
                rating_history = rating_history[-50:]
            
            # Update player in SQLite database
            db_player.rating = new_rating
            db_player.matches_played = new_matches
            db_player.wins = new_wins
            db_player.losses = new_losses
            db_player.recent_form = json.dumps(recent_form)
            db_player.rating_history = json.dumps(rating_history)
            db_player.last_updated = datetime.now()
        
        # CRITICAL FIX: Commit the rating changes to database
        await db_session.commit()
        print(f"✅ Successfully updated ratings for {len(all_player_ids)} players")
            
    except Exception as e:
        print(f"❌ Error updating player ratings: {e}")
        await db_session.rollback()
        # Continue without failing the match score update

def calculate_partner_score(player_a: str, player_b: str, histories: Dict[str, Any]) -> int:
    """Calculate how often two players have been partners"""
    partner_history = histories.get('partnerHistory', {})
    return partner_history.get(player_a, {}).get(player_b, 0)

def calculate_opponent_score(team_a: List[str], team_b: List[str], histories: Dict[str, Any]) -> int:
    """Calculate opponent history score between two teams"""
    opponent_history = histories.get('opponentHistory', {})
    total_score = 0
    
    for player_a in team_a:
        for player_b in team_b:
            total_score += opponent_history.get(player_a, {}).get(player_b, 0)
    
    return total_score

def calculate_team_rating_avg(team: List[str], players: List[Player]) -> float:
    """Calculate average rating for a team"""
    team_players = [p for p in players if p.id in team]
    if not team_players:
        return 3.0
    return sum(p.rating for p in team_players) / len(team_players)

def calculate_rating_variance(matches: List[Match], players: List[Player]) -> float:
    """Calculate rating variance across all matches for better balance"""
    if not matches:
        return 0.0
    
    rating_differences = []
    for match in matches:
        team_a_avg = calculate_team_rating_avg(match.teamA, players)
        team_b_avg = calculate_team_rating_avg(match.teamB, players)
        rating_differences.append(abs(team_a_avg - team_b_avg))
    
    return sum(rating_differences) / len(rating_differences)

def enhanced_shuffle_with_rating_balance(players: List[Player], num_iterations: int = 5) -> List[Player]:
    """
    Enhanced shuffling algorithm that considers rating balance
    Tries multiple random shuffles and picks the one with best rating distribution
    """
    if len(players) <= 2:
        return shuffle_list(players)
    
    best_shuffle = None
    best_balance_score = float('inf')
    
    for _ in range(num_iterations):
        shuffled = shuffle_list(players)
        
        # Calculate balance score - we want players of different ratings spread out
        balance_score = 0
        for i in range(len(shuffled) - 1):
            rating_diff = abs(shuffled[i].rating - shuffled[i+1].rating)
            balance_score += 1.0 / (rating_diff + 0.1)  # Penalty for similar ratings being adjacent
        
        if balance_score < best_balance_score:
            best_balance_score = balance_score
            best_shuffle = shuffled
    
    return best_shuffle or players

def update_histories(match: Match, histories: Dict[str, Any]) -> Dict[str, Any]:
    """Update partner and opponent histories based on a match"""
    if 'partnerHistory' not in histories:
        histories['partnerHistory'] = {}
    if 'opponentHistory' not in histories:
        histories['opponentHistory'] = {}
    
    # Update partner histories (for doubles)
    if match.matchType == MatchType.doubles:
        if len(match.teamA) == 2:
            a1, a2 = match.teamA[0], match.teamA[1]
            if a1 not in histories['partnerHistory']:
                histories['partnerHistory'][a1] = {}
            if a2 not in histories['partnerHistory']:
                histories['partnerHistory'][a2] = {}
            histories['partnerHistory'][a1][a2] = histories['partnerHistory'][a1].get(a2, 0) + 1
            histories['partnerHistory'][a2][a1] = histories['partnerHistory'][a2].get(a1, 0) + 1
        
        if len(match.teamB) == 2:
            b1, b2 = match.teamB[0], match.teamB[1]
            if b1 not in histories['partnerHistory']:
                histories['partnerHistory'][b1] = {}
            if b2 not in histories['partnerHistory']:
                histories['partnerHistory'][b2] = {}
            histories['partnerHistory'][b1][b2] = histories['partnerHistory'][b1].get(b2, 0) + 1
            histories['partnerHistory'][b2][b1] = histories['partnerHistory'][b2].get(b1, 0) + 1
    
    # Update opponent histories
    for player_a in match.teamA:
        for player_b in match.teamB:
            if player_a not in histories['opponentHistory']:
                histories['opponentHistory'][player_a] = {}
            if player_b not in histories['opponentHistory']:
                histories['opponentHistory'][player_b] = {}
            histories['opponentHistory'][player_a][player_b] = histories['opponentHistory'][player_a].get(player_b, 0) + 1
            histories['opponentHistory'][player_b][player_a] = histories['opponentHistory'][player_b].get(player_a, 0) + 1
    
    return histories

async def schedule_round(round_index: int, db_session: AsyncSession = None, club_name: str = "Main Club") -> List[Match]:
    """
    Core scheduling algorithm for round-robin matchmaking
    Implements category-based fair pairing with singles/doubles/auto-mix support
    """
    # Get a database session if not provided
    if db_session is None:
        async with AsyncSession(engine) as db_session:
            return await schedule_round(round_index, db_session)
    
    # Get current session and configuration - SQLite version with club support
    # club_name is now passed as parameter
    result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
    db_session_obj = result.scalar_one_or_none()
    if not db_session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Parse session data
    session_data = {
        'id': db_session_obj.id,
        'currentRound': db_session_obj.current_round,
        'phase': db_session_obj.phase,
        'timeRemaining': db_session_obj.time_remaining,
        'paused': db_session_obj.paused,
        'config': json.loads(db_session_obj.config) if db_session_obj.config else {},
        'histories': json.loads(db_session_obj.histories) if db_session_obj.histories else {"partnerHistory": {}, "opponentHistory": {}}
    }
    
    session_obj = SessionState(**session_data)
    config = session_obj.config
    
    # Get all players and categories - SQLite version
    result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
    db_players = result.scalars().all()
    
    result = await db_session.execute(select(DBCategory))
    db_categories = result.scalars().all()
    
    # Convert to pydantic models
    players_data = []
    for db_player in db_players:
        player_data = {
            'id': db_player.id,
            'name': db_player.name,
            'category': db_player.category,
            'sitNextRound': db_player.sit_next_round,
            'sitCount': db_player.sit_count,
            'missDueToCourtLimit': db_player.miss_due_to_court_limit,
            'isActive': db_player.is_active,  # CRITICAL FIX: Include isActive field
            'stats': {
                'wins': db_player.stats_wins,
                'losses': db_player.stats_losses,
                'pointDiff': db_player.stats_point_diff
            },
            'rating': db_player.rating,
            'matchesPlayed': db_player.matches_played,
            'wins': db_player.wins,
            'losses': db_player.losses,
            'recentForm': json.loads(db_player.recent_form) if db_player.recent_form else [],
            'ratingHistory': json.loads(db_player.rating_history) if db_player.rating_history else [],
            'lastUpdated': db_player.last_updated.isoformat() if db_player.last_updated else None
        }
        players_data.append(player_data)
    
    categories_data = []
    for db_category in db_categories:
        category_data = {
            'id': db_category.id,
            'name': db_category.name,
            'description': db_category.description
        }
        categories_data.append(category_data)
    
    players = [Player(**p) for p in players_data]
    categories = [Category(**c) for c in categories_data]
    
    # Group players by category or all together based on allowCrossCategory
    players_by_category = defaultdict(list)
    
    if config.allowCrossCategory:
        # Mix all players together in one group
        all_eligible = [p for p in players if not p.sitNextRound and p.isActive]
        if all_eligible:
            players_by_category["Mixed"] = all_eligible
    else:
        # Group by individual categories (original behavior)
        for player in players:
            if not player.sitNextRound and player.isActive:  # Exclude players forced to sit and inactive players
                players_by_category[player.category].append(player)
    
    # Initialize match planning
    court_plans = {}
    created_matches = []
    used_player_ids = set()
    
    # Plan matches per category
    categories_to_process = ["Mixed"] if config.allowCrossCategory else [cat.name for cat in categories]
    
    for cat_name in categories_to_process:
        eligible_players = players_by_category[cat_name]
        
        if len(eligible_players) < 2:
            # Not enough players for any match
            continue
        
        doubles_matches = 0
        singles_matches = 0
        
        # Determine match allocation based on new format system
        # Priority: Doubles first, then singles from remaining players
        if not config.allowSingles and not config.allowDoubles:
            # This should be caught by validation, but just in case
            continue
        
        count = len(eligible_players)
        
        # Base allocation logic
        if config.allowDoubles and count >= 4:
            # Priority: Create as many doubles matches as possible
            doubles_matches = count // 4
            remaining_players = count % 4
            
            # Handle remaining players with singles if allowed
            if config.allowSingles and remaining_players >= 2:
                if remaining_players == 3:
                    # 3 remaining: sit 1 lowest-sit player, make 1 singles match
                    eligible_players.sort(key=lambda p: (p.sitCount, p.missDueToCourtLimit, p.name))
                    sit_player = eligible_players.pop(0)
                    singles_matches = 1
                    count = len(eligible_players)  # Update count after sitting player
                    doubles_matches = (count - 2) // 4  # Recalculate doubles
                elif remaining_players == 2:
                    # 2 remaining: perfect for 1 singles match
                    singles_matches = 1
                # remaining_players == 1: sits out naturally
                # remaining_players == 0: all in doubles, perfect
            # If singles not allowed, remaining players sit out
            
        elif config.allowSingles and count >= 2:
            # Only singles allowed, or not enough players for doubles
            singles_matches = count // 2
            # Odd numbered player sits out naturally
        
        # Apply court optimization OVERRIDE if enabled
        if config.maximizeCourtUsage:
            # Maximize court usage: Fill ALL available courts, minimize sitouts
            # Strategy: Try to fill all numCourts with the best combination of doubles/singles
            
            courts_to_fill = config.numCourts
            best_doubles = 0
            best_singles = 0
            
            if config.allowDoubles and config.allowSingles:
                # Mixed approach: Try different combinations to use all courts
                # Prioritize doubles, then fill remaining courts with singles
                
                # Calculate maximum doubles we can make with available players
                max_possible_doubles = count // 4
                
                # Try to use all courts
                if max_possible_doubles >= courts_to_fill:
                    # We have enough players for all courts to be doubles
                    best_doubles = courts_to_fill
                    best_singles = 0
                else:
                    # Use all possible doubles, fill rest with singles
                    best_doubles = max_possible_doubles
                    remaining_players = count - (best_doubles * 4)
                    remaining_courts = courts_to_fill - best_doubles
                    
                    # Fill remaining courts with singles if we have enough players
                    possible_singles = remaining_players // 2
                    best_singles = min(possible_singles, remaining_courts)
                
                doubles_matches = best_doubles
                singles_matches = best_singles
                
            elif config.allowDoubles:
                # Doubles only - fill all courts with doubles
                doubles_matches = min(count // 4, courts_to_fill)
                singles_matches = 0
                
            elif config.allowSingles:
                # Singles only - fill all courts with singles
                doubles_matches = 0
                singles_matches = min(count // 2, courts_to_fill)
        
        court_plans[cat_name] = {
            'doubles': doubles_matches,
            'singles': singles_matches,
            'eligible_players': eligible_players
        }
        
        # Debug logging for optimization
        if config.maximizeCourtUsage:
            print(f"DEBUG: Category {cat_name} - {count} players -> {doubles_matches} doubles, {singles_matches} singles")
    
    # Calculate total courts needed - FIXED for optimization
    total_courts_needed = sum(plan['doubles'] + plan['singles'] for plan in court_plans.values())
    
    # CRITICAL FIX: When optimization is enabled, don't limit courts to initially planned amount
    if config.maximizeCourtUsage:
        available_courts = config.numCourts  # Use all available courts
        print(f"DEBUG: Optimization enabled - using all {available_courts} courts, planned {total_courts_needed} matches")
    else:
        available_courts = min(config.numCourts, total_courts_needed)
        print(f"DEBUG: Standard mode - limiting to {available_courts} courts for {total_courts_needed} matches")
    
    # Court Allocation Optimization: Maximize court usage if enabled
    if config.maximizeCourtUsage and total_courts_needed < config.numCourts:
        # Advanced optimization: Try to create more matches to utilize available courts
        # This uses a greedy approach to fill unused courts with additional matches
        
        additional_courts_available = config.numCourts - total_courts_needed
        
        # Instead of limiting to one match per category, allow multiple matches
        # when we have enough players and courts available
        for cat_name in list(court_plans.keys()):
            if additional_courts_available <= 0:
                break
                
            plan = court_plans[cat_name]
            eligible = plan['eligible_players']
            
            # Calculate how many players are currently used
            current_players_used = (plan['doubles'] * 4) + (plan['singles'] * 2)
            remaining_players = len(eligible) - current_players_used
            
            # Create additional doubles matches if possible
            if config.allowDoubles and remaining_players >= 4:
                additional_doubles_possible = min(remaining_players // 4, additional_courts_available)
                if additional_doubles_possible > 0:
                    plan['doubles'] += additional_doubles_possible
                    additional_courts_available -= additional_doubles_possible
                    remaining_players -= additional_doubles_possible * 4
            
            # Create additional singles matches with remaining players
            if config.allowSingles and remaining_players >= 2 and additional_courts_available > 0:
                additional_singles_possible = min(remaining_players // 2, additional_courts_available)
                if additional_singles_possible > 0:
                    plan['singles'] += additional_singles_possible
                    additional_courts_available -= additional_singles_possible
        
        # If we still have unused courts and players sitting out, try additional optimization
        if additional_courts_available > 0:
            # Collect all unused players across all categories
            all_unused_players = []
            for cat_name, plan in court_plans.items():
                current_players_used = (plan['doubles'] * 4) + (plan['singles'] * 2)
                unused_players = plan['eligible_players'][current_players_used:]
                all_unused_players.extend(unused_players)
            
            # Try to create additional matches with unused players to fill courts
            if len(all_unused_players) >= 4 and config.allowDoubles and additional_courts_available > 0:
                additional_doubles = min(len(all_unused_players) // 4, additional_courts_available)
                if additional_doubles > 0:
                    if "Mixed" in court_plans:
                        # Add to existing Mixed category
                        court_plans["Mixed"]['doubles'] += additional_doubles
                        court_plans["Mixed"]['eligible_players'].extend(all_unused_players[:additional_doubles * 4])
                    else:
                        # Create new Mixed category for cross-category matches
                        court_plans["Mixed"] = {
                            'doubles': additional_doubles,
                            'singles': 0,
                            'eligible_players': all_unused_players[:additional_doubles * 4]
                        }
                    additional_courts_available -= additional_doubles
                    all_unused_players = all_unused_players[additional_doubles * 4:]  # Remove used players
            
            # Remaining players for singles matches
            if len(all_unused_players) >= 2 and config.allowSingles and additional_courts_available > 0:
                additional_singles = min(len(all_unused_players) // 2, additional_courts_available)
                if additional_singles > 0:
                    if "Mixed" in court_plans:
                        court_plans["Mixed"]['singles'] += additional_singles
                        court_plans["Mixed"]['eligible_players'].extend(all_unused_players[:additional_singles * 2])
                    else:
                        court_plans["Mixed"] = {
                            'doubles': 0,
                            'singles': additional_singles,
                            'eligible_players': all_unused_players[:additional_singles * 2]
                        }
        
        # Recalculate total courts needed after optimization
        total_courts_needed = sum(plan['doubles'] + plan['singles'] for plan in court_plans.values())
        # DON'T override available_courts here - keep the optimization setting from above
        print(f"DEBUG: After optimization - total_courts_needed: {total_courts_needed}, available_courts: {available_courts}")
    
    # Fair court allocation across categories (rotate by round)
    if config.allowCrossCategory:
        rotated_categories = ["Mixed"]
    else:
        sorted_categories = sorted([cat.name for cat in categories])
        rotated_categories = sorted_categories[round_index % len(sorted_categories):] + sorted_categories[:round_index % len(sorted_categories)] if sorted_categories else []
    
    allocated_courts = {}
    courts_used = 0
    
    # Allocate courts in rotated order, doubles first
    for cat_name in rotated_categories:
        if cat_name not in court_plans:
            continue
        
        allocated_courts[cat_name] = {'doubles': 0, 'singles': 0}
        plan = court_plans[cat_name]
        
        # Allocate doubles courts first
        doubles_to_allocate = min(plan['doubles'], available_courts - courts_used)
        allocated_courts[cat_name]['doubles'] = doubles_to_allocate
        courts_used += doubles_to_allocate
        
        # Debug logging for court allocation
        if config.maximizeCourtUsage:
            print(f"DEBUG: Allocating {doubles_to_allocate}/{plan['doubles']} doubles for {cat_name}, courts_used: {courts_used}/{available_courts}")
        
        if courts_used >= available_courts:
            break
    
    # Allocate remaining courts for singles
    for cat_name in rotated_categories:
        if courts_used >= available_courts:
            break
        if cat_name not in court_plans:
            continue
        
        plan = court_plans[cat_name]
        singles_to_allocate = min(plan['singles'], available_courts - courts_used)
        allocated_courts[cat_name]['singles'] = singles_to_allocate
        courts_used += singles_to_allocate
    
    # Create actual matches
    court_index = 0
    
    for cat_name in rotated_categories:
        if cat_name not in allocated_courts:
            continue
        
        allocation = allocated_courts[cat_name]
        eligible_players = court_plans[cat_name]['eligible_players']
        
        # Create doubles matches
        if allocation['doubles'] > 0:
            doubles_matches = await create_doubles_matches(
                eligible_players, allocation['doubles'], cat_name, 
                round_index, court_index, session_obj.histories
            )
            created_matches.extend(doubles_matches)
            court_index += len(doubles_matches)
            
            # Track used players
            for match in doubles_matches:
                used_player_ids.update(match.teamA + match.teamB)
        
        # Create singles matches
        if allocation['singles'] > 0:
            # Get remaining players not used in doubles
            remaining_players = [p for p in eligible_players if p.id not in used_player_ids]
            
            singles_matches = await create_singles_matches(
                remaining_players, allocation['singles'], cat_name,
                round_index, court_index, session_obj.histories
            )
            created_matches.extend(singles_matches)
            court_index += len(singles_matches)
            
            # Track used players
            for match in singles_matches:
                used_player_ids.update(match.teamA + match.teamB)
    
    # Update sit counts and missDueToCourtLimit - SQLite version
    for player in players:
        if player.id not in used_player_ids and not player.sitNextRound:
            # Player is sitting due to court limitations
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player.id))
            db_player = result.scalar_one_or_none()
            if db_player:
                db_player.miss_due_to_court_limit += 1
        
        if player.id not in used_player_ids:
            # Player is sitting (either forced or due to limitations)
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player.id))
            db_player = result.scalar_one_or_none()
            if db_player:
                db_player.sit_count += 1
                # Mark in recentForm that player sat out this round
                recent_form = json.loads(db_player.recent_form) if db_player.recent_form else []
                recent_form.append('S')  # 'S' for Sitout
                if len(recent_form) > 10:
                    recent_form = recent_form[-10:]
                db_player.recent_form = json.dumps(recent_form)
        
        # CRITICAL FIX: Do NOT reset sitNextRound flag
        # Manual sitouts should persist until manually cleared by user (Option B behavior)
    
    # Save matches to database - SQLite version
    for match in created_matches:
        db_match = DBMatch(
            id=match.id,
            round_index=match.roundIndex,
            court_index=match.courtIndex,
            category=match.category,
            team_a=json.dumps(match.teamA),
            team_b=json.dumps(match.teamB),
            status=match.status.value,
            match_type=match.matchType.value,
            score_a=match.scoreA,
            score_b=match.scoreB,
            club_name=club_name
        )
        db_session.add(db_match)
        # Update histories
        session_obj.histories = update_histories(match, session_obj.histories)
    
    # Update session histories - SQLite version
    result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
    db_session_obj = result.scalar_one_or_none()
    if db_session_obj:
        db_session_obj.histories = json.dumps(session_obj.histories)
    
    await db_session.commit()
    
    return created_matches

async def create_doubles_matches(
    players: List[Player], 
    num_matches: int, 
    category: str, 
    round_index: int, 
    start_court_index: int,
    histories: Dict[str, Any]
) -> List[Match]:
    """Create doubles matches with enhanced partner pairing and rating balance"""
    matches = []
    
    # Use enhanced shuffling for better rating distribution
    shuffled_players = enhanced_shuffle_with_rating_balance(players, num_iterations=8)
    
    # Create teams (pairs) with improved partner selection
    teams = []
    used_indices = set()
    
    # Sort players by combination of sit count and rating for better fairness
    priority_players = sorted(shuffled_players, key=lambda p: (p.sitCount, -p.rating))
    
    for i, player_a in enumerate(priority_players):
        if i in used_indices:
            continue
        
        best_partner = None
        best_score = float('inf')
        best_index = -1
        
        # Find best partner considering both history and rating compatibility
        for j, player_b in enumerate(priority_players[i+1:], i+1):
            if j in used_indices:
                continue
            
            # Calculate composite score: partner history + rating difference penalty
            partner_history_score = calculate_partner_score(player_a.id, player_b.id, histories)
            rating_diff_penalty = abs(player_a.rating - player_b.rating) * 0.5  # Prefer similar ratings
            
            composite_score = partner_history_score + rating_diff_penalty
            
            # Tie-breaking with name for consistency
            if composite_score < best_score or (composite_score == best_score and player_b.name < (best_partner.name if best_partner else "zzz")):
                best_partner = player_b
                best_score = composite_score
                best_index = j
        
        if best_partner:
            teams.append([player_a.id, best_partner.id])
            used_indices.add(i)
            used_indices.add(best_index)
            
            if len(teams) >= num_matches * 2:
                break
    
    # Pair teams into matches with enhanced opponent selection
    used_team_indices = set()
    
    # VALIDATION: Check for duplicate players in teams list
    all_team_players = []
    for team in teams:
        all_team_players.extend(team)
    if len(all_team_players) != len(set(all_team_players)):
        # Found duplicates in teams - this shouldn't happen
        from collections import Counter
        player_counts = Counter(all_team_players)
        duplicates = [p for p, c in player_counts.items() if c > 1]
        print(f"ERROR: Duplicate players in teams: {duplicates}")
        # Remove duplicate teams to fix the issue
        seen_players = set()
        valid_teams = []
        for team in teams:
            if not any(p in seen_players for p in team):
                valid_teams.append(team)
                seen_players.update(team)
        teams = valid_teams
        print(f"Fixed: Reduced teams from {len(teams) + len(duplicates)} to {len(teams)}")
    
    # Try multiple team pairing combinations for better balance
    best_matches = []
    best_rating_variance = float('inf')
    
    for attempt in range(3):  # Try 3 different pairing approaches
        current_matches = []
        current_used = set()
        
        team_order = list(range(len(teams)))
        if attempt > 0:
            random.shuffle(team_order)
        
        for idx in team_order:
            if len(current_matches) >= num_matches:
                break
                
            if idx in current_used:
                continue
            
            team_a = teams[idx]
            best_opponent_team = None
            best_opponent_score = float('inf')
            best_opponent_index = -1
            
            # Find best opponent team considering history and rating balance
            for j_idx in team_order[idx+1:]:
                if j_idx in current_used:
                    continue
                
                team_b = teams[j_idx]
                
                # CRITICAL FIX: Check for duplicate players BEFORE scoring this opponent
                # 1. Ensure no player appears in both team_a and team_b (same match)
                if any(player in team_b for player in team_a):
                    # Skip this opponent - contains players already in team_a
                    continue
                
                # 2. Ensure no player from this proposed match appears in current matches
                players_in_proposed_match = team_a + team_b
                already_used = [p for p in players_in_proposed_match if any(p in m.teamA or p in m.teamB for m in current_matches)]
                if already_used:
                    # Skip this opponent - contains already-used players
                    continue
                
                # Calculate composite opponent score
                opponent_history_score = calculate_opponent_score(team_a, team_b, histories)
                
                # Rating balance factor - prefer closer team average ratings
                team_a_avg = calculate_team_rating_avg(team_a, players)
                team_b_avg = calculate_team_rating_avg(team_b, players)
                rating_balance_penalty = abs(team_a_avg - team_b_avg) * 0.3
                
                composite_opponent_score = opponent_history_score + rating_balance_penalty
                
                if composite_opponent_score < best_opponent_score:
                    best_opponent_team = team_b
                    best_opponent_score = composite_opponent_score
                    best_opponent_index = j_idx
            
            if best_opponent_team:
                match = Match(
                    roundIndex=round_index,
                    courtIndex=start_court_index + len(current_matches),
                    category=category,
                    teamA=team_a,
                    teamB=best_opponent_team,
                    matchType=MatchType.doubles,
                    status=MatchStatus.pending
                )
                current_matches.append(match)
                current_used.add(idx)
                current_used.add(best_opponent_index)
        
        # Evaluate this pairing attempt
        if current_matches:
            rating_variance = calculate_rating_variance(current_matches, players)
            if rating_variance < best_rating_variance:
                best_rating_variance = rating_variance
                best_matches = current_matches
    
    return best_matches or matches

async def create_singles_matches(
    players: List[Player], 
    num_matches: int, 
    category: str, 
    round_index: int, 
    start_court_index: int,
    histories: Dict[str, Any]
) -> List[Match]:
    """Create singles matches with enhanced opponent pairing and rating balance"""
    matches = []
    
    # Prioritize players with fewer sits and better rating distribution
    sorted_players = sorted(players, key=lambda p: (p.sitCount, p.missDueToCourtLimit, -p.rating))
    
    # Take players for singles matches with enhanced selection
    players_for_singles = sorted_players[:num_matches * 2]
    
    # Use enhanced shuffling for better distribution
    shuffled_singles = enhanced_shuffle_with_rating_balance(players_for_singles, num_iterations=5)
    
    # Try multiple pairing combinations for optimal balance
    best_matches = []
    best_rating_variance = float('inf')
    
    for attempt in range(3):  # Try different pairing approaches
        current_matches = []
        used_indices = set()
        
        player_order = list(range(len(shuffled_singles)))
        if attempt > 0:
            random.shuffle(player_order)
        
        for idx in player_order:
            if len(current_matches) >= num_matches:
                break
                
            if idx in used_indices:
                continue
            
            player_a = shuffled_singles[idx]
            best_opponent = None
            best_score = float('inf')
            best_index = -1
            
            # Find best opponent considering history and rating compatibility
            for j_idx in player_order[idx+1:]:
                if j_idx in used_indices:
                    continue
                
                player_b = shuffled_singles[j_idx]
                
                # Calculate composite score: opponent history + rating difference
                opponent_history_score = calculate_opponent_score([player_a.id], [player_b.id], histories)
                rating_diff_penalty = abs(player_a.rating - player_b.rating) * 0.4  # Prefer closer ratings
                sit_count_penalty = abs(player_a.sitCount - player_b.sitCount) * 2  # Balance sit counts
                
                composite_score = opponent_history_score + rating_diff_penalty + sit_count_penalty
                
                # Tie-breaking with name for consistency
                if composite_score < best_score or (composite_score == best_score and player_b.name < (best_opponent.name if best_opponent else "zzz")):
                    best_opponent = player_b
                    best_score = composite_score
                    best_index = j_idx
            
            if best_opponent:
                match = Match(
                    roundIndex=round_index,
                    courtIndex=start_court_index + len(current_matches),
                    category=category,
                    teamA=[player_a.id],
                    teamB=[best_opponent.id],
                    matchType=MatchType.singles,
                    status=MatchStatus.pending
                )
                current_matches.append(match)
                used_indices.add(idx)
                used_indices.add(best_index)
        
        # Evaluate this pairing attempt
        if current_matches:
            rating_variance = calculate_rating_variance(current_matches, players)
            if rating_variance < best_rating_variance:
                best_rating_variance = rating_variance
                best_matches = current_matches
    
    return best_matches

# API Routes

# Clubs
@api_router.get("/clubs", response_model=List[Club])
async def get_clubs(db_session: AsyncSession = Depends(get_db_session)):
    """Get all clubs"""
    try:
        result = await db_session.execute(select(DBClub))
        clubs = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models
        club_list = []
        for db_club in clubs:
            club_dict = {
                "name": db_club.name,
                "display_name": db_club.display_name,
                "description": db_club.description,
                "created_at": db_club.created_at.isoformat() if db_club.created_at else datetime.now().isoformat()
            }
            club_list.append(Club(**club_dict))
        
        return club_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clubs: {str(e)}")

@api_router.post("/clubs", response_model=Club)
async def create_club(club: ClubCreate, db_session: AsyncSession = Depends(get_db_session)):
    """Register a new club"""
    try:
        # Check if club already exists
        result = await db_session.execute(select(DBClub).where(DBClub.name == club.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Club name already exists")
        
        # Create new club
        db_club = DBClub(
            name=club.name,
            display_name=club.display_name,
            description=club.description,
            access_code=club.access_code
        )
        
        db_session.add(db_club)
        await db_session.commit()
        await db_session.refresh(db_club)
        
        # Create default session for the new club
        default_session = DBSession(
            club_name=club.name,
            config=json.dumps({
                "numCourts": 4,
                "playSeconds": 720,
                "bufferSeconds": 30,
                "allowSingles": True,
                "allowDoubles": True,
                "allowCrossCategory": False,
                "maximizeCourtUsage": False
            }),
            histories=json.dumps({
                "partnerHistory": {},
                "opponentHistory": {}
            })
        )
        db_session.add(default_session)
        await db_session.commit()
        
        # Convert to Pydantic model for response
        club_dict = {
            "name": db_club.name,
            "display_name": db_club.display_name,
            "description": db_club.description,
            "created_at": db_club.created_at.isoformat() if db_club.created_at else datetime.now().isoformat()
        }
        
        return Club(**club_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create club: {str(e)}")

# Authentication endpoints
@api_router.post("/auth/login", response_model=ClubSession)
async def club_login(login_data: ClubLogin, db_session: AsyncSession = Depends(get_db_session)):
    """Authenticate club access with club name and access code"""
    try:
        print(f"🔍 Login attempt: club_name='{login_data.club_name}', access_code='{login_data.access_code}'")
        
        # Find club by name or display_name
        result = await db_session.execute(
            select(DBClub).where(
                or_(
                    DBClub.name == login_data.club_name,
                    DBClub.display_name == login_data.club_name
                )
            )
        )
        club = result.scalar_one_or_none()
        
        print(f"🔍 Club found: {club.name if club else 'None'}")
        
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        # Verify access code
        if club.access_code != login_data.access_code:
            raise HTTPException(status_code=401, detail="Invalid access code")
        
        # Return session information
        return ClubSession(
            club_name=club.name,
            display_name=club.display_name,
            authenticated=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@api_router.post("/auth/register", response_model=ClubSession)
async def club_register(club_data: ClubCreate, db_session: AsyncSession = Depends(get_db_session)):
    """Register a new club and return session"""
    try:
        # Check if club name already exists
        result = await db_session.execute(select(DBClub).where(DBClub.name == club_data.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Club name already taken")
        
        # Create new club
        db_club = DBClub(
            name=club_data.name,
            display_name=club_data.display_name,
            description=club_data.description,
            access_code=club_data.access_code
        )
        
        db_session.add(db_club)
        
        # Create default session for the new club
        default_session = DBSession(
            club_name=club_data.name,
            config=json.dumps({
                "numCourts": 4,
                "playSeconds": 720,
                "bufferSeconds": 30,
                "allowSingles": True,
                "allowDoubles": True,
                "allowCrossCategory": False,
                "maximizeCourtUsage": False
            }),
            histories=json.dumps({
                "partnerHistory": {},
                "opponentHistory": {}
            })
        )
        db_session.add(default_session)
        
        await db_session.commit()
        
        # Return session information
        return ClubSession(
            club_name=db_club.name,
            display_name=db_club.display_name,
            authenticated=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# Categories
@api_router.get("/categories", response_model=List[Category])
async def get_categories(db_session: AsyncSession = Depends(get_db_session)):
    """Get all categories from SQLite database"""
    try:
        result = await db_session.execute(select(DBCategory))
        categories = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models
        category_list = []
        for db_category in categories:
            category_dict = {
                "id": db_category.id,
                "name": db_category.name,
                "description": db_category.description
            }
            category_list.append(Category(**category_dict))
        
        return category_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@api_router.post("/categories", response_model=Category)
async def create_category(category: CategoryCreate, db_session: AsyncSession = Depends(get_db_session)):
    """Create a new category in SQLite database"""
    try:
        # Check if category already exists
        result = await db_session.execute(select(DBCategory).where(DBCategory.name == category.name))
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Category already exists")
        
        # Create new category
        db_category = DBCategory(
            name=category.name,
            description=category.description
        )
        
        db_session.add(db_category)
        await db_session.commit()
        await db_session.refresh(db_category)
        
        # Convert to Pydantic model for response
        category_dict = {
            "id": db_category.id,
            "name": db_category.name,
            "description": db_category.description
        }
        
        return Category(**category_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, db_session: AsyncSession = Depends(get_db_session)):
    """Delete a category from SQLite database"""
    try:
        # Find the category
        result = await db_session.execute(select(DBCategory).where(DBCategory.id == category_id))
        db_category = result.scalar_one_or_none()
        
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Delete the category
        await db_session.delete(db_category)
        await db_session.commit()
        
        return {"message": "Category deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")

# Data Management
@api_router.delete("/clear-all-data", response_model=dict)
async def clear_all_data(db: AsyncSession = Depends(get_db_session)):
    """Clear all data from the database for fresh start"""
    try:
        # Clear all SQLite tables
        await db.execute(delete(DBPlayer))
        await db.execute(delete(DBCategory))  
        await db.execute(delete(DBMatch))
        await db.execute(delete(DBSession))
        
        # Reinitialize with default categories
        default_categories = [
            DBCategory(name="Beginner"),
            DBCategory(name="Intermediate"), 
            DBCategory(name="Advanced"),
            DBCategory(name="Social")
        ]
        
        for category in default_categories:
            db.add(category)
        
        # Create default club if it doesn't exist
        result = await db.execute(select(DBClub).where(DBClub.name == "Main Club"))
        main_club = result.scalar_one_or_none()
        
        if not main_club:
            main_club = DBClub(
                name="Main Club",
                display_name="Main Club",
                description="Default club for existing data migration"
            )
            db.add(main_club)
        
        # Create fresh session
        session_obj = DBSession(
            club_name="Main Club",  # Add required club_name
            config=json.dumps({
                "numCourts": 4,
                "playSeconds": 720,
                "bufferSeconds": 30,
                "allowSingles": True,
                "allowDoubles": True,
                "allowCrossCategory": False,
                "maximizeCourtUsage": False
            }),
            histories=json.dumps({
                "partnerHistory": {},
                "opponentHistory": {}
            })
        )
        db.add(session_obj)
        
        await db.commit()
        return {"message": "All data cleared successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@api_router.post("/add-test-data", response_model=dict)
async def add_test_data(db: AsyncSession = Depends(get_db_session)):
    """Add sample test players for testing purposes"""
    try:
        # Sample players with ratings
        test_players = [
            {"name": "John Smith", "category": "Beginner", "rating": 3.2},
            {"name": "Jane Doe", "category": "Beginner", "rating": 3.5},
            {"name": "Mike Johnson", "category": "Intermediate", "rating": 4.1},
            {"name": "Sarah Wilson", "category": "Intermediate", "rating": 4.3},
            {"name": "David Brown", "category": "Advanced", "rating": 5.2},
            {"name": "Lisa Garcia", "category": "Advanced", "rating": 5.5},
            {"name": "Tom Anderson", "category": "Beginner", "rating": 3.0},
            {"name": "Emily Chen", "category": "Intermediate", "rating": 4.0},
            {"name": "Robert Taylor", "category": "Advanced", "rating": 5.8},
            {"name": "Maria Rodriguez", "category": "Beginner", "rating": 3.3},
            {"name": "James Wilson", "category": "Intermediate", "rating": 4.2},
            {"name": "Ashley Johnson", "category": "Advanced", "rating": 5.1}
        ]
        
        # Clear existing players first
        await db.execute(delete(DBPlayer))
        
        # Add test players to Main Club
        created_count = 0
        for player_data in test_players:
            player = DBPlayer(
                name=player_data["name"],
                category=player_data["category"],
                club_name="Main Club",  # Assign to Main Club
                rating=player_data["rating"],
                is_active=True  # Explicitly set all test players as active
            )
            db.add(player)
            created_count += 1
        
        await db.commit()
        return {"message": f"Successfully added {created_count} test players"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add test data: {str(e)}")

# Players
@api_router.get("/players", response_model=List[Player])
async def get_players(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Get all players from SQLite database for a specific club"""
    try:
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
        players = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models for response
        player_list = []
        for db_player in players:
            # Parse JSON fields
            recent_form = json.loads(db_player.recent_form) if db_player.recent_form else []
            rating_history = json.loads(db_player.rating_history) if db_player.rating_history else []
            
            player_dict = {
                "id": db_player.id,
                "name": db_player.name,
                "category": db_player.category,
                "sitNextRound": db_player.sit_next_round,
                "sitCount": db_player.sit_count,
                "missDueToCourtLimit": db_player.miss_due_to_court_limit,
                "isActive": db_player.is_active,
                "rating": db_player.rating,
                "matchesPlayed": db_player.matches_played,
                "wins": db_player.wins,
                "losses": db_player.losses,
                "recentForm": recent_form,
                "ratingHistory": rating_history,
                "lastUpdated": db_player.last_updated.isoformat() if db_player.last_updated else datetime.now().isoformat(),
                "stats": {
                    "wins": db_player.stats_wins,
                    "losses": db_player.stats_losses,
                    "pointDiff": db_player.stats_point_diff
                }
            }
            player_list.append(Player(**player_dict))
        
        return player_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get players: {str(e)}")

# SQLite Players API (for testing)
@api_router.get("/sqlite/players")
async def get_sqlite_players(db_session: AsyncSession = Depends(get_db_session)):
    """Get players from SQLite database"""
    try:
        result = await db_session.execute(select(DBPlayer))
        players = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models for response
        player_list = []
        for db_player in players:
            # Parse JSON fields
            recent_form = json.loads(db_player.recent_form) if db_player.recent_form else []
            rating_history = json.loads(db_player.rating_history) if db_player.rating_history else []
            
            player_dict = {
                "id": db_player.id,
                "name": db_player.name,
                "category": db_player.category,
                "sitNextRound": db_player.sit_next_round,
                "sitCount": db_player.sit_count,
                "missDueToCourtLimit": db_player.miss_due_to_court_limit,
                "isActive": db_player.is_active,
                "rating": db_player.rating,
                "matchesPlayed": db_player.matches_played,
                "wins": db_player.wins,
                "losses": db_player.losses,
                "recentForm": recent_form,
                "ratingHistory": rating_history,
                "lastUpdated": db_player.last_updated.isoformat() if db_player.last_updated else datetime.now().isoformat(),
                "stats": {
                    "wins": db_player.stats_wins,
                    "losses": db_player.stats_losses,
                    "pointDiff": db_player.stats_point_diff
                }
            }
            player_list.append(player_dict)
        
        return player_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get players: {str(e)}")

@api_router.post("/players", response_model=Player)
async def create_player(player: PlayerCreate, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Create a new player in SQLite database"""
    try:
        # Create SQLAlchemy player object
        db_player = DBPlayer(
            name=player.name,
            category=player.category,
            club_name=club_name,  # Assign to specific club
            rating=3.0,  # Default DUPR rating
            recent_form=json.dumps([]),  # Empty recent form
            rating_history=json.dumps([])  # Empty rating history
        )
        
        db_session.add(db_player)
        await db_session.commit()
        await db_session.refresh(db_player)
        
        # Convert back to Pydantic model for response
        player_dict = {
            "id": db_player.id,
            "name": db_player.name,
            "category": db_player.category,
            "sitNextRound": db_player.sit_next_round,
            "sitCount": db_player.sit_count,
            "missDueToCourtLimit": db_player.miss_due_to_court_limit,
            "isActive": db_player.is_active,
            "rating": db_player.rating,
            "matchesPlayed": db_player.matches_played,
            "wins": db_player.wins,
            "losses": db_player.losses,
            "recentForm": [],
            "ratingHistory": [],
            "lastUpdated": db_player.last_updated.isoformat() if db_player.last_updated else datetime.now().isoformat(),
            "stats": {
                "wins": db_player.stats_wins,
                "losses": db_player.stats_losses,
                "pointDiff": db_player.stats_point_diff
            }
        }
        
        return Player(**player_dict)
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create player: {str(e)}")

@api_router.put("/players/{player_id}", response_model=Player)
async def update_player(player_id: str, updates: PlayerUpdate, db_session: AsyncSession = Depends(get_db_session)):
    """Update a player in SQLite database"""
    try:
        # Find the player
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id))
        db_player = result.scalar_one_or_none()
        
        if not db_player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Update fields that are provided
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if "name" in update_data:
            db_player.name = update_data["name"]
        if "category" in update_data:
            db_player.category = update_data["category"]
        if "sitNextRound" in update_data:
            db_player.sit_next_round = update_data["sitNextRound"]
        
        await db_session.commit()
        await db_session.refresh(db_player)
        
        # Convert back to Pydantic model for response
        recent_form = json.loads(db_player.recent_form) if db_player.recent_form else []
        rating_history = json.loads(db_player.rating_history) if db_player.rating_history else []
        
        player_dict = {
            "id": db_player.id,
            "name": db_player.name,
            "category": db_player.category,
            "sitNextRound": db_player.sit_next_round,
            "sitCount": db_player.sit_count,
            "missDueToCourtLimit": db_player.miss_due_to_court_limit,
            "isActive": db_player.is_active,
            "rating": db_player.rating,
            "matchesPlayed": db_player.matches_played,
            "wins": db_player.wins,
            "losses": db_player.losses,
            "recentForm": recent_form,
            "ratingHistory": rating_history,
            "lastUpdated": db_player.last_updated.isoformat() if db_player.last_updated else datetime.now().isoformat(),
            "stats": {
                "wins": db_player.stats_wins,
                "losses": db_player.stats_losses,
                "pointDiff": db_player.stats_point_diff
            }
        }
        
        return Player(**player_dict)
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update player: {str(e)}")

@api_router.delete("/players/{player_id}")
async def delete_player(player_id: str, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Permanently delete a player (use with caution - will lose all historical data)"""
    try:
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id, DBPlayer.club_name == club_name))
        player = result.scalar_one_or_none()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        await db_session.delete(player)
        await db_session.commit()
        
        return {"message": f"Player {player.name} permanently deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete player: {str(e)}")

@api_router.patch("/players/{player_id}/toggle-active")
async def toggle_player_active_status(player_id: str, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Toggle player's active status for daily sessions (soft delete/restore)"""
    try:
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id, DBPlayer.club_name == club_name))
        player = result.scalar_one_or_none()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Toggle active status
        player.is_active = not player.is_active
        await db_session.commit()
        
        status = "activated" if player.is_active else "deactivated"
        return {
            "message": f"Player {player.name} {status} for today's session",
            "isActive": player.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle player status: {str(e)}")

@api_router.get("/players/active")
async def get_active_players(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Get only active players for today's session"""
    try:
        result = await db_session.execute(
            select(DBPlayer).where(DBPlayer.club_name == club_name, DBPlayer.is_active)
        )
        db_players = result.scalars().all()
        
        players = []
        for db_player in db_players:
            player_data = {
                'id': db_player.id,
                'name': db_player.name,
                'category': db_player.category,
                'sitNextRound': db_player.sit_next_round,
                'sitCount': db_player.sit_count,
                'missDueToCourtLimit': db_player.miss_due_to_court_limit,
                'isActive': db_player.is_active,
                'stats': {
                    'wins': db_player.stats_wins,
                    'losses': db_player.stats_losses,
                    'pointDiff': db_player.stats_point_diff
                },
                'rating': db_player.rating,
                'matchesPlayed': db_player.matches_played,
                'recentForm': json.loads(db_player.recent_form) if db_player.recent_form else [],
                'ratingHistory': json.loads(db_player.rating_history) if db_player.rating_history else [],
                'lastUpdated': db_player.last_updated.isoformat() if db_player.last_updated else None
            }
            players.append(Player(**player_data))
        
        return players
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active players: {str(e)}")
@api_router.post("/players/reset-all-inactive")
async def reset_all_players_inactive(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Reset all players to inactive state"""
    try:
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
        players = result.scalars().all()
        
        for player in players:
            player.is_active = False
        
        await db_session.commit()
        return {"message": f"Reset {len(players)} players to inactive", "count": len(players)}
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/players/reset-all-active")
async def reset_all_players_active(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Reset all players to active state"""
    try:
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
        players = result.scalars().all()
        
        for player in players:
            player.is_active = True
        
        await db_session.commit()
        return {"message": f"Reset {len(players)} players to active", "count": len(players)}
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/players/reset-all-clubs-inactive")
async def reset_all_clubs_players_inactive(db_session: AsyncSession = Depends(get_db_session)):
    """Reset ALL players across ALL clubs to inactive state"""
    try:
        result = await db_session.execute(select(DBPlayer))
        players = result.scalars().all()
        
        for player in players:
            player.is_active = False
        
        await db_session.commit()
        return {"message": f"Reset {len(players)} players across all clubs to inactive", "count": len(players)}
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Matches
@api_router.get("/matches", response_model=List[Match])
async def get_matches(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Get matches for a specific club from SQLite database"""
    try:
        result = await db_session.execute(select(DBMatch).where(DBMatch.club_name == club_name))
        matches = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models
        match_list = []
        for db_match in matches:
            # Parse JSON fields
            team_a = json.loads(db_match.team_a) if db_match.team_a else []
            team_b = json.loads(db_match.team_b) if db_match.team_b else []
            
            match_dict = {
                "id": db_match.id,
                "roundIndex": db_match.round_index,
                "courtIndex": db_match.court_index,
                "category": db_match.category,
                "teamA": team_a,
                "teamB": team_b,
                "status": db_match.status,
                "matchType": db_match.match_type,
                "scoreA": db_match.score_a,
                "scoreB": db_match.score_b
            }
            match_list.append(Match(**match_dict))
        
        return match_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get matches: {str(e)}")

@api_router.get("/matches/round/{round_index}", response_model=List[Match])
async def get_matches_by_round(round_index: int, db_session: AsyncSession = Depends(get_db_session)):
    """Get matches by round from SQLite database"""
    try:
        result = await db_session.execute(select(DBMatch).where(DBMatch.round_index == round_index))
        matches = result.scalars().all()
        
        # Convert SQLAlchemy models to Pydantic models
        match_list = []
        for db_match in matches:
            # Parse JSON fields
            team_a = json.loads(db_match.team_a) if db_match.team_a else []
            team_b = json.loads(db_match.team_b) if db_match.team_b else []
            
            match_dict = {
                "id": db_match.id,
                "roundIndex": db_match.round_index,
                "courtIndex": db_match.court_index,
                "category": db_match.category,
                "teamA": team_a,
                "teamB": team_b,
                "status": db_match.status,
                "matchType": db_match.match_type,
                "scoreA": db_match.score_a,
                "scoreB": db_match.score_b
            }
            match_list.append(Match(**match_dict))
        
        return match_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get matches by round: {str(e)}")

@api_router.put("/matches/{match_id}/score", response_model=Match)
async def update_match_score(match_id: str, score_update: MatchScoreUpdate, db_session: AsyncSession = Depends(get_db_session)):
    """Update match score and player stats - SQLite version"""
    try:
        # Get match from SQLite
        result = await db_session.execute(select(DBMatch).where(DBMatch.id == match_id))
        db_match = result.scalar_one_or_none()
        
        if not db_match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Update match with scores and mark as saved
        db_match.score_a = score_update.scoreA
        db_match.score_b = score_update.scoreB
        db_match.status = MatchStatus.saved.value
        
        # Parse team data
        team_a = json.loads(db_match.team_a) if db_match.team_a else []
        team_b = json.loads(db_match.team_b) if db_match.team_b else []
        
        # Determine winner and loser
        if score_update.scoreA > score_update.scoreB:
            winner_team = team_a
            loser_team = team_b
            winner_score = score_update.scoreA
            loser_score = score_update.scoreB
        else:
            winner_team = team_b
            loser_team = team_a
            winner_score = score_update.scoreB
            loser_score = score_update.scoreA
        
        point_diff = winner_score - loser_score
        
        # Update winner stats
        for player_id in winner_team:
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id))
            player = result.scalar_one_or_none()
            if player:
                player.stats_wins += 1
                player.stats_point_diff += point_diff
        
        # Update loser stats
        for player_id in loser_team:
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.id == player_id))
            player = result.scalar_one_or_none()
            if player:
                player.stats_losses += 1
                player.stats_point_diff -= point_diff
        
        # Update DUPR-style ratings - SQLite version
        # Skip ratings for Top Court mode (only track wins/losses)
        result_session = await db_session.execute(select(DBSession).where(DBSession.club_name == db_match.club_name))
        session = result_session.scalar_one_or_none()
        
        if session:
            config_data = json.loads(session.config) if session.config else {}
            session_config = SessionConfig(**config_data)
            
            # Only update ratings for Legacy mode, not Top Court
            if session_config.rotationModel != 'top_court':
                match_dict = {
                    'id': db_match.id,
                    'teamA': team_a,
                    'teamB': team_b,
                    'category': db_match.category
                }
                await update_player_ratings(match_dict, score_update.scoreA, score_update.scoreB, db_session)
        
        await db_session.commit()
        await db_session.refresh(db_match)
        
        # Convert back to Pydantic model for response
        match_dict = {
            "id": db_match.id,
            "roundIndex": db_match.round_index,
            "courtIndex": db_match.court_index,
            "category": db_match.category,
            "teamA": team_a,
            "teamB": team_b,
            "status": db_match.status,
            "matchType": db_match.match_type,
            "scoreA": db_match.score_a,
            "scoreB": db_match.score_b
        }
        
        return Match(**match_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update match score: {str(e)}")

@api_router.put("/matches/{match_id}/incomplete")
async def mark_match_incomplete(match_id: str, db_session: AsyncSession = Depends(get_db_session)):
    """Mark a match as incomplete when round ends without score entry"""
    try:
        # Get match from SQLite
        result = await db_session.execute(select(DBMatch).where(DBMatch.id == match_id))
        db_match = result.scalar_one_or_none()
        
        if not db_match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Mark match as incomplete
        db_match.status = "incomplete"
        
        await db_session.commit()
        
        return {"message": f"Match {match_id} marked as incomplete"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to mark match as incomplete: {str(e)}")

@api_router.put("/matches/{match_id}")
async def update_match(match_id: str, request: Request, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Update match team assignments (for manual player swaps)"""
    try:
        body = await request.json()
        team_a = body.get('teamA', [])
        team_b = body.get('teamB', [])
        
        result = await db_session.execute(
            select(DBMatch).where(and_(DBMatch.id == match_id, DBMatch.club_name == club_name))
        )
        match = result.scalar_one_or_none()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Update team assignments
        match.team_a = json.dumps(team_a)
        match.team_b = json.dumps(team_b)
        
        await db_session.commit()
        
        return {"message": "Match updated", "id": match_id}
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update match: {str(e)}")

# Session Management
@api_router.get("/session", response_model=SessionState)
async def get_session(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Get current session from SQLite database for a specific club"""
    try:
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            # Create default session for this club
            session_obj = SessionState()
            db_session_record = DBSession(
                club_name=club_name,
                current_round=session_obj.currentRound,
                phase=session_obj.phase.value,
                time_remaining=session_obj.timeRemaining,
                paused=session_obj.paused,
                config=json.dumps(session_obj.config.dict()),
                histories=json.dumps(session_obj.histories)
            )
            db_session.add(db_session_record)
            await db_session.commit()
            await db_session.refresh(db_session_record)
            return session_obj
        
        # Convert SQLAlchemy model back to Pydantic model
        config = json.loads(session.config) if session.config else {}
        histories = json.loads(session.histories) if session.histories else {}
        
        # Format session_date as ISO string (YYYY-MM-DD)
        session_date_str = None
        if session.session_date:
            session_date_str = session.session_date.strftime('%Y-%m-%d') if hasattr(session.session_date, 'strftime') else str(session.session_date)
        
        session_state = SessionState(
            id=session.id,
            currentRound=session.current_round,
            phase=session.phase,
            timeRemaining=session.time_remaining,
            paused=session.paused,
            sessionDate=session_date_str,
            config=SessionConfig(**config),
            histories=histories
        )
        
        return session_state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@api_router.put("/session/config", response_model=SessionState)
async def update_session_config(config: SessionConfig, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Update session configuration in SQLite database"""
    try:
        # Validate that at least one format is selected
        if not config.allowSingles and not config.allowDoubles:
            raise HTTPException(
                status_code=400, 
                detail="At least one format (Singles or Doubles) must be selected"
            )
        
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            # Create new session with provided config
            session_obj = SessionState(config=config)
            db_session_record = DBSession(
                club_name=club_name,
                current_round=session_obj.currentRound,
                phase=session_obj.phase.value,
                time_remaining=session_obj.timeRemaining,
                paused=session_obj.paused,
                config=json.dumps(config.dict()),
                histories=json.dumps(session_obj.histories)
            )
            db_session.add(db_session_record)
            await db_session.commit()
            await db_session.refresh(db_session_record)
            return session_obj
        
        # Update existing session config
        session.config = json.dumps(config.dict())
        await db_session.commit()
        await db_session.refresh(session)
        
        # Convert back to Pydantic model for response
        config_data = json.loads(session.config) if session.config else {}
        histories = json.loads(session.histories) if session.histories else {}
        
        session_state = SessionState(
            id=session.id,
            currentRound=session.current_round,
            phase=session.phase,
            timeRemaining=session.time_remaining,
            paused=session.paused,
            config=SessionConfig(**config_data),
            histories=histories
        )
        
        return session_state
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session config: {str(e)}")

@api_router.post("/session/generate-matches", response_model=SessionState)
async def generate_matches(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Generate matches and set session to 'ready' phase - players can see assignments"""
    try:
        # Get current session
        session_obj = await get_session(club_name, db_session)
        
        # Check if we have enough players based on enabled formats
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name, DBPlayer.is_active == True))
        players = result.scalars().all()
        players_count = len(players)
        
        # Validate format configuration
        if not session_obj.config.allowSingles and not session_obj.config.allowDoubles:
            raise HTTPException(
                status_code=400,
                detail="At least one format (Singles or Doubles) must be enabled"
            )
        
        # Determine minimum players needed
        if session_obj.config.allowDoubles:
            min_players = 4  # Need at least 4 for doubles
        elif session_obj.config.allowSingles:
            min_players = 2  # Need at least 2 for singles
        else:
            min_players = 2  # Fallback
        
        if players_count < min_players:
            raise HTTPException(
                status_code=400, 
                detail=f"Need at least {min_players} players to generate matches"
            )
        
        # Reset all matches
        await db_session.execute(delete(DBMatch).where(DBMatch.club_name == club_name))
        
        # Use the advanced schedule_round function for first round generation
        # This ensures all optimization logic (maximize courts, isActive filtering, etc.) is applied
        matches_created = await schedule_round(1, db_session, club_name)
        
        # Update session to 'ready' phase
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if session:
            session.current_round = 1
            session.phase = SessionPhase.ready.value
            session.time_remaining = session_obj.config.playSeconds
            session.paused = False
        
        await db_session.commit()
        
        return await get_session(club_name, db_session)
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate matches: {str(e)}")

@api_router.post("/session/start", response_model=SessionState)
async def start_session(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Start the timer for matches that are already generated"""
    try:
        session_obj = await get_session(club_name, db_session)
        
        # Must be in 'ready' phase to start timer
        if session_obj.phase != SessionPhase.ready:
            raise HTTPException(
                status_code=400,
                detail="Session must be in 'ready' phase to start timer. Generate matches first."
            )
        
        # Start the timer by setting phase to 'play'
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if session:
            session.phase = SessionPhase.play.value
            session.time_remaining = session_obj.config.playSeconds
        
        await db_session.commit()
        
        return await get_session(club_name, db_session)
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

async def schedule_top_court_round(round_index: int, db_session: AsyncSession, club_name: str, session_config: SessionConfig) -> List[Match]:
    """
    Top Court round scheduler: Winners move up, losers stay (and both split)
    - Court 0 (Top Court): Winners stay, losers drop to bottom court
    - Other courts: Winners move up one court, losers stay
    - IMPORTANT: Previous partners are split to play AGAINST each other
    """
    try:
        # Get previous round's matches to determine winners/losers
        result = await db_session.execute(
            select(DBMatch).where(
                and_(DBMatch.club_name == club_name, DBMatch.round_index == round_index - 1)
            ).order_by(DBMatch.court_index)
        )
        previous_matches = result.scalars().all()
        
        print(f"\n🎾 ===== TOP COURT ROUND {round_index} GENERATION =====")
        print(f"📋 Found {len(previous_matches)} matches from Round {round_index - 1}")
        
        if not previous_matches:
            # First round - use legacy scheduling
            print("⚠️ No previous matches found, using legacy scheduling")
            return await schedule_round(round_index, db_session, club_name)
        
        # Track groups of 2 players (previous partners) that will be split
        num_courts = session_config.numCourts
        court_groups = [[] for _ in range(num_courts)]  # Each entry is a list of 2-player groups
        
        for match in previous_matches:
            court_idx = match.court_index
            team_a = json.loads(match.team_a) if isinstance(match.team_a, str) else match.team_a
            team_b = json.loads(match.team_b) if isinstance(match.team_b, str) else match.team_b
            
            print(f"  🏓 Court {court_idx}: {team_a} vs {team_b} = {match.score_a}-{match.score_b}")
            
            # Determine winners and losers based on score
            # CRITICAL FIX: Handle unscored matches (both scores are 0)
            if match.score_a == 0 and match.score_b == 0:
                # Match not scored - treat all players as "stayed on same court"
                # Both teams stay on their current court for fair rotation
                print(f"     ⚠️ Unscored match - both teams stay at Court {court_idx}")
                court_groups[court_idx].append(team_a)
                court_groups[court_idx].append(team_b)
                continue  # Skip normal winner/loser logic
            elif match.score_a > match.score_b:
                winners = team_a  # Keep as group [player1, player2]
                losers = team_b
                print(f"     ✅ Winners: {winners}, Losers: {losers}")
            elif match.score_b > match.score_a:
                winners = team_b
                losers = team_a
                print(f"     ✅ Winners: {winners}, Losers: {losers}")
            else:
                # Tie - treat both as staying on same court
                print(f"     ⚠️ Tie match - both teams stay at Court {court_idx}")
                court_groups[court_idx].append(team_a)
                court_groups[court_idx].append(team_b)
                continue
            
            # Apply Top Court movement rules - move groups, not individuals
            if court_idx == 0:
                # Top Court: winner group stays at top, loser group drops to bottom
                court_groups[0].append(winners)
                court_groups[num_courts - 1].append(losers)
                print(f"     ↗️ Winners {winners} stay at Court 0")
                print(f"     ↘️ Losers {losers} drop to Court {num_courts - 1}")
            else:
                # Other courts: winner group moves up, loser group stays
                target_court = court_idx - 1
                court_groups[target_court].append(winners)
                court_groups[court_idx].append(losers)
                print(f"     ↗️ Winners {winners} move up to Court {target_court}")
                print(f"     ↔️ Losers {losers} stay at Court {court_idx}")
        
        # Delete previous matches
        await db_session.execute(delete(DBMatch).where(DBMatch.club_name == club_name))
        
        # Get all active players to handle sitouts
        result = await db_session.execute(
            select(DBPlayer).where(and_(DBPlayer.club_name == club_name, DBPlayer.is_active == True))
        )
        all_active_players = result.scalars().all()
        all_active_ids = {p.id for p in all_active_players}
        
        # Track which players are in matches
        players_in_matches = set()
        for court_groups_list in court_groups:
            for group in court_groups_list:
                players_in_matches.update(group)
        
        # Find players sitting out (active but not in any match)
        sitting_players = [p.id for p in all_active_players if p.id not in players_in_matches and not p.sit_next_round]
        
        print(f"🔍 Top Court Debug: {len(sitting_players)} players sitting, {len(players_in_matches)} playing")
        
        # Create new matches with previous partners playing AGAINST each other
        new_matches = []
        for court_idx in range(num_courts):
            groups_on_court = court_groups[court_idx]
            
            # CRITICAL FIX: Handle courts without exactly 2 groups
            if len(groups_on_court) < 2:
                # Not enough groups - try to fill with sitting players
                print(f"⚠️ Court {court_idx} has {len(groups_on_court)} groups, need 2. Filling with sitting players...")
                
                while len(groups_on_court) < 2 and len(sitting_players) >= 2:
                    # Take 2 sitting players as a new group
                    new_group = [sitting_players.pop(0), sitting_players.pop(0)]
                    groups_on_court.append(new_group)
                    print(f"✅ Added group to court {court_idx}: {new_group}")
                
                if len(groups_on_court) < 2:
                    print(f"❌ Court {court_idx} still has only {len(groups_on_court)} groups, skipping")
                    continue
                    
            elif len(groups_on_court) > 2:
                # Too many groups - keep only first 2 and put rest back as sitting
                print(f"⚠️ Court {court_idx} has {len(groups_on_court)} groups, keeping first 2")
                for extra_group in groups_on_court[2:]:
                    sitting_players.extend(extra_group)
                groups_on_court = groups_on_court[:2]
            
            # We have 2 groups of 2 players each
            group1 = groups_on_court[0]  # [player1, player2] - were partners
            group2 = groups_on_court[1]  # [player3, player4] - were partners
            
            # Split partners to play AGAINST each other:
            # Team A: player1 (from group1) + player3 (from group2)
            # Team B: player2 (from group1) + player4 (from group2)
            team_a = [group1[0], group2[0]]
            team_b = [group1[1], group2[1]]
            
            # Get player objects to determine category
            result = await db_session.execute(
                select(DBPlayer).where(DBPlayer.id.in_(team_a + team_b))
            )
            match_players = result.scalars().all()
            
            # Use category of first player
            category = match_players[0].category if match_players else "Intermediate"
            
            # Create match
            new_match = DBMatch(
                id=str(uuid.uuid4()),
                round_index=round_index,
                court_index=court_idx,
                category=category,
                club_name=club_name,
                match_type="doubles",
                team_a=json.dumps(team_a),
                team_b=json.dumps(team_b),
                score_a=0,
                score_b=0,
                status="active",
                match_date=datetime.utcnow()
            )
            
            db_session.add(new_match)
            new_matches.append({
                'id': new_match.id,
                'roundIndex': round_index,
                'courtIndex': court_idx,
                'category': category,
                'teamA': team_a,
                'teamB': team_b
            })
        
        await db_session.flush()
        return new_matches
        
    except Exception as e:
        print(f"Error in schedule_top_court_round: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


@api_router.post("/session/next-round")
async def start_next_round(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Generate the next round of matches with player reshuffling - SQLite version"""
    try:
        # Get current session
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse session config
        config_data = json.loads(session.config) if session.config else {}
        session_config = SessionConfig(**config_data)
        
        next_round = session.current_round + 1
        
        # Check if Top Court mode
        if session_config.rotationModel == 'top_court':
            # Top Court algorithm: move winners up, losers down
            matches_created = await schedule_top_court_round(next_round, db_session, club_name, session_config)
        else:
            # Clear previous round matches for legacy mode
            await db_session.execute(delete(DBMatch).where(DBMatch.club_name == club_name))
            
            # CRITICAL FIX: Commit the deletion before creating new matches
            await db_session.commit()
            print(f"🗑️ Deleted all previous matches for legacy mode round {next_round}")
            
            # Get all players for reshuffling
            result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
            players = result.scalars().all()
            
            if len(players) < 2:
                raise HTTPException(status_code=400, detail="Not enough players for matches")
            
            # USE ENHANCED RESHUFFLING ALGORITHM - Call schedule_round function with club_name
            matches_created = await schedule_round(next_round, db_session, club_name)
        
        # Update session to ready phase for next round
        session.current_round = next_round
        session.phase = SessionPhase.ready.value  # Set to ready so Let's Play appears
        session.time_remaining = session_config.playSeconds
        session.paused = False
        
        await db_session.commit()
        
        return {
            "message": f"Round {next_round} generated with {'Top Court' if session_config.rotationModel == 'top_court' else 'enhanced reshuffled'} players",
            "round": next_round,
            "matches_created": len(matches_created),
            "phase": "ready"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate next round: {str(e)}")

@api_router.post("/session/buffer")
async def start_buffer_phase(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Start buffer phase after round completion"""
    try:
        # Get current session
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse session config
        config_data = json.loads(session.config) if session.config else {}
        session_config = SessionConfig(**config_data)
        
        # Update session to buffer phase
        session.phase = SessionPhase.buffer.value
        session.time_remaining = session_config.bufferSeconds
        session.paused = False
        
        await db_session.commit()
        
        return {
            "message": "Buffer phase started",
            "phase": "buffer",
            "time_remaining": session_config.bufferSeconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start buffer phase: {str(e)}")

@api_router.post("/session/play")
async def start_play(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Start the play phase with timer"""
    try:
        # Get current session - SQLite version
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse session config
        config_data = json.loads(session.config) if session.config else {}
        session_config = SessionConfig(**config_data)
        
        # Update session to play phase
        session.phase = SessionPhase.play.value
        session.time_remaining = session_config.playSeconds
        session.paused = False
        
        await db_session.commit()
        
        return {"message": "Play started", "phase": "play", "timeRemaining": session_config.playSeconds}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start play: {str(e)}")

@api_router.post("/session/update-date")
async def update_session_date(request: Request, club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Update session date to current date (auto-update for new day)"""
    try:
        body = await request.json()
        new_date_str = body.get('sessionDate')
        
        if not new_date_str:
            raise HTTPException(status_code=400, detail="sessionDate is required")
        
        # Parse the date string
        from datetime import datetime
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
        
        # Get current session
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session date
        session.session_date = new_date
        await db_session.commit()
        
        return {"message": f"Session date updated to {new_date_str}", "sessionDate": new_date_str}
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session date: {str(e)}")

@api_router.post("/session/pause")
async def pause_session(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Pause the session"""
    try:
        # Get current session - SQLite version
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.paused = True
        await db_session.commit()
        
        return {"message": "Session paused"}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to pause session: {str(e)}")

@api_router.post("/session/resume")
async def resume_session(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Resume the session"""
    try:
        # Get current session - SQLite version
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.paused = False
        await db_session.commit()
        
        return {"message": "Session resumed"}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")

@api_router.post("/session/horn")
async def horn_now(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Manual horn activation and phase transition"""
    try:
        # Get current session - SQLite version
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Parse session data
        config_data = json.loads(session.config) if session.config else {}
        session_config = SessionConfig(**config_data)
        
        if session.phase == SessionPhase.play.value:
            # Transition to buffer
            session.phase = SessionPhase.buffer.value
            session.time_remaining = session_config.bufferSeconds
            
            await db_session.commit()
            return {"message": "Horn activated - Buffer phase", "phase": "buffer", "horn": "end"}
        
        elif session.phase == SessionPhase.buffer.value:
            # Transition to next round or end session
            total_rounds = math.floor(7200 / max(1, session_config.playSeconds + session_config.bufferSeconds))
            
            if session.current_round >= total_rounds:
                # End session
                session.phase = SessionPhase.ended.value
                session.time_remaining = 0
                
                await db_session.commit()
                return {"message": "Session ended", "phase": "ended", "horn": "end"}
            else:
                # Start next round
                try:
                    matches = await schedule_round(session.current_round + 1, db_session)
                    session.current_round = session.current_round + 1
                    session.phase = SessionPhase.play.value
                    session.time_remaining = session_config.playSeconds
                    
                    await db_session.commit()
                    return {
                        "message": f"Round {session.current_round} started", 
                        "phase": "play", 
                        "horn": "start",
                        "round": session.current_round,
                        "matches_created": len(matches)
                    }
                except Exception as e:
                    await db_session.rollback()
                    raise HTTPException(status_code=500, detail=f"Failed to start next round: {str(e)}")
        
        return {"message": "Horn activated", "horn": "manual"}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate horn: {str(e)}")

@api_router.post("/session/reset")
async def reset_session(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Reset session state to idle and clear all matches - SQLite version"""
    try:
        # Clear all matches for this club
        await db_session.execute(delete(DBMatch).where(DBMatch.club_name == club_name))
        
        # Reset player counters and stats for this club
        result = await db_session.execute(select(DBPlayer).where(DBPlayer.club_name == club_name))
        players = result.scalars().all()
        
        for player in players:
            player.sit_next_round = False
            player.sit_count = 0
            player.miss_due_to_court_limit = 0
            player.stats_wins = 0
            player.stats_losses = 0
            player.stats_point_diff = 0
        
        # Get current session to preserve config
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if session:
            # Parse config to get play time
            try:
                config_data = json.loads(session.config) if session.config else {}
                play_time = config_data.get('playSeconds', 720)
            except:
                play_time = 720  # default 12 minutes
                
            # Reset session state
            session.current_round = 0
            session.phase = SessionPhase.idle.value
            session.time_remaining = play_time
            session.paused = False
            session.histories = json.dumps({"partnerHistory": {}, "opponentHistory": {}})
        
        await db_session.commit()
        
        return {"message": "Session reset"}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {str(e)}")

@api_router.post("/init")
async def initialize_data(club_name: str = "Main Club", db_session: AsyncSession = Depends(get_db_session)):
    """Initialize default categories and session - SQLite version"""
    try:
        # Check if categories exist (categories are global, not club-specific)
        result = await db_session.execute(select(DBCategory))
        existing_cats = result.scalars().all()
        
        if not existing_cats:
            default_categories = [
                {"name": "Beginner", "description": "New to pickleball"},
                {"name": "Intermediate", "description": "Some experience"},
                {"name": "Advanced", "description": "Experienced players"},
                {"name": "Social", "description": "Casual play - no scoring required"}
            ]
            
            for cat_data in default_categories:
                db_category = DBCategory(
                    id=str(uuid.uuid4()),
                    name=cat_data["name"],
                    description=cat_data["description"]
                )
                db_session.add(db_category)
        
        # Ensure session exists for this club
        result = await db_session.execute(select(DBSession).where(DBSession.club_name == club_name))
        session = result.scalar_one_or_none()
        
        if not session:
            # Create default session config
            default_config = {
                "numCourts": 6,
                "playSeconds": 720,
                "bufferSeconds": 30,
                "allowSingles": False,
                "allowDoubles": True,
                "allowCrossCategory": True,
                "maximizeCourtUsage": False
            }
            
            session_obj = DBSession(
                id=str(uuid.uuid4()),
                current_round=0,
                phase=SessionPhase.idle.value,
                time_remaining=720,
                paused=False,
                config=json.dumps(default_config),
                histories=json.dumps({"partnerHistory": {}, "opponentHistory": {}}),
                club_name=club_name
            )
            db_session.add(session_obj)
        
        await db_session.commit()
        return {"message": "Data initialized"}
        
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to initialize data: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_database()
    print("✅ SQLite database initialized")

@app.on_event("shutdown") 
async def shutdown_event():
    print("🔄 Shutting down...")

# Initialize database on startup