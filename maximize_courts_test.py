#!/usr/bin/env python3
"""
Backend Testing for CourtChime - Maximize Courts Fix
Testing the court filling logic to ensure ALL available courts are used first
"""

import requests
import json
import sys
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://chime-roster.preview.emergentagent.com/api"

class MaximizeCourtsBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.club_name = "Main Club"
        self.access_code = "demo123"
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def authenticate(self) -> bool:
        """Authenticate with the backend"""
        try:
            response = self.session.post(f"{self.backend_url}/auth/login", json={
                "club_name": self.club_name,
                "access_code": self.access_code
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Authentication", True, f"Logged in as {data.get('club_name')}")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Error: {str(e)}")
            return False
    
    def setup_test_players(self, num_players: int) -> bool:
        """Setup test players for match generation"""
        try:
            # Clear existing data
            response = self.session.delete(f"{self.backend_url}/clear-all-data")
            if response.status_code != 200:
                self.log_result("Clear Data", False, f"Status: {response.status_code}")
                return False
            
            # Clear any existing matches
            try:
                self.session.delete(f"{self.backend_url}/matches?club_name={self.club_name}")
            except:
                pass  # Ignore if endpoint doesn't exist
            
            # Add test data to get base players
            response = self.session.post(f"{self.backend_url}/add-test-data")
            if response.status_code != 200:
                self.log_result("Add Test Data", False, f"Status: {response.status_code}")
                return False
            
            # Get current players
            response = self.session.get(f"{self.backend_url}/players?club_name={self.club_name}")
            if response.status_code != 200:
                return False
                
            players = response.json()
            
            # If we need more players than available, create additional ones
            if len(players) < num_players:
                categories = ["Beginner", "Intermediate", "Advanced"]
                for i in range(len(players), num_players):
                    player_data = {
                        "name": f"TestPlayer{i+1}",
                        "category": categories[i % len(categories)]
                    }
                    response = self.session.post(
                        f"{self.backend_url}/players?club_name={self.club_name}",
                        json=player_data
                    )
                    if response.status_code != 200:
                        self.log_result("Create Player", False, f"Failed to create player {i+1}")
                        return False
            
            # If we have too many players, deactivate some
            elif len(players) > num_players:
                for i in range(num_players, len(players)):
                    player_id = players[i]['id']
                    response = self.session.patch(
                        f"{self.backend_url}/players/{player_id}/toggle-active?club_name={self.club_name}"
                    )
                    if response.status_code != 200:
                        self.log_result("Deactivate Player", False, f"Failed to deactivate player {i+1}")
                        return False
            
            self.log_result("Setup Test Players", True, f"Configured {num_players} active players")
            return True
            
        except Exception as e:
            self.log_result("Setup Test Players", False, f"Error: {str(e)}")
            return False
    
    def update_session_config(self, num_courts: int, allow_doubles: bool = True, allow_singles: bool = True, maximize_courts: bool = True) -> bool:
        """Update session configuration"""
        try:
            config_data = {
                "numCourts": num_courts,
                "playSeconds": 720,
                "bufferSeconds": 30,
                "allowSingles": allow_singles,
                "allowDoubles": allow_doubles,
                "allowCrossCategory": True,  # Enable cross-category for testing
                "maximizeCourtUsage": maximize_courts,
                "rotationModel": "legacy"
            }
            
            response = self.session.put(
                f"{self.backend_url}/session/config?club_name={self.club_name}",
                json=config_data
            )
            
            if response.status_code == 200:
                self.log_result("Update Session Config", True, f"Courts: {num_courts}, Maximize: {maximize_courts}")
                return True
            else:
                self.log_result("Update Session Config", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Update Session Config", False, f"Error: {str(e)}")
            return False
    
    def generate_matches(self) -> List[Dict[str, Any]]:
        """Generate matches and return the matches list"""
        try:
            # First, generate the matches
            response = self.session.post(f"{self.backend_url}/session/generate-matches?club_name={self.club_name}")
            
            if response.status_code != 200:
                self.log_result("Generate Matches", False, f"Status: {response.status_code}, Response: {response.text}")
                return []
            
            # Then, fetch the generated matches
            response = self.session.get(f"{self.backend_url}/matches?club_name={self.club_name}")
            
            if response.status_code == 200:
                matches = response.json()
                self.log_result("Generate Matches", True, f"Generated {len(matches)} matches")
                return matches
            else:
                self.log_result("Fetch Matches", False, f"Status: {response.status_code}, Response: {response.text}")
                return []
                
        except Exception as e:
            self.log_result("Generate Matches", False, f"Error: {str(e)}")
            return []
    
    def analyze_match_results(self, matches: List[Dict], expected_courts: int, expected_players_in_matches: int, test_name: str) -> bool:
        """Analyze match generation results"""
        try:
            if not matches:
                self.log_result(test_name, False, "No matches generated")
                return False
            
            # Count courts used
            courts_used = set()
            total_players_in_matches = 0
            doubles_count = 0
            singles_count = 0
            
            for match in matches:
                courts_used.add(match['courtIndex'])
                team_a_size = len(match['teamA'])
                team_b_size = len(match['teamB'])
                total_players_in_matches += team_a_size + team_b_size
                
                if match['matchType'] == 'doubles':
                    doubles_count += 1
                elif match['matchType'] == 'singles':
                    singles_count += 1
            
            courts_used_count = len(courts_used)
            
            # Check if all expected courts are used (when sufficient players exist)
            courts_success = courts_used_count == expected_courts
            
            # Check if expected number of players are in matches
            players_success = total_players_in_matches == expected_players_in_matches
            
            # Verify court indices are sequential (0, 1, 2, ...)
            expected_court_indices = set(range(courts_used_count))
            sequential_success = courts_used == expected_court_indices
            
            details = f"Courts used: {courts_used_count}/{expected_courts}, Players in matches: {total_players_in_matches}/{expected_players_in_matches}, Doubles: {doubles_count}, Singles: {singles_count}"
            
            if not sequential_success:
                details += f", Court indices: {sorted(courts_used)} (expected: {sorted(expected_court_indices)})"
            
            success = courts_success and players_success and sequential_success
            self.log_result(test_name, success, details)
            
            return success
            
        except Exception as e:
            self.log_result(test_name, False, f"Analysis error: {str(e)}")
            return False
    
    def test_16_players_3_courts(self) -> bool:
        """Test: 16 players, 3 courts (Both Doubles & Singles enabled)
        Expected: 3 doubles matches (12 players), 4 sitouts, All 3 courts used"""
        
        if not self.setup_test_players(16):
            return False
        
        if not self.update_session_config(num_courts=3, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 3 doubles matches using all 3 courts, 12 players in matches, 4 sitouts
        return self.analyze_match_results(matches, expected_courts=3, expected_players_in_matches=12, test_name="16 Players, 3 Courts")
    
    def test_10_players_3_courts(self) -> bool:
        """Test: 10 players, 3 courts (Both Doubles & Singles enabled)
        Expected: 2 doubles + 1 singles (10 players), 0 sitouts, All 3 courts used"""
        
        if not self.setup_test_players(10):
            return False
        
        if not self.update_session_config(num_courts=3, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: All 10 players in matches, all 3 courts used
        return self.analyze_match_results(matches, expected_courts=3, expected_players_in_matches=10, test_name="10 Players, 3 Courts")
    
    def test_20_players_4_courts(self) -> bool:
        """Test: 20 players, 4 courts (Both Doubles & Singles enabled)
        Expected: 4 doubles matches (16 players), 4 sitouts, All 4 courts used"""
        
        if not self.setup_test_players(20):
            return False
        
        if not self.update_session_config(num_courts=4, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 4 doubles matches using all 4 courts, 16 players in matches, 4 sitouts
        return self.analyze_match_results(matches, expected_courts=4, expected_players_in_matches=16, test_name="20 Players, 4 Courts")
    
    def test_14_players_5_courts(self) -> bool:
        """Test: 14 players, 5 courts (Both Doubles & Singles enabled)
        Expected: 3 doubles + 1 singles (14 players), 0 sitouts, 4 courts used"""
        
        if not self.setup_test_players(14):
            return False
        
        if not self.update_session_config(num_courts=5, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: All 14 players in matches, 4 courts used (1 court empty)
        return self.analyze_match_results(matches, expected_courts=4, expected_players_in_matches=14, test_name="14 Players, 5 Courts")
    
    def test_12_players_3_courts_doubles_only(self) -> bool:
        """Test: 12 players, 3 courts (Doubles only)
        Expected: 3 doubles matches, 0 sitouts, All 3 courts used"""
        
        if not self.setup_test_players(12):
            return False
        
        if not self.update_session_config(num_courts=3, allow_doubles=True, allow_singles=False, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 3 doubles matches, all 12 players in matches, all 3 courts used
        return self.analyze_match_results(matches, expected_courts=3, expected_players_in_matches=12, test_name="12 Players, 3 Courts (Doubles Only)")
    
    def test_12_players_3_courts_singles_only(self) -> bool:
        """Test: 12 players, 3 courts (Singles only)
        Expected: 3 singles matches (6 players), 6 sitouts, All 3 courts used"""
        
        if not self.setup_test_players(12):
            return False
        
        if not self.update_session_config(num_courts=3, allow_doubles=False, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 3 singles matches, 6 players in matches, 6 sitouts, all 3 courts used
        return self.analyze_match_results(matches, expected_courts=3, expected_players_in_matches=6, test_name="12 Players, 3 Courts (Singles Only)")
    
    def test_4_players_3_courts(self) -> bool:
        """Test: 4 players, 3 courts (Edge case - very few players)
        Expected: 1 doubles match, 1 court used"""
        
        if not self.setup_test_players(4):
            return False
        
        if not self.update_session_config(num_courts=3, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 1 doubles match, 4 players in matches, 1 court used
        return self.analyze_match_results(matches, expected_courts=1, expected_players_in_matches=4, test_name="4 Players, 3 Courts (Edge Case)")
    
    def test_8_players_10_courts(self) -> bool:
        """Test: 8 players, 10 courts (Many courts, few players)
        Expected: 2 doubles matches, 2 courts used"""
        
        if not self.setup_test_players(8):
            return False
        
        if not self.update_session_config(num_courts=10, allow_doubles=True, allow_singles=True, maximize_courts=True):
            return False
        
        matches = self.generate_matches()
        if not matches:
            return False
        
        # Expected: 2 doubles matches, 8 players in matches, 2 courts used
        return self.analyze_match_results(matches, expected_courts=2, expected_players_in_matches=8, test_name="8 Players, 10 Courts (Many Courts)")
    
    def test_session_configuration_verification(self) -> bool:
        """Verify session configuration is properly read"""
        try:
            response = self.session.get(f"{self.backend_url}/session?club_name={self.club_name}")
            
            if response.status_code == 200:
                session_data = response.json()
                config = session_data.get('config', {})
                
                # Check if maximizeCourtUsage is properly set
                maximize_courts = config.get('maximizeCourtUsage', False)
                allow_doubles = config.get('allowDoubles', False)
                allow_singles = config.get('allowSingles', False)
                num_courts = config.get('numCourts', 0)
                
                success = isinstance(maximize_courts, bool) and isinstance(num_courts, int) and num_courts > 0
                details = f"maximizeCourtUsage: {maximize_courts}, numCourts: {num_courts}, allowDoubles: {allow_doubles}, allowSingles: {allow_singles}"
                
                self.log_result("Session Configuration Verification", success, details)
                return success
            else:
                self.log_result("Session Configuration Verification", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Session Configuration Verification", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all maximize courts tests"""
        print("🎯 Starting CourtChime Backend Tests - Maximize Courts Fix")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            return False
        
        # Test session configuration
        if not self.test_session_configuration_verification():
            return False
        
        # Run all test scenarios
        test_methods = [
            self.test_16_players_3_courts,
            self.test_10_players_3_courts,
            self.test_20_players_4_courts,
            self.test_14_players_5_courts,
            self.test_12_players_3_courts_doubles_only,
            self.test_12_players_3_courts_singles_only,
            self.test_4_players_3_courts,
            self.test_8_players_10_courts
        ]
        
        passed = 0
        total = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed += 1
        
        print("=" * 60)
        print(f"🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL TESTS PASSED - Maximize Courts logic is working correctly!")
            return True
        else:
            print(f"❌ {total - passed} tests failed - Issues found with Maximize Courts logic")
            return False

def main():
    """Main test execution"""
    tester = MaximizeCourtsBackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Backend testing completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Backend testing found issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()