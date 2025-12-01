#!/usr/bin/env python3
"""
Debug test for toggle issue
"""

import requests
import json
import time

BACKEND_URL = "https://chime-roster.preview.emergentagent.com/api"

def debug_toggle_issue():
    session = requests.Session()
    
    # Get a player
    response = session.get(f"{BACKEND_URL}/players")
    players = response.json()
    test_player = players[0]
    player_id = test_player["id"]
    player_name = test_player["name"]
    
    print(f"Testing with player: {player_name} (ID: {player_id})")
    
    # Get initial state
    initial_status = test_player.get("isActive", True)
    print(f"Initial status: {initial_status}")
    
    # Toggle 1
    print("\n--- Toggle 1 ---")
    response = session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active")
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result}")
        expected = not initial_status
        actual = result.get("isActive")
        print(f"Expected: {expected}, Got: {actual}, Match: {expected == actual}")
    
    # Check database
    time.sleep(0.5)
    response = session.get(f"{BACKEND_URL}/players")
    players = response.json()
    player = next((p for p in players if p["id"] == player_id), None)
    db_status = player.get("isActive") if player else None
    print(f"Database status: {db_status}")
    
    # Toggle 2
    print("\n--- Toggle 2 ---")
    response = session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active")
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result}")
        expected = not db_status
        actual = result.get("isActive")
        print(f"Expected: {expected}, Got: {actual}, Match: {expected == actual}")
    
    # Check database again
    time.sleep(0.5)
    response = session.get(f"{BACKEND_URL}/players")
    players = response.json()
    player = next((p for p in players if p["id"] == player_id), None)
    db_status_2 = player.get("isActive") if player else None
    print(f"Database status: {db_status_2}")
    
    # Toggle 3
    print("\n--- Toggle 3 ---")
    response = session.patch(f"{BACKEND_URL}/players/{player_id}/toggle-active")
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result}")
        expected = not db_status_2
        actual = result.get("isActive")
        print(f"Expected: {expected}, Got: {actual}, Match: {expected == actual}")

if __name__ == "__main__":
    debug_toggle_issue()