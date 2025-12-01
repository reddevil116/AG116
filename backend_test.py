#!/usr/bin/env python3
"""
CourtChime Backend Testing - Critical Bug Fixes Verification
Testing the rating system updates and next round generation fixes
"""

import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

class CourtChimeBackendTester:
    def __init__(self):
        self.base_url = "https://chime-roster.preview.emergentagent.com/api"
        self.club_name = "Sandyford Pickleball Club"  # As requested in review
        self.access_code = "demo123"  # Standard access code
        self.session_data = None
        self.players = []
        self.matches = []
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, params=params, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": 200 <= response.status_code < 300
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response"},
                "success": False
            }
    
    def test_1_initial_setup(self):
        """Test 1: Initial Setup - Club and Player State Verification"""
        print("\n🎯 TEST 1: INITIAL SETUP")
        
        # Check if Sandyford Pickleball Club exists
        response = self.make_request("GET", "/clubs")
        if not response["success"]:
            self.log_test("Club List Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        clubs = response["data"]
        sandyford_exists = any(club.get("name") == self.club_name for club in clubs)
        
        if not sandyford_exists:
            # Create Sandyford Pickleball Club
            club_data = {
                "name": self.club_name,
                "display_name": self.club_name,
                "description": "Test club for comprehensive end-to-end testing",
                "access_code": self.access_code
            }
            response = self.make_request("POST", "/clubs", club_data)
            if not response["success"]:
                self.log_test("Club Creation", "FAIL", f"Status: {response['status_code']}")
                return False
            self.log_test("Club Creation", "PASS", f"Created {self.club_name}")
        else:
            self.log_test("Club Exists", "PASS", f"{self.club_name} found")
        
        # Authenticate with club
        login_data = {
            "club_name": self.club_name,
            "access_code": self.access_code
        }
        response = self.make_request("POST", "/auth/login", login_data)
        if not response["success"]:
            self.log_test("Club Authentication", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.session_data = response["data"]
        self.log_test("Club Authentication", "PASS", f"Authenticated as {self.session_data.get('display_name')}")
        
        # Get current players
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/players", params=params)
        if not response["success"]:
            self.log_test("Player Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.players = response["data"]
        total_players = len(self.players)
        active_players = [p for p in self.players if p.get("isActive", True)]
        inactive_players = [p for p in self.players if not p.get("isActive", True)]
        
        self.log_test("Player Count Verification", "PASS", 
                     f"Total: {total_players}, Active: {len(active_players)}, Inactive: {len(inactive_players)}")
        
        # If we don't have enough players, create test players
        if total_players < 87:
            self.create_test_players(87 - total_players)
        
        return True
    
    def create_test_players(self, count: int):
        """Create test players to reach the required count"""
        print(f"\n📝 Creating {count} test players...")
        
        categories = ["Beginner", "Intermediate", "Advanced", "Social"]
        names = [
            "Alex Johnson", "Blake Smith", "Casey Brown", "Drew Wilson", "Emery Davis",
            "Finley Miller", "Gray Anderson", "Harper Taylor", "Indigo Moore", "Jordan Jackson",
            "Kai Martin", "Lane Thompson", "Morgan White", "Nova Harris", "Ocean Clark",
            "Parker Lewis", "Quinn Walker", "River Hall", "Sage Allen", "Taylor Young",
            "Uma King", "Vale Wright", "West Lopez", "Xara Hill", "Yara Green", "Zion Adams",
            "Aria Baker", "Bryce Nelson", "Cora Carter", "Dean Mitchell", "Ella Perez",
            "Felix Roberts", "Grace Turner", "Hugo Phillips", "Iris Campbell", "Jude Parker",
            "Kira Evans", "Luca Edwards", "Maya Collins", "Noel Stewart", "Orion Sanchez",
            "Piper Morris", "Quincy Rogers", "Ruby Reed", "Sage Cook", "Tate Bailey",
            "Uma Rivera", "Vera Cooper", "Wade Richardson", "Xyla Cox", "Yuki Howard",
            "Zara Ward", "Aiden Torres", "Bella Peterson", "Caleb Gray", "Delia Ramirez",
            "Ethan James", "Fiona Watson", "Gabe Brooks", "Hana Kelly", "Ivan Sanders",
            "Jade Price", "Knox Bennett", "Luna Wood", "Max Barnes", "Nora Ross",
            "Owen Henderson", "Pia Coleman", "Quin Jenkins", "Rosa Perry", "Sam Powell",
            "Tara Long", "Ulric Patterson", "Vera Hughes", "Will Flores", "Xena Washington",
            "Yael Butler", "Zoe Simmons", "Arlo Foster", "Bria Gonzales", "Cade Bryant",
            "Dana Alexander", "Ezra Russell", "Faye Griffin", "Gage Diaz", "Hope Hayes"
        ]
        
        created_count = 0
        for i in range(count):
            if i < len(names):
                name = names[i]
            else:
                name = f"Player {i + len(self.players) + 1}"
            
            player_data = {
                "name": name,
                "category": random.choice(categories)
            }
            
            params = {"club_name": self.club_name}
            response = self.make_request("POST", "/players", player_data, params=params)
            if response["success"]:
                created_count += 1
                # Set most players to inactive (as requested - mostly inactive)
                if random.random() < 0.85:  # 85% chance to be inactive
                    player_id = response["data"].get("id")
                    if player_id:
                        toggle_params = {"club_name": self.club_name}
                        self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=toggle_params)
        
        self.log_test("Test Player Creation", "PASS", f"Created {created_count} players")
        
        # Refresh player list
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/players", params=params)
        if response["success"]:
            self.players = response["data"]
    
    def test_2_player_management(self):
        """Test 2: Player Management - Active vs Inactive Players"""
        print("\n🎯 TEST 2: PLAYER MANAGEMENT")
        
        # Get current player state
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/players", params=params)
        if not response["success"]:
            self.log_test("Player State Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.players = response["data"]
        active_players = [p for p in self.players if p.get("isActive", True)]
        inactive_players = [p for p in self.players if not p.get("isActive", True)]
        
        self.log_test("Player State Analysis", "PASS", 
                     f"Active: {len(active_players)}, Inactive: {len(inactive_players)}")
        
        # Verify inactive players are excluded from match generation
        if len(inactive_players) > 0:
            self.log_test("Inactive Player Verification", "PASS", 
                         f"Found {len(inactive_players)} inactive players (should have green Add buttons)")
        else:
            self.log_test("Inactive Player Verification", "WARN", 
                         "No inactive players found - may need to deactivate some players")
        
        # Test player toggle functionality
        if len(active_players) > 0:
            test_player = active_players[0]
            player_id = test_player["id"]
            
            # Toggle player to inactive
            params = {"club_name": self.club_name}
            response = self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=params)
            if response["success"]:
                self.log_test("Player Toggle (Active→Inactive)", "PASS", 
                             f"Toggled {test_player['name']} to inactive")
                
                # Toggle back to active
                response = self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=params)
                if response["success"]:
                    self.log_test("Player Toggle (Inactive→Active)", "PASS", 
                                 f"Toggled {test_player['name']} back to active")
                else:
                    self.log_test("Player Toggle (Inactive→Active)", "FAIL", 
                                 f"Failed to toggle back: {response['status_code']}")
            else:
                self.log_test("Player Toggle (Active→Inactive)", "FAIL", 
                             f"Failed to toggle: {response['status_code']}")
        
        return True
    
    def test_3_match_generation_first_round(self):
        """Test 3: Match Generation (First Round) - Only Active Players"""
        print("\n🎯 TEST 3: MATCH GENERATION (FIRST ROUND)")
        
        # Ensure we have some active players for testing
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/players", params=params)
        if not response["success"]:
            self.log_test("Player Retrieval for Match Gen", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.players = response["data"]
        active_players = [p for p in self.players if p.get("isActive", True)]
        
        # Activate some players if needed (simulate Add button clicks)
        if len(active_players) < 12:
            inactive_players = [p for p in self.players if not p.get("isActive", True)]
            players_to_activate = min(12 - len(active_players), len(inactive_players))
            
            for i in range(players_to_activate):
                player_id = inactive_players[i]["id"]
                params = {"club_name": self.club_name}
                response = self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=params)
                if response["success"]:
                    active_players.append(inactive_players[i])
            
            self.log_test("Player Activation", "PASS", 
                         f"Activated {players_to_activate} players for testing")
        
        # Generate matches
        params = {"club_name": self.club_name}
        response = self.make_request("POST", "/session/generate-matches", params=params)
        if not response["success"]:
            self.log_test("Match Generation", "FAIL", f"Status: {response['status_code']}")
            return False
        
        # Get generated matches
        response = self.make_request("GET", "/matches", params=params)
        if not response["success"]:
            self.log_test("Match Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.matches = response["data"]
        
        # Verify only active players in matches
        all_match_players = set()
        for match in self.matches:
            team_a = match.get("teamA", [])
            team_b = match.get("teamB", [])
            all_match_players.update(team_a + team_b)
        
        # Check if any inactive players are in matches
        inactive_player_ids = {p["id"] for p in self.players if not p.get("isActive", True)}
        inactive_in_matches = all_match_players.intersection(inactive_player_ids)
        
        if inactive_in_matches:
            self.log_test("Active Player Verification", "FAIL", 
                         f"Found {len(inactive_in_matches)} inactive players in matches")
        else:
            self.log_test("Active Player Verification", "PASS", 
                         "Only active players included in matches")
        
        # Verify court utilization
        courts_used = len(set(match.get("courtIndex", 0) for match in self.matches))
        self.log_test("Court Utilization", "PASS", 
                     f"Generated {len(self.matches)} matches using {courts_used} courts")
        
        # Verify team assignments (no duplicates)
        for i, match in enumerate(self.matches):
            team_a = match.get("teamA", [])
            team_b = match.get("teamB", [])
            
            # Check for duplicates within teams
            if len(team_a) != len(set(team_a)) or len(team_b) != len(set(team_b)):
                self.log_test(f"Match {i+1} Team Integrity", "FAIL", 
                             "Duplicate players within team")
                return False
            
            # Check for players in both teams
            if set(team_a).intersection(set(team_b)):
                self.log_test(f"Match {i+1} Team Separation", "FAIL", 
                             "Player appears in both teams")
                return False
        
        self.log_test("Team Assignment Integrity", "PASS", 
                     "No duplicate players across teams")
        
        return True
    
    def test_4_player_swap_persistence(self):
        """Test 4: Player Swap Persistence - Critical Test"""
        print("\n🎯 TEST 4: PLAYER SWAP PERSISTENCE (CRITICAL)")
        
        if len(self.matches) < 1:
            self.log_test("Swap Test Prerequisites", "FAIL", "No matches available for swap testing")
            return False
        
        # Get initial match lineup
        test_match = self.matches[0]
        match_id = test_match["id"]
        original_team_a = test_match["teamA"].copy()
        original_team_b = test_match["teamB"].copy()
        
        self.log_test("Initial Match State", "PASS", 
                     f"Match {match_id}: TeamA={len(original_team_a)}, TeamB={len(original_team_b)}")
        
        # Perform player swap (swap first player from each team)
        if len(original_team_a) > 0 and len(original_team_b) > 0:
            new_team_a = original_team_a.copy()
            new_team_b = original_team_b.copy()
            
            # Swap first players
            new_team_a[0], new_team_b[0] = new_team_b[0], new_team_a[0]
            
            swap_data = {
                "teamA": new_team_a,
                "teamB": new_team_b
            }
            
            params = {"club_name": self.club_name}
            response = self.make_request("PUT", f"/matches/{match_id}", swap_data, params=params)
            if not response["success"]:
                self.log_test("Player Swap Execution", "FAIL", f"Status: {response['status_code']}")
                return False
            
            self.log_test("Player Swap Execution", "PASS", "Successfully swapped players")
            
            # Verify swap saved in database
            response = self.make_request("GET", "/matches", params=params)
            if not response["success"]:
                self.log_test("Swap Verification", "FAIL", f"Status: {response['status_code']}")
                return False
            
            updated_matches = response["data"]
            updated_match = next((m for m in updated_matches if m["id"] == match_id), None)
            
            if not updated_match:
                self.log_test("Swap Persistence Check", "FAIL", "Match not found after swap")
                return False
            
            if (updated_match["teamA"] == new_team_a and updated_match["teamB"] == new_team_b):
                self.log_test("Swap Persistence Check", "PASS", "Swap correctly saved in database")
            else:
                self.log_test("Swap Persistence Check", "FAIL", "Swap not persisted correctly")
                return False
            
            # Start session (Let's Play)
            response = self.make_request("POST", "/session/start", params=params)
            if not response["success"]:
                self.log_test("Session Start", "FAIL", f"Status: {response['status_code']}")
                return False
            
            self.log_test("Session Start", "PASS", "Session started successfully")
            
            # Verify swapped players still in new positions (NOT reset)
            response = self.make_request("GET", "/matches", params=params)
            if not response["success"]:
                self.log_test("Post-Start Match Retrieval", "FAIL", f"Status: {response['status_code']}")
                return False
            
            final_matches = response["data"]
            final_match = next((m for m in final_matches if m["id"] == match_id), None)
            
            if not final_match:
                self.log_test("Post-Start Match Verification", "FAIL", "Match not found after session start")
                return False
            
            if (final_match["teamA"] == new_team_a and final_match["teamB"] == new_team_b):
                self.log_test("CRITICAL: Swap Persistence Through Session Start", "PASS", 
                             "Swapped players maintained positions after session start")
            else:
                self.log_test("CRITICAL: Swap Persistence Through Session Start", "FAIL", 
                             "Swaps were RESET after session start - CRITICAL BUG")
                return False
        
        return True
    
    def test_5_session_state_management(self):
        """Test 5: Session State Management"""
        print("\n🎯 TEST 5: SESSION STATE MANAGEMENT")
        
        # Get session state
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/session", params=params)
        if not response["success"]:
            self.log_test("Session State Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        session = response["data"]
        
        # Verify session phase
        expected_phase = "play"  # Should be in play phase after session start
        actual_phase = session.get("phase", "unknown")
        
        if actual_phase == expected_phase:
            self.log_test("Session Phase Verification", "PASS", f"Phase: {actual_phase}")
        else:
            self.log_test("Session Phase Verification", "WARN", 
                         f"Expected: {expected_phase}, Actual: {actual_phase}")
        
        # Verify timer state
        paused = session.get("paused", True)
        time_remaining = session.get("timeRemaining", 0)
        
        if not paused:
            self.log_test("Timer State Verification", "PASS", 
                         f"Timer running, {time_remaining}s remaining")
        else:
            self.log_test("Timer State Verification", "WARN", 
                         f"Timer paused, {time_remaining}s remaining")
        
        # Verify session date
        session_date = session.get("sessionDate")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if session_date == today:
            self.log_test("Session Date Verification", "PASS", f"Date: {session_date}")
        else:
            self.log_test("Session Date Verification", "WARN", 
                         f"Expected: {today}, Actual: {session_date}")
        
        return True
    
    def test_6_score_saving_rating_updates(self):
        """Test 6: Score Saving & Rating Updates - Critical Test"""
        print("\n🎯 TEST 6: SCORE SAVING & RATING UPDATES (CRITICAL)")
        
        if len(self.matches) < 1:
            self.log_test("Score Test Prerequisites", "FAIL", "No matches available for scoring")
            return False
        
        # Get a match to score
        test_match = self.matches[0]
        match_id = test_match["id"]
        team_a_players = test_match["teamA"]
        team_b_players = test_match["teamB"]
        
        # Get initial player ratings
        initial_ratings = {}
        for player_id in team_a_players + team_b_players:
            player = next((p for p in self.players if p["id"] == player_id), None)
            if player:
                initial_ratings[player_id] = {
                    "rating": player.get("rating", 3.0),
                    "matchesPlayed": player.get("matchesPlayed", 0),
                    "wins": player.get("wins", 0),
                    "losses": player.get("losses", 0),
                    "recentForm": player.get("recentForm", [])
                }
        
        # Save match score (Team A wins 11-9)
        score_data = {
            "scoreA": 11,
            "scoreB": 9
        }
        
        params = {"club_name": self.club_name}
        response = self.make_request("PUT", f"/matches/{match_id}/score", score_data, params=params)
        if not response["success"]:
            self.log_test("Score Saving", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.log_test("Score Saving", "PASS", "Match score saved successfully")
        
        # Verify match status changed to "saved"
        response = self.make_request("GET", "/matches", params=params)
        if response["success"]:
            updated_matches = response["data"]
            scored_match = next((m for m in updated_matches if m["id"] == match_id), None)
            
            if scored_match and scored_match.get("status") == "saved":
                self.log_test("Match Status Update", "PASS", "Match status changed to 'saved'")
            else:
                self.log_test("Match Status Update", "FAIL", 
                             f"Expected status 'saved', got '{scored_match.get('status') if scored_match else 'None'}'")
        
        # Get updated player data
        response = self.make_request("GET", "/players", params=params)
        if not response["success"]:
            self.log_test("Updated Player Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        updated_players = response["data"]
        
        # Verify rating updates
        rating_updates_found = 0
        matches_played_updates = 0
        wins_losses_updates = 0
        recent_form_updates = 0
        
        for player_id in team_a_players + team_b_players:
            initial = initial_ratings.get(player_id, {})
            updated_player = next((p for p in updated_players if p["id"] == player_id), None)
            
            if updated_player:
                # Check rating change
                old_rating = initial.get("rating", 3.0)
                new_rating = updated_player.get("rating", 3.0)
                if new_rating != old_rating:
                    rating_updates_found += 1
                
                # Check matches played increment
                old_matches = initial.get("matchesPlayed", 0)
                new_matches = updated_player.get("matchesPlayed", 0)
                if new_matches > old_matches:
                    matches_played_updates += 1
                
                # Check wins/losses update
                old_wins = initial.get("wins", 0)
                old_losses = initial.get("losses", 0)
                new_wins = updated_player.get("wins", 0)
                new_losses = updated_player.get("losses", 0)
                if new_wins > old_wins or new_losses > old_losses:
                    wins_losses_updates += 1
                
                # Check recent form update
                old_form = initial.get("recentForm", [])
                new_form = updated_player.get("recentForm", [])
                if len(new_form) > len(old_form):
                    recent_form_updates += 1
        
        # Verify updates
        total_players = len(team_a_players + team_b_players)
        
        if rating_updates_found > 0:
            self.log_test("Rating Updates", "PASS", 
                         f"{rating_updates_found}/{total_players} players had rating changes")
        else:
            self.log_test("Rating Updates", "FAIL", "No player ratings were updated")
        
        if matches_played_updates > 0:
            self.log_test("Matches Played Updates", "PASS", 
                         f"{matches_played_updates}/{total_players} players had matchesPlayed incremented")
        else:
            self.log_test("Matches Played Updates", "FAIL", "No matchesPlayed counters were updated")
        
        if wins_losses_updates > 0:
            self.log_test("Wins/Losses Updates", "PASS", 
                         f"{wins_losses_updates}/{total_players} players had wins/losses updated")
        else:
            self.log_test("Wins/Losses Updates", "FAIL", "No wins/losses were updated")
        
        if recent_form_updates > 0:
            self.log_test("Recent Form Updates", "PASS", 
                         f"{recent_form_updates}/{total_players} players had recentForm updated")
        else:
            self.log_test("Recent Form Updates", "FAIL", "No recentForm was updated")
        
        return True
    
    def test_7_top_court_rotation(self):
        """Test 7: Top Court Rotation (Next Round)"""
        print("\n🎯 TEST 7: TOP COURT ROTATION (NEXT ROUND)")
        
        # Save winners for all matches to enable next round
        params = {"club_name": self.club_name}
        
        # Get current matches
        response = self.make_request("GET", "/matches", params=params)
        if not response["success"]:
            self.log_test("Match Retrieval for Rotation", "FAIL", f"Status: {response['status_code']}")
            return False
        
        current_matches = response["data"]
        unsaved_matches = [m for m in current_matches if m.get("status") != "saved"]
        
        # Save remaining matches
        for match in unsaved_matches:
            match_id = match["id"]
            # Randomly assign winner
            score_data = {
                "scoreA": random.randint(8, 11),
                "scoreB": random.randint(8, 11)
            }
            # Ensure different scores
            while score_data["scoreA"] == score_data["scoreB"]:
                score_data["scoreB"] = random.randint(8, 11)
            
            response = self.make_request("PUT", f"/matches/{match_id}/score", score_data, params=params)
            if response["success"]:
                self.log_test(f"Match {match_id[:8]} Scoring", "PASS", 
                             f"Score: {score_data['scoreA']}-{score_data['scoreB']}")
        
        # Generate next round
        response = self.make_request("POST", "/session/next-round", params=params)
        if not response["success"]:
            self.log_test("Next Round Generation", "FAIL", f"Status: {response['status_code']}")
            return False
        
        self.log_test("Next Round Generation", "PASS", "Round 2 matches generated")
        
        # Get Round 2 matches
        response = self.make_request("GET", "/matches", params=params)
        if not response["success"]:
            self.log_test("Round 2 Match Retrieval", "FAIL", f"Status: {response['status_code']}")
            return False
        
        all_matches = response["data"]
        round_2_matches = [m for m in all_matches if m.get("roundIndex") == 1]  # Round 2 (0-indexed)
        
        if len(round_2_matches) > 0:
            self.log_test("Round 2 Match Verification", "PASS", 
                         f"Generated {len(round_2_matches)} Round 2 matches")
            
            # Verify court assignments (basic check)
            courts_used = set(m.get("courtIndex", 0) for m in round_2_matches)
            self.log_test("Round 2 Court Assignment", "PASS", 
                         f"Using courts: {sorted(courts_used)}")
        else:
            self.log_test("Round 2 Match Verification", "FAIL", "No Round 2 matches generated")
            return False
        
        return True
    
    def test_8_timer_session_controls(self):
        """Test 8: Timer & Session Controls"""
        print("\n🎯 TEST 8: TIMER & SESSION CONTROLS")
        
        params = {"club_name": self.club_name}
        
        # Test pause
        response = self.make_request("POST", "/session/pause", params=params)
        if response["success"]:
            self.log_test("Session Pause", "PASS", "Session paused successfully")
            
            # Verify paused state
            response = self.make_request("GET", "/session", params=params)
            if response["success"]:
                session = response["data"]
                if session.get("paused", False):
                    self.log_test("Pause State Verification", "PASS", "Session is paused")
                else:
                    self.log_test("Pause State Verification", "FAIL", "Session not showing as paused")
        else:
            self.log_test("Session Pause", "FAIL", f"Status: {response['status_code']}")
        
        # Test resume
        response = self.make_request("POST", "/session/resume", params=params)
        if response["success"]:
            self.log_test("Session Resume", "PASS", "Session resumed successfully")
            
            # Verify resumed state
            response = self.make_request("GET", "/session", params=params)
            if response["success"]:
                session = response["data"]
                if not session.get("paused", True):
                    self.log_test("Resume State Verification", "PASS", "Session is not paused")
                else:
                    self.log_test("Resume State Verification", "FAIL", "Session still showing as paused")
        else:
            self.log_test("Session Resume", "FAIL", f"Status: {response['status_code']}")
        
        # Test reset
        response = self.make_request("POST", "/session/reset", params=params)
        if response["success"]:
            self.log_test("Session Reset", "PASS", "Session reset successfully")
            
            # Verify reset state
            response = self.make_request("GET", "/session", params=params)
            if response["success"]:
                session = response["data"]
                phase = session.get("phase", "unknown")
                if phase in ["ready", "idle"]:
                    self.log_test("Reset State Verification", "PASS", f"Phase back to: {phase}")
                else:
                    self.log_test("Reset State Verification", "WARN", f"Unexpected phase after reset: {phase}")
        else:
            self.log_test("Session Reset", "FAIL", f"Status: {response['status_code']}")
        
        return True
    
    def test_9_social_category_integration(self):
        """Test 9: Social Category Integration"""
        print("\n🎯 TEST 9: SOCIAL CATEGORY INTEGRATION")
        
        # Check if we have social players
        social_players = [p for p in self.players if p.get("category") == "Social"]
        
        if len(social_players) == 0:
            # Create a social player for testing
            player_data = {
                "name": "Social Test Player",
                "category": "Social"
            }
            params = {"club_name": self.club_name}
            response = self.make_request("POST", "/players", player_data, params=params)
            if response["success"]:
                # Activate the social player
                player_id = response["data"]["id"]
                self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=params)
                self.log_test("Social Player Creation", "PASS", "Created and activated social player")
            else:
                self.log_test("Social Player Creation", "FAIL", f"Status: {response['status_code']}")
                return False
        else:
            # Ensure at least one social player is active
            active_social = [p for p in social_players if p.get("isActive", True)]
            if len(active_social) == 0 and len(social_players) > 0:
                player_id = social_players[0]["id"]
                params = {"club_name": self.club_name}
                self.make_request("PATCH", f"/players/{player_id}/toggle-active", params=params)
                self.log_test("Social Player Activation", "PASS", "Activated existing social player")
        
        # Generate matches with social players
        params = {"club_name": self.club_name}
        response = self.make_request("POST", "/session/generate-matches", params=params)
        if response["success"]:
            self.log_test("Match Generation with Social", "PASS", "Matches generated including social players")
        else:
            self.log_test("Match Generation with Social", "FAIL", f"Status: {response['status_code']}")
            return False
        
        # Verify social players are included
        response = self.make_request("GET", "/matches", params=params)
        if response["success"]:
            matches = response["data"]
            all_match_players = set()
            for match in matches:
                all_match_players.update(match.get("teamA", []) + match.get("teamB", []))
            
            # Refresh player list
            response = self.make_request("GET", "/players", params=params)
            if response["success"]:
                updated_players = response["data"]
                social_in_matches = [p for p in updated_players 
                                   if p["category"] == "Social" and p["id"] in all_match_players]
                
                if len(social_in_matches) > 0:
                    self.log_test("Social Player Inclusion", "PASS", 
                                 f"{len(social_in_matches)} social players in matches")
                else:
                    self.log_test("Social Player Inclusion", "WARN", "No social players found in matches")
        
        return True
    
    def test_10_data_integrity(self):
        """Test 10: Data Integrity"""
        print("\n🎯 TEST 10: DATA INTEGRITY")
        
        params = {"club_name": self.club_name}
        
        # Get current matches
        response = self.make_request("GET", "/matches", params=params)
        if not response["success"]:
            self.log_test("Data Integrity Check Setup", "FAIL", f"Status: {response['status_code']}")
            return False
        
        matches = response["data"]
        
        # Check for duplicate players across matches
        all_players_in_matches = []
        for match in matches:
            team_a = match.get("teamA", [])
            team_b = match.get("teamB", [])
            all_players_in_matches.extend(team_a + team_b)
        
        unique_players = set(all_players_in_matches)
        if len(all_players_in_matches) == len(unique_players):
            self.log_test("No Duplicate Players", "PASS", 
                         f"{len(unique_players)} unique players across {len(matches)} matches")
        else:
            duplicates = len(all_players_in_matches) - len(unique_players)
            self.log_test("No Duplicate Players", "FAIL", 
                         f"Found {duplicates} duplicate player assignments")
        
        # Validate player IDs exist
        response = self.make_request("GET", "/players", params=params)
        if response["success"]:
            valid_player_ids = {p["id"] for p in response["data"]}
            invalid_ids = unique_players - valid_player_ids
            
            if len(invalid_ids) == 0:
                self.log_test("Valid Player IDs", "PASS", "All player IDs in matches are valid")
            else:
                self.log_test("Valid Player IDs", "FAIL", 
                             f"Found {len(invalid_ids)} invalid player IDs in matches")
        
        # Check team sizes
        invalid_team_sizes = 0
        for i, match in enumerate(matches):
            team_a = match.get("teamA", [])
            team_b = match.get("teamB", [])
            match_type = match.get("matchType", "unknown")
            
            if match_type == "doubles":
                if len(team_a) != 2 or len(team_b) != 2:
                    invalid_team_sizes += 1
            elif match_type == "singles":
                if len(team_a) != 1 or len(team_b) != 1:
                    invalid_team_sizes += 1
        
        if invalid_team_sizes == 0:
            self.log_test("Correct Team Sizes", "PASS", "All matches have correct team sizes")
        else:
            self.log_test("Correct Team Sizes", "FAIL", 
                         f"{invalid_team_sizes} matches have incorrect team sizes")
        
        # Check for null/undefined values in critical fields
        null_value_issues = 0
        for match in matches:
            critical_fields = ["id", "teamA", "teamB", "courtIndex", "roundIndex", "matchType"]
            for field in critical_fields:
                if field not in match or match[field] is None:
                    null_value_issues += 1
        
        if null_value_issues == 0:
            self.log_test("No Null Critical Values", "PASS", "All critical fields have valid values")
        else:
            self.log_test("No Null Critical Values", "FAIL", 
                         f"Found {null_value_issues} null/missing critical field values")
        
        return True
    
    def run_comprehensive_test(self):
        """Run all comprehensive end-to-end tests"""
        print("🚀 STARTING COMPREHENSIVE END-TO-END TESTING")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_1_initial_setup,
            self.test_2_player_management,
            self.test_3_match_generation_first_round,
            self.test_4_player_swap_persistence,
            self.test_5_session_state_management,
            self.test_6_score_saving_rating_updates,
            self.test_7_top_court_rotation,
            self.test_8_timer_session_controls,
            self.test_9_social_category_integration,
            self.test_10_data_integrity
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_func in tests:
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                else:
                    failed_tests += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} CRASHED: {str(e)}")
                failed_tests += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = passed_tests + failed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Print detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        # Critical issues summary
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and "CRITICAL" in r["test"]]
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"❌ {failure['test']}: {failure['details']}")
        
        return success_rate >= 80  # Consider 80%+ success rate as passing

if __name__ == "__main__":
    tester = CourtChimeBackendTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️ COMPREHENSIVE TESTING COMPLETED WITH ISSUES")