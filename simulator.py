import json
import time
import random
import os
from datetime import datetime

# Setup directory
os.makedirs('beatblast_events_raw', exist_ok=True)

# Define simulation parameters
songs = ["song_001", "song_002", "song_003"]
countries = ["US", "IN", "GB", "CA"]
platforms = ["android", "ios", "web"]

while True:
    event = {
        "eventType": random.choice(["songPlay", "songSkip", "songLike", "appOpen"]),
        "eventTimestamp": datetime.utcnow().isoformat() + "Z",
        "songId": random.choice(songs),
        "userId": f"user_{random.randint(1, 100)}",
        "sessionId": f"sess_{random.randint(1, 1000)}",
        "platform": random.choice(platforms),
        "country": random.choice(countries)
    }
    
    filename = f"beatblast_events_raw/event_{int(time.time()*1000)}.json"
    with open(filename, 'w') as f:
        json.dump(event, f)
    
    print(f"Generated: {event['eventType']} at {event['eventTimestamp']}")
    time.sleep(1)
