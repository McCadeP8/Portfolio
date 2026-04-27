"""
Utah Mammoth Goal Horn 🥅🎹
Watches the NHL live feed and fires a chord on your Baldwin piano when Utah scores.

SETUP INSTRUCTIONS:
1. Install dependencies:       pip install requests mido python-rtmidi pygame
2. Find your piano's IP:       Open the QRSFinder app → note the IP address shown
3. Fill in PIANO_IP below
4. Run normally:               python mammoth_goal_horn.py
   Run in test mode:           python mammoth_goal_horn.py --test
   (--test plays the chord through your laptop speakers, no piano needed)
"""

import requests
import time
import sys

TEST_MODE = "--test" in sys.argv

# rtmidi requires a C++ compiler to install on Windows.
# It's only needed for USB/Bluetooth MIDI — not for test mode.
if not TEST_MODE:
    try:
        import mido
        import mido.backends.rtmidi
    except ImportError:
        print("⚠️  mido/rtmidi not available — run with --test to use laptop speakers.")
        print("    To install rtmidi on Windows, see: https://python-rtmidi.readthedocs.io")
        sys.exit(1)
from datetime import date

TEST_MODE = "--test" in sys.argv

# ─────────────────────────────────────────────
#  CONFIGURATION  ← Edit these two lines
# ─────────────────────────────────────────────
PIANO_IP       = "192.168.1.X"   # ← Replace with your piano's IP from QRSFinder
MIDI_PORT_NAME = None             # ← Leave as None to auto-detect, or set e.g. "QRS Piano"
# ─────────────────────────────────────────────

UTAH_TEAM_ID   = 59               # Utah Mammoth NHL team ID
CHECK_INTERVAL = 30               # Seconds between score checks
NOTE_DURATION  = 2.0              # Seconds to hold the chord
NOTE_VELOCITY  = 100              # Volume (0–127)

# B3=59, C#4=61, F4=65, G#4=68
CHORD_NOTES = [59, 61, 65, 68]


# ── NHL API helpers ──────────────────────────

def get_todays_game():
    """Find today's Utah Mammoth game, if any."""
    today = date.today().strftime("%Y-%m-%d")
    url = f"https://api-web.nhle.com/v1/score/{today}"
    try:
        data = requests.get(url, timeout=10).json()
        for game in data.get("games", []):
            home = game.get("homeTeam", {}).get("id")
            away = game.get("awayTeam", {}).get("id")
            if UTAH_TEAM_ID in (home, away):
                return game
    except Exception as e:
        print(f"  [NHL API error] {e}")
    return None


def get_utah_score(game):
    """Return Utah's current score from a game object."""
    if game["homeTeam"]["id"] == UTAH_TEAM_ID:
        return game["homeTeam"].get("score", 0)
    return game["awayTeam"].get("score", 0)


def game_is_live(game):
    """True if the game is currently in progress."""
    state = game.get("gameState", "")
    return state in ("LIVE", "CRIT")


# ── Piano helpers ────────────────────────────

def find_midi_port():
    """Find the QRS piano MIDI port, or fall back to the first available port."""
    ports = mido.get_output_names()
    if not ports:
        return None
    if MIDI_PORT_NAME:
        for p in ports:
            if MIDI_PORT_NAME.lower() in p.lower():
                return p
    # Auto-detect: prefer anything with 'QRS' or 'piano' in the name
    for p in ports:
        if any(k in p.lower() for k in ("qrs", "piano", "baldwin")):
            return p
    return ports[0]   # fall back to first available


def play_goal_chord():
    """Send B + C# + F + G# as a chord to the piano via MIDI."""
    import mido
    port_name = find_midi_port()
    if not port_name:
        print("  ⚠️  No MIDI port found. Is the piano connected via USB?")
        print("      (WiFi-only pianos need the HTTP method — see README below)")
        return

    print(f"  🎹 Playing chord on: {port_name}")
    try:
        with mido.open_output(port_name) as port:
            # All notes on simultaneously
            for note in CHORD_NOTES:
                port.send(mido.Message("note_on", note=note, velocity=NOTE_VELOCITY))
            time.sleep(NOTE_DURATION)
            # All notes off
            for note in CHORD_NOTES:
                port.send(mido.Message("note_off", note=note, velocity=0))
        print("  ✅ Chord played!")
    except Exception as e:
        print(f"  ⚠️  MIDI error: {e}")


