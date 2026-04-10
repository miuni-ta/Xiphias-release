#!/usr/bin/env python3
from array import array
import math
import threading

from audio_output import detect_output_format, get_shared_audio_output


SPLASH_SOUND_SAMPLE_RATE = 22050
SPLASH_SOUND_MASTER_GAIN = 0.22
SPLASH_JINGLE_BPM = 272
SPLASH_JINGLE_REST_BEATS = 0.5
SPLASH_JINGLE_TAIL_SEC = 0.2


class SplashJinglePlayer:
    def __init__(self, client_name="gamehub-console", stream_name="gamehub-ui-cues"):
        self.sample_rate, self.channel_count, self.default_sink_name = detect_output_format(
            SPLASH_SOUND_SAMPLE_RATE,
            1,
        )
        self.output = get_shared_audio_output(
            sample_rate=self.sample_rate,
            channel_count=self.channel_count,
            client_name=client_name,
            stream_name=stream_name,
        )
        self.backend_name = self.output.backend_name
        self.lock = threading.Lock()
        self.cached_pcm = None

    def available(self):
        return self.output.available()

    def quarter_duration(self):
        return 60.0 / float(SPLASH_JINGLE_BPM)

    def harmonic_value(self, phase, brightness):
        return (
            (0.72 * math.sin(phase))
            + (0.2 * math.sin(phase * 2.0))
            + ((0.08 + (0.1 * brightness)) * math.sin(phase * 3.0))
        )

    def envelope_level(self, index, sample_count, attack_sec, release_sec):
        attack_samples = max(1, min(sample_count, int(round(attack_sec * self.sample_rate))))
        release_samples = max(1, min(sample_count, int(round(release_sec * self.sample_rate))))
        if index < attack_samples:
            return 0.45 + (0.55 * (index / max(1, attack_samples - 1)))
        release_start = max(0, sample_count - release_samples)
        if index >= release_start:
            release_progress = (index - release_start) / max(1, release_samples - 1)
            return math.exp(math.log(0.0009) * release_progress)
        return 1.0

    def render_note(self, frequency, duration_sec, volume, brightness, attack_sec, release_sec):
        sample_count = max(1, int(round(duration_sec * self.sample_rate)))
        phase = 0.0
        frames = array("h")
        for index in range(sample_count):
            phase += (2.0 * math.pi * float(frequency)) / self.sample_rate
            envelope = self.envelope_level(index, sample_count, attack_sec, release_sec)
            sample = (
                self.harmonic_value(phase, brightness)
                * float(volume)
                * SPLASH_SOUND_MASTER_GAIN
                * envelope
            )
            sample_value = int(max(-32767, min(32767, round(sample * 32767))))
            for _ in range(self.channel_count):
                frames.append(sample_value)
        return frames.tobytes()

    def silence(self, duration_sec):
        if duration_sec <= 0.0:
            return b""
        frame_count = max(1, int(round(duration_sec * self.sample_rate * self.channel_count)))
        return b"\x00\x00" * frame_count

    def build_phrase(self):
        quarter = self.quarter_duration()
        triplet_note = quarter / 3.0
        segments = [
            self.render_note(
                220.0,
                duration_sec=quarter,
                volume=0.92,
                brightness=0.22,
                attack_sec=0.008,
                release_sec=0.028,
            ),
            self.render_note(
                247.0,
                duration_sec=quarter,
                volume=0.88,
                brightness=0.28,
                attack_sec=0.008,
                release_sec=0.03,
            ),
            self.silence(quarter * SPLASH_JINGLE_REST_BEATS),
            self.render_note(
                440.0,
                duration_sec=triplet_note,
                volume=1.0,
                brightness=0.7,
                attack_sec=0.005,
                release_sec=0.02,
            ),
            self.render_note(
                330.0,
                duration_sec=triplet_note,
                volume=0.78,
                brightness=0.4,
                attack_sec=0.005,
                release_sec=0.02,
            ),
            self.render_note(
                311.0,
                duration_sec=triplet_note,
                volume=0.74,
                brightness=0.32,
                attack_sec=0.005,
                release_sec=0.05,
            ),
            self.silence(SPLASH_JINGLE_TAIL_SEC),
        ]
        return b"".join(segments)

    def play(self):
        if not self.available():
            return False
        with self.lock:
            if self.cached_pcm is None:
                self.cached_pcm = self.build_phrase()
            pcm_bytes = self.cached_pcm
        if not pcm_bytes:
            return False
        return self.output.play(
            pcm_bytes,
            family="boot-splash",
            replace_family=True,
            replace_all=True,
        )
