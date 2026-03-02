"""
LiveKit Transcription Agent for LLARS Messaging.

Automatically joins call rooms as an invisible transcription bot,
subscribes to audio tracks, and streams transcript chunks to the
Flask backend via REST API.
"""

import logging
import os
import time

import requests
from livekit import agents, rtc

logger = logging.getLogger("livekit-transcription-agent")
logging.basicConfig(level=logging.INFO)

# Configuration from environment
FLASK_API_URL = os.getenv("FLASK_API_URL", "http://backend-flask-service:8081")
TRANSCRIPT_ENDPOINT = f"{FLASK_API_URL}/api/messaging/calls/transcript-chunk"
STT_PROVIDER = os.getenv("STT_DEFAULT_PROVIDER", "openai_whisper")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def post_transcript_chunk(room_name: str, speaker: str, text: str, timestamp: float):
    """Send a transcript chunk to the Flask backend."""
    try:
        resp = requests.post(
            TRANSCRIPT_ENDPOINT,
            json={
                "room_name": room_name,
                "speaker": speaker,
                "text": text,
                "timestamp": timestamp,
            },
            timeout=5,
        )
        if resp.status_code != 200:
            logger.warning("Failed to post transcript chunk: %s", resp.text)
    except Exception as e:
        logger.error("Error posting transcript chunk: %s", e)


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the transcription agent."""
    logger.info("Transcription agent joining room: %s", ctx.room.name)

    # Wait for the first participant to connect
    await ctx.connect()

    # Use OpenAI Whisper for STT via LiveKit plugins
    try:
        from livekit.plugins.openai import STT

        stt_instance = STT(
            api_key=OPENAI_API_KEY,
            model="whisper-1",
        )
    except ImportError:
        logger.error("livekit-plugins-openai not installed")
        return

    # Track participants for speaker identification
    participants = {}

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        participants[participant.sid] = participant.identity
        logger.info("Participant connected: %s", participant.identity)

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        participants.pop(participant.sid, None)
        logger.info("Participant disconnected: %s", participant.identity)

    # Register existing participants
    for p in ctx.room.remote_participants.values():
        participants[p.sid] = p.identity

    # Process audio tracks for transcription
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return

        logger.info(
            "Subscribed to audio track from %s", participant.identity
        )

        # Create STT stream for this track
        async def process_audio():
            audio_stream = rtc.AudioStream(track)
            stt_stream = stt_instance.stream()

            async for event in audio_stream:
                stt_stream.push_frame(event.frame)

            # Process STT results
            async for stt_event in stt_stream:
                if stt_event.type == agents.stt.SpeechEventType.FINAL_TRANSCRIPT:
                    text = stt_event.alternatives[0].text.strip()
                    if text:
                        speaker = participant.identity
                        ts = time.time()
                        logger.info("[%s] %s", speaker, text)
                        post_transcript_chunk(
                            ctx.room.name, speaker, text, ts
                        )

        import asyncio
        asyncio.ensure_future(process_audio())

    # Keep the agent alive until the room is empty or disconnected
    @ctx.room.on("disconnected")
    def on_disconnected():
        logger.info("Disconnected from room: %s", ctx.room.name)


if __name__ == "__main__":
    # Define the worker with auto-subscribe to rooms
    worker = agents.Worker(
        entrypoint=entrypoint,
        # Auto-join rooms matching the LLARS messaging call pattern
        worker_type=agents.WorkerType.ROOM,
    )
    agents.run_app(worker)
