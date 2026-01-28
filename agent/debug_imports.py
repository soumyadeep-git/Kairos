import livekit.agents
print("LiveKit Agents Path:", livekit.agents.__file__)
print("Contents of livekit.agents:", dir(livekit.agents))

try:
    from livekit.agents import pipeline
    print("✅ Pipeline module found!")
except ImportError:
    print("❌ Pipeline module NOT found in top level")

try:
    from livekit.agents.pipeline import VoicePipelineAgent
    print("✅ VoicePipelineAgent found!")
except ImportError:
    print("❌ VoicePipelineAgent NOT found")