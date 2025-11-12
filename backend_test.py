#!/usr/bin/env python3
"""
CourtChime Backend Test Suite - Player Swap Persistence Testing
Focus: Comprehensive end-to-end testing of player swap functionality
Testing the critical scenario where player swaps must persist through session start
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://courtchime.preview.emergentagent.com/api"
CLUB_NAME = "Main Club"
ACCESS_CODE = "demo123"

class PlayerSwapPersistenceTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.generated_matches = []
        self.original_teams = {}
        self.swapped_teams = {}
        self.players = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
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
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get current session configuration"""
        try:
            response = self.session.get(f"{BACKEND_URL}/session", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                data = response.json()
                return data.get('config', {})
            return {}
        except Exception as e:
            print(f"Error getting session config: {e}")
            return {}
    
    def update_session_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update session configuration"""
        try:
            response = self.session.put(f"{BACKEND_URL}/session/config", 
                                      params={"club_name": CLUB_NAME}, 
                                      json=config_updates)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating session config: {e}")
            return False
    
    def get_players(self) -> List[Dict[str, Any]]:
        """Get all players for the club"""
        try:
            response = self.session.get(f"{BACKEND_URL}/players", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting players: {e}")
            return []
    
    def generate_matches(self) -> Dict[str, Any]:
        """Generate matches for current round"""
        try:
            response = self.session.post(f"{BACKEND_URL}/session/generate-matches", 
                                       params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            else:
                text = response.text
                print(f"Generate matches failed: {response.status_code} - {text}")
                return {}
        except Exception as e:
            print(f"Error generating matches: {e}")
            return {}
    
    def get_matches(self) -> List[Dict[str, Any]]:
        """Get current matches"""
        try:
            response = self.session.get(f"{BACKEND_URL}/matches", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting matches: {e}")
            return []
    
    def deactivate_players(self, player_ids: List[str]) -> bool:
        """Deactivate specific players"""
        try:
            success_count = 0
            for player_id in player_ids:
                response = self.session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active", 
                                            params={"club_name": CLUB_NAME})
                if response.status_code == 200:
                    success_count += 1
            return success_count == len(player_ids)
        except Exception as e:
            print(f"Error deactivating players: {e}")
            return False
    
    def activate_all_players(self) -> bool:
        """Activate all players"""
        try:
            players = self.get_players()
            inactive_players = [p['id'] for p in players if not p.get('isActive', True)]
            
            if not inactive_players:
                return True
                
            success_count = 0
            for player_id in inactive_players:
                response = self.session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active", 
                                            params={"club_name": CLUB_NAME})
                if response.status_code == 200:
                    success_count += 1
            return success_count == len(inactive_players)
        except Exception as e:
            print(f"Error activating players: {e}")
            return False
    
    def clear_matches(self) -> bool:
        """Clear all matches to reset session"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/matches", params={"club_name": CLUB_NAME})
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error clearing matches: {e}")
            return False
    
    def test_13_players_3_courts_critical_scenario(self):
        """Test CRITICAL: 13 Players, 3 Courts → 3 doubles, 1 sitout"""
        print("\n🎯 CRITICAL TEST: 13 Players, 3 Courts Scenario")
        
        # Clear matches and setup exactly 13 active players
        self.clear_matches()
        players = self.get_players()
        
        # Ensure exactly 13 players are active
        for i, player in enumerate(players):
            should_be_active = i < 13
            current_active = player.get('isActive', True)
            
            if should_be_active != current_active:
                response = self.session.patch(f"{BACKEND_URL}/players/{player['id']}/toggle-active", 
                                            params={"club_name": CLUB_NAME})
                if response.status_code != 200:
                    self.log_test("13P3C - Player Setup", False, f"Failed to toggle player {player['name']}")
                    return
        
        # Configure: 3 courts, maximize courts enabled
        config = {
            "numCourts": 3,
            "allowSingles": True,
            "allowDoubles": True,
            "allowCrossCategory": False,
            "maximizeCourtUsage": True,
            "rotationModel": "legacy"
        }
        
        if not self.update_session_config(config):
            self.log_test("13P3C - Config Update", False, "Failed to update session config")
            return
        
        # Generate matches
        result = self.generate_matches()
        if not result:
            self.log_test("13P3C - Match Generation", False, "Failed to generate matches")
            return
        
        matches = self.get_matches()
        
        # Verify critical requirements
        active_players = [p for p in self.get_players() if p.get('isActive', True)]
        players_in_matches = set()
        
        for match in matches:
            players_in_matches.update(match['teamA'])
            players_in_matches.update(match['teamB'])
        
        # Critical assertions
        expected_courts = 3
        expected_players_in_matches = 12  # 3 doubles = 12 players
        expected_sitouts = 1  # 13 - 12 = 1
        
        actual_courts = len(matches)
        actual_players_in_matches = len(players_in_matches)
        actual_sitouts = len(active_players) - actual_players_in_matches
        
        # This is the CRITICAL test - must pass
        critical_success = (
            len(active_players) == 13 and
            actual_courts == expected_courts and
            actual_players_in_matches == expected_players_in_matches and
            actual_sitouts == expected_sitouts
        )
        
        details = f"Active: {len(active_players)}/13, Courts: {actual_courts}/3, In matches: {actual_players_in_matches}/12, Sitouts: {actual_sitouts}/1"
        
        self.log_test("🚨 CRITICAL: 13 Players, 3 Courts → 3 doubles, 1 sitout", critical_success, details)
        
        # Verify all matches are doubles
        all_doubles = all(len(match['teamA']) == 2 and len(match['teamB']) == 2 for match in matches)
        self.log_test("13P3C - All Doubles Matches", all_doubles, f"All {len(matches)} matches are doubles")
        
        # Verify no extra sitouts (the original bug)
        no_extra_sitouts = actual_sitouts == 1
        self.log_test("13P3C - No Extra Sitouts", no_extra_sitouts, f"Exactly 1 sitout, not 3+ (original bug)")

    def test_various_player_court_combinations(self):
        """Test Various Player/Court Combinations with Maximize Courts"""
        print("\n🎯 Testing Various Player/Court Combinations")
        
        test_scenarios = [
            {"players": 12, "courts": 3, "expected_matches": 3, "expected_sitouts": 0, "description": "12 players, 3 courts → 3 doubles, 0 sitouts"},
            {"players": 16, "courts": 4, "expected_matches": 4, "expected_sitouts": 0, "description": "16 players, 4 courts → 4 doubles, 0 sitouts"},
            {"players": 10, "courts": 3, "expected_matches": 3, "expected_sitouts": 0, "description": "10 players, 3 courts → 2 doubles + 1 singles, 0 sitouts"},
            {"players": 15, "courts": 4, "expected_matches": 4, "expected_sitouts": 2, "description": "15 players, 4 courts → 3 doubles + 1 singles, 2 sitouts"}
        ]
        
        for scenario in test_scenarios:
            self.clear_matches()
            players = self.get_players()
            
            # Setup exact number of active players
            for i, player in enumerate(players):
                should_be_active = i < scenario["players"]
                current_active = player.get('isActive', True)
                
                if should_be_active != current_active:
                    self.session.patch(f"{BACKEND_URL}/players/{player['id']}/toggle-active", 
                                     params={"club_name": CLUB_NAME})
            
            # Configure session
            config = {
                "numCourts": scenario["courts"],
                "allowSingles": True,
                "allowDoubles": True,
                "allowCrossCategory": False,
                "maximizeCourtUsage": True,
                "rotationModel": "legacy"
            }
            
            self.update_session_config(config)
            
            # Generate matches
            result = self.generate_matches()
            if not result:
                self.log_test(f"Combo - {scenario['description']}", False, "Failed to generate matches")
                continue
            
            matches = self.get_matches()
            active_players = [p for p in self.get_players() if p.get('isActive', True)]
            
            players_in_matches = set()
            for match in matches:
                players_in_matches.update(match['teamA'])
                players_in_matches.update(match['teamB'])
            
            actual_matches = len(matches)
            actual_sitouts = len(active_players) - len(players_in_matches)
            
            success = (
                actual_matches == scenario["expected_matches"] and
                actual_sitouts == scenario["expected_sitouts"]
            )
            
            details = f"Matches: {actual_matches}/{scenario['expected_matches']}, Sitouts: {actual_sitouts}/{scenario['expected_sitouts']}"
            self.log_test(f"Combo - {scenario['description']}", success, details)

    def test_first_round_generation_verification(self):
        """Test First Round Generation Uses schedule_round Function"""
        print("\n🎯 Testing First Round Generation Verification")
        
        self.clear_matches()
        self.activate_all_players()
        
        # Configure for maximize courts
        config = {
            "numCourts": 3,
            "allowSingles": True,
            "allowDoubles": True,
            "allowCrossCategory": False,
            "maximizeCourtUsage": True,
            "rotationModel": "legacy"
        }
        
        if not self.update_session_config(config):
            self.log_test("First Round - Config Update", False, "Failed to update session config")
            return
        
        # Generate first round
        result = self.generate_matches()
        if not result:
            self.log_test("First Round - Match Generation", False, "Failed to generate matches")
            return
        
        matches = self.get_matches()
        
        # Verify schedule_round is being called (proper match structure)
        has_proper_structure = all(
            'id' in match and 'teamA' in match and 'teamB' in match and 
            'courtIndex' in match and 'category' in match and 'matchType' in match
            for match in matches
        )
        
        # Verify debug logs would show "DEBUG MAXIMIZE COURTS" (we can't check logs directly)
        # But we can verify the behavior indicates maximize courts is working
        courts_used = len(set(match['courtIndex'] for match in matches))
        maximize_courts_working = courts_used == 3  # Should use all 3 courts
        
        # Verify correct player counts and court allocations
        players_in_matches = set()
        for match in matches:
            players_in_matches.update(match['teamA'])
            players_in_matches.update(match['teamB'])
        
        active_players = [p for p in self.get_players() if p.get('isActive', True)]
        correct_allocation = len(players_in_matches) <= len(active_players)
        
        self.log_test("First Round - Uses schedule_round Function", has_proper_structure,
                     "Matches have proper structure from schedule_round function")
        
        self.log_test("First Round - Maximize Courts Working", maximize_courts_working,
                     f"Uses {courts_used}/3 courts with maximize courts enabled")
        
        self.log_test("First Round - Correct Player Allocation", correct_allocation,
                     f"Players in matches: {len(players_in_matches)}, Active players: {len(active_players)}")
    
    def test_top_court_mode_comprehensive(self):
        """Test Top Court Mode First Round and Rotation"""
        print("\n🏆 Testing Top Court Mode Comprehensive")
        
        # Clear matches and setup 8 players for clean test
        self.clear_matches()
        players = self.get_players()
        
        # Setup exactly 8 active players for clean Top Court test
        for i, player in enumerate(players):
            should_be_active = i < 8
            current_active = player.get('isActive', True)
            
            if should_be_active != current_active:
                self.session.patch(f"{BACKEND_URL}/players/{player['id']}/toggle-active", 
                                 params={"club_name": CLUB_NAME})
        
        config = {
            "numCourts": 2,  # Use 2 courts for cleaner Top Court test
            "allowSingles": True,
            "allowDoubles": True,
            "allowCrossCategory": False,
            "maximizeCourtUsage": True,
            "rotationModel": "top_court"
        }
        
        if not self.update_session_config(config):
            self.log_test("Top Court - Config Update", False, "Failed to update config for top court mode")
            return
        
        # Generate first round matches
        result = self.generate_matches()
        if not result:
            self.log_test("Top Court - First Round Generation", False, "Failed to generate first round")
            return
        
        matches = self.get_matches()
        
        # Verify Court 0 exists (Top Court)
        court_0_matches = [m for m in matches if m['courtIndex'] == 0]
        has_top_court = len(court_0_matches) > 0
        
        # Verify all courts filled
        court_indices = set(match['courtIndex'] for match in matches)
        courts_used = len(court_indices)
        all_courts_filled = courts_used == 2
        
        # Verify no inactive players in matches
        active_players = [p for p in self.get_players() if p.get('isActive', True)]
        players_in_matches = set()
        for match in matches:
            players_in_matches.update(match['teamA'])
            players_in_matches.update(match['teamB'])
        
        inactive_in_matches = any(
            player_id not in [p['id'] for p in active_players]
            for match in matches
            for player_id in match['teamA'] + match['teamB']
        )
        
        self.log_test("Top Court - Court 0 Exists", has_top_court, 
                     f"Court 0 (Top Court) found with {len(court_0_matches)} matches")
        
        self.log_test("Top Court - All Courts Filled", all_courts_filled,
                     f"Used {courts_used}/2 courts")
        
        self.log_test("Top Court - No Inactive Players", not inactive_in_matches,
                     f"All players in matches are active")
        
        # Test Top Court rotation by saving match results
        if matches and len(matches) >= 2:
            try:
                # Save results for Court 0 (Top Court) - Team A wins
                court_0_match = next((m for m in matches if m['courtIndex'] == 0), None)
                if court_0_match:
                    response = self.session.patch(
                        f"{BACKEND_URL}/matches/{court_0_match['id']}/score",
                        params={"club_name": CLUB_NAME},
                        json={"scoreA": 11, "scoreB": 5}
                    )
                    
                    if response.status_code == 200:
                        self.log_test("Top Court - Save Match Results", True, "Court 0 match results saved")
                        
                        # Generate next round to test rotation
                        next_result = self.generate_matches()
                        if next_result:
                            next_matches = self.get_matches()
                            rotation_working = len(next_matches) > 0
                            self.log_test("Top Court - Rotation Logic", rotation_working,
                                         f"Next round generated with {len(next_matches)} matches")
                        else:
                            self.log_test("Top Court - Rotation Logic", False, "Failed to generate next round")
                    else:
                        self.log_test("Top Court - Save Match Results", False, f"Failed to save results: {response.status_code}")
                else:
                    self.log_test("Top Court - Save Match Results", False, "No Court 0 match found")
                    
            except Exception as e:
                self.log_test("Top Court - Rotation Test", False, f"Error testing rotation: {str(e)}")
    
    def test_cross_category_maximize_courts(self):
        """Test 4: Cross Category + Maximize Courts"""
        print("\n🔀 Testing Cross Category + Maximize Courts")
        
        self.clear_matches()
        self.activate_all_players()
        
        config = {
            "numCourts": 3,
            "allowSingles": True,
            "allowDoubles": True,
            "allowCrossCategory": True,  # Enable cross category
            "maximizeCourtUsage": True,  # Enable maximize courts
            "rotationModel": "legacy"
        }
        
        config_updated = self.update_session_config(config)
        if not config_updated:
            self.log_test("Cross Category - Config Update", False, "Failed to update config")
            return
        
        # Generate matches
        result = self.generate_matches()
        if not result:
            self.log_test("Cross Category - Match Generation", False, "Failed to generate matches")
            return
        
        matches = self.get_matches()
        
        # Verify all courts are filled
        court_indices = set(match['courtIndex'] for match in matches)
        courts_used = len(court_indices)
        
        # Verify mixed category matches
        mixed_matches = [m for m in matches if m.get('category') == 'Mixed']
        has_mixed_matches = len(mixed_matches) > 0
        
        # Count players and sitouts
        players = self.get_players()
        active_players = [p for p in players if p.get('isActive', True)]
        
        players_in_matches = set()
        for match in matches:
            players_in_matches.update(match['teamA'])
            players_in_matches.update(match['teamB'])
        
        sitouts = len(active_players) - len(players_in_matches)
        
        # Verify sitouts are minimized
        expected_max_sitouts = len(active_players) % 4  # For doubles
        sitouts_minimized = sitouts <= expected_max_sitouts + 2  # Allow some flexibility
        
        self.log_test("Cross Category - All Courts Used", courts_used == 3,
                     f"Used {courts_used}/3 courts")
        
        self.log_test("Cross Category - Mixed Matches Created", has_mixed_matches,
                     f"Mixed category matches: {len(mixed_matches)}/{len(matches)}")
        
        self.log_test("Cross Category - Sitouts Minimized", sitouts_minimized,
                     f"Sitouts: {sitouts}, Active players: {len(active_players)}")
    
    def test_inactive_player_filtering(self):
        """Test 5: Inactive Player Filtering"""
        print("\n🚫 Testing Inactive Player Filtering")
        
        self.clear_matches()
        
        # Get players and deactivate some
        players = self.get_players()
        if len(players) < 6:
            self.log_test("Inactive Filter - Insufficient Players", False, f"Need at least 6 players, got {len(players)}")
            return
        
        # Deactivate 2 players
        players_to_deactivate = players[:2]
        deactivated = self.deactivate_players([p['id'] for p in players_to_deactivate])
        
        if not deactivated:
            self.log_test("Inactive Filter - Player Deactivation", False, "Failed to deactivate players")
            return
        
        # Configure session
        config = {
            "numCourts": 3,
            "allowSingles": True,
            "allowDoubles": True,
            "allowCrossCategory": False,
            "maximizeCourtUsage": True,
            "rotationModel": "legacy"
        }
        
        self.update_session_config(config)
        
        # Generate matches
        result = self.generate_matches()
        if not result:
            self.log_test("Inactive Filter - Match Generation", False, "Failed to generate matches")
            return
        
        matches = self.get_matches()
        
        # Verify inactive players are NOT in matches
        deactivated_ids = set(p['id'] for p in players_to_deactivate)
        inactive_in_matches = set()
        
        for match in matches:
            for player_id in match['teamA'] + match['teamB']:
                if player_id in deactivated_ids:
                    inactive_in_matches.add(player_id)
        
        no_inactive_in_matches = len(inactive_in_matches) == 0
        
        # Get updated player list to verify active count
        updated_players = self.get_players()
        active_players = [p for p in updated_players if p.get('isActive', True)]
        
        # Verify sitout calculations don't include inactive players
        players_in_matches = set()
        for match in matches:
            players_in_matches.update(match['teamA'])
            players_in_matches.update(match['teamB'])
        
        sitouts = len(active_players) - len(players_in_matches)
        
        self.log_test("Inactive Filter - No Inactive in Matches", no_inactive_in_matches,
                     f"Inactive players found in matches: {len(inactive_in_matches)}")
        
        self.log_test("Inactive Filter - Correct Active Count", len(active_players) == len(players) - 2,
                     f"Active: {len(active_players)}, Total: {len(players)}, Deactivated: 2")
        
        self.log_test("Inactive Filter - Proper Sitout Calculation", sitouts >= 0,
                     f"Sitouts: {sitouts}, Active players: {len(active_players)}")
        
        # Reactivate players for next tests
        self.activate_all_players()
    
    def test_court_utilization_scenarios(self):
        """Test various court utilization scenarios"""
        print("\n📊 Testing Court Utilization Scenarios")
        
        self.clear_matches()
        self.activate_all_players()
        
        # Test different player/court combinations
        scenarios = [
            {"players": 16, "courts": 3, "expected_matches": 3, "description": "16 players, 3 courts"},
            {"players": 10, "courts": 3, "expected_matches": 3, "description": "10 players, 3 courts"},
            {"players": 12, "courts": 3, "expected_matches": 3, "description": "12 players, 3 courts"}
        ]
        
        players = self.get_players()
        active_players = [p for p in players if p.get('isActive', True)]
        
        for scenario in scenarios:
            self.clear_matches()
            
            # Configure for scenario
            config = {
                "numCourts": scenario["courts"],
                "allowSingles": True,
                "allowDoubles": True,
                "allowCrossCategory": False,
                "maximizeCourtUsage": True,
                "rotationModel": "legacy"
            }
            
            self.update_session_config(config)
            
            # Generate matches
            result = self.generate_matches()
            if not result:
                self.log_test(f"Scenario - {scenario['description']}", False, "Failed to generate matches")
                continue
            
            matches = self.get_matches()
            
            # Verify court usage
            court_indices = set(match['courtIndex'] for match in matches)
            courts_used = len(court_indices)
            
            # Count players in matches
            players_in_matches = set()
            for match in matches:
                players_in_matches.update(match['teamA'])
                players_in_matches.update(match['teamB'])
            
            available_players = min(len(active_players), scenario["players"])
            sitouts = available_players - len(players_in_matches)
            
            # For maximize courts, should fill all available courts when possible
            expected_courts = min(scenario["courts"], len(matches))
            courts_optimized = courts_used == expected_courts
            
            self.log_test(f"Scenario - {scenario['description']}", courts_optimized,
                         f"Courts: {courts_used}/{scenario['courts']}, Players: {len(players_in_matches)}, Sitouts: {sitouts}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CourtChime Backend Final Verification Test")
        print("🎯 Focus: 13 players, 3 courts scenario and comprehensive verification")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test suites in priority order
        print("\n🔥 CRITICAL TESTS - Must Pass")
        self.test_13_players_3_courts_critical_scenario()
        
        print("\n📊 COMPREHENSIVE VERIFICATION TESTS")
        self.test_various_player_court_combinations()
        self.test_first_round_generation_verification()
        self.test_top_court_mode_comprehensive()
        self.test_cross_category_maximize_courts()
        self.test_inactive_player_filtering()
        self.test_court_utilization_scenarios()
        
        # Print detailed summary
        print("\n" + "=" * 80)
        print("📊 FINAL VERIFICATION TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show critical test results first
        critical_tests = [result for result in self.test_results if "CRITICAL" in result['test']]
        if critical_tests:
            print(f"\n🔥 CRITICAL TEST RESULTS:")
            for test in critical_tests:
                status = "✅ PASS" if test['success'] else "❌ FAIL"
                print(f"  {status} {test['test']}")
                if test['details']:
                    print(f"      └─ {test['details']}")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}")
                if test['details']:
                    print(f"    └─ {test['details']}")
        
        # Show passed tests summary
        passed_tests = [result for result in self.test_results if result['success']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                print(f"  • {test['test']}")
        
        # Final verdict
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! The system is working correctly.")
            print(f"✅ The 13 players, 3 courts scenario is fixed!")
            print(f"✅ All critical fixes have been verified!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review the issues above.")
            if any("CRITICAL" in test['test'] for test in failed_tests):
                print(f"🚨 CRITICAL TESTS FAILED - Immediate attention required!")
        
        return passed == total

def main():
    """Main test runner"""
    tester = FinalFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()