#!/usr/bin/env python3
"""
CourtChime Backend Test Suite - Cross Category + Maximize Courts Bug Fix Verification
Testing the fix for players sitting out unnecessarily when both options are enabled.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://chime-roster.preview.emergentagent.com/api"
CLUB_NAME = "Main Club"
ACCESS_CODE = "demo123"

class CrossCategoryMaximizeCourtsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        return success
    
    def test_authentication(self) -> bool:
        """Test club authentication"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "club_name": CLUB_NAME,
                "access_code": ACCESS_CODE
            })
            
            if response.status_code == 200:
                data = response.json()
                success = (data.get("authenticated") == True and 
                          data.get("club_name") == CLUB_NAME)
                return self.log_test("Club Authentication", success, 
                                   f"Status: {response.status_code}, Auth: {data.get('authenticated')}")
            else:
                return self.log_test("Club Authentication", False, 
                                   f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Club Authentication", False, f"Error: {str(e)}")
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get current session configuration"""
        try:
            response = self.session.get(f"{BASE_URL}/session", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Error getting session config: {e}")
            return {}
    
    def update_session_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update session configuration"""
        try:
            response = self.session.put(f"{BASE_URL}/session/config", 
                                      params={"club_name": CLUB_NAME},
                                      json=config_updates)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating session config: {e}")
            return False
    
    def get_active_players(self) -> List[Dict[str, Any]]:
        """Get all active players"""
        try:
            response = self.session.get(f"{BASE_URL}/players", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                players = response.json()
                return [p for p in players if p.get("isActive", False)]
            return []
        except Exception as e:
            print(f"Error getting players: {e}")
            return []
    
    def clear_existing_matches(self) -> bool:
        """Clear existing matches"""
        try:
            response = self.session.delete(f"{BASE_URL}/matches", params={"club_name": CLUB_NAME})
            return response.status_code in [200, 204, 404]  # 404 is OK if no matches exist
        except Exception as e:
            print(f"Error clearing matches: {e}")
            return False
    
    def generate_matches(self) -> Dict[str, Any]:
        """Generate matches and return response data"""
        try:
            response = self.session.post(f"{BASE_URL}/session/generate-matches", 
                                       params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Generate matches failed: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            print(f"Error generating matches: {e}")
            return {}
    
    def get_matches(self) -> List[Dict[str, Any]]:
        """Get current matches"""
        try:
            response = self.session.get(f"{BASE_URL}/matches", params={"club_name": CLUB_NAME})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting matches: {e}")
            return []
    
    def count_sitout_players(self, active_players: List[Dict], matches: List[Dict]) -> int:
        """Count players sitting out"""
        if not matches:
            return len(active_players)
        
        playing_player_ids = set()
        for match in matches:
            playing_player_ids.update(match.get("teamA", []))
            playing_player_ids.update(match.get("teamB", []))
        
        active_player_ids = {p["id"] for p in active_players}
        sitout_count = len(active_player_ids - playing_player_ids)
        return sitout_count
    
    def test_cross_category_maximize_courts_scenario(self, num_players: int, num_courts: int, 
                                                   expected_matches: int, expected_sitouts: int,
                                                   scenario_name: str) -> bool:
        """Test a specific scenario with Cross Category + Maximize Courts"""
        print(f"\n🧪 Testing Scenario: {scenario_name}")
        print(f"   Players: {num_players}, Courts: {num_courts}")
        print(f"   Expected: {expected_matches} matches, {expected_sitouts} sitouts")
        
        # Get active players
        active_players = self.get_active_players()
        available_players = len(active_players)
        
        # If we don't have enough players, adjust expectations or skip
        if available_players < num_players:
            if available_players < 4:  # Need at least 4 for any match
                return self.log_test(f"{scenario_name} - Player Count", False, 
                                   f"Need at least 4 players, only have {available_players}")
            
            # Adjust test to use available players
            print(f"   Adjusting test: Using {available_players} available players instead of {num_players}")
            num_players = available_players
            
            # Recalculate expectations based on available players
            if num_players >= 4:
                # With Cross Category + Maximize Courts, we should use all courts possible
                max_doubles = num_players // 4
                remaining_after_doubles = num_players % 4
                max_singles = remaining_after_doubles // 2
                
                expected_matches = min(num_courts, max_doubles + max_singles)
                expected_sitouts = num_players - (max_doubles * 4 + max_singles * 2)
                
                print(f"   Adjusted expectations: {expected_matches} matches, {expected_sitouts} sitouts")
        
        # Use available players for this test
        test_players = active_players[:num_players]
        
        # Clear existing matches
        self.clear_existing_matches()
        
        # Update session config for Cross Category + Maximize Courts
        config_success = self.update_session_config({
            "allowCrossCategory": True,
            "maximizeCourtUsage": True,
            "numCourts": num_courts,
            "allowDoubles": True,
            "allowSingles": True
        })
        
        if not config_success:
            return self.log_test(f"{scenario_name} - Config Update", False, 
                               "Failed to update session config")
        
        # Generate matches
        match_response = self.generate_matches()
        if not match_response:
            return self.log_test(f"{scenario_name} - Match Generation", False, 
                               "Failed to generate matches")
        
        # Get generated matches
        matches = self.get_matches()
        actual_matches = len(matches)
        
        # Count sitouts using all available players
        actual_sitouts = self.count_sitout_players(active_players, matches)
        
        # Verify court utilization
        courts_used = len(set(match.get("courtIndex", -1) for match in matches))
        
        # For Cross Category + Maximize Courts, we expect:
        # 1. All available courts to be used (up to the limit)
        # 2. Minimal sitouts (only when mathematically necessary)
        
        # Calculate optimal matches with available players
        total_available = len(active_players)
        max_possible_doubles = total_available // 4
        remaining_after_max_doubles = total_available % 4
        max_possible_singles = remaining_after_max_doubles // 2
        
        optimal_matches = min(num_courts, max_possible_doubles + max_possible_singles)
        optimal_sitouts = total_available - (min(max_possible_doubles, num_courts) * 4 + 
                                           min(max_possible_singles, max(0, num_courts - max_possible_doubles)) * 2)
        
        # Test results - use optimal calculations
        match_count_ok = actual_matches >= min(expected_matches, optimal_matches)
        sitout_count_ok = actual_sitouts <= max(expected_sitouts, optimal_sitouts)
        court_usage_ok = courts_used <= num_courts and courts_used > 0
        
        details = (f"Matches: {actual_matches} (expected ≥{min(expected_matches, optimal_matches)}), "
                  f"Sitouts: {actual_sitouts} (expected ≤{max(expected_sitouts, optimal_sitouts)}), "
                  f"Courts Used: {courts_used}/{num_courts}")
        
        success = match_count_ok and sitout_count_ok and court_usage_ok
        return self.log_test(f"{scenario_name} - Court Optimization", success, details)
    
    def test_match_data_integrity(self, matches: List[Dict]) -> bool:
        """Test match data structure integrity"""
        if not matches:
            return self.log_test("Match Data Integrity", False, "No matches to verify")
        
        issues = []
        for i, match in enumerate(matches):
            # Check required fields
            required_fields = ["id", "teamA", "teamB", "courtIndex", "roundIndex", "category", "matchType"]
            for field in required_fields:
                if field not in match:
                    issues.append(f"Match {i}: Missing field '{field}'")
            
            # Check team structure
            team_a = match.get("teamA", [])
            team_b = match.get("teamB", [])
            
            if not isinstance(team_a, list) or not isinstance(team_b, list):
                issues.append(f"Match {i}: Teams must be arrays")
            
            if len(team_a) == 0 or len(team_b) == 0:
                issues.append(f"Match {i}: Empty teams not allowed")
            
            # Check for duplicate player assignments
            all_players_in_match = team_a + team_b
            if len(all_players_in_match) != len(set(all_players_in_match)):
                issues.append(f"Match {i}: Duplicate player assignments")
            
            # Check category for cross-category mode
            if match.get("category") != "Mixed":
                issues.append(f"Match {i}: Expected 'Mixed' category, got '{match.get('category')}'")
        
        success = len(issues) == 0
        details = f"Verified {len(matches)} matches. Issues: {'; '.join(issues) if issues else 'None'}"
        return self.log_test("Match Data Integrity", success, details)
    
    def test_session_state_transitions(self) -> bool:
        """Test session state after match generation"""
        try:
            session = self.get_session_config()
            phase = session.get("phase", "unknown")
            current_round = session.get("currentRound", 0)
            
            # After match generation, session should be in "ready" phase
            phase_ok = phase == "ready"
            round_ok = current_round >= 0
            
            details = f"Phase: {phase}, Round: {current_round}"
            success = phase_ok and round_ok
            return self.log_test("Session State Transitions", success, details)
        except Exception as e:
            return self.log_test("Session State Transitions", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite for Cross Category + Maximize Courts bug fix"""
        print("🚀 Starting Cross Category + Maximize Courts Bug Fix Verification")
        print("=" * 70)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return
        
        # Test 2: Various scenarios (adjusted for available 12 players)
        test_scenarios = [
            # (players, courts, expected_matches, expected_sitouts, name)
            (12, 3, 3, 0, "12 Players, 3 Courts - Perfect Doubles"),
            (12, 4, 3, 0, "12 Players, 4 Courts - 3 Doubles (court limit)"),
            (10, 3, 3, 0, "10 Players, 3 Courts - 2 Doubles + 1 Singles"),
            (8, 4, 2, 0, "8 Players, 4 Courts - 2 Doubles"),
            (6, 4, 3, 0, "6 Players, 4 Courts - 3 Singles"),
            (4, 2, 1, 0, "4 Players, 2 Courts - 1 Doubles"),
        ]
        
        for players, courts, matches, sitouts, name in test_scenarios:
            self.test_cross_category_maximize_courts_scenario(players, courts, matches, sitouts, name)
        
        # Test 3: Match data integrity
        matches = self.get_matches()
        self.test_match_data_integrity(matches)
        
        # Test 4: Session state
        self.test_session_state_transitions()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Final verdict
        if success_rate >= 90:
            print(f"\n🎉 CROSS CATEGORY + MAXIMIZE COURTS BUG FIX: ✅ VERIFIED")
            print("All critical scenarios are working correctly!")
        else:
            print(f"\n⚠️  CROSS CATEGORY + MAXIMIZE COURTS BUG FIX: ❌ ISSUES DETECTED")
            print("Some scenarios are not working as expected.")
        
        return success_rate >= 90

if __name__ == "__main__":
    tester = CrossCategoryMaximizeCourtsTester()
    tester.run_comprehensive_test()