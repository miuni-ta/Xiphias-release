#!/usr/bin/env python3
from array import array
import re
import shutil
import subprocess
import threading
import time


AUDIO_CHUNK_FRAMES = 64
AUDIO_LATENCY_MSEC = 4
AUDIO_PROCESS_TIME_MSEC = 2
AUDIO_RESTART_DELAY_SEC = 0.15
SHARED_OUTPUTS = {}
SHARED_OUTPUTS_LOCK = threading.Lock()


def detect_output_format(default_sample_rate, default_channels):
    sample_rate = max(8000, int(default_sample_rate))
    channel_count = max(1, int(default_channels))
    default_sink_name = ""
    if not shutil.which("pactl"):
        return sample_rate, channel_count, default_sink_name
    try:
        output = subprocess.check_output(
            ["pactl", "info"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return sample_rate, channel_count, default_sink_name
    for line in output.splitlines():
        if line.startswith("Default Sink:"):
            default_sink_name = line.partition(":")[2].strip()
            continue
        if not line.startswith("Default Sample Specification:"):
            continue
        match = re.search(r"(\d+)ch\s+(\d+)Hz", line)
        if match is None:
            continue
        channel_count = max(1, int(match.group(1)))
        sample_rate = max(8000, int(match.group(2)))
    return sample_rate, channel_count, default_sink_name


def get_shared_audio_output(sample_rate, channel_count, client_name="gamehub-console", stream_name="gamehub-ui-cues"):
    key = (
        max(8000, int(sample_rate)),
        max(1, int(channel_count)),
        str(client_name),
    )
    with SHARED_OUTPUTS_LOCK:
        output = SHARED_OUTPUTS.get(key)
        if output is None:
            output = PersistentPcmAudioOutput(
                sample_rate=key[0],
                channel_count=key[1],
                client_name=key[2],
                stream_name=stream_name,
            )
            SHARED_OUTPUTS[key] = output
        return output


class PersistentPcmAudioOutput:
    def __init__(self, sample_rate, channel_count, client_name, stream_name):
        self.sample_rate = max(8000, int(sample_rate))
        self.channel_count = max(1, int(channel_count))
        self.client_name = str(client_name)
        self.stream_name = str(stream_name)
        self.chunk_frames = AUDIO_CHUNK_FRAMES
        self.chunk_duration_sec = self.chunk_frames / float(self.sample_rate)
        self.samples_per_chunk = self.chunk_frames * self.channel_count
        self.silence_chunk = b"\x00\x00" * self.samples_per_chunk
        self.backend_name, self.command = self.detect_backend()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.voices = []
        self.global_generation = 0
        self.family_generations = {}
        self.process = None
        self.worker = None
        self.running = bool(self.command)
        if self.running:
            self.worker = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker.start()

    def detect_backend(self):
        if shutil.which("pacat"):
            return (
                "pacat",
                [
                    "pacat",
                    "--raw",
                    "--playback",
                    "--no-remix",
                    f"--rate={self.sample_rate}",
                    "--format=s16le",
                    f"--channels={self.channel_count}",
                    f"--latency-msec={AUDIO_LATENCY_MSEC}",
                    f"--process-time-msec={AUDIO_PROCESS_TIME_MSEC}",
                    "--property=media.role=event",
                    f"--client-name={self.client_name}",
                    f"--stream-name={self.stream_name}",
                ],
            )
        if shutil.which("aplay"):
            return (
                "aplay",
                [
                    "aplay",
                    "-q",
                    "-t",
                    "raw",
                    "-f",
                    "S16_LE",
                    "-r",
                    str(self.sample_rate),
                    "-c",
                    str(self.channel_count),
                ],
            )
        return None, []

    def available(self):
        return bool(self.command)

    def play(self, pcm_bytes, family=None, replace_family=False, replace_all=False):
        if not self.available() or not pcm_bytes:
            return False
        samples = array("h")
        samples.frombytes(pcm_bytes)
        if not samples:
            return False
        with self.condition:
            if replace_all:
                self.global_generation += 1
                self.voices = []
            family_generation = 0
            if family and replace_family:
                family_generation = self.family_generations.get(family, 0) + 1
                self.family_generations[family] = family_generation
                self.voices = [item for item in self.voices if item.get("family") != family]
            elif family:
                family_generation = self.family_generations.get(family, 0)
            voice = {
                "family": family,
                "position": 0,
                "samples": samples,
                "global_generation": self.global_generation,
                "family_generation": family_generation,
            }
            self.voices.append(voice)
            self.condition.notify()
        return True

    def _voice_still_valid(self, voice):
        with self.lock:
            if voice.get("global_generation", 0) != self.global_generation:
                return False
            family = voice.get("family")
            if not family:
                return True
            return voice.get("family_generation", 0) == self.family_generations.get(family, 0)

    def _ensure_process(self):
        process = self.process
        if process is not None and process.poll() is None and process.stdin is not None:
            return True
        self._stop_process()
        try:
            self.process = subprocess.Popen(
                list(self.command),
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
            return True
        except Exception:
            self.process = None
            return False

    def _stop_process(self):
        process = self.process
        self.process = None
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
        except Exception:
            pass
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

    def _next_chunk(self):
        with self.condition:
            if not self.voices:
                return None
            voices = self.voices
            self.voices = []

        mixed = [0] * self.samples_per_chunk
        remaining_voices = []
        for voice in voices:
            if not self._voice_still_valid(voice):
                continue
            samples = voice["samples"]
            start = voice["position"]
            if start >= len(samples):
                continue
            end = min(len(samples), start + self.samples_per_chunk)
            source = samples[start:end]
            for index, value in enumerate(source):
                mixed[index] += value
            voice["position"] = end
            if end < len(samples) and self._voice_still_valid(voice):
                remaining_voices.append(voice)

        if remaining_voices:
            with self.condition:
                self.voices = remaining_voices + self.voices

        if not any(mixed):
            return self.silence_chunk

        chunk = array("h")
        chunk.extend(max(-32767, min(32767, value)) for value in mixed)
        return chunk.tobytes()

    def _worker_loop(self):
        next_deadline = 0.0
        while self.running:
            with self.condition:
                while self.running and not self.voices:
                    next_deadline = 0.0
                    self.condition.wait()
                if not self.running:
                    break

            if not self._ensure_process():
                time.sleep(AUDIO_RESTART_DELAY_SEC)
                continue

            chunk = self._next_chunk()
            if chunk is None:
                continue

            try:
                self.process.stdin.write(chunk)
                self.process.stdin.flush()
            except Exception:
                self._stop_process()
                next_deadline = 0.0
                time.sleep(AUDIO_RESTART_DELAY_SEC)
                continue

            if next_deadline <= 0.0:
                next_deadline = time.monotonic()
            next_deadline += self.chunk_duration_sec
            sleep_duration = next_deadline - time.monotonic()
            if sleep_duration > 0.0:
                time.sleep(sleep_duration)
            elif sleep_duration < -self.chunk_duration_sec:
                next_deadline = time.monotonic()

        self._stop_process()
