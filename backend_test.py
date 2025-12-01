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
        self.club_name = "Main Club"  # As specified in review request
        self.access_code = "demo123"  # Standard access code
        self.session_data = None
        self.players = []
        self.matches = []
        self.test_results = []
        self.initial_player_data = {}
        
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
    
    def authenticate_club(self) -> bool:
        """Authenticate with Main Club"""
        login_data = {
            "club_name": self.club_name,
            "access_code": self.access_code
        }
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            self.session_data = response["data"]
            self.log_test("Club Authentication", "PASS", f"Authenticated as {self.session_data.get('display_name')}")
            return True
        else:
            self.log_test("Club Authentication", "FAIL", f"Status: {response['status_code']}")
            return False
    
    def get_players(self) -> List[Dict]:
        """Get current player data"""
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/players", params=params)
        if response["success"]:
            self.players = response["data"]
            active_count = len([p for p in self.players if p.get('isActive', False)])
            self.log_test("Get Players", "PASS", f"Retrieved {len(self.players)} players ({active_count} active)")
            return self.players
        else:
            self.log_test("Get Players", "FAIL", f"Status: {response['status_code']}")
            return []
    
    def record_initial_player_stats(self):
        """Record initial player ratings and stats for comparison"""
        self.get_players()
        for player in self.players:
            if player.get('isActive', False):
                self.initial_player_data[player['id']] = {
                    'name': player['name'],
                    'rating': player['rating'],
                    'wins': player['wins'],
                    'losses': player['losses'],
                    'matchesPlayed': player['matchesPlayed'],
                    'recentForm': player['recentForm'].copy()
                }
        
        active_count = len(self.initial_player_data)
        self.log_test("Record Initial Stats", "PASS", f"Recorded stats for {active_count} active players")
    
    def generate_round1_matches(self) -> bool:
        """Generate Round 1 matches"""
        params = {"club_name": self.club_name}
        response = self.make_request("POST", "/session/generate-matches", params=params)
        if response["success"]:
            matches_count = response["data"].get('matchesGenerated', 0)
            self.log_test("Generate Round 1", "PASS", f"Generated {matches_count} matches")
            return True
        else:
            self.log_test("Generate Round 1", "FAIL", f"Status: {response['status_code']}")
            return False
    
    def start_session(self) -> bool:
        """Start the session (transition to play phase)"""
        params = {"club_name": self.club_name}
        response = self.make_request("POST", "/session/start", params=params)
        if response["success"]:
            phase = response["data"].get('phase', 'unknown')
            self.log_test("Start Session", "PASS", f"Session phase: {phase}")
            return True
        else:
            self.log_test("Start Session", "FAIL", f"Status: {response['status_code']}")
            return False
    
    def get_matches(self) -> List[Dict]:
        """Get current matches"""
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/matches", params=params)
        if response["success"]:
            self.matches = response["data"]
            self.log_test("Get Matches", "PASS", f"Retrieved {len(self.matches)} matches")
            return self.matches
        else:
            self.log_test("Get Matches", "FAIL", f"Status: {response['status_code']}")
            return []
    
    def save_match_score(self, match_id: str, score_a: int, score_b: int) -> bool:
        """Save score for a specific match"""
        params = {"club_name": self.club_name}
        score_data = {"scoreA": score_a, "scoreB": score_b}
        
        response = self.make_request("PUT", f"/matches/{match_id}/score", score_data, params=params)
        if response["success"]:
            self.log_test("Save Match Score", "PASS", f"Match {match_id[:8]}... scored {score_a}-{score_b}")
            return True
        else:
            self.log_test("Save Match Score", "FAIL", f"Status: {response['status_code']}")
            return False
    
    def get_session_state(self) -> Dict:
        """Get current session state"""
        params = {"club_name": self.club_name}
        response = self.make_request("GET", "/session", params=params)
        if response["success"]:
            session_data = response["data"]
            current_round = session_data.get('currentRound', 0)
            phase = session_data.get('phase', 'unknown')
            self.log_test("Get Session State", "PASS", f"Round {current_round}, Phase: {phase}")
            return session_data
        else:
            self.log_test("Get Session State", "FAIL", f"Status: {response['status_code']}")
            return {}
    
    def advance_to_next_round(self) -> bool:
        """Advance to next round"""
        params = {"club_name": self.club_name}
        response = self.make_request("POST", "/session/next-round", params=params)
        if response["success"]:
            new_round = response["data"].get('round', 0)
            self.log_test("Advance to Next Round", "PASS", f"Advanced to round {new_round}")
            return True
        else:
            self.log_test("Advance to Next Round", "FAIL", f"Status: {response['status_code']}")
            return False
    
    def verify_rating_updates(self) -> bool:
        """Verify that player ratings have been updated after scoring matches"""
        current_players = self.get_players()
        
        rating_changes_found = 0
        wins_updates_found = 0
        losses_updates_found = 0
        matches_played_updates = 0
        recent_form_updates = 0
        
        print("\n📊 RATING SYSTEM VERIFICATION:")
        print("=" * 60)
        
        for player in current_players:
            if not player.get('isActive', False):
                continue
                
            player_id = player['id']
            if player_id not in self.initial_player_data:
                continue
            
            initial = self.initial_player_data[player_id]
            current_rating = player['rating']
            current_wins = player['wins']
            current_losses = player['losses']
            current_matches = player['matchesPlayed']
            current_form = player['recentForm']
            
            # Check for changes
            rating_changed = abs(current_rating - initial['rating']) > 0.01
            wins_changed = current_wins != initial['wins']
            losses_changed = current_losses != initial['losses']
            matches_changed = current_matches != initial['matchesPlayed']
            form_changed = len(current_form) != len(initial['recentForm'])
            
            if rating_changed or wins_changed or losses_changed or matches_changed or form_changed:
                print(f"\n🏓 {player['name']}:")
                print(f"   Rating: {initial['rating']:.2f} → {current_rating:.2f} " +
                      f"({'✅' if rating_changed else '❌'})")
                print(f"   Wins: {initial['wins']} → {current_wins} " +
                      f"({'✅' if wins_changed else '❌'})")
                print(f"   Losses: {initial['losses']} → {current_losses} " +
                      f"({'✅' if losses_changed else '❌'})")
                print(f"   Matches: {initial['matchesPlayed']} → {current_matches} " +
                      f"({'✅' if matches_changed else '❌'})")
                print(f"   Recent Form: {initial['recentForm']} → {current_form} " +
                      f"({'✅' if form_changed else '❌'})")
            
            if rating_changed:
                rating_changes_found += 1
            if wins_changed:
                wins_updates_found += 1
            if losses_changed:
                losses_updates_found += 1
            if matches_changed:
                matches_played_updates += 1
            if form_changed:
                recent_form_updates += 1
        
        print(f"\n📈 SUMMARY:")
        print(f"   Players with rating changes: {rating_changes_found}")
        print(f"   Players with wins updates: {wins_updates_found}")
        print(f"   Players with losses updates: {losses_updates_found}")
        print(f"   Players with matches played updates: {matches_played_updates}")
        print(f"   Players with recent form updates: {recent_form_updates}")
        
        # Rating system is working if we see updates in key metrics
        rating_system_working = (rating_changes_found > 0 and 
                               matches_played_updates > 0 and
                               (wins_updates_found > 0 or losses_updates_found > 0))
        
        self.log_test("Rating System Updates", "PASS" if rating_system_working else "FAIL",
                      f"Found {rating_changes_found} rating changes, {matches_played_updates} match updates")
        
        return rating_system_working
    
    def test_rating_system_updates(self) -> bool:
        """Test 1: Rating System Updates"""
        print("\n🎯 TEST 1: RATING SYSTEM UPDATES")
        print("=" * 50)
        
        # Step 1: Record initial player stats
        self.record_initial_player_stats()
        
        # Step 2: Generate Round 1 matches
        if not self.generate_round1_matches():
            return False
        
        # Step 3: Start the session
        if not self.start_session():
            return False
        
        # Step 4: Get matches and save scores for 2-3 matches
        matches = self.get_matches()
        if not matches:
            self.log_test("Test 1 - Get Matches", "FAIL", "No matches found")
            return False
        
        # Score first 3 matches with realistic scores
        test_scores = [(11, 9), (11, 7), (8, 11)]
        scored_matches = 0
        
        for i, match in enumerate(matches[:3]):
            if i >= len(test_scores):
                break
            score_a, score_b = test_scores[i]
            if self.save_match_score(match['id'], score_a, score_b):
                scored_matches += 1
        
        if scored_matches == 0:
            self.log_test("Test 1 - Score Matches", "FAIL", "No matches scored successfully")
            return False
        
        self.log_test("Test 1 - Score Matches", "PASS", f"Scored {scored_matches} matches")
        
        # Step 5: Verify rating updates
        return self.verify_rating_updates()
    
    def test_next_round_generation(self) -> bool:
        """Test 2: Next Round Generation"""
        print("\n🎯 TEST 2: NEXT ROUND GENERATION")
        print("=" * 50)
        
        # Ensure we have Round 1 matches with scores
        matches = self.get_matches()
        round1_matches = [m for m in matches if m.get('roundIndex') == 1]
        
        if not round1_matches:
            self.log_test("Test 2 - Round 1 Check", "FAIL", "No Round 1 matches found")
            return False
        
        # Check if matches have scores
        scored_matches = [m for m in round1_matches if m.get('scoreA') is not None]
        if len(scored_matches) == 0:
            self.log_test("Test 2 - Scored Matches Check", "FAIL", "No scored matches in Round 1")
            return False
        
        self.log_test("Test 2 - Round 1 Check", "PASS", 
                     f"Found {len(round1_matches)} Round 1 matches, {len(scored_matches)} scored")
        
        # Advance to Round 2
        if not self.advance_to_next_round():
            return False
        
        # Verify session is now in Round 2
        session_state = self.get_session_state()
        current_round = session_state.get('currentRound', 0)
        
        if current_round != 2:
            self.log_test("Test 2 - Round Check", "FAIL", 
                          f"Expected round 2, got round {current_round}")
            return False
        
        # Get matches and check for Round 2 matches
        all_matches = self.get_matches()
        round2_matches = [m for m in all_matches if m.get('roundIndex') == 2]
        
        if not round2_matches:
            self.log_test("Test 2 - Round 2 Matches", "FAIL", "No Round 2 matches generated")
            return False
        
        # Verify Round 2 matches have proper structure
        valid_matches = 0
        for match in round2_matches:
            if (match.get('teamA') and match.get('teamB') and 
                match.get('courtIndex') is not None and
                match.get('roundIndex') == 2):
                valid_matches += 1
        
        success = valid_matches > 0
        self.log_test("Test 2 - Round 2 Matches", "PASS" if success else "FAIL",
                     f"Generated {len(round2_matches)} Round 2 matches, {valid_matches} valid")
        
        # Verify session phase
        phase = session_state.get('phase', 'unknown')
        phase_correct = phase == 'ready'
        self.log_test("Test 2 - Session Phase", "PASS" if phase_correct else "FAIL", f"Phase: {phase}")
        
        return success and phase_correct
    
    def test_multi_round_flow(self) -> bool:
        """Test 3: Multi-Round Flow"""
        print("\n🎯 TEST 3: MULTI-ROUND FLOW")
        print("=" * 50)
        
        # Record initial stats for accumulation tracking
        initial_players = self.get_players()
        initial_stats = {}
        for player in initial_players:
            if player.get('isActive', False):
                initial_stats[player['id']] = {
                    'rating': player['rating'],
                    'wins': player['wins'],
                    'losses': player['losses'],
                    'matchesPlayed': player['matchesPlayed']
                }
        
        # Get current session state
        session_state = self.get_session_state()
        starting_round = session_state.get('currentRound', 1)
        
        self.log_test("Test 3 - Initial State", "PASS", f"Starting from round {starting_round}")
        
        # If we're not in Round 2 yet, we need to complete Round 1 first
        if starting_round < 2:
            # Score any unscored Round 1 matches
            matches = self.get_matches()
            round1_matches = [m for m in matches if m.get('roundIndex') == 1 and m.get('scoreA') is None]
            
            for match in round1_matches[:2]:  # Score a couple more matches
                self.save_match_score(match['id'], 11, 8)
            
            # Advance to Round 2
            if not self.advance_to_next_round():
                return False
        
        # Now we should be in Round 2 - score some Round 2 matches
        matches = self.get_matches()
        round2_matches = [m for m in matches if m.get('roundIndex') == 2]
        
        if not round2_matches:
            self.log_test("Test 3 - Round 2 Matches", "FAIL", "No Round 2 matches found")
            return False
        
        # Score Round 2 matches
        scored_r2 = 0
        for match in round2_matches[:2]:
            if self.save_match_score(match['id'], 11, 6):
                scored_r2 += 1
        
        self.log_test("Test 3 - Score Round 2", "PASS" if scored_r2 > 0 else "FAIL", 
                     f"Scored {scored_r2} Round 2 matches")
        
        # Advance to Round 3
        if not self.advance_to_next_round():
            return False
        
        # Verify Round 3 generation
        session_state = self.get_session_state()
        current_round = session_state.get('currentRound', 0)
        
        if current_round != 3:
            self.log_test("Test 3 - Round 3 Check", "FAIL", 
                          f"Expected round 3, got round {current_round}")
            return False
        
        # Check for Round 3 matches
        all_matches = self.get_matches()
        round3_matches = [m for m in all_matches if m.get('roundIndex') == 3]
        
        round3_success = len(round3_matches) > 0
        self.log_test("Test 3 - Round 3 Generation", "PASS" if round3_success else "FAIL",
                     f"Generated {len(round3_matches)} Round 3 matches")
        
        # Verify rating accumulation across rounds
        final_players = self.get_players()
        accumulation_verified = 0
        
        print("\n📊 MULTI-ROUND ACCUMULATION VERIFICATION:")
        for player in final_players:
            if not player.get('isActive', False):
                continue
                
            player_id = player['id']
            if player_id not in initial_stats:
                continue
            
            initial = initial_stats[player_id]
            final_matches = player['matchesPlayed']
            final_rating = player['rating']
            
            matches_increased = final_matches > initial['matchesPlayed']
            rating_changed = abs(final_rating - initial['rating']) > 0.01
            
            if matches_increased or rating_changed:
                print(f"   {player['name']}: Matches {initial['matchesPlayed']}→{final_matches}, " +
                      f"Rating {initial['rating']:.2f}→{final_rating:.2f}")
                accumulation_verified += 1
        
        accumulation_success = accumulation_verified > 0
        self.log_test("Test 3 - Stats Accumulation", "PASS" if accumulation_success else "FAIL",
                     f"{accumulation_verified} players show stat accumulation")
        
        return round3_success and accumulation_success
    
    def run_critical_bug_fix_tests(self):
        """Run all critical bug fix verification tests"""
        print("🚀 COURTCHIME CRITICAL BUG FIXES VERIFICATION")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"Club: {self.club_name}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Authenticate first
        if not self.authenticate_club():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run the three critical tests
        test1_result = self.test_rating_system_updates()
        test2_result = self.test_next_round_generation()
        test3_result = self.test_multi_round_flow()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 CRITICAL BUG FIXES VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['status'] == 'PASS')
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 CRITICAL TESTS SUMMARY:")
        print(f"✅ Test 1 - Rating System Updates: {'PASS' if test1_result else 'FAIL'}")
        print(f"✅ Test 2 - Next Round Generation: {'PASS' if test2_result else 'FAIL'}")
        print(f"✅ Test 3 - Multi-Round Flow: {'PASS' if test3_result else 'FAIL'}")
        
        all_critical_passed = test1_result and test2_result and test3_result
        
        print(f"\n🏆 OVERALL RESULT: {'ALL CRITICAL FIXES VERIFIED ✅' if all_critical_passed else 'CRITICAL ISSUES REMAIN ❌'}")
        
        return all_critical_passed

if __name__ == "__main__":
    tester = CourtChimeBackendTester()
    success = tester.run_critical_bug_fix_tests()
    
    if success:
        print("\n🎉 CRITICAL BUG FIX TESTING COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️ CRITICAL BUG FIX TESTING COMPLETED WITH ISSUES")