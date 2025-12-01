#!/usr/bin/env python3
"""
CourtChime Backend Comprehensive End-to-End Testing
Test Focus: Complete Session Flow as requested in review
"""

import requests
import json
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

class CourtChimeBackendTester:
    def __init__(self):
        self.base_url = "https://courtchime.preview.emergentagent.com/api"
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
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self) -> bool:
        """Authenticate with the club"""
        try:
            login_data = {
                "club_name": CLUB_NAME,
                "access_code": ACCESS_CODE
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Club Authentication", True, f"Authenticated as {data.get('club_name')}")
                return True
            else:
                self.log_test("Club Authentication", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Club Authentication", False, f"Error: {str(e)}")
            return False
    
    def get_active_players(self) -> List[Dict]:
        """Get all active players"""
        try:
            response = self.session.get(f"{BACKEND_URL}/players", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                players = response.json()
                active_players = [p for p in players if p.get('isActive', True)]
                self.players = active_players
                self.log_test("Get Active Players", True, f"Found {len(active_players)} active players")
                return active_players
            else:
                self.log_test("Get Active Players", False, f"Status: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Active Players", False, f"Error: {str(e)}")
            return []
    
    def generate_matches(self) -> bool:
        """Generate initial matches"""
        try:
            response = self.session.post(f"{BACKEND_URL}/session/generate-matches", 
                                       params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                self.log_test("Generate Matches", True, "Generated matches successfully")
                return True
            else:
                error_text = response.text
                self.log_test("Generate Matches", False, f"Status {response.status_code}: {error_text}")
                return False
        except Exception as e:
            self.log_test("Generate Matches", False, f"Error: {str(e)}")
            return False
    
    def get_matches(self) -> List[Dict]:
        """Get current matches"""
        try:
            response = self.session.get(f"{BACKEND_URL}/matches", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                matches = response.json()
                self.log_test("Get Matches", True, f"Retrieved {len(matches)} matches")
                return matches
            else:
                error_text = response.text
                self.log_test("Get Matches", False, f"Status {response.status_code}: {error_text}")
                return []
        except Exception as e:
            self.log_test("Get Matches", False, f"Error: {str(e)}")
            return []
    
    def update_match_teams(self, match_id: str, team_a: List[str], team_b: List[str]) -> bool:
        """Update match teams via PUT endpoint"""
        try:
            update_data = {
                "teamA": team_a,
                "teamB": team_b
            }
            
            response = self.session.put(f"{BACKEND_URL}/matches/{match_id}", 
                                      params={"club_name": CLUB_NAME}, 
                                      json=update_data)
            if response.status_code == 200:
                self.log_test("Update Match Teams", True, f"Updated match {match_id[:8]}...")
                return True
            else:
                error_text = response.text
                self.log_test("Update Match Teams", False, f"Status {response.status_code}: {error_text}")
                return False
        except Exception as e:
            self.log_test("Update Match Teams", False, f"Error: {str(e)}")
            return False
    
    def start_session(self) -> bool:
        """Start the session (ready -> play)"""
        try:
            response = self.session.post(f"{BACKEND_URL}/session/start", 
                                       params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                self.log_test("Start Session", True, "Session started successfully")
                return True
            else:
                error_text = response.text
                self.log_test("Start Session", False, f"Status {response.status_code}: {error_text}")
                return False
        except Exception as e:
            self.log_test("Start Session", False, f"Error: {str(e)}")
            return False
    
    def get_session_state(self) -> Optional[Dict]:
        """Get current session state"""
        try:
            response = self.session.get(f"{BACKEND_URL}/session", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                session_data = response.json()
                self.log_test("Get Session State", True, f"Phase: {session_data.get('phase', 'unknown')}")
                return session_data
            else:
                error_text = response.text
                self.log_test("Get Session State", False, f"Status {response.status_code}: {error_text}")
                return None
        except Exception as e:
            self.log_test("Get Session State", False, f"Error: {str(e)}")
            return None
    
    def record_original_teams(self, matches: List[Dict]):
        """Record original team assignments"""
        self.original_teams = {}
        for match in matches:
            self.original_teams[match['id']] = {
                'teamA': match['teamA'].copy(),
                'teamB': match['teamB'].copy()
            }
        self.log_test("Record Original Teams", True, f"Recorded teams for {len(matches)} matches")
    
    def create_swap_scenario(self, matches: List[Dict]) -> Dict[str, Any]:
        """Create a realistic player swap scenario"""
        if len(matches) < 2:
            self.log_test("Create Swap Scenario", False, "Need at least 2 matches for swap scenario")
            return None
            
        # Find two matches to swap players between
        match1 = matches[0]
        match2 = matches[1] if len(matches) > 1 else matches[0]
        
        # Create swap: Take one player from match1 teamA and swap with one from match2 teamA
        if len(match1['teamA']) > 0 and len(match2['teamA']) > 0:
            player1_id = match1['teamA'][0]
            player2_id = match2['teamA'][0]
            
            # Find player names for logging
            player1_name = next((p['name'] for p in self.players if p['id'] == player1_id), "Unknown")
            player2_name = next((p['name'] for p in self.players if p['id'] == player2_id), "Unknown")
            
            # Create new team assignments
            new_match1_teamA = match1['teamA'].copy()
            new_match2_teamA = match2['teamA'].copy()
            
            # Swap the players
            new_match1_teamA[0] = player2_id
            new_match2_teamA[0] = player1_id
            
            swap_scenario = {
                'match1': {
                    'id': match1['id'],
                    'original_teamA': match1['teamA'].copy(),
                    'original_teamB': match1['teamB'].copy(),
                    'new_teamA': new_match1_teamA,
                    'new_teamB': match1['teamB'].copy()
                },
                'match2': {
                    'id': match2['id'],
                    'original_teamA': match2['teamA'].copy(),
                    'original_teamB': match2['teamB'].copy(),
                    'new_teamA': new_match2_teamA,
                    'new_teamB': match2['teamB'].copy()
                },
                'swapped_players': {
                    'player1': {'id': player1_id, 'name': player1_name},
                    'player2': {'id': player2_id, 'name': player2_name}
                }
            }
            
            self.log_test("Create Swap Scenario", True, 
                         f"Swapping {player1_name} ↔ {player2_name} between matches")
            return swap_scenario
            
        self.log_test("Create Swap Scenario", False, "Could not create valid swap scenario")
        return None
    
    def execute_player_swaps(self, swap_scenario: Dict[str, Any]) -> bool:
        """Execute the player swaps via API"""
        try:
            # Update match 1
            success1 = self.update_match_teams(
                swap_scenario['match1']['id'],
                swap_scenario['match1']['new_teamA'],
                swap_scenario['match1']['new_teamB']
            )
            
            # Update match 2 (if different from match 1)
            success2 = True
            if swap_scenario['match1']['id'] != swap_scenario['match2']['id']:
                success2 = self.update_match_teams(
                    swap_scenario['match2']['id'],
                    swap_scenario['match2']['new_teamA'],
                    swap_scenario['match2']['new_teamB']
                )
            
            if success1 and success2:
                # Record swapped teams for verification
                self.swapped_teams[swap_scenario['match1']['id']] = {
                    'teamA': swap_scenario['match1']['new_teamA'],
                    'teamB': swap_scenario['match1']['new_teamB']
                }
                if swap_scenario['match1']['id'] != swap_scenario['match2']['id']:
                    self.swapped_teams[swap_scenario['match2']['id']] = {
                        'teamA': swap_scenario['match2']['new_teamA'],
                        'teamB': swap_scenario['match2']['new_teamB']
                    }
                
                self.log_test("Execute Player Swaps", True, "All swaps executed successfully")
                return True
            else:
                self.log_test("Execute Player Swaps", False, "One or more swaps failed")
                return False
                
        except Exception as e:
            self.log_test("Execute Player Swaps", False, f"Error: {str(e)}")
            return False
    
    def verify_swaps_persisted(self, matches: List[Dict]) -> bool:
        """Verify that swaps are still present in retrieved matches"""
        try:
            all_swaps_verified = True
            
            for match in matches:
                match_id = match['id']
                if match_id in self.swapped_teams:
                    expected_teamA = self.swapped_teams[match_id]['teamA']
                    expected_teamB = self.swapped_teams[match_id]['teamB']
                    actual_teamA = match['teamA']
                    actual_teamB = match['teamB']
                    
                    if actual_teamA != expected_teamA or actual_teamB != expected_teamB:
                        self.log_test("Verify Swaps Persisted", False, 
                                     f"Match {match_id[:8]}... teams don't match expected swapped teams")
                        all_swaps_verified = False
                        break
            
            if all_swaps_verified:
                self.log_test("Verify Swaps Persisted", True, 
                             f"All {len(self.swapped_teams)} swapped matches verified")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test("Verify Swaps Persisted", False, f"Error: {str(e)}")
            return False
    
    def verify_no_reset_to_original(self, matches: List[Dict]) -> bool:
        """Verify matches haven't been reset to original teams"""
        try:
            reset_detected = False
            
            for match in matches:
                match_id = match['id']
                if match_id in self.swapped_teams and match_id in self.original_teams:
                    # Check if current teams match original (which would be bad)
                    current_teamA = match['teamA']
                    current_teamB = match['teamB']
                    original_teamA = self.original_teams[match_id]['teamA']
                    original_teamB = self.original_teams[match_id]['teamB']
                    
                    if current_teamA == original_teamA and current_teamB == original_teamB:
                        self.log_test("Verify No Reset to Original", False, 
                                     f"Match {match_id[:8]}... was reset to original teams")
                        reset_detected = True
                        break
            
            if not reset_detected:
                self.log_test("Verify No Reset to Original", True, 
                             "No matches were reset to original teams")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test("Verify No Reset to Original", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_swaps(self, matches: List[Dict]) -> bool:
        """Test multiple consecutive swaps on the same match"""
        if len(matches) < 1:
            self.log_test("Multiple Swaps Test", False, "No matches available for multiple swap test")
            return False
            
        # Try swapping the same match multiple times
        match = matches[0]
        
        # First swap - reverse team A order if possible
        if len(match['teamA']) >= 2:
            new_teamA = [match['teamA'][1], match['teamA'][0]]
            if len(match['teamA']) > 2:
                new_teamA.extend(match['teamA'][2:])
            
            success1 = self.update_match_teams(match['id'], new_teamA, match['teamB'])
            
            if success1:
                # Second swap - swap first player with a different player if available
                if len(self.players) > len(match['teamA']) + len(match['teamB']):
                    # Find a player not in this match
                    players_in_match = set(match['teamA'] + match['teamB'])
                    available_players = [p for p in self.players if p['id'] not in players_in_match]
                    
                    if available_players:
                        # Swap first player of teamA with an available player
                        final_teamA = new_teamA.copy()
                        final_teamA[0] = available_players[0]['id']
                        
                        success2 = self.update_match_teams(match['id'], final_teamA, match['teamB'])
                        
                        if success2:
                            self.log_test("Multiple Swaps Test", True, "Multiple consecutive swaps successful")
                            return True
                        else:
                            self.log_test("Multiple Swaps Test", False, "Second swap failed")
                            return False
                    else:
                        self.log_test("Multiple Swaps Test", False, "No available players for second swap")
                        return False
                else:
                    self.log_test("Multiple Swaps Test", False, "Not enough players for multiple swaps")
                    return False
            else:
                self.log_test("Multiple Swaps Test", False, "First swap failed")
                return False
        else:
            self.log_test("Multiple Swaps Test", False, "Not enough players in team for swap test")
            return False
    
    def run_comprehensive_test(self):
        """Run the comprehensive player swap persistence test"""
        print("🎯 STARTING COMPREHENSIVE PLAYER SWAP PERSISTENCE TEST")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - aborting test")
            return
        
        # Step 2: Get active players
        players = self.get_active_players()
        if len(players) < 8:
            self.log_test("Player Count Check", False, f"Need at least 8 players, found {len(players)}")
            return
        else:
            self.log_test("Player Count Check", True, f"Found {len(players)} active players")
        
        # Step 3: Generate initial matches
        if not self.generate_matches():
            print("❌ Match generation failed - aborting test")
            return
        
        # Step 4: Get initial matches and record original teams
        initial_matches = self.get_matches()
        if len(initial_matches) < 2:
            self.log_test("Initial Match Count", False, f"Need at least 2 matches, found {len(initial_matches)}")
            return
        else:
            self.log_test("Initial Match Count", True, f"Found {len(initial_matches)} matches")
        
        self.record_original_teams(initial_matches)
        
        # Step 5: Create and execute swap scenario
        swap_scenario = self.create_swap_scenario(initial_matches)
        if not swap_scenario:
            print("❌ Could not create swap scenario - aborting test")
            return
        
        if not self.execute_player_swaps(swap_scenario):
            print("❌ Player swaps failed - aborting test")
            return
        
        # Step 6: Verify swaps are saved in database
        matches_after_swap = self.get_matches()
        if not self.verify_swaps_persisted(matches_after_swap):
            print("❌ Swaps not persisted - critical failure")
            return
        
        # Step 7: Start session (ready -> play)
        if not self.start_session():
            print("❌ Session start failed - aborting test")
            return
        
        # Step 8: Verify session phase changed
        session_state = self.get_session_state()
        if session_state and session_state.get('phase') == 'play':
            self.log_test("Session Phase Verification", True, "Session phase is 'play'")
        else:
            self.log_test("Session Phase Verification", False, 
                         f"Expected 'play', got '{session_state.get('phase') if session_state else 'unknown'}'")
        
        # Step 9: CRITICAL TEST - Get matches after session start
        matches_after_session_start = self.get_matches()
        
        # Step 10: Verify swaps still persist (not reset)
        if not self.verify_swaps_persisted(matches_after_session_start):
            print("❌ CRITICAL FAILURE: Swaps lost after session start")
            return
        
        # Step 11: Verify no reset to original teams
        if not self.verify_no_reset_to_original(matches_after_session_start):
            print("❌ CRITICAL FAILURE: Matches reset to original teams")
            return
        
        # Step 12: Edge case testing - Multiple swaps
        self.test_multiple_swaps(matches_after_session_start)
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST COMPLETED")
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len([t for t in self.test_results if not t['success']])
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['test']}: {test['details']}")
        
        # Critical test results
        critical_tests = [
            "Update Match Teams",
            "Verify Swaps Persisted", 
            "Verify No Reset to Original",
            "Start Session"
        ]
        
        critical_failures = [t for t in self.test_results 
                           if t['test'] in critical_tests and not t['success']]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES DETECTED:")
            for test in critical_failures:
                print(f"  - {test['test']}: {test['details']}")
            print(f"\n❌ PLAYER SWAP PERSISTENCE: FAILED")
        else:
            print(f"\n✅ PLAYER SWAP PERSISTENCE: WORKING CORRECTLY")

def main():
    """Main test execution"""
    tester = PlayerSwapPersistenceTester()
    tester.run_comprehensive_test()
    
    # Return exit code based on test results
    critical_tests = [
        "Update Match Teams",
        "Verify Swaps Persisted", 
        "Verify No Reset to Original",
        "Start Session"
    ]
    
    critical_failures = [t for t in tester.test_results 
                       if t['test'] in critical_tests and not t['success']]
    
    sys.exit(0 if len(critical_failures) == 0 else 1)

if __name__ == "__main__":
    main()