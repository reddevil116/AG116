import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, SafeAreaView, StatusBar, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as DocumentPicker from 'expo-document-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// LoginPage Component
function LoginPage({ onLoginSuccess }: { onLoginSuccess: (sessionData: any) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [clubName, setClubName] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!clubName.trim() || !accessCode.trim()) {
      Alert.alert('Error', 'Please enter both club name and access code');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          club_name: clubName.trim(),
          access_code: accessCode.trim(),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        onLoginSuccess(data);
      } else {
        Alert.alert('Login Failed', data.detail || 'Invalid club name or access code');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!clubName.trim() || !displayName.trim() || !accessCode.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: clubName.trim(),
          display_name: displayName.trim(),
          access_code: accessCode.trim(),
          description: description.trim() || null,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        onLoginSuccess(data);
      } else {
        Alert.alert('Registration Failed', data.detail || 'Failed to create club');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const tryDemo = async () => {
    setClubName('Main Club');
    setAccessCode('demo123');
    setTimeout(() => handleLogin(), 100);
  };

  return (
    <SafeAreaView style={{flex: 1, backgroundColor: '#ffffff'}}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      <KeyboardAvoidingView 
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={{flex: 1, padding: 24, justifyContent: 'center'}}>
          
          {/* Logo and Title */}
          <View style={{alignItems: 'center', marginBottom: 48}}>
            <Text style={{fontSize: 32, fontWeight: 'bold', color: '#3b82f6', marginBottom: 8}}>
              🏓 CourtChime
            </Text>
            <Text style={{fontSize: 16, color: '#64748b', textAlign: 'center'}}>
              {mode === 'login' ? 'Sign into your club' : 'Create a new club'}
            </Text>
          </View>

          {/* Form */}
          <View style={{marginBottom: 24}}>
            <View style={{marginBottom: 20}}>
              <Text style={{fontSize: 16, fontWeight: '600', color: '#1e293b', marginBottom: 8}}>
                Club Name
              </Text>
              <TextInput
                style={{
                  borderWidth: 1,
                  borderColor: '#e2e8f0',
                  borderRadius: 12,
                  padding: 16,
                  fontSize: 16,
                  backgroundColor: '#f8fafc',
                  color: '#1e293b'
                }}
                value={clubName}
                onChangeText={setClubName}
                placeholder="Enter your club name"
                placeholderTextColor="#94a3b8"
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            {mode === 'register' && (
              <View style={{marginBottom: 20}}>
                <Text style={{fontSize: 16, fontWeight: '600', color: '#1e293b', marginBottom: 8}}>
                  Display Name
                </Text>
                <TextInput
                  style={{
                    borderWidth: 1,
                    borderColor: '#e2e8f0',
                    borderRadius: 12,
                    padding: 16,
                    fontSize: 16,
                    backgroundColor: '#f8fafc',
                    color: '#1e293b'
                  }}
                  value={displayName}
                  onChangeText={setDisplayName}
                  placeholder="How your club appears to members"
                  placeholderTextColor="#94a3b8"
                  autoCapitalize="words"
                />
              </View>
            )}

            <View style={{marginBottom: 20}}>
              <Text style={{fontSize: 16, fontWeight: '600', color: '#1e293b', marginBottom: 8}}>
                Access Code
              </Text>
              <TextInput
                style={{
                  borderWidth: 1,
                  borderColor: '#e2e8f0',
                  borderRadius: 12,
                  padding: 16,
                  fontSize: 16,
                  backgroundColor: '#f8fafc',
                  color: '#1e293b'
                }}
                value={accessCode}
                onChangeText={setAccessCode}
                placeholder={mode === 'login' ? 'Enter access code' : 'Create access code'}
                placeholderTextColor="#94a3b8"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {mode === 'register' && (
              <View style={{marginBottom: 20}}>
                <Text style={{fontSize: 16, fontWeight: '600', color: '#1e293b', marginBottom: 8}}>
                  Description (Optional)
                </Text>
                <TextInput
                  style={{
                    borderWidth: 1,
                    borderColor: '#e2e8f0',
                    borderRadius: 12,
                    padding: 16,
                    fontSize: 16,
                    backgroundColor: '#f8fafc',
                    color: '#1e293b'
                  }}
                  value={description}
                  onChangeText={setDescription}
                  placeholder="Brief description of your club"
                  placeholderTextColor="#94a3b8"
                  multiline
                />
              </View>
            )}
          </View>

          {/* Action Buttons */}
          <View style={{marginBottom: 24}}>
            <TouchableOpacity 
              onPress={mode === 'login' ? handleLogin : handleRegister}
              disabled={loading}
            >
              <LinearGradient
                colors={['#3b82f6', '#06b6d4']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={{
                  borderRadius: 12,
                  paddingVertical: 16,
                  paddingHorizontal: 24,
                  marginBottom: 12
                }}
              >
                <Text style={{
                  fontSize: 16,
                  fontWeight: '600',
                  color: '#ffffff',
                  textAlign: 'center'
                }}>
                  {loading ? 'Processing...' : (mode === 'login' ? 'Sign In' : 'Create Club')}
                </Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity 
              style={{
                borderWidth: 1,
                borderColor: '#3b82f6',
                borderRadius: 12,
                paddingVertical: 16,
                paddingHorizontal: 24
              }}
              onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
            >
              <Text style={{
                fontSize: 16,
                fontWeight: '600',
                color: '#3b82f6',
                textAlign: 'center'
              }}>
                {mode === 'login' ? 'Create New Club' : 'Sign Into Existing Club'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Mode Switch Text */}
          <Text style={{
            fontSize: 14,
            color: '#64748b',
            textAlign: 'center',
            marginTop: 16
          }}>
            {mode === 'login' 
              ? "Don't have a club? " 
              : "Already have a club? "
            }
            <Text 
              style={{color: '#3b82f6', fontWeight: '600'}}
              onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
            >
              {mode === 'login' ? 'Create one' : 'Sign in'}
            </Text>
          </Text>

          {/* Demo Section */}
          {mode === 'login' && (
            <View style={{
              backgroundColor: '#f8fafc',
              borderRadius: 12,
              padding: 16,
              marginTop: 24
            }}>
              <Text style={{
                fontSize: 16,
                fontWeight: '600',
                color: '#1e293b',
                marginBottom: 8
              }}>
                <Ionicons name="flask" size={16} color="#3b82f6" /> Try Demo
              </Text>
              <Text style={{
                fontSize: 14,
                color: '#64748b',
                lineHeight: 20
              }}>
                Club: "Main Club" | Access Code: "demo123"
              </Text>
              <TouchableOpacity 
                onPress={tryDemo}
                style={{ marginTop: 12 }}
              >
                <Text style={{color: '#3b82f6', fontWeight: '600'}}>Quick Demo Access →</Text>
              </TouchableOpacity>
            </View>
          )}

        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// Modern aesthetic color palette with white/grey base and vibrant accents
const colors = {
  // Clean white/grey foundation
  background: '#ffffff',
  surface: '#f8fafc',        // Softer light grey
  surfaceElevated: '#f1f5f9', // Elevated surfaces
  border: '#e2e8f0',         // Subtle borders
  borderLight: '#f1f5f9',
  
  // Modern text hierarchy
  text: '#1e293b',           // Rich dark text
  textSecondary: '#64748b',   // Medium grey
  textMuted: '#94a3b8',      // Light grey
  textLight: '#cbd5e1',      // Very light grey
  
  // Vibrant gradient primary (Blue to Teal)
  primary: '#3b82f6',        // Bright blue
  primaryDark: '#2563eb',    // Darker blue
  primaryLight: '#dbeafe',   // Light blue tint
  primaryGradient: ['#3b82f6', '#06b6d4'], // Blue to Teal gradient
  
  // Success with modern green
  success: '#10b981',        // Emerald green
  successDark: '#059669',
  successLight: '#d1fae5',
  
  // Warning with warm amber
  warning: '#f59e0b',        // Amber
  warningDark: '#d97706',
  warningLight: '#fef3c7',
  
  // Error with modern red
  error: '#ef4444',          // Red
  errorDark: '#dc2626',
  errorLight: '#fef2f2',
  
  // Vibrant accent colors for variety
  accent: '#8b5cf6',         // Purple accent
  accentLight: '#f3f4f6',
  coral: '#ff6b6b',          // Coral accent
  coralLight: '#ffe0e0',
  teal: '#14b8a6',          // Teal accent
  tealLight: '#ccfbf1',
  
  // Shadow and depth colors
  shadow: '#1e293b',
  shadowLight: '#64748b',
};

// Types
interface Player {
  id: string;
  name: string;
  category: string;
  sitNextRound: boolean;
  sitCount: number;
  missDueToCourtLimit: number;
  isActive: boolean;  // Can be toggled for daily sessions
  // DUPR-style rating fields
  rating: number;
  matchesPlayed: number;
  wins: number;
  losses: number;
  recentForm: string[];
  ratingHistory: Array<{
    date: string;
    oldRating: number;
    newRating: number;
    change: number;
    matchId: string;
    result: string;
  }>;
  lastUpdated: string;
  stats: {
    wins: number;
    losses: number;
    pointDiff: number;
  };
}

interface Category {
  id: string;
  name: string;
  description?: string;
}

interface Match {
  id: string;
  roundIndex: number;
  courtIndex: number;
  category: string;
  teamA: string[];
  teamB: string[];
  status: 'pending' | 'active' | 'buffer' | 'done' | 'saved';
  matchType: 'singles' | 'doubles';
  scoreA?: number;
  scoreB?: number;
  matchDate: string;  // ISO date string when match was created
}

type RotationModel = 'legacy' | 'top_court';

interface CourtRoundResult {
  courtIndex: number;
  teamA: string[];
  teamB: string[];
  winner?: 'A' | 'B';
}

interface HistoryState {
  partnerCounts: Record<string, Record<string, number>>;
  courtHistory: Record<string, number[]>;
  wins: Record<string, number>;
}

interface SessionConfig {
  numCourts: number;
  playSeconds: number;
  bufferSeconds: number;
  allowSingles: boolean;
  allowDoubles: boolean;
  allowCrossCategory: boolean;
  maximizeCourtUsage: boolean;
  rotationModel?: RotationModel;
}

interface SessionState {
  id: string;
  currentRound: number;
  phase: 'idle' | 'play' | 'buffer' | 'ended';
  timeRemaining: number;
  paused: boolean;
  config: SessionConfig;
  histories: any;
}

// Audio functionality removed - will be added later with custom sounds

// CSV Processing Functions
const parseCSVLine = (line: string): string[] => {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  result.push(current.trim());
  return result;
};

const parseCSV = (csvText: string) => {
  const lines = csvText.trim().split('\n');
  const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase());
  
  const players: Array<{name: string, category: string, date?: string}> = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length >= 2) {
      const player: any = {};
      
      // Map headers to values
      headers.forEach((header, index) => {
        const value = values[index]?.replace(/"/g, '').trim();
        if (header.includes('name')) {
          player.name = value;
        } else if (header.includes('level') || header.includes('category')) {
          player.category = value;
        } else if (header.includes('rating')) {
          player.rating = parseFloat(value) || 3.0; // Default to 3.0 if invalid
        } else if (header.includes('date')) {
          player.date = value;
        }
      });
      
      if (player.name && player.category) {
        players.push(player);
      }
    }
  }
  
  return players;
};

const generateCSV = (matches: Match[], players: Player[]) => {
  let csv = 'Round,Court,Category,TeamA_Player1,TeamA_Player2,TeamB_Player1,TeamB_Player2,ScoreA,ScoreB,Status\n';
  
  // Add matches
  matches.forEach(match => {
    const teamA1 = players.find(p => p.id === match.teamA[0])?.name || '';
    const teamA2 = match.teamA[1] ? players.find(p => p.id === match.teamA[1])?.name || '' : '';
    const teamB1 = players.find(p => p.id === match.teamB[0])?.name || '';
    const teamB2 = match.teamB[1] ? players.find(p => p.id === match.teamB[1])?.name || '' : '';
    
    csv += `${match.roundIndex},${match.courtIndex + 1},${match.category},"${teamA1}","${teamA2}","${teamB1}","${teamB2}",${match.scoreA || ''},${match.scoreB || ''},${match.status}\n`;
  });
  
  // Add player stats section
  csv += '\nPLAYER STATS\n';
  csv += 'Name,Category,Wins,Losses,PointDiff,Sits,MissedDueToCourts\n';
  
  players.forEach(player => {
    csv += `"${player.name}",${player.category},${player.stats.wins},${player.stats.losses},${player.stats.pointDiff},${player.sitCount},${player.missDueToCourtLimit}\n`;
  });
  
  return csv;
};

export default function PickleballManager() {
  const [activeTab, setActiveTab] = useState('admin');
  const [players, setPlayers] = useState<Player[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [session, setSession] = useState<SessionState | null>(null);
  const [loading, setLoading] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [clubSession, setClubSession] = useState<any>(null);
  const [hasInitialized, setHasInitialized] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const oneMinuteWarningPlayedRef = useRef(false);

  // Initialize data
  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      const session = await AsyncStorage.getItem('clubSession');
      if (session) {
        const parsedSession = JSON.parse(session);
        setClubSession(parsedSession);
        setAuthenticated(true);
        await initializeAppWithSession(parsedSession);
      } else {
        // No session found - show login page
        setLoading(false);
        setAuthenticated(false);
        setClubSession(null);
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      setLoading(false);
      setAuthenticated(false);
      setClubSession(null);
    }
  };

  const handleLoginSuccess = async (sessionData: any) => {
    console.log('🔐 handleLoginSuccess called');
    try {
      // Store session in AsyncStorage first
      await AsyncStorage.setItem('clubSession', JSON.stringify(sessionData));
      
      setClubSession(sessionData);
      setAuthenticated(true);
      setLoading(true);
      
      // Use the sessionData directly instead of relying on state
      await initializeAppWithSession(sessionData);
      console.log('✅ Login success flow completed');
    } catch (error) {
      console.error('❌ Error in handleLoginSuccess:', error);
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.removeItem('clubSession');
      setAuthenticated(false);
      setClubSession(null);
      // Don't use router.push - just let the component re-render to show login
      // The LoginPage will be shown automatically when authenticated is false
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  // Optimized timer effect - minimal operations
  useEffect(() => {
    // Cleanup function only
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []);

  // Reset warning flag when new round starts and manage timer
  useEffect(() => {
    if (session?.phase === 'play') {
      oneMinuteWarningPlayedRef.current = false;
      // Start timer countdown for play phase
      if (!session.paused && !timerRef.current) { // Only start if not already running
        startTimerCountdown();
      }
    } else if (session?.phase === 'buffer') {
      // Start timer countdown for buffer phase  
      if (!session.paused && !timerRef.current) { // Only start if not already running
        startTimerCountdown();
      }
    } else {
      // Stop timer for idle/ended/ready phases
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [session?.phase, session?.paused]); // Removed session?.currentRound to prevent infinite loop

  const handleTimeUp = async (currentSession: SessionState) => {
    try {
      if (currentSession.phase === 'play') {
        // Play phase ended - start buffer phase automatically
        // playHorn('end'); // Audio removed
        
        // Show notification
        Alert.alert('⏰ Round Complete', 'Starting buffer time - preparing next round...', [{ text: 'OK' }]);
        
        // Start buffer phase
        await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/buffer?club_name=${clubSession?.club_name || 'Main Club'}`, { method: 'POST' });
        
        // Fetch updated session
        await fetchSession();
        
      } else if (currentSession.phase === 'buffer') {
        // Buffer phase ended - prompt for next round
        await handleBufferEnd(currentSession);
      }
    } catch (error) {
      console.error('Error handling time up:', error);
      Alert.alert('Error', 'Failed to progress to next phase. Please try manually.');
    }
  };

  const handleBufferEnd = async (currentSession: SessionState) => {
    // Buffer ended - no automatic progression, wait for manual "Next Round" button click
    console.log('Buffer phase completed. Waiting for manual Next Round button click.');
  };

  const initializeAppWithSession = async (sessionData: any) => {
    try {
      setLoading(true);
      
      // Initialize backend data with club context
      await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/init?club_name=${sessionData.club_name}`, {
        method: 'POST',
      });

      // Optimize: Fetch essential data first, then secondary data
      await Promise.all([
        fetchSessionWithClub(sessionData.club_name),
        fetchPlayersWithClub(sessionData.club_name)
      ]);
      
      // Fetch secondary data after main data loads
      await Promise.all([
        fetchCategories(),
        fetchMatchesWithClub(sessionData.club_name)
      ]);
    } catch (error) {
      console.error('Error initializing app:', error);
      Alert.alert('Error', 'Failed to initialize app');
    } finally {
      setLoading(false);
    }
  };

  const initializeApp = async () => {
    if (!clubSession) {
      console.error('No club session available for initialization');
      setLoading(false);
      return;
    }
    
    return initializeAppWithSession(clubSession);
  };

  const fetchPlayersWithClub = async (clubName: string) => {
    try {
      const timestamp = new Date().getTime();
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players?club_name=${clubName}&t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      const data = await response.json();
      console.log('🔄 Fetched players data:', data.map(p => ({id: p.id, name: p.name, isActive: p.isActive})));
      setPlayers(data);
      console.log('✅ Players state updated with', data.length, 'players');
    } catch (error) {
      console.error('❌ Error fetching players:', error);
    }
  };

  const fetchPlayers = async () => {
    if (!clubSession) {
      // Fallback to Main Club if no session
      return fetchPlayersWithClub('Main Club');
    }
    return fetchPlayersWithClub(clubSession.club_name);
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/categories`);
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchSessionWithClub = async (clubName: string) => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session?club_name=${clubName}`);
      const data = await response.json();
      
      // CRITICAL FIX: Only reset phase on FIRST app load, not during active play
      if (!hasInitialized) {
        // If session is in play/buffer phase but paused, reset to ready (app was closed/refreshed during pause)
        if ((data.phase === 'play' || data.phase === 'buffer') && data.paused) {
          console.log(`⚠️ Session paused in ${data.phase} phase on app initialization. Resetting to ready...`);
          await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/reset?club_name=${clubName}`, { method: 'POST' });
          // Refetch session after reset
          const resetResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session?club_name=${clubName}`);
          const resetData = await resetResponse.json();
          setSession(resetData);
        } else if ((data.phase === 'play' || data.phase === 'buffer') && !data.paused) {
          // Session is actively playing - resume it (don't pause!)
          console.log(`✅ Session is actively playing, continuing...`);
          setSession(data);
        } else {
          setSession(data);
        }
        setHasInitialized(true);
      } else {
        // During active gameplay, just update session state
        setSession(data);
      }
      
      // Auto-update session date if it's a new day
      const todayDate = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      if (data.sessionDate && data.sessionDate !== todayDate) {
        console.log(`📅 New day detected! Updating session date from ${data.sessionDate} to ${todayDate}`);
        await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/update-date?club_name=${clubName}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionDate: todayDate })
        });
        // Refresh session to get updated date
        const updatedResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session?club_name=${clubName}`);
        const updatedData = await updatedResponse.json();
        setSession(updatedData);
      }
    } catch (error) {
      console.error('Error fetching session:', error);
    }
  };

  const fetchSession = async () => {
    if (!clubSession) return;
    return fetchSessionWithClub(clubSession.club_name);
  };

  const fetchMatchesWithClub = async (clubName: string) => {
    try {
      // Add cache-busting parameter to ensure fresh data
      const timestamp = new Date().getTime();
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches?club_name=${clubName}&t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      const data = await response.json();
      console.log('Fetched matches data:', data.map(m => ({id: m.id, status: m.status, scoreA: m.scoreA, scoreB: m.scoreB})));
      setMatches(data);
    } catch (error) {
      console.error('Error fetching matches:', error);
    }
  };

  const fetchMatches = async () => {
    if (!clubSession) {
      // Fallback to Main Club if no session
      return fetchMatchesWithClub('Main Club');
    }
    return fetchMatchesWithClub(clubSession.club_name);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Memoized computation to prevent unnecessary recalculations
  const computeRoundsPlanned = useMemo(() => {
    if (!session) return 0;
    const totalSeconds = session.config.playSeconds + session.config.bufferSeconds;
    return Math.floor(7200 / Math.max(1, totalSeconds)); // 2 hours = 7200 seconds
  }, [session]); // Only recompute when session changes

  // Timer countdown function that updates the top right timer
  const startTimerCountdown = () => {
    // Clear any existing timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    // Start countdown timer
    timerRef.current = setInterval(async () => {
      setSession(prev => {
        if (!prev || prev.timeRemaining <= 0 || prev.phase === 'idle') {
          return prev;
        }
        
        const newTimeRemaining = prev.timeRemaining - 1;
        
        // One-minute warning siren (only during play phase)
        if (prev.phase === 'play' && newTimeRemaining === 60 && !oneMinuteWarningPlayedRef.current) {
          // playHorn('warning'); // Audio removed
          oneMinuteWarningPlayedRef.current = true;
          Alert.alert('⚠️ One Minute Warning', 'One minute remaining in this round!', [{ text: 'OK' }]);
        }
        
        if (newTimeRemaining <= 0) {
          // Reset warning flag when round ends
          oneMinuteWarningPlayedRef.current = false;
          // Time's up - trigger automatic phase transition
          handleTimeUp(prev);
        }
        
        return { ...prev, timeRemaining: newTimeRemaining };
      });
    }, 1000);
  };

  // Reset timer function - stops timer and resets to play time
  const resetTimer = async () => {
    try {
      // Stop the current timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      
      // Reset session via backend API
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/reset?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh data to get the reset session state
        await fetchSession();
        await fetchPlayers();
        await fetchCategories();
        await fetchMatches();
        
        Alert.alert('Session Reset', 'Timer stopped and reset to play time');
      }
    } catch (error) {
      console.error('Error resetting timer:', error);
      Alert.alert('Error', 'Failed to reset session');
    }
  };

  // Generate matches function (without starting timer)
  const generateMatches = async () => {
    if (!clubSession) return;
    
    try {
      // Initialize audio on user interaction
      // initializeAudio(); // Audio removed
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/generate-matches?club_name=${clubSession.club_name}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Refresh data to get the updated session state
        await fetchSession();
        await fetchPlayers();
        await fetchCategories();
        await fetchMatches();
        
        Alert.alert('Matches Generated!', 'Players can now see their court assignments. Go to Courts tab and click "Let\'s Play" when ready.');
      }
    } catch (error) {
      console.error('Error generating matches:', error);
      Alert.alert('Error', 'Failed to generate matches');
    }
  };

  // Start session function (just starts timer)
  const nextRound = async () => {
    if (!session || !clubSession) return;
    
    // Validate that all matches have scores saved
    const unsavedMatches = matches.filter(m => 
      m.roundIndex === session.currentRound && 
      m.status !== 'saved'
    );
    
    if (unsavedMatches.length > 0) {
      Alert.alert(
        '⚠️ Unsaved Scores',
        `${unsavedMatches.length} court(s) have unsaved scores. Please save all scores before proceeding to the next round.`,
        [{ text: 'OK' }]
      );
      return;
    }
    
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/next-round?club_name=${clubSession.club_name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        Alert.alert('✅ Round Ready', `Round ${session.currentRound + 1} is ready! Check courts and click "Let's Play" when ready.`);
        // Refresh all data
        await Promise.all([fetchSession(), fetchPlayers(), fetchMatches()]);
      } else {
        Alert.alert('Error', 'Failed to generate next round');
      }
    } catch (error) {
      console.error('Error generating next round:', error);
      Alert.alert('Error', 'Failed to generate next round');
    }
  };

  // Player management functions removed - logic moved inline to avoid scope issues

  // Start session function (just starts timer)
  const startSession = async () => {
    try {
      // Initialize audio on user interaction
      // initializeAudio(); // Audio removed
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/start?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // playHorn('start'); // Audio removed
        
        // Refresh data to get the updated session state
        // DO NOT re-fetch matches - this would reset manual player swaps
        await fetchSession();
        await fetchPlayers();
        await fetchCategories();
        
        // Timer will be started automatically by useEffect when session phase changes to 'play'
      }
    } catch (error) {
      console.error('Error starting session:', error);
      Alert.alert('Error', 'Failed to start session');
    }
  };

  // CSV Import Function
  const importCSV = async () => {
    try {
      console.log('🔄 Import CSV button clicked!');
      Alert.alert('Import Started', 'Starting CSV import process...');
      
      // Check if we're running in a web browser
      if (Platform.OS === 'web') {
        console.log('📱 Running on web platform');
        // For web, use HTML file input
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv,text/csv';
        input.onchange = async (event: any) => {
          const file = event.target.files[0];
          if (file) {
            console.log('📁 File selected:', file.name, file.size, file.type);
            Alert.alert('Processing', `Reading file: ${file.name}`);
            
            try {
              const csvText = await file.text();
              console.log('📄 CSV Text Length:', csvText.length);
              
              await processCSVData(csvText, file.name);
            } catch (error) {
              console.error('❌ Error reading file:', error);
              Alert.alert('Import Failed', `Could not read file: ${error}`);
            }
          }
        };
        input.click();
      } else {
        console.log('📱 Running on mobile platform');
        // For mobile, use expo-document-picker
        const result = await DocumentPicker.getDocumentAsync({
          type: ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
          copyToCacheDirectory: true,
        });

        if (result.type === 'cancel') {
          Alert.alert('Import Cancelled', 'No file selected');
          return;
        }

        console.log('📁 File selected:', result.name, result.size, result.type);

        if (result.type === 'success') {
          // Check if it's an Excel file
          if (result.name?.endsWith('.xlsx') || result.name?.endsWith('.xls')) {
            Alert.alert(
              'Excel File Detected', 
              `File: ${result.name}\n\nPlease convert your Excel file to CSV format first. You can do this by opening the file in Excel and using "Save As" → "CSV (Comma delimited)".`,
              [{ text: 'OK' }]
            );
            return;
          }

          Alert.alert('Processing', `Reading file: ${result.name}`);

          try {
            const response = await fetch(result.uri);
            const csvText = await response.text();
            console.log('📄 CSV Text Length:', csvText.length);
            
            await processCSVData(csvText, result.name);
          } catch (fetchError) {
            console.error('❌ Error reading file:', fetchError);
            Alert.alert('Import Failed - File Reading Error', `Could not read the selected file: ${fetchError}`);
          }
        }
      }
    } catch (error) {
      console.error('❌ Import error:', error);
      Alert.alert('Import Failed - Unexpected Error', `An unexpected error occurred: ${error}`);
    }
  };

  const addTestData = async () => {
    try {
      Alert.alert('Adding Test Data', 'Adding sample players...');
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/add-test-data`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        Alert.alert('✅ Test Data Added!', result.message + '\n\nRefreshing data...');
        await Promise.all([fetchSession(), fetchPlayers(), fetchCategories()]);
      } else {
        const errorText = await response.text();
        Alert.alert('❌ Failed to Add Test Data', errorText);
      }
    } catch (error) {
      console.error('Error adding test data:', error);
      Alert.alert('❌ Error', 'Failed to add test data');
    }
  };

  const processCSVData = async (csvText: string, fileName: string) => {
    try {
      console.log('🔍 Processing CSV data...');
      
      if (!csvText || csvText.trim().length === 0) {
        Alert.alert('Import Failed', 'The selected file appears to be empty.');
        return;
      }

      Alert.alert('Processing', 'Parsing CSV data...');
      
      const importedPlayers = parseCSV(csvText);
      
      console.log('👥 Parsed Players:', importedPlayers);
      
      if (importedPlayers.length === 0) {
        Alert.alert(
          'Import Failed - No Valid Data', 
          `No valid players found in CSV file.\n\nFile: ${fileName}\nFile preview:\n${csvText.substring(0, 150)}...\n\nRequired format:\nName,Category,Rating\nJohn,Beginner,3.2\nJane,Intermediate,4.5`,
          [{ text: 'OK' }]
        );
        return;
      }

      Alert.alert('Processing', `Found ${importedPlayers.length} players. Creating in database...`);

      // Import players with progress tracking
      let successCount = 0;
      let errorCount = 0;
      const errors: string[] = [];

      for (const player of importedPlayers) {
        try {
          console.log('➕ Creating player:', player);
          
          const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players?club_name=${clubSession?.club_name || 'Main Club'}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: player.name,
              category: player.category,
              rating: player.rating || 3.0
            })
          });

          if (response.ok) {
            successCount++;
            console.log(`✅ Created player: ${player.name}`);
          } else {
            const errorText = await response.text();
            console.error(`❌ Failed to create player ${player.name}:`, errorText);
            errorCount++;
            errors.push(`${player.name}: ${errorText}`);
          }
        } catch (error) {
          console.error(`❌ Error creating player ${player.name}:`, error);
          errorCount++;
          errors.push(`${player.name}: ${error}`);
        }
      }

      // Final result notification
      if (successCount > 0 && errorCount === 0) {
        Alert.alert(
          '✅ Import Successful!', 
          `Successfully imported ${successCount} players!\n\nRefreshing data...`,
          [{ text: 'OK' }]
        );
        await Promise.all([fetchSession(), fetchPlayers(), fetchCategories()]);
      } else if (successCount > 0 && errorCount > 0) {
        Alert.alert(
          '⚠️ Partial Import', 
          `Imported ${successCount} players successfully.\n${errorCount} failed.\n\nErrors:\n${errors.slice(0, 3).join('\n')}`,
          [{ text: 'OK' }]
        );
        await Promise.all([fetchSession(), fetchPlayers(), fetchCategories()]);
      } else {
        Alert.alert(
          '❌ Import Failed', 
          `Failed to import any players.\n\nErrors:\n${errors.slice(0, 3).join('\n')}`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('❌ Error processing CSV:', error);
      Alert.alert('Import Failed', `Error processing CSV data: ${error}`);
    }
  };

  // CSV Export Function
  const exportCSV = () => {
    try {
      const csvContent = generateCSV(matches, players);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `courtchime-session-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      Alert.alert('Success', 'CSV exported successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to export CSV');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor={colors.background} />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading CourtChime...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show login page if not authenticated
  if (!authenticated || !clubSession) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={colors.background} />
      
      {/* Header with Gradient */}
      <LinearGradient
        colors={colors.primaryGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          {/* Title on the left */}
          <View style={styles.headerLeft}>
            <Text style={styles.headerTitle}>CourtChime</Text>
            {clubSession && (
              <Text style={styles.clubName}>{clubSession.display_name}</Text>
            )}
          </View>
          
          {/* Logout button on top right */}
          <TouchableOpacity 
            style={styles.logoutButton}
            onPress={logout}
          >
            <Ionicons name="log-out-outline" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>

        {/* Session info pushed to the right below */}
        {session && (
          <View style={styles.sessionInfoContainer}>
            <View style={styles.sessionInfo}>
              <Text style={styles.sessionText}>
                Round {session.currentRound}/{computeRoundsPlanned} | {session.phase.toUpperCase()}
                {session.paused && ' (PAUSED)'}
              </Text>
              {session.timeRemaining > 0 && (
                <Text style={[
                  styles.timerText,
                  session.timeRemaining <= 60 && session.phase === 'play' ? styles.timerWarning : null,
                  session.phase === 'idle' ? styles.timerIdle : null
                ]}>
                  {formatTime(session.timeRemaining)}
                </Text>
              )}
            </View>
          </View>
        )}
      </LinearGradient>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'admin' && styles.activeTab]}
          onPress={() => setActiveTab('admin')}
        >
          <Ionicons 
            name="settings" 
            size={22} 
            color={activeTab === 'admin' ? colors.text : colors.textMuted} 
          />
          <Text style={[styles.tabText, activeTab === 'admin' && styles.activeTabText]}>
            Admin
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'dashboard' && styles.activeTab]}
          onPress={() => setActiveTab('dashboard')}
        >
          <Ionicons 
            name="grid" 
            size={22} 
            color={activeTab === 'dashboard' ? colors.text : colors.textMuted} 
          />
          <Text style={[styles.tabText, activeTab === 'dashboard' && styles.activeTabText]}>
            Courts
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'players' && styles.activeTab]}
          onPress={() => setActiveTab('players')}
        >
          <Ionicons 
            name="people" 
            size={22} 
            color={activeTab === 'players' ? colors.text : colors.textMuted} 
          />
          <Text style={[styles.tabText, activeTab === 'players' && styles.activeTabText]}>
            Standings
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView style={styles.content}>
          {activeTab === 'admin' && (
            <AdminConsole 
              session={session}
              categories={categories}
              players={players}
              clubSession={clubSession}
              onRefresh={() => {
                fetchSession();
                fetchPlayers();
                fetchCategories();
              }}
              onImportCSV={importCSV}
              onExportCSV={exportCSV}
              onGenerateMatches={generateMatches}
              onResetTimer={resetTimer}
              onAddTestData={addTestData}
              onFetchPlayers={fetchPlayers}
            />
          )}
          
          {activeTab === 'dashboard' && (
            <CourtsDashboard 
              session={session}
              matches={matches}
              players={players}
              onRefresh={() => {
                fetchMatches();
                fetchPlayers();
                fetchSession();
              }}
              onStartSession={startSession}
              onNextRound={nextRound}
              setMatches={setMatches}
            />
          )}
          
          {activeTab === 'players' && (
            <PlayersBoard players={players} matches={matches} session={session} />
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// Admin Console Component
function AdminConsole({ 
  session, 
  categories, 
  players, 
  clubSession,
  onRefresh,
  onImportCSV,
  onExportCSV,
  onGenerateMatches,
  onResetTimer,
  onAddTestData,
  onFetchPlayers
}: { 
  session: SessionState | null;
  categories: Category[];
  players: Player[];
  clubSession: any;
  onRefresh: () => void;
  onImportCSV: () => void;
  onExportCSV: () => void;
  onGenerateMatches: () => void;
  onResetTimer: () => void;
  onAddTestData: () => void;
  onFetchPlayers: () => Promise<void>;
}) {
  const [newPlayerName, setNewPlayerName] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [editingConfig, setEditingConfig] = useState(false);
  const [configForm, setConfigForm] = useState({
    numCourts: '6',
    playMinutes: '12',
    playSeconds: '00',
    bufferSeconds: '30',
    allowSingles: true,
    allowDoubles: true,
    allowCrossCategory: false,
    maximizeCourtUsage: false,
    rotationModel: 'legacy' as RotationModel
  });

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (categories.length > 0 && !selectedCategory) {
      setSelectedCategory(categories[0].name);
    }
  }, [categories]);

  useEffect(() => {
    // Only reset form when explicitly not editing AND when session first loads or changes significantly
    if (session?.config && !editingConfig) {
      const playMins = Math.floor(session.config.playSeconds / 60);
      const playSecs = session.config.playSeconds % 60;
      const newFormData = {
        numCourts: session.config.numCourts.toString(),
        playMinutes: playMins.toString(),
        playSeconds: playSecs.toString().padStart(2, '0'),
        bufferSeconds: session.config.bufferSeconds.toString(),
        allowSingles: session.config.allowSingles ?? true,
        allowDoubles: session.config.allowDoubles ?? true,
        allowCrossCategory: session.config.allowCrossCategory || false,
        maximizeCourtUsage: session.config.maximizeCourtUsage || false,
        rotationModel: (session.config.rotationModel || 'legacy') as RotationModel
      };
      
      // Only update if the form data is actually different to avoid unnecessary resets
      const currentFormString = JSON.stringify(configForm);
      const newFormString = JSON.stringify(newFormData);
      if (currentFormString !== newFormString) {
        setConfigForm(newFormData);
      }
    }
  }, [session?.config, editingConfig]); // More specific dependency

  const addPlayer = async () => {
    if (!newPlayerName.trim() || !selectedCategory) {
      Alert.alert('Error', 'Please enter player name and select category');
      return;
    }

    try {
      await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPlayerName.trim(),
          category: selectedCategory
        })
      });
      
      setNewPlayerName('');
      onRefresh();
    } catch (error) {
      Alert.alert('Error', 'Failed to add player');
    }
  };

  const saveConfiguration = async () => {
    if (!session) return;

    try {
      // Validate that at least one format is selected
      if (!configForm.allowSingles && !configForm.allowDoubles) {
        Alert.alert('Error', 'At least one format (Singles or Doubles) must be selected');
        return;
      }

      const playSeconds = parseInt(configForm.playMinutes) * 60 + parseInt(configForm.playSeconds);
      const bufferSeconds = parseInt(configForm.bufferSeconds);
      const numCourts = parseInt(configForm.numCourts);

      if (numCourts < 1 || numCourts > 20) {
        Alert.alert('Error', 'Number of courts must be between 1 and 20');
        return;
      }

      if (playSeconds < 60 || playSeconds > 3600) {
        Alert.alert('Error', 'Play time must be between 1 and 60 minutes');
        return;
      }

      if (bufferSeconds < 0 || bufferSeconds > 300) {
        Alert.alert('Error', 'Buffer time must be between 0 and 5 minutes');
        return;
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/config?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          numCourts,
          playSeconds,
          bufferSeconds,
          allowSingles: configForm.allowSingles,
          allowDoubles: configForm.allowDoubles,
          allowCrossCategory: configForm.allowCrossCategory,
          maximizeCourtUsage: configForm.maximizeCourtUsage,
          rotationModel: configForm.rotationModel
        })
      });

      if (response.ok) {
        setEditingConfig(false);
        onRefresh();
        Alert.alert('Success', 'Configuration saved successfully!');
      } else {
        const errorText = await response.text();
        Alert.alert('Error', `Failed to save configuration: ${errorText}`);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to save configuration');
    }
  };

  const pauseResume = async () => {
    try {
      const endpoint = session?.paused ? 'resume' : 'pause';
      await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/${endpoint}?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'POST'
      });
      onRefresh();
    } catch (error) {
      Alert.alert('Error', 'Failed to pause/resume session');
    }
  };

  const manualHorn = async () => {
    try {
      // initializeAudio(); // Audio removed
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/session/horn?club_name=${clubSession?.club_name || 'Main Club'}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        // playHorn(data.horn || 'manual'); // Audio removed
        onRefresh();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to activate horn');
    }
  };

  // Removed session check to prevent loading loop

  return (
    <View style={styles.adminContainer}>
      {/* Session Controls */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Session Configuration</Text>
          <TouchableOpacity 
            style={styles.editButtonLarge}
            onPress={() => {
              setEditingConfig(!editingConfig);
            }}
          >
            <Text style={styles.editButtonText}>
              {editingConfig ? 'Done' : 'Edit'}
            </Text>
          </TouchableOpacity>
        </View>
        
        {/* Session Date Display */}
        {session?.sessionDate && (
          <View style={styles.sessionDateContainer}>
            <Ionicons name="calendar-outline" size={16} color={colors.primary} />
            <Text style={styles.sessionDateText}>
              Session Date: {session.sessionDate}
            </Text>
          </View>
        )}
        
        {editingConfig ? (
          <View style={styles.configForm}>
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Courts:</Text>
              <TextInput
                style={styles.configInput}
                value={configForm.numCourts}
                onChangeText={(text) => setConfigForm({...configForm, numCourts: text})}
                keyboardType="numeric"
                maxLength={2}
              />
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Play Time:</Text>
              <View style={styles.timeInputs}>
                <TextInput
                  style={styles.timeInput}
                  value={configForm.playMinutes}
                  onChangeText={(text) => setConfigForm({...configForm, playMinutes: text})}
                  keyboardType="numeric"
                  maxLength={2}
                  placeholder="12"
                  placeholderTextColor={colors.textMuted}
                />
                <Text style={styles.timeColon}>:</Text>
                <TextInput
                  style={styles.timeInput}
                  value={configForm.playSeconds}
                  onChangeText={(text) => setConfigForm({...configForm, playSeconds: text})}
                  keyboardType="numeric"
                  maxLength={2}
                  placeholder="00"
                  placeholderTextColor={colors.textMuted}
                />
              </View>
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Buffer (sec):</Text>
              <TextInput
                style={styles.configInput}
                value={configForm.bufferSeconds}
                onChangeText={(text) => setConfigForm({...configForm, bufferSeconds: text})}
                keyboardType="numeric"
                maxLength={3}
              />
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Formats:</Text>
              <View style={styles.formatCheckboxes}>
                <TouchableOpacity
                  style={[styles.checkboxButton, configForm.allowSingles && styles.checkboxButtonActive]}
                  onPress={() => setConfigForm({...configForm, allowSingles: !configForm.allowSingles})}
                >
                  <Text style={[styles.checkboxButtonText, configForm.allowSingles && styles.checkboxButtonTextActive]}>
                    Singles
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.checkboxButton, configForm.allowDoubles && styles.checkboxButtonActive]}
                  onPress={() => setConfigForm({...configForm, allowDoubles: !configForm.allowDoubles})}
                >
                  <Text style={[styles.checkboxButtonText, configForm.allowDoubles && styles.checkboxButtonTextActive]}>
                    Doubles
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Model:</Text>
              <View style={styles.formatCheckboxes}>
                <TouchableOpacity
                  style={[styles.checkboxButton, configForm.rotationModel === 'legacy' && styles.checkboxButtonActive]}
                  onPress={() => setConfigForm({...configForm, rotationModel: 'legacy'})}
                >
                  <Text style={[styles.checkboxButtonText, configForm.rotationModel === 'legacy' && styles.checkboxButtonTextActive]}>
                    Legacy
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.checkboxButton, 
                    configForm.rotationModel === 'top_court' && styles.checkboxButtonActive,
                    !configForm.allowDoubles && styles.checkboxButtonDisabled
                  ]}
                  onPress={() => {
                    if (configForm.allowDoubles) {
                      setConfigForm({...configForm, rotationModel: 'top_court'});
                    } else {
                      Alert.alert('Top Court Unavailable', 'Top Court is Doubles-only. Please enable Doubles format first.');
                    }
                  }}
                  disabled={!configForm.allowDoubles}
                >
                  <Text style={[
                    styles.checkboxButtonText, 
                    configForm.rotationModel === 'top_court' && styles.checkboxButtonTextActive,
                    !configForm.allowDoubles && styles.checkboxButtonTextDisabled
                  ]}>
                    Top Court
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Cross-Category:</Text>
              <TouchableOpacity
                style={[styles.toggleButton, configForm.allowCrossCategory && styles.toggleButtonActive]}
                onPress={() => setConfigForm({...configForm, allowCrossCategory: !configForm.allowCrossCategory})}
              >
                <Text style={[styles.toggleButtonText, configForm.allowCrossCategory && styles.toggleButtonTextActive]}>
                  {configForm.allowCrossCategory ? 'Enabled' : 'Disabled'}
                </Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.configRow}>
              <Text style={styles.configLabel}>Maximize Courts:</Text>
              <TouchableOpacity
                style={[styles.toggleButton, configForm.maximizeCourtUsage && styles.toggleButtonActive]}
                onPress={() => setConfigForm({...configForm, maximizeCourtUsage: !configForm.maximizeCourtUsage})}
              >
                <Text style={[styles.toggleButtonText, configForm.maximizeCourtUsage && styles.toggleButtonTextActive]}>
                  {configForm.maximizeCourtUsage ? 'Enabled' : 'Disabled'}
                </Text>
              </TouchableOpacity>
            </View>
            
            <TouchableOpacity 
              style={styles.saveButton}
              onPress={saveConfiguration}
            >
              <Text style={styles.saveButtonText}>Save Configuration</Text>
            </TouchableOpacity>
          </View>
        ) : session?.config ? (
          <View style={styles.sessionStats}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Courts</Text>
              <Text style={styles.statValue}>{session.config.numCourts}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Rounds Planned</Text>
              <Text style={styles.statValue}>{Math.floor(7200 / Math.max(1, session.config.playSeconds + session.config.bufferSeconds))}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Format</Text>
              <Text style={styles.statValue}>
                {(() => {
                  const formats = [];
                  if (session.config.allowSingles) formats.push('Singles');
                  if (session.config.allowDoubles) formats.push('Doubles');
                  return formats.length > 0 ? formats.join(' + ') : 'None';
                })()}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Play Time</Text>
              <Text style={styles.statValue}>{formatTime(session.config.playSeconds)}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Buffer</Text>
              <Text style={styles.statValue}>{session.config.bufferSeconds}s</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Cross-Category</Text>
              <Text style={styles.statValue}>{session.config.allowCrossCategory ? 'Yes' : 'No'}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Maximize Courts</Text>
              <Text style={styles.statValue}>{session.config.maximizeCourtUsage ? 'Yes' : 'No'}</Text>
            </View>
          </View>
        ) : (
          <Text style={styles.emptyText}>Loading session configuration...</Text>
        )}

        {/* Session Control Buttons */}
        <View style={styles.sessionControlButtons}>
          <TouchableOpacity 
            onPress={onGenerateMatches}
            disabled={players.length < 4 || (session && session.phase !== 'idle')}
            style={(players.length < 4 || (session && session.phase !== 'idle')) && styles.buttonDisabled}
          >
            <LinearGradient
              colors={players.length < 4 || (session && session.phase !== 'idle') 
                ? [colors.textMuted, colors.textLight] 
                : colors.primaryGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.primaryButton}
            >
              <Ionicons name="calendar" size={20} color="#ffffff" style={styles.buttonIcon} />
              <Text style={styles.buttonText}>Generate Matches</Text>
            </LinearGradient>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.secondaryButton, !session || session.phase === 'idle' ? styles.buttonDisabled : {}]}
            onPress={onResetTimer}
            disabled={!session || session.phase === 'idle'}
          >
            <Ionicons name="stop" size={20} color={colors.textSecondary} style={styles.buttonIcon} />
            <Text style={styles.secondaryButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* CSV Import/Export */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Data Management</Text>
        <Text style={styles.cardSubtitle}>
          Import/Export player data. CSV Format: Name, Category, Rating (optional)
        </Text>
        <Text style={styles.cardSubtitle}>
          📝 Excel files: Please convert to CSV first (Excel → Save As → CSV)
        </Text>
        
        <View style={styles.buttonRow}>
          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={onImportCSV}
          >
            <Ionicons name="cloud-upload" size={20} color={colors.primary} style={styles.buttonIcon} />
            <Text style={styles.secondaryButtonText}>Import CSV</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={onExportCSV}
          >
            <Ionicons name="cloud-download" size={20} color={colors.primary} style={styles.buttonIcon} />
            <Text style={styles.secondaryButtonText}>Export CSV</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity 
          onPress={onAddTestData}
        >
          <LinearGradient
            colors={[colors.accent, colors.teal]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={[styles.primaryButton, { marginTop: 12 }]}
          >
            <Ionicons name="flask" size={20} color="#ffffff" style={styles.buttonIcon} />
            <Text style={styles.buttonText}>Add Test Data (12 Players)</Text>
          </LinearGradient>
        </TouchableOpacity>
        
        <Text style={styles.helpText}>
          CSV Format: Player Name, Player Level, Date (optional)
        </Text>
      </View>

      {/* Add Player */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Add Player</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Player Name</Text>
          <TextInput
            style={styles.textInput}
            value={newPlayerName}
            onChangeText={setNewPlayerName}
            placeholder="Enter player name"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="words"
            returnKeyType="done"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Category</Text>
          <View style={styles.categoryButtons}>
            {categories.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoryButton,
                  selectedCategory === cat.name && styles.categoryButtonActive
                ]}
                onPress={() => setSelectedCategory(cat.name)}
              >
                <Text style={[
                  styles.categoryButtonText,
                  selectedCategory === cat.name && styles.categoryButtonTextActive
                ]}>
                  {cat.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity 
          style={[styles.primaryButton, !newPlayerName.trim() && styles.buttonDisabled]}
          onPress={addPlayer}
          disabled={!newPlayerName.trim()}
        >
          <Text style={styles.buttonText}>Add Player</Text>
        </TouchableOpacity>
      </View>

      {/* Player Roster */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Player Roster ({players.filter(p => p.isActive).length} playing today / {players.length} total)</Text>
        {players.length === 0 ? (
          <Text style={styles.emptyText}>No players added yet</Text>
        ) : (
          <View style={styles.playersList}>
            {categories.map((category) => {
              const categoryPlayers = players.filter(p => p.category === category.name);
              if (categoryPlayers.length === 0) return null;
              
              return (
                <View key={category.id} style={styles.categorySection}>
                  <Text style={styles.categoryHeader}>{category.name} ({categoryPlayers.length})</Text>
                  {categoryPlayers.map((player) => (
                    <View key={`${player.id}-${player.isActive}`} style={[
                      styles.playerItem,
                      !player.isActive && styles.playerItemInactive
                    ]}>
                      <View style={styles.playerMainInfo}>
                        <Text style={[
                          styles.playerName,
                          !player.isActive && styles.playerNameInactive
                        ]}>
                          {player.name}
                        </Text>
                        {!player.isActive && (
                          <Text style={styles.notPlayingBadge}>Not Playing Today</Text>
                        )}
                        <View style={styles.playerStats}>
                          <Text style={styles.playerStat}>W: {player.stats.wins}</Text>
                          <Text style={styles.playerStat}>L: {player.stats.losses}</Text>
                          <Text style={styles.playerStat}>Sits: {player.sitCount}</Text>
                        </View>
                      </View>
                      <View style={styles.playerActions}>
                        <TouchableOpacity
                          onPress={async () => {
                            console.log('🚀 BUTTON CLICKED! Starting toggle for:', { playerId: player.id, playerName: player.name, currentStatus: player.isActive });
                            alert(`Button clicked! Toggling ${player.name} (currently ${player.isActive ? 'active' : 'inactive'})`);
                            
                            try {
                              console.log('📞 Making API call to:', `${EXPO_PUBLIC_BACKEND_URL}/api/players/${player.id}/toggle-active`);
                              const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players/${player.id}/toggle-active?club_name=${clubSession?.club_name || 'Main Club'}`, {
                                method: 'PATCH',
                                headers: { 'Content-Type': 'application/json' }
                              });
                              
                              console.log('📡 API Response received:', response.status, response.statusText);
                              
                              if (response.ok) {
                                const result = await response.json();
                                console.log('✅ API Response data:', result);
                                alert(`API Success! Player is now ${result.isActive ? 'active' : 'inactive'}`);
                                
                                console.log('🔄 About to refresh players...');
                                await onFetchPlayers();
                                console.log('✅ onFetchPlayers completed');
                                
                              } else {
                                const errorText = await response.text();
                                console.error('❌ API Error:', response.status, errorText);
                                alert(`API Error: ${response.status} - ${errorText}`);
                              }
                            } catch (error) {
                              console.error('❌ Network/JS Error:', error);
                              alert(`Error: ${error.message}`);
                            }
                          }}
                          style={[
                            styles.playerActionButton,
                            player.isActive ? styles.removeButton : styles.addButton
                          ]}
                        >
                          <Ionicons 
                            name={player.isActive ? "remove-circle" : "add-circle"} 
                            size={20} 
                            color="#ffffff" 
                          />
                          <Text style={styles.playerActionText}>
                            {player.isActive ? 'Remove' : 'Add'}
                          </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => {
                            Alert.alert(
                              '⚠️ Permanent Delete', 
                              `Are you sure you want to permanently delete ${player.name}? This will remove all their historical data and cannot be undone.`,
                              [
                                { text: 'Cancel', style: 'cancel' },
                                { 
                                  text: 'Delete Forever', 
                                  style: 'destructive',
                                  onPress: async () => {
                                    try {
                                      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players/${player.id}?club_name=${clubSession?.club_name || 'Main Club'}`, {
                                        method: 'DELETE'
                                      });
                                      
                                      if (response.ok) {
                                        Alert.alert('Deleted', `${player.name} has been permanently deleted`);
                                        await onFetchPlayers(); // Refresh player list
                                      } else {
                                        Alert.alert('Error', 'Failed to delete player');
                                      }
                                    } catch (error) {
                                      console.error('Error deleting player:', error);
                                      Alert.alert('Error', 'Failed to delete player');
                                    }
                                  }
                                }
                              ]
                            );
                          }}
                          style={[styles.playerActionButton, styles.deleteButton]}
                        >
                          <Ionicons name="trash" size={20} color="#ffffff" />
                          <Text style={styles.playerActionText}>Delete</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  ))}
                </View>
              );
            })}
          </View>
        )}
      </View>
    </View>
  );
}

// Courts Dashboard Component (same structure, updated styles)
// Draggable Player Component with tap-to-select functionality
function DraggablePlayer({ 
  playerId, 
  playerName, 
  matchId, 
  team, 
  index, 
  onMove, 
  onSwap,
  isSelected,
  onSelect 
}: {
  playerId: string;
  playerName: string;
  matchId: string;
  team: 'A' | 'B';
  index: number;
  onMove: (fromMatchId: string, fromTeam: 'A' | 'B', fromIndex: number, toMatchId: string, toTeam: 'A' | 'B', toIndex: number) => void;
  onSwap: (match1Id: string, team1: 'A' | 'B', index1: number, match2Id: string, team2: 'A' | 'B', index2: number) => void;
  isSelected: boolean;
  onSelect: (matchId: string, team: 'A' | 'B', index: number) => void;
}) {
  
  const handlePress = () => {
    onSelect(matchId, team, index);
  };
  
  return (
    <TouchableOpacity
      style={[styles.draggablePlayer, isSelected && styles.selectedPlayer]}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <View style={[styles.playerChip, isSelected && styles.selectedPlayerChip]}>
        <Ionicons name="person" size={16} color={isSelected ? '#ffffff' : colors.primary} />
        <Text style={[styles.draggablePlayerName, isSelected && styles.selectedPlayerName]}>{playerName}</Text>
        <Ionicons name="swap-horizontal" size={16} color={isSelected ? '#ffffff' : colors.textMuted} />
      </View>
    </TouchableOpacity>
  );
}

// Drop Zone Component removed - using tap-to-swap instead

function CourtsDashboard({ 
  session, 
  matches, 
  players, 
  onRefresh,
  onStartSession,
  onNextRound,
  setMatches
}: { 
  session: SessionState | null;
  matches: Match[];
  players: Player[];
  onRefresh: () => void;
  onStartSession: () => void;
  onNextRound: () => void;
  setMatches: (matches: Match[]) => void;
}) {
  const [scoreInputs, setScoreInputs] = useState<{[matchId: string]: {scoreA: string, scoreB: string}}>({});
  const [winnerSelections, setWinnerSelections] = useState<{[matchId: string]: 'A' | 'B' | null}>({});
  const [originalMatches, setOriginalMatches] = useState<Match[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<{matchId: string, team: 'A' | 'B', index: number | string} | null>(null);

  // Calculate sitting out players - using useMemo for better performance
  const sittingOutPlayers = useMemo(() => {
    const activePlayers = players.filter(p => p.isActive);
    const playingPlayerIds = new Set<string>();
    
    // Collect all player IDs in current matches
    matches.forEach(match => {
      match.teamA.forEach((id: string) => playingPlayerIds.add(id));
      match.teamB.forEach((id: string) => playingPlayerIds.add(id));
    });
    
    // Return players who are active but not in any match
    return activePlayers.filter(p => !playingPlayerIds.has(p.id));
  }, [matches, players]);

  // Store original matches when they first load - but only in ready phase
  useEffect(() => {
    console.log('🔍 useEffect triggered - matches.length:', matches.length, 'originalMatches.length:', originalMatches.length, 'session phase:', session?.phase);
    if (matches.length > 0 && session?.phase === 'ready') {
      // Clear and store fresh original matches when entering ready phase with new matches
      if (originalMatches.length === 0 || session?.currentRound !== originalMatches[0]?.roundIndex) {
        console.log('✅ Storing fresh original matches:', matches.length, 'matches');
        setOriginalMatches([...matches]);
      }
    } else if (session?.phase !== 'ready' && originalMatches.length > 0) {
      // Clear original matches when leaving ready phase
      console.log('🧹 Clearing original matches - not in ready phase');
      setOriginalMatches([]);
    }
  }, [matches, session?.phase, session?.currentRound]); // Depend on matches, session phase, and current round

  const getPlayerName = (playerId: string) => {
    console.log('🔍 Getting player name for ID:', playerId);
    console.log('🔍 Available players:', players.length, players.map(p => ({id: p.id, name: p.name})));
    const player = players.find(p => p.id === playerId);
    const result = player ? player.name : 'Unknown Player';
    console.log('🔍 Result:', result);
    return result;
  };

  const resetToOriginal = () => {
    console.log('🔄 Reset to Original clicked');
    console.log('🔄 Original matches count:', originalMatches.length);
    console.log('🔄 Current matches count:', matches.length);
    if (originalMatches.length > 0) {
      console.log('🔄 Resetting matches to original');
      setMatches([...originalMatches]);
      setSelectedPlayer(null);
    } else {
      console.log('❌ No original matches stored - storing current as original');
      // If no original matches stored, store current ones as original
      if (matches.length > 0) {
        setOriginalMatches([...matches]);
      }
    }
  };

  const handlePlayerSelect = (matchId: string, team: 'A' | 'B', index: number) => {
    if (!selectedPlayer) {
      // First selection
      setSelectedPlayer({ matchId, team, index });
    } else {
      // Second selection - perform swap
      if (selectedPlayer.matchId === matchId && selectedPlayer.team === team && selectedPlayer.index === index) {
        // Same player clicked - deselect
        setSelectedPlayer(null);
      } else if (selectedPlayer.matchId === 'sitout') {
        // Sitout player selected, now tapping court player - swap with sitout
        const match = matches.find(m => m.id === matchId);
        if (match) {
          const courtTeam = team === 'A' ? match.teamA : match.teamB;
          const courtPlayerId = courtTeam[index];
          handlePlayerSwap(matchId, courtPlayerId);
        }
      } else {
        // Court to court swap - use existing logic
        swapPlayers(
          selectedPlayer.matchId, selectedPlayer.team, selectedPlayer.index,
          matchId, team, index
        );
        setSelectedPlayer(null);
      }
    }
  };

  const swapPlayers = async (match1Id: string, team1: 'A' | 'B', index1: number, match2Id: string, team2: 'A' | 'B', index2: number) => {
    const updatedMatches = [...matches];
    
    // Find matches
    const match1Index = updatedMatches.findIndex(m => m.id === match1Id);
    const match2Index = updatedMatches.findIndex(m => m.id === match2Id);
    
    if (match1Index === -1 || match2Index === -1) return;
    
    const match1 = updatedMatches[match1Index];
    const match2 = updatedMatches[match2Index];
    
    const team1Players = team1 === 'A' ? match1.teamA : match1.teamB;
    const team2Players = team2 === 'A' ? match2.teamA : match2.teamB;
    
    if (index1 >= team1Players.length || index2 >= team2Players.length) return;
    
    // Swap players
    const temp = team1Players[index1];
    team1Players[index1] = team2Players[index2];
    team2Players[index2] = temp;
    
    setMatches(updatedMatches);
    
    // Save both matches to backend
    try {
      await Promise.all([
        fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches/${match1Id}?club_name=${clubSession?.club_name || 'Main Club'}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            teamA: match1.teamA,
            teamB: match1.teamB
          })
        }),
        fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches/${match2Id}?club_name=${clubSession?.club_name || 'Main Club'}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            teamA: match2.teamA,
            teamB: match2.teamB
          })
        })
      ]);
      console.log('✅ Court-to-court swap saved to backend');
    } catch (error) {
      console.error('❌ Error saving swap to backend:', error);
    }
  };

  const validateCourts = () => {
    const currentMatches = matches;
    let isValid = true;
    let errors: string[] = [];
    
    currentMatches.forEach((match, index) => {
      const totalPlayers = match.teamA.length + match.teamB.length;
      const expectedPlayers = match.matchType === 'singles' ? 2 : 4;
      
      if (totalPlayers !== expectedPlayers) {
        isValid = false;
        errors.push(`Court ${match.courtIndex + 1}: Expected ${expectedPlayers} players, has ${totalPlayers}`);
      }
    });
    
    if (!isValid) {
      Alert.alert('Invalid Court Configuration', errors.join('\n'));
    }
    
    return isValid;
  };

  const getCurrentMatches = () => {
    if (!session) return [];
    return matches.filter(m => m.roundIndex === session.currentRound);
  };

  const movePlayer = (matchId: string, fromTeam: 'A' | 'B', fromIndex: number, toTeam: 'A' | 'B', toIndex: number) => {
    console.log('Moving player within match:', { matchId, fromTeam, fromIndex, toTeam, toIndex });
    
    const match = matches.find(m => m.id === matchId);
    if (!match) return;

    const sourceTeam = fromTeam === 'A' ? [...match.teamA] : [...match.teamB];
    const targetTeam = toTeam === 'A' ? [...match.teamA] : [...match.teamB];

    // Swap or move players
    const temp = sourceTeam[fromIndex];
    
    if (fromTeam === toTeam) {
      // Swapping within same team
      sourceTeam[fromIndex] = targetTeam[toIndex];
      targetTeam[toIndex] = temp;
    } else {
      // Moving between teams
      sourceTeam[fromIndex] = targetTeam[toIndex];
      targetTeam[toIndex] = temp;
    }

    // Update match
    setMatches(prevMatches => 
      prevMatches.map(m => {
        if (m.id === matchId) {
          return {
            ...m,
            teamA: fromTeam === 'A' ? sourceTeam : targetTeam,
            teamB: fromTeam === 'B' ? sourceTeam : targetTeam
          };
        }
        return m;
      })
    );
  };

  const handlePlayerSwap = async (targetMatchId: string, targetPlayerId: string) => {
    if (!selectedPlayer) return;

    // Handle sitout to court OR court to sitout swaps
    if (selectedPlayer.matchId === 'sitout' || targetMatchId === 'sitout') {
      // One player is in sitout
      const courtMatchId = selectedPlayer.matchId === 'sitout' ? targetMatchId : selectedPlayer.matchId;
      const courtMatch = matches.find(m => m.id === courtMatchId);
      const sitoutPlayerId = selectedPlayer.matchId === 'sitout' ? selectedPlayer.index : targetPlayerId;

      if (!courtMatch) {
        console.log('Court match not found');
        setSelectedPlayer(null);
        return;
      }

      // Get the court player details
      let courtPlayerTeam: 'A' | 'B' | null = null;
      let courtPlayerIndex: number = -1;

      if (selectedPlayer.matchId !== 'sitout') {
        // Selected player is on court, target is sitout
        courtPlayerTeam = selectedPlayer.team;
        courtPlayerIndex = selectedPlayer.index;
      } else {
        // Selected player is sitout, need to find target player on court
        courtMatch.teamA.forEach((pId, idx) => {
          if (pId === targetPlayerId) {
            courtPlayerTeam = 'A';
            courtPlayerIndex = idx;
          }
        });
        courtMatch.teamB.forEach((pId, idx) => {
          if (pId === targetPlayerId) {
            courtPlayerTeam = 'B';
            courtPlayerIndex = idx;
          }
        });
      }

      if (courtPlayerTeam === null || courtPlayerIndex === -1) {
        console.log('Could not find court player');
        setSelectedPlayer(null);
        return;
      }

      // Swap: Replace court player with sitout player
      setMatches(prevMatches =>
        prevMatches.map(m => {
          if (m.id === courtMatchId) {
            const team = courtPlayerTeam === 'A' ? [...m.teamA] : [...m.teamB];
            team[courtPlayerIndex] = sitoutPlayerId;

            return {
              ...m,
              teamA: courtPlayerTeam === 'A' ? team : m.teamA,
              teamB: courtPlayerTeam === 'B' ? team : m.teamB
            };
          }
          return m;
        })
      );

      // Save swap to backend
      try {
        const matchToUpdate = updatedMatches.find(m => m.id === courtMatchId);
        if (matchToUpdate) {
          await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches/${courtMatchId}?club_name=${clubSession?.club_name || 'Main Club'}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              teamA: matchToUpdate.teamA,
              teamB: matchToUpdate.teamB
            })
          });
        }
      } catch (error) {
        console.error('Error saving swap to backend:', error);
      }

      console.log('Swapped court player with sitout player');
      setSelectedPlayer(null);
      return;
    }

    // Handle court to court swaps (existing logic)
    const targetMatch = matches.find(m => m.id === targetMatchId);
    if (!targetMatch) {
      setSelectedPlayer(null);
      return;
    }

    let targetTeam: 'A' | 'B' | null = null;
    let targetIndex = -1;

    targetMatch.teamA.forEach((pId, idx) => {
      if (pId === targetPlayerId) {
        targetTeam = 'A';
        targetIndex = idx;
      }
    });

    targetMatch.teamB.forEach((pId, idx) => {
      if (pId === targetPlayerId) {
        targetTeam = 'B';
        targetIndex = idx;
      }
    });

    if (targetTeam === null) {
      setSelectedPlayer(null);
      return;
    }

    if (selectedPlayer.matchId === targetMatchId) {
      // Same match - swap within match
      movePlayer(selectedPlayer.matchId, selectedPlayer.team, selectedPlayer.index, targetTeam, targetIndex);
    } else {
      // Different matches - swap between matches
      const selectedMatch = matches.find(m => m.id === selectedPlayer.matchId);
      if (!selectedMatch) {
        setSelectedPlayer(null);
        return;
      }

      const selectedTeam = selectedPlayer.team === 'A' ? [...selectedMatch.teamA] : [...selectedMatch.teamB];
      const targetTeamArray = targetTeam === 'A' ? [...targetMatch.teamA] : [...targetMatch.teamB];

      const temp = selectedTeam[selectedPlayer.index];
      selectedTeam[selectedPlayer.index] = targetTeamArray[targetIndex];
      targetTeamArray[targetIndex] = temp;

      setMatches(prevMatches =>
        prevMatches.map(m => {
          if (m.id === selectedPlayer.matchId) {
            return {
              ...m,
              teamA: selectedPlayer.team === 'A' ? selectedTeam : m.teamA,
              teamB: selectedPlayer.team === 'B' ? selectedTeam : m.teamB
            };
          }
          if (m.id === targetMatchId) {
            return {
              ...m,
              teamA: targetTeam === 'A' ? targetTeamArray : m.teamA,
              teamB: targetTeam === 'B' ? targetTeamArray : m.teamB
            };
          }
          return m;
        })
      );
    }

    setSelectedPlayer(null);
  };

  const saveScore = async (match: Match) => {
    const scores = scoreInputs[match.id];
    if (!scores) {
      Alert.alert('Error', 'Please enter scores for both teams');
      return;
    }

    const scoreA = parseInt(scores.scoreA);
    const scoreB = parseInt(scores.scoreB);

    if (isNaN(scoreA) || isNaN(scoreB)) {
      Alert.alert('Error', 'Please enter valid numeric scores');
      return;
    }

    if (scoreA < 0 || scoreB < 0 || scoreA > 50 || scoreB > 50) {
      Alert.alert('Error', 'Scores must be between 0 and 50');
      return;
    }

    try {
      console.log('Saving score for match:', match.id, 'Current status:', match.status);
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches/${match.id}/score`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scoreA, scoreB })
      });

      if (response.ok) {
        const updatedMatch = await response.json();
        console.log('Score saved successfully, updated match status:', updatedMatch.status);
        
        // Immediately update the specific match in state
        setMatches(prevMatches => 
          prevMatches.map(m => 
            m.id === match.id 
              ? { ...m, status: updatedMatch.status, scoreA: updatedMatch.scoreA, scoreB: updatedMatch.scoreB }
              : m
          )
        );
        
        // Clear score inputs for this match
        setScoreInputs(prev => {
          const newInputs = { ...prev };
          delete newInputs[match.id];
          return newInputs;
        });

        // Also refresh matches data as backup
        console.log('Refreshing matches data...');
        await fetchMatches();
        console.log('Matches data refreshed');
        
        Alert.alert('Success', 'Score saved successfully!');
      } else {
        const errorData = await response.json();
        console.error('Failed to save score:', errorData);
        Alert.alert('Error', `Failed to save score: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving score:', error);
      Alert.alert('Error', 'Failed to save score');
    }
  };

  const updateScoreInput = (matchId: string, team: 'A' | 'B', value: string) => {
    setScoreInputs(prev => ({
      ...prev,
      [matchId]: {
        ...prev[matchId],
        [`score${team}`]: value
      }
    }));
  };

  const selectWinner = (matchId: string, team: 'A' | 'B') => {
    setWinnerSelections(prev => ({
      ...prev,
      [matchId]: prev[matchId] === team ? null : team // Toggle selection
    }));
  };

  const saveWinner = async (match: Match) => {
    const winner = winnerSelections[match.id];
    if (!winner) {
      Alert.alert('Error', 'Please select a winning team');
      return;
    }

    try {
      console.log('Saving winner for match:', match.id, 'Winner:', winner);
      
      // For MVP, we'll use the score endpoint with dummy scores based on winner
      const scoreA = winner === 'A' ? 11 : 9;
      const scoreB = winner === 'B' ? 11 : 9;
      
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/matches/${match.id}/score`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scoreA, scoreB })
      });

      if (response.ok) {
        const updatedMatch = await response.json();
        console.log('Winner saved successfully');
        
        // Update match in state
        setMatches(prevMatches => 
          prevMatches.map(m => 
            m.id === match.id 
              ? { ...m, status: updatedMatch.status, scoreA: updatedMatch.scoreA, scoreB: updatedMatch.scoreB }
              : m
          )
        );
        
        // Clear winner selection
        setWinnerSelections(prev => {
          const newSelections = { ...prev };
          delete newSelections[match.id];
          return newSelections;
        });
        
        await fetchMatches();
        Alert.alert('Success', 'Winner saved successfully!');
      } else {
        const errorData = await response.json();
        console.error('Failed to save winner:', errorData);
        Alert.alert('Error', `Failed to save winner: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving winner:', error);
      Alert.alert('Error', 'Failed to save winner');
    }
  };

  if (!session) return <Text style={styles.loadingText}>Loading courts...</Text>;
  
  // Helper function to determine if Next Round button should be enabled
  const isNextRoundEnabled = () => {
    // Button is enabled ONLY when buffer phase ends (timeRemaining reaches 0)
    // Button should be DISABLED during play phase and buffer phase countdown
    return session.phase === 'buffer' && session.timeRemaining === 0;
  };

  // Next Round Button Component (visible during play and buffer phases)
  const NextRoundButton = () => {
    // Show button during play and buffer phases (when rounds are in progress)
    if (session.phase !== 'play' && session.phase !== 'buffer') {
      return null;
    }
    
    const enabled = isNextRoundEnabled();
    
    return (
      <View style={styles.nextRoundContainer}>
        <TouchableOpacity 
          onPress={onNextRound}
          disabled={!enabled}
          style={styles.nextRoundButton}
        >
          <LinearGradient
            colors={enabled ? [colors.success, colors.success] : ['#e0e0e0', '#bdbdbd']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={[
              styles.nextRoundButtonGradient,
              !enabled && styles.nextRoundButtonDisabledGradient
            ]}
          >
            <Ionicons 
              name="arrow-forward" 
              size={20} 
              color={enabled ? "#ffffff" : "#888888"} 
            />
            <Text style={[
              styles.nextRoundButtonText,
              !enabled && styles.nextRoundButtonTextDisabled
            ]}>
              Next Round
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    );
  };
  
  if (session.phase === 'idle') {
    return (
      <View style={styles.dashboardContainer}>
        <View style={styles.card}>
          <Ionicons name="tennisball" size={48} color={colors.success} />
          <Text style={styles.emptyTitle}>Session Not Started</Text>
          <Text style={styles.emptyText}>
            Generate matches from the Admin tab to see court assignments
          </Text>
        </View>
      </View>
    );
  }

  if (session.phase === 'ready') {
    const currentMatches = matches;
    return (
      <View style={styles.dashboardContainer}>
        {/* Show court assignments */}
        <ScrollView style={styles.courtsScroll}>
          {Array.from({ length: session.config.numCourts }, (_, i) => i).map((courtIndex) => {
            const match = currentMatches.find(m => m.courtIndex === courtIndex);
            
            return (
              <View key={courtIndex} style={styles.courtCard}>
                <View style={styles.courtHeader}>
                  <Text style={styles.courtTitle}>Court {courtIndex + 1}</Text>
                  {session?.config?.rotationModel === 'top_court' && courtIndex === 0 && (
                    <View style={styles.topCourtBadge}>
                      <Text style={styles.topCourtBadgeText}>👑 Top Court</Text>
                    </View>
                  )}
                  {match && (
                    <>
                      <Text style={styles.matchDate}>
                        {new Date(match.matchDate).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </Text>
                    </>
                  )}
                </View>
                {match ? (
                  <View style={styles.courtMatch}>
                    <View style={styles.matchTeams}>
                      <View style={styles.team}>
                        <Text style={styles.teamLabel}>Team A:</Text>
                        {match.teamA.map((playerId, playerIndex) => (
                          <DraggablePlayer 
                            key={`${match.id}-A-${playerIndex}`}
                            playerId={playerId}
                            playerName={getPlayerName(playerId)}
                            matchId={match.id}
                            team="A"
                            index={playerIndex}
                            onMove={movePlayer}
                            onSwap={swapPlayers}
                            isSelected={selectedPlayer?.matchId === match.id && selectedPlayer?.team === 'A' && selectedPlayer?.index === playerIndex}
                            onSelect={handlePlayerSelect}
                          />
                        ))}
                      </View>
                      <Text style={styles.vs}>VS</Text>
                      <View style={styles.team}>
                        <Text style={styles.teamLabel}>Team B:</Text>
                        {match.teamB.map((playerId, playerIndex) => (
                          <DraggablePlayer 
                            key={`${match.id}-B-${playerIndex}`}
                            playerId={playerId}
                            playerName={getPlayerName(playerId)}
                            matchId={match.id}
                            team="B"
                            index={playerIndex}
                            onMove={movePlayer}
                            onSwap={swapPlayers}
                            isSelected={selectedPlayer?.matchId === match.id && selectedPlayer?.team === 'B' && selectedPlayer?.index === playerIndex}
                            onSelect={handlePlayerSelect}
                          />
                        ))}
                      </View>
                    </View>
                    <Text style={styles.matchType}>{match.matchType.toUpperCase()}</Text>
                  </View>
                ) : (
                  <Text style={styles.emptyCourt}>No match assigned</Text>
                )}
              </View>
            );
          })}
        </ScrollView>

        {/* Sitting Out Section - Interactive for player swapping */}
        {sittingOutPlayers.length > 0 && (
          <View style={styles.sittingOutSection}>
            <View style={styles.sittingOutHeader}>
              <Ionicons name="pause-circle-outline" size={24} color={colors.warning} />
              <Text style={styles.sittingOutTitle}>
                Sitting Out ({sittingOutPlayers.length})
              </Text>
            </View>
            <View style={styles.sittingOutList}>
              {sittingOutPlayers.map((player) => (
                <TouchableOpacity
                  key={player.id}
                  style={[
                    styles.sittingOutPlayer,
                    selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id && styles.sittingOutPlayerSelected
                  ]}
                  onPress={() => {
                    if (selectedPlayer) {
                      // Player already selected from court - move them to sitout
                      handlePlayerSwap('sitout', player.id);
                    } else {
                      // Select this sitout player to move to court
                      setSelectedPlayer({ matchId: 'sitout', team: 'A', index: player.id });
                    }
                  }}
                >
                  <Ionicons 
                    name={selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id ? "checkbox" : "person-outline"} 
                    size={16} 
                    color={selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id ? colors.primary : colors.textSecondary} 
                  />
                  <Text style={[
                    styles.sittingOutPlayerName,
                    selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id && styles.sittingOutPlayerNameSelected
                  ]}>
                    {player.name}
                  </Text>
                  <View style={styles.sittingOutCategory}>
                    <Text style={styles.sittingOutCategoryText}>{player.category}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Reshuffling Controls */}
        <View style={styles.reshuffleContainer}>
          <Text style={styles.dragHint}>
            💡 Tap players to swap positions or move to/from sitout
          </Text>
        </View>

        {/* Let's Play Button - only show when ready */}
        <View style={styles.readyActionContainer}>
          <Text style={styles.readyMessage}>
            ✅ Court assignments ready! Tap "Let's Play" or rearrange players first.
          </Text>
          <TouchableOpacity 
            onPress={() => {
              if (validateCourts()) {
                onStartSession();
              }
            }}
          >
            <LinearGradient
              colors={[colors.success, colors.teal]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.letsPlayButton}
            >
              <Ionicons name="play" size={24} color="#ffffff" />
              <Text style={styles.letsPlayText}>Let's Play!</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const currentMatches = matches;
  const courts = Array.from({ length: session.config.numCourts }, (_, i) => i);
  
  return (
    <View style={styles.dashboardContainer}>
      <NextRoundButton />
      {courts.map((courtIndex) => {
        const match = currentMatches.find(m => m.courtIndex === courtIndex);
        
        return (
          <View key={courtIndex} style={styles.courtCard}>
            <View style={styles.courtHeader}>
              <Text style={styles.courtTitle}>Court {courtIndex + 1}</Text>
              {match && (
                <View style={styles.matchBadge}>
                  <Text style={styles.matchBadgeText}>{match.category}</Text>
                </View>
              )}
            </View>

            {match ? (
              <View style={styles.matchDetails}>
                <View style={styles.matchType}>
                  <Ionicons 
                    name={match.matchType === 'singles' ? 'person' : 'people'} 
                    size={16} 
                    color={colors.success} 
                  />
                  <Text style={styles.matchTypeText}>
                    {match.matchType.charAt(0).toUpperCase() + match.matchType.slice(1)}
                  </Text>
                </View>

                <View style={styles.teamsContainer}>
                  {/* Team A */}
                  <View style={styles.team}>
                    <Text style={styles.teamLabel}>Team A</Text>
                    {match.teamA.map((playerId, index) => (
                      <Text key={index} style={styles.playerNameInMatch}>
                        {getPlayerName(playerId)}
                      </Text>
                    ))}
                  </View>

                  <Text style={styles.vsText}>VS</Text>

                  {/* Team B */}
                  <View style={styles.team}>
                    <Text style={styles.teamLabel}>Team B</Text>
                    {match.teamB.map((playerId, index) => (
                      <Text key={index} style={styles.playerNameInMatch}>
                        {getPlayerName(playerId)}
                      </Text>
                    ))}
                  </View>
                </View>

                {match.status === 'saved' ? (
                  <View style={styles.finalScore}>
                    <Text style={styles.finalScoreText}>
                      Final Score: {match.scoreA} - {match.scoreB}
                    </Text>
                  </View>
                ) : session?.config?.rotationModel === 'top_court' ? (
                  // Winner Checkbox for Top Court mode
                  <View style={styles.winnerSelection}>
                    <Text style={styles.winnerLabel}>Select Winning Team:</Text>
                    <View style={styles.winnerButtons}>
                      <TouchableOpacity
                        style={[
                          styles.winnerButton,
                          winnerSelections[match.id] === 'A' && styles.winnerButtonSelected
                        ]}
                        onPress={() => selectWinner(match.id, 'A')}
                      >
                        <View style={styles.winnerButtonContent}>
                          <Ionicons 
                            name={winnerSelections[match.id] === 'A' ? "checkbox-outline" : "square-outline"} 
                            size={24} 
                            color={winnerSelections[match.id] === 'A' ? colors.primary : colors.textSecondary} 
                          />
                          <Text style={[
                            styles.winnerButtonText,
                            winnerSelections[match.id] === 'A' && styles.winnerButtonTextSelected
                          ]}>
                            Team A Wins
                          </Text>
                        </View>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={[
                          styles.winnerButton,
                          winnerSelections[match.id] === 'B' && styles.winnerButtonSelected
                        ]}
                        onPress={() => selectWinner(match.id, 'B')}
                      >
                        <View style={styles.winnerButtonContent}>
                          <Ionicons 
                            name={winnerSelections[match.id] === 'B' ? "checkbox-outline" : "square-outline"} 
                            size={24} 
                            color={winnerSelections[match.id] === 'B' ? colors.primary : colors.textSecondary} 
                          />
                          <Text style={[
                            styles.winnerButtonText,
                            winnerSelections[match.id] === 'B' && styles.winnerButtonTextSelected
                          ]}>
                            Team B Wins
                          </Text>
                        </View>
                      </TouchableOpacity>
                    </View>
                    
                    <TouchableOpacity
                      style={[
                        styles.saveScoreButton,
                        !winnerSelections[match.id] && styles.saveScoreButtonDisabled
                      ]}
                      onPress={() => saveWinner(match)}
                      disabled={!winnerSelections[match.id]}
                    >
                      <Text style={styles.saveScoreButtonText}>Save Winner</Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  // Legacy Score Input
                  <View style={styles.scoreInput}>
                    <View style={styles.scoreInputRow}>
                      <Text style={styles.scoreLabel}>Team A:</Text>
                      <TextInput
                        style={styles.scoreInputField}
                        value={scoreInputs[match.id]?.scoreA || ''}
                        onChangeText={(text) => updateScoreInput(match.id, 'A', text)}
                        keyboardType="numeric"
                        placeholder="0"
                        placeholderTextColor={colors.textMuted}
                        maxLength={2}
                      />
                      
                      <Text style={styles.scoreLabel}>Team B:</Text>
                      <TextInput
                        style={styles.scoreInputField}
                        value={scoreInputs[match.id]?.scoreB || ''}
                        onChangeText={(text) => updateScoreInput(match.id, 'B', text)}
                        keyboardType="numeric"
                        placeholder="0"
                        placeholderTextColor={colors.textMuted}
                        maxLength={2}
                      />
                    </View>
                    
                    <TouchableOpacity
                      style={styles.saveScoreButton}
                      onPress={() => saveScore(match)}
                    >
                      <Text style={styles.saveScoreButtonText}>Save Score</Text>
                    </TouchableOpacity>
                  </View>
                )}

                <View style={styles.matchStatus}>
                  <Text style={styles.matchStatusText}>
                    Status: {match.status.charAt(0).toUpperCase() + match.status.slice(1)}
                  </Text>
                </View>
              </View>
            ) : (
              <View style={styles.emptyCourt}>
                <Ionicons name="tennisball-outline" size={32} color={colors.textMuted} />
                <Text style={styles.emptyCourtText}>No match assigned</Text>
              </View>
            )}
          </View>
        );
      })}
      
      {/* Sitting Out Section - Interactive for player swapping */}
      {sittingOutPlayers.length > 0 && (
        <View style={styles.sittingOutSection}>
          <View style={styles.sittingOutHeader}>
            <Ionicons name="pause-circle-outline" size={24} color={colors.warning} />
            <Text style={styles.sittingOutTitle}>
              Sitting Out ({sittingOutPlayers.length})
            </Text>
          </View>
          <View style={styles.sittingOutList}>
            {sittingOutPlayers.map((player) => (
              <TouchableOpacity
                key={player.id}
                style={[
                  styles.sittingOutPlayer,
                  selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id && styles.sittingOutPlayerSelected
                ]}
                onPress={() => {
                  if (selectedPlayer) {
                    // Player already selected from court - move them to sitout
                    handlePlayerSwap('sitout', player.id);
                  } else {
                    // Select this sitout player to move to court
                    setSelectedPlayer({ matchId: 'sitout', team: 'A', index: player.id });
                  }
                }}
              >
                <Ionicons 
                  name={selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id ? "checkbox" : "person-outline"} 
                  size={16} 
                  color={selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id ? colors.primary : colors.textSecondary} 
                />
                <Text style={[
                  styles.sittingOutPlayerName,
                  selectedPlayer && selectedPlayer.matchId === 'sitout' && selectedPlayer.index === player.id && styles.sittingOutPlayerNameSelected
                ]}>
                  {player.name}
                </Text>
                <View style={styles.sittingOutCategory}>
                  <Text style={styles.sittingOutCategoryText}>{player.category}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </View>
  );
}

// Players Board Component (same structure, updated styles)
function PlayersBoard({ players, matches, session }: { players: Player[]; matches: Match[]; session: Session | null }) {
  // Show all players sorted by name
  const sortedPlayers = [...players].sort((a, b) => a.name.localeCompare(b.name));
  
  const formatRecentForm = (recentForm: string[]) => {
    if (!recentForm || recentForm.length === 0) return 'No recent matches';
    return recentForm.slice(-5).join('-'); // Show last 5 results
  };
  
  const formatRating = (rating: number) => {
    return rating ? rating.toFixed(2) : '3.00';
  };

  if (sortedPlayers.length === 0) {
    return (
      <View style={styles.dashboardContainer}>
        <View style={styles.card}>
          <Ionicons name="trophy" size={48} color={colors.primary} />
          <Text style={styles.emptyTitle}>No Players</Text>
          <Text style={styles.emptyText}>
            Add players from the Admin tab to get started.
          </Text>
        </View>
      </View>
    );
  }

  // Get top 5 players by wins
  const topWinners = [...sortedPlayers]
    .sort((a, b) => (b.wins || 0) - (a.wins || 0))
    .slice(0, 5)
    .filter(p => (p.wins || 0) > 0); // Only show players with at least 1 win

  console.log('🏆 Top Winners Debug:', {
    totalPlayers: sortedPlayers.length,
    topWinnersCount: topWinners.length,
    topWinners: topWinners.map(p => ({ name: p.name, wins: p.wins }))
  });

  return (
    <View style={styles.standingsContainer}>
      {/* Header */}
      <View style={styles.standingsHeader}>
        <Text style={styles.standingsTitle}>
          Players
        </Text>
        <Text style={styles.standingsSubtitle}>
          {sortedPlayers.length} players
        </Text>
      </View>

      {/* Top 5 Winners Chart */}
      {topWinners.length > 0 ? (
        <View style={styles.chartCard}>
          <View style={styles.chartHeader}>
            <Ionicons name="trophy" size={24} color="#FFD700" />
            <Text style={styles.chartTitle}>Top 5 Winners</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chartScroll}>
            <View style={styles.barChartContainer}>
              {topWinners.map((player, index) => {
                const maxWins = topWinners[0]?.wins || 1;
                const barHeight = ((player.wins || 0) / maxWins) * 120;
                
                return (
                  <View key={player.id} style={styles.barWrapper}>
                    {/* Bar */}
                    <View style={styles.barColumn}>
                      <Text style={styles.barValue}>{player.wins || 0}</Text>
                      <View 
                        style={[
                          styles.bar, 
                          { 
                            height: Math.max(barHeight, 20),
                            backgroundColor: index === 0 ? '#FFD700' : 
                                           index === 1 ? '#C0C0C0' : 
                                           index === 2 ? '#CD7F32' : 
                                           colors.primary
                          }
                        ]} 
                      />
                    </View>
                    {/* Player Name */}
                    <Text style={styles.barLabel} numberOfLines={2}>
                      {player.name.split(' ')[0]}
                    </Text>
                    {/* Rank Badge */}
                    <View style={[
                      styles.rankBadge,
                      index === 0 && styles.goldBadge,
                      index === 1 && styles.silverBadge,
                      index === 2 && styles.bronzeBadge
                    ]}>
                      <Text style={styles.rankBadgeText}>#{index + 1}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          </ScrollView>
        </View>
      ) : (
        <View style={{ padding: 20, backgroundColor: '#FF6B6B', borderRadius: 8, margin: 16 }}>
          <Text style={{ color: '#FFF', textAlign: 'center' }}>
            No top winners yet - topWinners.length = {topWinners.length}
          </Text>
        </View>
      )}
      
      {/* Standings List */}
      <ScrollView style={styles.standingsList}>
        {sortedPlayers.map((player, index) => {
          return (
            <View key={player.id} style={styles.standingRow}>
              {/* Rank */}
              <View style={styles.rankContainer}>
                <Text style={styles.rankNumber}>{index + 1}</Text>
              </View>
              
              {/* Player Info */}
              <View style={styles.playerInfo}>
                <Text style={styles.standingPlayerName}>{player.name}</Text>
                {/* Category Sticker */}
                <View style={[
                  styles.categorySticker, 
                  player.category === 'Beginner' && styles.categoryBeginner,
                  player.category === 'Intermediate' && styles.categoryIntermediate,
                  player.category === 'Advanced' && styles.categoryAdvanced,
                  player.category === 'Social' && styles.categorySocial
                ]}>
                  <Text style={[
                    styles.categoryStickerText,
                    player.category === 'Beginner' && styles.categoryBeginnerText,
                    player.category === 'Intermediate' && styles.categoryIntermediateText,
                    player.category === 'Advanced' && styles.categoryAdvancedText,
                    player.category === 'Social' && styles.categorySocialText
                  ]}>
                    {player.category.toUpperCase()}
                  </Text>
                </View>
              </View>
              
              {/* Stats */}
              <View style={styles.playerStats}>
                <Text style={styles.ratingText}>
                  Rating: {formatRating(player.rating || 3.0)}
                </Text>
                <Text style={styles.recentForm}>
                  Form: {formatRecentForm(player.recentForm || [])}
                </Text>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  header: {
    padding: 24,
    paddingBottom: 20,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  headerLeft: {
    flex: 1,
  },
  headerLogo: {
    width: 180,
    height: 50,
  },
  logo: {
    width: 180,
    height: 50,
  },
  headerCenter: {
    flex: 2,
    alignItems: 'center',
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
    marginBottom: 2,
  },
  clubName: {
    fontSize: 14,
    color: '#ffffff',
    opacity: 0.8,
  },
  logoutButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  sessionInfoContainer: {
    alignItems: 'flex-end',
  },
  sessionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 12,
    padding: 12,
    paddingHorizontal: 16,
    backdropFilter: 'blur(10px)',
    minWidth: 280,
  },
  sessionText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
    opacity: 0.9,
  },
  timerText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  timerWarning: {
    color: colors.coral,
    textShadowColor: 'rgba(255, 107, 107, 0.5)',
  },
  timerIdle: {
    color: '#ffffff',
    opacity: 0.7,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceElevated,
    padding: 6,
    borderRadius: 16,
    marginHorizontal: 20,
    marginBottom: 24,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  activeTab: {
    backgroundColor: colors.background,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 2,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 6,
    color: colors.textMuted,
  },
  activeTabText: {
    color: colors.primary,
    fontWeight: '700',
  },
  content: {
    flex: 1,
  },
  keyboardContainer: {
    flex: 1,
  },
  adminContainer: {
    padding: 20,
  },
  card: {
    backgroundColor: colors.background,
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  cardTitle: {
    color: colors.textDark,
    fontSize: 16,
    fontWeight: '600', // Notion uses 600 weight, not 700
    marginBottom: 12,
    letterSpacing: -0.2, // Tight spacing like Notion
  },
  cardSubtitle: {
    color: colors.textSecondary,
    fontSize: 14,
    marginBottom: 16,
    lineHeight: 20, // Better line height for readability
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  sessionDateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    padding: 12,
    backgroundColor: colors.cardBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  sessionDateText: {
    fontSize: 14,
    color: colors.text,
    marginLeft: 8,
    fontWeight: '500',
  },
  editButtonLarge: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.primary,
    minWidth: 70,
  },
  editButtonText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  configForm: {
    gap: 20,
  },
  configRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  configLabel: {
    color: colors.textSecondary,
    fontSize: 14, // Notion-style smaller labels
    fontWeight: '500',
    flex: 1,
  },
  configInput: {
    color: colors.text,
    fontSize: 14,
    padding: 8, // Notion-style tighter padding
    backgroundColor: colors.background,
    borderRadius: 4, // Notion-style subtle rounding
    borderWidth: 1,
    borderColor: colors.border,
    textAlign: 'center',
    minWidth: 60, // Smaller minimum width
  },
  timeInputs: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timeInput: {
    color: colors.text,
    fontSize: 16,
    padding: 12,
    backgroundColor: colors.surfaceLight,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    textAlign: 'center',
    width: 50,
  },
  timeColon: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '700',
  },
  toggleButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 4, // Notion-style subtle rounding
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  toggleButtonActive: {
    backgroundColor: colors.accent, // Use grey accent instead of primary
    borderColor: colors.accent,
  },
  toggleButtonText: {
    color: colors.textSecondary,
    fontSize: 12, // Smaller Notion-style text
    fontWeight: '500',
    textAlign: 'center',
  },
  toggleButtonTextActive: {
    color: colors.background, // White text on active buttons
    fontWeight: '600',
  },
  saveButton: {
    backgroundColor: colors.success,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 12,
    shadowColor: colors.success,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  saveButtonText: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
  sessionStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 16,
  },
  statItem: {
    alignItems: 'center',
    minWidth: '30%',
  },
  statLabel: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statValue: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '700',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  sessionControlButtons: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 8,
  },
  buttonColumn: {
    gap: 12,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    minHeight: 48,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  warningButton: {
    flex: 1,
    backgroundColor: colors.warning,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    minHeight: 40,
  },
  dangerButton: {
    flex: 1,
    backgroundColor: colors.error, // Updated to use error instead of danger
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    minHeight: 40,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: colors.background,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    minHeight: 40,
  },
  buttonDisabled: {
    opacity: 0.4, // Notion-style opacity
  },
  buttonIcon: {
    marginRight: 6, // Tighter spacing like Notion
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
  secondaryButtonText: {
    color: colors.text, // Dark text on secondary buttons
    fontSize: 14,
    fontWeight: '600',
  },
  helpText: {
    color: colors.textMuted,
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  textInput: {
    backgroundColor: colors.background,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: 14,
    padding: 18,
    fontSize: 16,
    color: colors.text,
    marginBottom: 16,
    shadowColor: colors.shadowLight,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 3,
  },
  categoryButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  categoryButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  categoryButtonText: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  categoryButtonTextActive: {
    color: colors.text,
    fontWeight: '600',
  },
  formatCheckboxes: {
    flexDirection: 'row',
    gap: 10,
  },
  checkboxButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  checkboxButtonActive: {
    backgroundColor: colors.accent, // Use grey accent instead of primary
    borderColor: colors.accent,
  },
  checkboxButtonDisabled: {
    opacity: 0.5,
    backgroundColor: colors.surfaceLight,
  },
  checkboxButtonText: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '500',
  },
  checkboxButtonTextActive: {
    color: colors.text,
    fontWeight: '600',
  },
  checkboxButtonTextDisabled: {
    color: colors.textMuted,
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: 16,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  playersList: {
    gap: 16,
  },
  categorySection: {
    marginBottom: 20,
  },
  categoryHeader: {
    color: colors.success,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  playerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: colors.surfaceLight,
    borderRadius: 10,
    marginBottom: 6,
  },
  playerName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  playerStats: {
    flexDirection: 'row',
    gap: 16,
  },
  playerStat: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: '500',
  },
  dashboardContainer: {
    padding: 20,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
  },
  courtCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  courtHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  courtTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '700',
  },
  matchBadge: {
    backgroundColor: colors.success,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  matchBadgeText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  matchDetails: {
    gap: 16,
  },
  matchType: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  matchTypeText: {
    color: colors.success,
    fontSize: 14,
    fontWeight: '600',
  },
  teamsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    backgroundColor: colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
  },
  team: {
    alignItems: 'center',
    flex: 1,
  },
  teamLabel: {
    color: colors.textSecondary,
    fontSize: 12,
    marginBottom: 8,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  playerNameInMatch: {
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
    textAlign: 'center',
  },
  vsText: {
    color: colors.success,
    fontSize: 18,
    fontWeight: '700',
    marginHorizontal: 20,
  },
  scoreInput: {
    backgroundColor: colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
  },
  scoreInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  scoreLabel: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '600',
  },
  scoreInputField: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: colors.text,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    minWidth: 70,
  },
  saveScoreButton: {
    backgroundColor: colors.success,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  saveScoreButtonDisabled: {
    backgroundColor: colors.surfaceLight,
    opacity: 0.6,
  },
  saveScoreButtonText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
  },
  winnerSelection: {
    backgroundColor: colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  winnerLabel: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  winnerButtons: {
    gap: 12,
  },
  winnerButton: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: 14,
    borderWidth: 2,
    borderColor: colors.border,
  },
  winnerButtonSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  winnerButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  winnerButtonText: {
    color: colors.textSecondary,
    fontSize: 15,
    fontWeight: '500',
  },
  winnerButtonTextSelected: {
    color: colors.primary,
    fontWeight: '600',
  },
  finalScore: {
    backgroundColor: colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  finalScoreText: {
    color: colors.success,
    fontSize: 18,
    fontWeight: '700',
  },
  matchStatus: {
    alignItems: 'center',
  },
  matchStatusText: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '500',
    fontStyle: 'italic',
  },
  emptyCourt: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyCourtText: {
    color: colors.textMuted,
    fontSize: 16,
    marginTop: 12,
  },
  playersContainer: {
    padding: 20,
  },
  playerCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  playerCardName: {
    color: colors.text,
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 6,
  },
  playerCardCategory: {
    color: colors.success,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 16,
  },
  playerCardStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  playerCardStat: {
    color: colors.textSecondary,
    fontSize: 12,
    fontWeight: '500',
  },
  playerAssignment: {
    color: colors.textMuted,
    fontSize: 16,
    fontWeight: '500',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 8,
  },
  playerAssigned: {
    color: colors.success,
    fontWeight: '600',
    fontStyle: 'normal',
  },
  // New standings styles
  standingsContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  standingsHeader: {
    alignItems: 'center',
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    marginBottom: 16,
  },
  standingsTitle: {
    color: colors.text,
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  standingsSubtitle: {
    color: colors.textMuted,
    fontSize: 14,
    fontStyle: 'italic',
  },
  standingsList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  standingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 12, // Reduced padding
    marginBottom: 8, // Reduced margin
    borderWidth: 1,
    borderColor: colors.border,
    minHeight: 70, // Reduced height
  },
  rankContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 40, // Further reduced
    marginRight: 8, // Reduced margin
  },
  rankNumber: {
    color: colors.text,
    fontSize: 16, // Reduced font size
    fontWeight: '700',
    marginBottom: 2, // Reduced margin
  },
  playerInfo: {
    flex: 1,
    marginRight: 8, // Reduced margin
    justifyContent: 'center',
  },
  standingPlayerName: {
    color: colors.text,
    fontSize: 14, // Reduced font size
    fontWeight: '600',
    marginBottom: 2,
    numberOfLines: 1, // Prevent text wrapping
  },
  standingPlayerCategory: {
    color: colors.textMuted,
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  ratingContainer: {
    alignItems: 'center',
    marginRight: 8, // Reduced margin
  },
  ratingBox: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceLight,
    borderRadius: 6, // Reduced border radius
    padding: 6, // Reduced padding
    minWidth: 45, // Further reduced
  },
  ratingNumber: {
    fontSize: 14, // Reduced font size
    fontWeight: '700',
    marginBottom: 0, // Removed margin
  },
  winsLabel: {
    fontSize: 10,
    color: colors.textMuted,
    fontWeight: '500',
    marginTop: 2,
  },
  playerStats: {
    alignItems: 'flex-end',
    minWidth: 80, // Further reduced
    maxWidth: 90, // Reduced max width
  },
  statText: {
    color: colors.text,
    fontSize: 12, // Reduced font size
    fontWeight: '600',
    marginBottom: 1, // Reduced margin
  },
  statSubtext: {
    color: colors.textMuted,
    fontSize: 10, // Reduced font size
    marginBottom: 2, // Reduced margin
  },
  recentForm: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  ratingText: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  ratingsLegend: {
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: 16,
    marginTop: 8,
  },
  legendTitle: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  legendRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 6,
  },
  legendText: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '500',
  },
  // Category sticker styles
  categorySticker: {
    paddingHorizontal: 4, // Reduced padding
    paddingVertical: 1, // Reduced padding
    borderRadius: 6, // Reduced border radius
    alignSelf: 'flex-start',
    marginTop: 2, // Reduced margin
    borderWidth: 1,
  },
  categoryBeginner: {
    backgroundColor: '#E8F5E8',
    borderColor: '#4CAF50',
  },
  categoryIntermediate: {
    backgroundColor: '#FFF3E0',
    borderColor: '#FF9800',
  },
  categoryAdvanced: {
    backgroundColor: '#FCE4EC',
    borderColor: '#E91E63',
  },
  categoryStickerText: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  categoryBeginnerText: {
    color: '#2E7D32',
  },
  categoryIntermediateText: {
    color: '#F57C00',
  },
  categoryAdvancedText: {
    color: '#C2185B',
  },
  // Ready phase styles
  courtsScroll: {
    flex: 1,
    paddingHorizontal: 16,
  },
  readyActionContainer: {
    padding: 20,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    alignItems: 'center',
  },
  readyMessage: {
    color: colors.success,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
  },
  letsPlayButton: {
    paddingVertical: 18,
    paddingHorizontal: 36,
    borderRadius: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 220,
    shadowColor: colors.success,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  letsPlayText: {
    color: '#ffffff',
    fontSize: 19,
    fontWeight: '700',
    marginLeft: 10,
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  nextRoundContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  nextRoundButton: {
    alignSelf: 'center',
  },
  nextRoundButtonGradient: {
    paddingVertical: 16,  // Increased from 12 to 16 for better touch target
    paddingHorizontal: 32, // Increased from 24 to 32 for better touch target
    borderRadius: 25,     // Increased from 20 to 25 for better appearance
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 160,        // Increased from 140 to 160
    minHeight: 48,        // Added minimum height for touch-friendly button
  },
  nextRoundButtonDisabledGradient: {
    opacity: 1, // Keep full opacity for the gradient itself
  },
  nextRoundButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  nextRoundButtonTextDisabled: {
    color: '#888888', // Darker text for disabled state
  },
  
  // Drag and Drop Styles
  reshuffleContainer: {
    padding: 16,
    backgroundColor: colors.surface,
    marginHorizontal: 16,
    borderRadius: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  resetButtonText: {
    color: colors.primary,
    fontWeight: '600',
    marginLeft: 4,
  },
  dragHint: {
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
    flex: 1,
    textAlign: 'right',
  },
  draggablePlayer: {
    marginVertical: 2,
  },
  draggingPlayer: {
    opacity: 0.7,
    transform: [{ scale: 1.05 }],
  },
  playerChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: colors.border,
    marginVertical: 2,
  },
  draggablePlayerName: {
    flex: 1,
    marginLeft: 6,
    marginRight: 4,
    fontSize: 14,
    color: colors.text,
    fontWeight: '500',
  },
  dropZone: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    marginVertical: 4,
    borderWidth: 2,
    borderColor: colors.border,
    borderStyle: 'dashed',
    borderRadius: 8,
    backgroundColor: colors.surface,
  },
  dropZoneText: {
    marginLeft: 4,
    fontSize: 12,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  selectedPlayer: {
    transform: [{ scale: 1.05 }],
  },
  selectedPlayerChip: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryDark,
  },
  selectedPlayerName: {
    color: '#ffffff',
    fontWeight: '600',
  },
  // Player management styles
  playerMainInfo: {
    flex: 1,
  },
  playerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 12,
  },
  playerActionButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 80,
  },
  playerActionText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  removeButton: {
    backgroundColor: colors.warning,
  },
  addButton: {
    backgroundColor: colors.success,
  },
  deleteButton: {
    backgroundColor: colors.danger,
  },
  playerItemInactive: {
    opacity: 0.6,
    backgroundColor: '#f5f5f5',
  },
  playerNameInactive: {
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  notPlayingBadge: {
    fontSize: 11,
    color: colors.warning,
    fontStyle: 'italic',
    marginTop: 2,
  },
  // Court header and date styles
  courtHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  matchDate: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '500',
    backgroundColor: colors.background,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    overflow: 'hidden',
    flexShrink: 0,
    whiteSpace: 'nowrap',
  },
  socialBadge: {
    backgroundColor: colors.tealLight,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  socialBadgeText: {
    fontSize: 11,
    color: colors.teal,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  topCourtBadge: {
    backgroundColor: colors.warning + '20',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    marginLeft: 8,
  },
  topCourtBadgeText: {
    fontSize: 11,
    color: colors.warning,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  sittingOutSection: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sittingOutHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  sittingOutTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  sittingOutList: {
    gap: 8,
  },
  sittingOutPlayer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceLight,
    padding: 12,
    borderRadius: 8,
    gap: 10,
  },
  sittingOutPlayerSelected: {
    backgroundColor: colors.primaryLight,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  sittingOutPlayerName: {
    fontSize: 14,
    color: colors.text,
    fontWeight: '500',
    flex: 1,
  },
  sittingOutPlayerNameSelected: {
    color: colors.primary,
    fontWeight: '700',
  },
  sittingOutCategory: {
    backgroundColor: colors.accent,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  sittingOutCategoryText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  // Top 5 Winners Chart Styles
  chartCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  chartHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
  chartScroll: {
    marginHorizontal: -8,
  },
  barChartContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 20,
    paddingHorizontal: 8,
    paddingBottom: 8,
    minWidth: '100%',
  },
  barWrapper: {
    alignItems: 'center',
    flex: 1,
    minWidth: 60,
  },
  barColumn: {
    alignItems: 'center',
    justifyContent: 'flex-end',
    height: 140,
    marginBottom: 8,
  },
  bar: {
    width: 40,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
    minHeight: 20,
  },
  barValue: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 4,
  },
  barLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
    width: 60,
  },
  rankBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 4,
  },
  goldBadge: {
    backgroundColor: '#FFD700',
  },
  silverBadge: {
    backgroundColor: '#C0C0C0',
  },
  bronzeBadge: {
    backgroundColor: '#CD7F32',
  },
  rankBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});