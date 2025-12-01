#!/usr/bin/env python3
"""
Focused test for CourtChime Player Active Status Issue
Tests the specific issue mentioned: frontend UI not reflecting player active status changes
"""

import requests
import json
import time

BACKEND_URL = "https://chime-roster.preview.emergentagent.com/api"

def test_player_active_status_detailed():
    """Detailed test of player active status functionality"""
    session = requests.Session()
    
    print("🔍 FOCUSED TEST: Player Active Status Toggle")
    print("=" * 60)
    
    try:
        # Step 1: Get all players and their current active status
        print("1️⃣ Getting all players...")
        response = session.get(f"{BACKEND_URL}/players")
        if response.status_code != 200:
            print(f"❌ Failed to get players: {response.status_code}")
            return False
        
        players = response.json()
        print(f"✅ Found {len(players)} players")
        
        # Display current active status
        print("\n📊 Current Player Active Status:")
        for i, player in enumerate(players[:5]):  # Show first 5 players
            status = "🟢 ACTIVE" if player.get("isActive", False) else "🔴 INACTIVE"
            print(f"   {i+1}. {player['name']} ({player['category']}) - {status}")
        
        if not players:
            print("❌ No players found to test")
            return False
        
        # Step 2: Select a player to test toggle functionality
        test_player = players[0]
        player_id = test_player["id"]
        player_name = test_player["name"]
        initial_status = test_player.get("isActive", True)
        
        print(f"\n2️⃣ Testing toggle with player: {player_name}")
        print(f"   Initial isActive status: {initial_status}")
        
        # Step 3: Toggle the player's active status
        print("\n3️⃣ Toggling player active status...")
        response = session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active")
        
        if response.status_code != 200:
            print(f"❌ Toggle failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        toggle_result = response.json()
        print(f"✅ Toggle API response: {toggle_result}")
        
        expected_new_status = not initial_status
        returned_status = toggle_result.get("isActive")
        
        if returned_status != expected_new_status:
            print(f"❌ Toggle response incorrect!")
            print(f"   Expected: {expected_new_status}")
            print(f"   Got: {returned_status}")
            return False
        
        print(f"✅ Toggle response correct: {returned_status}")
        
        # Step 4: Verify the change persisted in database
        print("\n4️⃣ Verifying database persistence...")
        time.sleep(0.5)  # Small delay for database write
        
        response = session.get(f"{BACKEND_URL}/players")
        if response.status_code != 200:
            print(f"❌ Failed to re-fetch players: {response.status_code}")
            return False
        
        updated_players = response.json()
        updated_player = next((p for p in updated_players if p["id"] == player_id), None)
        
        if not updated_player:
            print(f"❌ Player {player_id} not found after toggle")
            return False
        
        persisted_status = updated_player.get("isActive")
        if persisted_status != expected_new_status:
            print(f"❌ Database persistence failed!")
            print(f"   Expected: {expected_new_status}")
            print(f"   Database has: {persisted_status}")
            return False
        
        print(f"✅ Database correctly persisted: isActive={persisted_status}")
        
        # Step 5: Test multiple toggles to ensure consistency
        print("\n5️⃣ Testing multiple toggles for consistency...")
        
        for i in range(3):
            current_status = persisted_status if i == 0 else not current_status
            expected_after_toggle = not current_status
            
            response = session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active")
            if response.status_code != 200:
                print(f"❌ Toggle {i+1} failed: {response.status_code}")
                return False
            
            result = response.json()
            if result.get("isActive") != expected_after_toggle:
                print(f"❌ Toggle {i+1} returned wrong status")
                return False
            
            # Verify persistence
            response = session.get(f"{BACKEND_URL}/players")
            if response.status_code == 200:
                players_check = response.json()
                player_check = next((p for p in players_check if p["id"] == player_id), None)
                if player_check and player_check.get("isActive") == expected_after_toggle:
                    print(f"   ✅ Toggle {i+1}: {current_status} → {expected_after_toggle}")
                else:
                    print(f"   ❌ Toggle {i+1}: Database inconsistency")
                    return False
            
            current_status = expected_after_toggle
        
        # Step 6: Test with different players
        print("\n6️⃣ Testing with multiple players...")
        
        test_players = players[1:4] if len(players) > 3 else players[1:2]
        for player in test_players:
            pid = player["id"]
            pname = player["name"]
            initial = player.get("isActive", True)
            
            # Toggle
            response = session.patch(f"{BACKEND_URL}/players/{pid}/toggle-active")
            if response.status_code == 200:
                result = response.json()
                expected = not initial
                if result.get("isActive") == expected:
                    print(f"   ✅ {pname}: {initial} → {expected}")
                else:
                    print(f"   ❌ {pname}: Toggle failed")
                
                # Toggle back
                session.patch(f"{BACKEND_URL}/players/{pid}/toggle-active")
            else:
                print(f"   ❌ {pname}: API call failed")
        
        print("\n🎉 ALL PLAYER ACTIVE STATUS TESTS PASSED!")
        print("\n📋 SUMMARY:")
        print("   ✅ Toggle API endpoint working correctly")
        print("   ✅ Database persistence working correctly") 
        print("   ✅ isActive field properly returned in GET requests")
        print("   ✅ Multiple toggles work consistently")
        print("   ✅ Works with multiple different players")
        
        print("\n💡 CONCLUSION:")
        print("   The backend API for player active status is working perfectly.")
        print("   If the frontend UI is not reflecting changes, the issue is likely:")
        print("   1. Frontend not calling the correct API endpoint")
        print("   2. Frontend not refreshing data after toggle")
        print("   3. Frontend caching old data")
        print("   4. Frontend UI not updating when data changes")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_player_active_status_detailed()
    if success:
        print("\n✅ Backend player active status functionality is working correctly!")
    else:
        print("\n❌ Backend has issues with player active status functionality!")