def trigger_piano_wifi():
    """
    WiFi fallback: sends an HTTP command to the QRS web interface.

    HOW TO FIND YOUR ENDPOINT:
      1. Connect a laptop to the same WiFi as your piano
      2. Open Chrome and go to http://<PIANO_IP>
      3. Press F12 → Network tab → filter by 'Fetch/XHR'
      4. Hit Play on a song in the QRS interface
      5. Note the URL and payload that appears in the Network tab
      6. Paste that URL into `endpoint` below

    This is a placeholder — fill it in after completing step 4-5 above.
    """
    endpoint = f"http://{PIANO_IP}/play"   # ← Update after sniffing the real endpoint
    payload  = {"action": "play"}          # ← Update with real payload

    try:
        r = requests.post(endpoint, json=payload, timeout=5)
        print(f"  🌐 WiFi command sent → HTTP {r.status_code}")
    except Exception as e:
        print(f"  ⚠️  WiFi command failed: {e}")


def midi_note_to_hz(note):
    """Convert a MIDI note number to its frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def play_chord_on_laptop():
    """Play the chord through laptop speakers using sine waves — no MIDI device needed."""
    try:
        import pygame
        import numpy as np

        sample_rate = 44100
        duration    = NOTE_DURATION
        samples     = int(sample_rate * duration)
        t           = np.linspace(0, duration, samples, endpoint=False)

        # Build the chord by summing sine waves for each note
        wave = np.zeros(samples)
        for note in CHORD_NOTES:
            freq  = midi_note_to_hz(note)
            wave += np.sin(2 * np.pi * freq * t)

        # Add a natural fade-out so it doesn't cut off abruptly
        fade  = np.linspace(1.0, 0.0, samples) ** 2
        wave *= fade

        # Normalize and convert to 16-bit stereo
        wave   = wave / np.max(np.abs(wave))
        wave   = (wave * 32767 * 0.5).astype(np.int16)
        stereo = np.column_stack((wave, wave))

        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
        sound = pygame.sndarray.make_sound(stereo)

        print("  💻 Playing chord through laptop speakers...")
        sound.play()
        time.sleep(duration + 0.2)
        print("  ✅ Chord played!")

    except Exception as e:
        print(f"  ⚠️  Laptop audio error: {e}")
        print("      Make sure these are installed:  pip install pygame numpy")


def celebrate_goal():
    print("\n  🚨🦣  UTAH MAMMOTH GOAL! 🦣🚨")
    if TEST_MODE:
        play_chord_on_laptop()
    else:
        play_goal_chord()
        # Uncomment the line below if using WiFi instead of / in addition to USB MIDI:
        # trigger_piano_wifi()


# ── Main loop ────────────────────────────────

def main():
    print("=" * 50)
    print("  🥅  Utah Mammoth Goal Horn  🎹")
    print("=" * 50)
    if TEST_MODE:
        print("  ⚠️  TEST MODE — chord plays through laptop speakers")
    print(f"  Checking NHL scores every {CHECK_INTERVAL} seconds...")
    print("  Press Enter to manually trigger a goal. Press Ctrl+C to stop.\n")

    # Start a background thread that fires a goal when you press Enter
    import threading
    def manual_trigger():
        while True:
            input()
            print("  🎯 Manual trigger!")
            celebrate_goal()
    t = threading.Thread(target=manual_trigger, daemon=True)
    t.start()

    last_score   = None
    watching     = False

    while True:
        game = get_todays_game()

        if not game:
            if watching:
                print("  Game over (or no game found). Waiting for next game...")
                watching   = False
                last_score = None
        elif not game_is_live(game):
            state = game.get("gameState", "unknown")
            if not watching:
                print(f"  Game found but not live yet (state: {state}). Waiting...")
        else:
            score = get_utah_score(game)

            if not watching:
                print(f"  🟢 Game is LIVE! Utah score: {score}. Watching for goals...")
                last_score = score
                watching   = True
            elif score > last_score:
                goals_scored = score - last_score
                for _ in range(goals_scored):
                    celebrate_goal()
                last_score = score
            else:
                opp_name = (
                    game["awayTeam"].get("name", "Opponent")
                    if game["homeTeam"]["id"] == UTAH_TEAM_ID
                    else game["homeTeam"].get("name", "Opponent")
                )
                print(f"  ... Utah {score} | {opp_name} — no new goals")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Stopped. Go Mammoth! 🦣")