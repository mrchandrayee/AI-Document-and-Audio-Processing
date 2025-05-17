import os
import tempfile
import librosa
import soundfile as sf
import numpy as np
from scipy import signal
from openai import OpenAI

class WhisperService:
    """Service for handling audio transcription using Whisper with optimizations."""
    
    def __init__(self, client=None):
        """Initialize the WhisperService.
        
        Args:
            client: OpenAI client instance (optional)
        """
        self.client = client or OpenAI()
    
    def _remove_noise(self, audio_path):
        """Remove noise from audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Path to processed audio file
        """
        # Load the audio file
        y, sr = librosa.load(audio_path, sr=None)
        
        # Apply noise reduction techniques
        
        # 1. High-pass filter to remove low-frequency noise
        # This helps remove rumble, hum, and some ambient noise
        b, a = signal.butter(5, 100/(sr/2), 'highpass')
        y = signal.filtfilt(b, a, y)
        
        # 2. Low-pass filter to remove high-frequency noise
        b, a = signal.butter(5, 8000/(sr/2), 'lowpass')
        y = signal.filtfilt(b, a, y)
        
        # 3. Spectral gating for more advanced noise reduction
        # Estimate noise profile from the first second of audio or from silent parts
        noise_sample = y[:int(sr)]
        noise_profile = np.mean(np.abs(librosa.stft(noise_sample)))
        
        # Apply spectral gating
        S = librosa.stft(y)
        S_mag = np.abs(S)
        S_phase = np.angle(S)
        
        # Create a mask to remove noise
        mask = S_mag > 2 * noise_profile
        
        # Apply mask to magnitude spectrogram
        S_mag = S_mag * mask
        
        # Reconstruct signal
        S_denoised = S_mag * np.exp(1j * S_phase)
        y_denoised = librosa.istft(S_denoised)
        
        # Save the processed audio to a temporary file
        temp_dir = tempfile.mkdtemp()
        processed_path = os.path.join(temp_dir, 'processed_audio.wav')
        sf.write(processed_path, y_denoised, sr)
        
        return processed_path
    
    def transcribe_audio(self, audio_path, remove_noise=True, force_english=True):
        """Transcribe audio using Whisper with optimizations.
        
        Args:
            audio_path: Path to audio file
            remove_noise: Whether to apply noise removal (default: True)
            force_english: Whether to force English transcription (default: True)
            
        Returns:
            Transcription text
        """
        # Process audio if noise removal is requested
        if remove_noise:
            processed_path = self._remove_noise(audio_path)
        else:
            processed_path = audio_path
        
        # Open the audio file
        with open(processed_path, "rb") as audio_file:
            # Call the Whisper API with the appropriate parameters
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en" if force_english else None,
                response_format="text"
            )
        
        # Clean up temporary file if it was created
        if remove_noise and processed_path != audio_path:
            try:
                os.remove(processed_path)
                os.rmdir(os.path.dirname(processed_path))
            except:
                pass
        
        return response
    
    def transcribe_audio_file(self, file, remove_noise=True, force_english=True):
        """Transcribe an uploaded file using Whisper with optimizations.
        
        Args:
            file: FastAPI UploadFile object
            remove_noise: Whether to apply noise removal (default: True)
            force_english: Whether to force English transcription (default: True)
            
        Returns:
            Transcription text
        """
        # Save the uploaded file to a temporary file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        # Reset the file pointer for future reads
        file.file.seek(0)
        
        # Transcribe the audio
        result = self.transcribe_audio(temp_path, remove_noise, force_english)
        
        # Clean up the temporary file
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass
            
        return result
