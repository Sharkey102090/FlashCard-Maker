"""
Audio and Multimedia Support
============================

Audio recording, playback, and multimedia management for flashcards.
Perfect for language learning with pronunciation practice.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import base64
import io
import os
import tempfile
from pathlib import Path
import threading
import time

# Audio support with fallback handling
try:
    import pyaudio  # type: ignore
    import wave
    AUDIO_AVAILABLE = True
    PyAudioType = pyaudio.PyAudio
    AudioFormat = int
except ImportError:
    pyaudio = None
    wave = None
    AUDIO_AVAILABLE = False
    PyAudioType = None
    AudioFormat = None

try:
    import pygame  # type: ignore
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

# Alternative audio libraries
try:
    import sounddevice as sd  # type: ignore
    import soundfile as sf  # type: ignore
    import numpy as np  # type: ignore
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    sf = None
    np = None
    SOUNDDEVICE_AVAILABLE = False

class AudioRecorder:
    """Audio recording functionality with multiple backend support."""
    
    def __init__(self):
        self.is_recording = False
        self.audio_data = None
        self.sample_rate = 44100
        self.channels = 1
        self.chunk_size = 1024
        self.format = None
        self.stream = None
        self.frames = []
        
        # Initialize audio backend
        self.backend = self._initialize_backend()
    
    def _initialize_backend(self) -> str:
        """Initialize the best available audio backend."""
        if SOUNDDEVICE_AVAILABLE and sd is not None:
            return "sounddevice"
        elif AUDIO_AVAILABLE and pyaudio is not None:
            try:
                self.audio = pyaudio.PyAudio()
                self.format = pyaudio.paInt16
                return "pyaudio"
            except:
                pass
        
        return "none"
    
    def start_recording(self) -> bool:
        """Start audio recording."""
        if self.is_recording:
            return False
        
        try:
            if self.backend == "sounddevice":
                return self._start_recording_sounddevice()
            elif self.backend == "pyaudio":
                return self._start_recording_pyaudio()
            else:
                return False
        except Exception as e:
            print(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return audio data."""
        if not self.is_recording:
            return None
        
        try:
            if self.backend == "sounddevice":
                return self._stop_recording_sounddevice()
            elif self.backend == "pyaudio":
                return self._stop_recording_pyaudio()
            else:
                return None
        except Exception as e:
            print(f"Failed to stop recording: {e}")
            return None
    
    def _start_recording_sounddevice(self) -> bool:
        """Start recording using sounddevice."""
        if not SOUNDDEVICE_AVAILABLE or sd is None:
            return False
        
        self.frames = []
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if self.is_recording:
                self.frames.append(indata.copy())
        
        try:
            self.stream = sd.InputStream(
                callback=audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='int16'
            )
            self.stream.start()
            return True
        except Exception:
            self.is_recording = False
            return False
    
    def _stop_recording_sounddevice(self) -> Optional[bytes]:
        """Stop recording using sounddevice."""
        if not self.is_recording or not self.stream or sd is None or sf is None or np is None:
            return None
        
        self.is_recording = False
        if hasattr(self.stream, 'stop'):
            self.stream.stop()  # type: ignore
        if hasattr(self.stream, 'close'):
            self.stream.close()  # type: ignore
        
        if not self.frames:
            return None
        
        # Combine frames and save as WAV
        audio_data = np.concatenate(self.frames, axis=0)
        
        # Convert to WAV format
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, self.sample_rate)
            
            # Read back as bytes
            with open(tmp_file.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return wav_data
    
    def _start_recording_pyaudio(self) -> bool:
        """Start recording using PyAudio."""
        if not AUDIO_AVAILABLE or not self.audio or self.format is None or pyaudio is None:
            return False
        
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.frames = []
            self.is_recording = True
            
            # Start recording in background thread
            self.recording_thread = threading.Thread(target=self._record_audio_pyaudio)
            self.recording_thread.start()
            
            return True
        except Exception:
            return False
    
    def _record_audio_pyaudio(self):
        """Record audio data in background thread."""
        while self.is_recording and self.stream is not None:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)
            except Exception:
                break
    
    def _stop_recording_pyaudio(self) -> Optional[bytes]:
        """Stop recording using PyAudio."""
        if not self.is_recording or wave is None or pyaudio is None or self.format is None:
            return None
        
        self.is_recording = False
        
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=1.0)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if not self.frames or not self.audio:
            return None
        
        # Create WAV file from frames
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            with wave.open(tmp_file.name, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.frames))
            
            # Read back as bytes
            with open(tmp_file.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return wav_data
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.is_recording:
            self.stop_recording()
        
        if self.backend == "pyaudio" and hasattr(self, 'audio'):
            try:
                self.audio.terminate()
            except:
                pass

class AudioPlayer:
    """Audio playback functionality with multiple backend support."""
    
    def __init__(self):
        self.is_playing = False
        self.backend = self._initialize_backend()
    
    def _initialize_backend(self) -> str:
        """Initialize the best available audio backend."""
        if PYGAME_AVAILABLE and pygame is not None:
            try:
                pygame.mixer.init()
                return "pygame"
            except:
                pass
        
        if SOUNDDEVICE_AVAILABLE and sd is not None:
            return "sounddevice"
        
        return "none"
    
    def play_audio(self, audio_data: bytes) -> bool:
        """Play audio data."""
        if self.is_playing:
            return False
        
        try:
            if self.backend == "pygame":
                return self._play_audio_pygame(audio_data)
            elif self.backend == "sounddevice":
                return self._play_audio_sounddevice(audio_data)
            else:
                return False
        except Exception as e:
            print(f"Failed to play audio: {e}")
            return False
    
    def _play_audio_pygame(self, audio_data: bytes) -> bool:
        """Play audio using pygame."""
        if not PYGAME_AVAILABLE or pygame is None:
            return False
        
        try:
            # Write audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()
                
                # Play the file
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                self.is_playing = True
                
                # Clean up after playing (in background)
                def cleanup():
                    if pygame is not None:
                        while pygame.mixer.music.get_busy():  # type: ignore
                            time.sleep(0.1)
                    self.is_playing = False
                    try:
                        os.unlink(tmp_file.name)
                    except:
                        pass
                
                threading.Thread(target=cleanup, daemon=True).start()
                return True
        except Exception:
            return False
    
    def _play_audio_sounddevice(self, audio_data: bytes) -> bool:
        """Play audio using sounddevice."""
        if not SOUNDDEVICE_AVAILABLE or sd is None or sf is None:
            return False
        
        try:
            # Write to temporary file and read back
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()
                
                # Read audio data
                data, sample_rate = sf.read(tmp_file.name)
                
                # Play audio
                self.is_playing = True
                
                def play_and_cleanup():
                    try:
                        if sd is not None:
                            sd.play(data, sample_rate)  # type: ignore
                            sd.wait()  # Wait until finished  # type: ignore
                    finally:
                        self.is_playing = False
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
                
                threading.Thread(target=play_and_cleanup, daemon=True).start()
                return True
        except Exception:
            return False
    
    def stop_audio(self):
        """Stop audio playback."""
        if not self.is_playing:
            return
        
        try:
            if self.backend == "pygame" and pygame is not None:
                pygame.mixer.music.stop()
            elif self.backend == "sounddevice" and sd is not None:
                sd.stop()
        except:
            pass
        
        self.is_playing = False

class AudioWidget(ctk.CTkFrame):
    """Widget for audio recording and playback in flashcards."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.audio_data: Optional[bytes] = None
        self.on_audio_changed: Optional[Callable] = None
        
        # Initialize audio components
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        
        # Recording state
        self.recording_start_time = None
        self.recording_timer = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create audio control widgets."""
        self.grid_columnconfigure(1, weight=1)
        
        # Record button
        self.record_button = ctk.CTkButton(
            self,
            text="🎤 Record",
            command=self._toggle_recording,
            width=100
        )
        self.record_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="No audio recorded",
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Play button
        self.play_button = ctk.CTkButton(
            self,
            text="▶️ Play",
            command=self._play_audio,
            width=80,
            state="disabled"
        )
        self.play_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Delete button
        self.delete_button = ctk.CTkButton(
            self,
            text="🗑️",
            command=self._delete_audio,
            width=40,
            state="disabled"
        )
        self.delete_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Load from file button
        self.load_button = ctk.CTkButton(
            self,
            text="📁 Load",
            command=self._load_audio_file,
            width=80
        )
        self.load_button.grid(row=0, column=4, padx=5, pady=5)
        
        # Check if audio is available
        if self.recorder.backend == "none":
            self.record_button.configure(state="disabled")
            self.status_label.configure(text="Audio recording not available")
    
    def _toggle_recording(self):
        """Toggle audio recording."""
        if not self.recorder.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start audio recording."""
        success = self.recorder.start_recording()
        if success:
            self.recording_start_time = time.time()
            self.record_button.configure(text="⏹️ Stop", fg_color="red")
            self.status_label.configure(text="Recording...")
            self._update_recording_timer()
        else:
            messagebox.showerror("Error", "Failed to start recording. Check microphone permissions.")
    
    def _stop_recording(self):
        """Stop audio recording."""
        audio_data = self.recorder.stop_recording()
        
        # Stop timer
        if self.recording_timer:
            self.after_cancel(self.recording_timer)
            self.recording_timer = None
        
        self.record_button.configure(text="🎤 Record", fg_color=("gray75", "gray25"))
        
        if audio_data:
            self.audio_data = audio_data
            duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            self.status_label.configure(text=f"Audio recorded ({duration:.1f}s)")
            self.play_button.configure(state="normal")
            self.delete_button.configure(state="normal")
            
            if self.on_audio_changed:
                self.on_audio_changed(audio_data)
        else:
            self.status_label.configure(text="Recording failed")
    
    def _update_recording_timer(self):
        """Update recording timer display."""
        if self.recorder.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            self.status_label.configure(text=f"Recording... {elapsed:.1f}s")
            self.recording_timer = self.after(100, self._update_recording_timer)
    
    def _play_audio(self):
        """Play recorded audio."""
        if self.audio_data and not self.player.is_playing:
            success = self.player.play_audio(self.audio_data)
            if success:
                self.play_button.configure(text="⏸️ Stop", fg_color="orange")
                self.status_label.configure(text="Playing audio...")
                self._check_playback_status()
            else:
                messagebox.showerror("Error", "Failed to play audio.")
        elif self.player.is_playing:
            self.player.stop_audio()
            self._reset_play_button()
    
    def _check_playback_status(self):
        """Check if audio is still playing."""
        if self.player.is_playing:
            self.after(100, self._check_playback_status)
        else:
            self._reset_play_button()
    
    def _reset_play_button(self):
        """Reset play button to normal state."""
        self.play_button.configure(text="▶️ Play", fg_color=("gray75", "gray25"))
        if self.audio_data:
            self.status_label.configure(text="Audio ready")
    
    def _delete_audio(self):
        """Delete recorded audio."""
        if messagebox.askyesno("Confirm", "Delete recorded audio?"):
            self.audio_data = None
            self.status_label.configure(text="No audio recorded")
            self.play_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            
            if self.on_audio_changed:
                self.on_audio_changed(None)
    
    def _load_audio_file(self):
        """Load audio from file."""
        file_path = filedialog.askopenfilename(
            title="Load Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.ogg *.flac"),
                ("WAV Files", "*.wav"),
                ("MP3 Files", "*.mp3"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    self.audio_data = f.read()
                
                file_name = Path(file_path).name
                self.status_label.configure(text=f"Loaded: {file_name}")
                self.play_button.configure(state="normal")
                self.delete_button.configure(state="normal")
                
                if self.on_audio_changed:
                    self.on_audio_changed(self.audio_data)
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio file:\n{e}")
    
    def set_audio_data(self, audio_data: Optional[bytes]):
        """Set audio data programmatically."""
        self.audio_data = audio_data
        
        if audio_data:
            self.status_label.configure(text="Audio loaded")
            self.play_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.status_label.configure(text="No audio recorded")
            self.play_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
    
    def get_audio_data(self) -> Optional[bytes]:
        """Get current audio data."""
        return self.audio_data
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.recording_timer:
            self.after_cancel(self.recording_timer)
        
        self.player.stop_audio()
        self.recorder.cleanup()

def encode_audio_for_storage(audio_data: bytes) -> str:
    """Encode audio data as base64 for storage in flashcard."""
    return base64.b64encode(audio_data).decode('utf-8')

def decode_audio_from_storage(encoded_data: str) -> bytes:
    """Decode base64 audio data from flashcard storage."""
    return base64.b64decode(encoded_data.encode('utf-8'))

# Check audio availability and provide user feedback
def get_audio_status() -> Dict[str, Any]:
    """Get current audio system status."""
    return {
        "recording_available": AUDIO_AVAILABLE or SOUNDDEVICE_AVAILABLE,
        "playback_available": PYGAME_AVAILABLE or SOUNDDEVICE_AVAILABLE,
        "backends": {
            "pyaudio": AUDIO_AVAILABLE,
            "sounddevice": SOUNDDEVICE_AVAILABLE,
            "pygame": PYGAME_AVAILABLE
        },
        "recommended_packages": [
            "pip install pyaudio",
            "pip install sounddevice soundfile",
            "pip install pygame"
        ]
    }