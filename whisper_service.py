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
        
        # Configure librosa to be more memory efficient
        import os
        # Set environment variables for librosa to use less memory
        os.environ['LIBROSA_CACHE_DIR'] = tempfile.mkdtemp()
        os.environ['LIBROSA_CACHE_LEVEL'] = '10'  # Lowest level of caching
        
        # Try importing audioread as backup
        try:
            import audioread
            print("Audioread is available as a fallback for audio loading")
        except ImportError:
            print("Warning: audioread not available, consider installing it")
        
        # Check if ffmpeg is available
        try:
            import subprocess
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            self.ffmpeg_available = True
            print("ffmpeg is available for audio processing")
        except:
            self.ffmpeg_available = False
            print("ffmpeg not available - advanced audio processing may be limited")
        
        # Define supported media formats
        self.supported_audio_formats = ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'wma', 'aiff', 'alac']
        self.supported_video_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'mpeg']
        self.all_supported_formats = self.supported_audio_formats + self.supported_video_formats
    
    def _remove_noise(self, audio_path):
        """Remove noise from audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Path to processed audio file
        """
        # Create output path first
        temp_dir = tempfile.mkdtemp()
        processed_path = os.path.join(temp_dir, 'processed_audio.wav')
        
        try:
            # Try using soundfile directly which is more memory efficient
            try:
                # First try to get info without loading the whole file
                info = sf.info(audio_path)
                sr = info.samplerate
                
                # For very large files, we'll use a chunked approach
                if info.frames > 10000000:  # Roughly 3-4 minutes of audio at 44.1kHz
                    # Process in chunks of ~10MB of audio
                    chunk_size = 2500000  # Adjust based on available memory
                    
                    # Create an output file with the same sample rate
                    with sf.SoundFile(processed_path, 'w', sr, channels=1, format='WAV') as outfile:
                        # Process in chunks to avoid memory issues
                        for block_idx in range(0, info.frames, chunk_size):
                            # Read a chunk
                            with sf.SoundFile(audio_path) as infile:
                                infile.seek(block_idx)
                                chunk_frames = min(chunk_size, info.frames - block_idx)
                                y = infile.read(chunk_frames)
                                
                                # Convert to mono if stereo
                                if len(y.shape) > 1 and y.shape[1] > 1:
                                    y = np.mean(y, axis=1)
                                
                                # Apply simple filtering (less memory intensive)
                                # High-pass filter
                                b, a = signal.butter(5, 100/(sr/2), 'highpass')
                                y_filtered = signal.lfilter(b, a, y)
                                
                                # Low-pass filter
                                b, a = signal.butter(5, 8000/(sr/2), 'lowpass')
                                y_filtered = signal.lfilter(b, a, y_filtered)
                                
                                # Write the processed chunk to output file
                                outfile.write(y_filtered.astype(np.float32))
                    
                    return processed_path
                
            except Exception as e:
                print(f"Warning: SoundFile processing failed: {e}. Falling back to librosa.")
            
            # If we get here, either the file wasn't large or soundfile failed
            # Load with librosa but with memory optimization
            y, sr = librosa.load(audio_path, sr=None, mono=True, res_type='kaiser_fast')
            
            # Apply noise reduction techniques
            
            # 1. High-pass filter to remove low-frequency noise
            b, a = signal.butter(5, 100/(sr/2), 'highpass')
            y = signal.filtfilt(b, a, y)
            
            # 2. Low-pass filter to remove high-frequency noise
            b, a = signal.butter(5, 8000/(sr/2), 'lowpass')
            y = signal.filtfilt(b, a, y)
            
            # If the file is large, use simplified noise removal
            if len(y) > 5000000:
                # Save the processed audio directly without spectral gating
                sf.write(processed_path, y, sr)
                return processed_path
            
            # 3. Spectral gating for more advanced noise reduction
            noise_sample = y[:min(int(sr), len(y))]
            noise_profile = np.mean(np.abs(librosa.stft(noise_sample)))
            
            # Apply spectral gating with memory efficiency
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
            
            # Free up memory
            del S, S_mag, S_phase, S_denoised
            
            # Save the processed audio to a temporary file
            sf.write(processed_path, y_denoised, sr)
            
            return processed_path
            
        except Exception as e:
            # If any processing fails, convert the file to WAV using ffmpeg if available
            try:
                import subprocess
                print(f"Audio processing failed: {e}. Trying to convert with ffmpeg.")
                subprocess.run(["ffmpeg", "-i", audio_path, "-ac", "1", "-ar", "16000", processed_path], 
                             check=True, capture_output=True)
                return processed_path
            except:
                # If all else fails, just return the original file
                print(f"All audio processing failed. Using original file.")
                return audio_path

    def transcribe_audio(self, media_path, remove_noise=True, force_english=True):
        """Transcribe audio using Whisper with optimizations.
        
        Args:
            media_path: Path to media file (audio or video)
            remove_noise: Whether to apply noise removal (default: True)
            force_english: Whether to force English transcription (default: True)
            
        Returns:
            Transcription text
        """
        processed_path = media_path
        created_temp_file = False
        converted_media = False
        temp_dir = None
        
        try:
            # First, detect and convert media if needed
            try:
                temp_dir = tempfile.mkdtemp()
                audio_path, converted_media = self._detect_and_convert_media(media_path, temp_dir)
                if converted_media:
                    processed_path = audio_path
                    created_temp_file = True
                else:
                    processed_path = media_path
            except ValueError as e:
                print(f"Media format issue: {e}")
                raise
            
            # Check file size
            file_size = os.path.getsize(processed_path) / (1024 * 1024)  # Size in MB
            print(f"Processing audio file of size: {file_size:.2f} MB")
            
            # Process audio if noise removal is requested and we haven't already converted the media
            if remove_noise and not converted_media:
                try:
                    noise_removed_path = self._remove_noise(processed_path)
                    
                    # If we already created a temporary file, clean it up
                    if created_temp_file and processed_path != media_path:
                        try:
                            os.remove(processed_path)
                        except:
                            pass
                    
                    processed_path = noise_removed_path
                    created_temp_file = True
                except MemoryError:
                    print("Memory error during noise removal. Skipping noise removal.")
                except Exception as e:
                    print(f"Error during noise removal: {e}. Skipping noise removal.")
            
            # If the file is still too large for Whisper API (which has a 25MB limit)
            if os.path.getsize(processed_path) > 24 * 1024 * 1024:
                # Try to compress with ffmpeg if available
                if hasattr(self, 'ffmpeg_available') and self.ffmpeg_available:
                    try:
                        import subprocess
                        temp_dir = tempfile.mkdtemp()
                        compressed_path = os.path.join(temp_dir, 'compressed_audio.mp3')
                        
                        subprocess.run([
                            "ffmpeg", "-i", processed_path,
                            "-ac", "1",                # Convert to mono
                            "-ar", "16000",            # 16kHz sample rate
                            "-b:a", "64k",             # Lower bitrate
                            compressed_path
                        ], check=True, capture_output=True)
                        
                        # Clean up previous processed file if it was temporary
                        if created_temp_file:
                            try:
                                os.remove(processed_path)
                                os.rmdir(os.path.dirname(processed_path))
                            except:
                                pass
                        
                        processed_path = compressed_path
                        created_temp_file = True
                        print(f"Compressed audio file to: {os.path.getsize(processed_path)/1024/1024:.2f} MB")
                        
                    except Exception as e:
                        print(f"Failed to compress audio: {e}")
                else:
                    print("Audio file is large and ffmpeg is not available for compression.")
            
            # Open the audio file
            with open(processed_path, "rb") as audio_file:
                # Call the Whisper API with the appropriate parameters
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en" if force_english else None,
                    response_format="text"
                )
            
            return response
        
        finally:
            # Clean up temporary files if they were created
            if created_temp_file and processed_path != media_path:
                try:
                    os.remove(processed_path)
                except Exception as e:
                    print(f"Failed to clean up temporary file {processed_path}: {e}")
            
            # Clean up the temp directory if we created one
            if temp_dir and os.path.exists(temp_dir):
                try:
                    for file_name in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file_name)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"Failed to clean up temporary directory: {e}")

    def transcribe_audio_file(self, file, remove_noise=True, force_english=True):
        """Transcribe an uploaded file using Whisper with optimizations.
        
        Args:
            file: FastAPI UploadFile object
            remove_noise: Whether to apply noise removal (default: True)
            force_english: Whether to force English transcription (default: True)
            
        Returns:
            Transcription text
        """
        # Get file extension and check if it's supported
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
        
        if not (file_ext in self.supported_audio_formats or 
                (file_ext in self.supported_video_formats and self.ffmpeg_available)):
            supported_formats = ", ".join(self.all_supported_formats)
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {supported_formats}")
        
        # Save the uploaded file to a temporary file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        # Check file size before processing
        file_content = file.file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        # If the file is extremely large (over 30MB), we may need to downsample before processing
        extremely_large = file_size_mb > 30
        
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Reset the file pointer for future reads
        file.file.seek(0)
        
        try:
            # For extremely large files, try to preprocess with ffmpeg if available
            if extremely_large:
                try:
                    import subprocess
                    print(f"File size: {file_size_mb:.2f} MB - Using ffmpeg preprocessing")
                    
                    # Create a downsampled version with ffmpeg
                    optimized_path = os.path.join(temp_dir, 'optimized_audio.wav')
                    subprocess.run([
                        "ffmpeg", "-i", temp_path, 
                        "-ac", "1",                # Convert to mono
                        "-ar", "16000",            # 16kHz sample rate
                        "-q:a", "3",               # Lower quality for smaller size
                        optimized_path
                    ], check=True, capture_output=True)
                    
                    # Use the optimized file instead
                    temp_path = optimized_path
                except Exception as e:
                    print(f"ffmpeg preprocessing failed: {e}")
            
            # Try to transcribe with noise removal first
            try:
                if remove_noise:
                    result = self.transcribe_audio(temp_path, remove_noise=True, force_english=force_english)
                else:
                    result = self.transcribe_audio(temp_path, remove_noise=False, force_english=force_english)
                
            except Exception as e:
                # If it fails with noise removal, try again without it
                if remove_noise:
                    print(f"Transcription with noise removal failed: {e}. Trying without noise removal.")
                    result = self.transcribe_audio(temp_path, remove_noise=False, force_english=force_english)
                else:
                    # If we're already not using noise removal, re-raise the exception
                    raise
        
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_path)
                # Remove any other files in the temp dir
                for file_name in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(temp_dir)
            except Exception as e:
                print(f"Failed to clean up temporary files: {e}")
        
        return result

    def _detect_and_convert_media(self, input_path, output_dir=None):
        """Detect media format and convert to audio format compatible with Whisper if needed.
        
        Args:
            input_path: Path to input media file
            output_dir: Directory to save converted file (optional)
            
        Returns:
            Path to audio file ready for processing
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        # Get the file extension
        file_ext = os.path.splitext(input_path)[1].lower().lstrip('.')
        
        # If file format is already a supported audio format
        if file_ext in self.supported_audio_formats:
            return input_path, False  # No conversion needed
        
        # For video files or unsupported formats, try to extract/convert audio using ffmpeg
        if self.ffmpeg_available:
            try:
                # Generate output path for audio
                output_path = os.path.join(output_dir, 'extracted_audio.wav')
                
                # Run ffmpeg to extract audio or convert format
                import subprocess
                print(f"Converting media file format: {file_ext} to wav")
                
                subprocess.run([
                    "ffmpeg", 
                    "-i", input_path,
                    "-vn",                 # No video
                    "-ac", "1",            # Convert to mono
                    "-ar", "16000",        # 16kHz sample rate
                    "-y",                  # Overwrite output file if exists
                    output_path
                ], check=True, capture_output=True)
                
                return output_path, True   # Return path and flag indicating conversion
                
            except Exception as e:
                print(f"Failed to convert media file: {e}")
                if file_ext in self.supported_video_formats:
                    raise ValueError(f"Failed to extract audio from video file. Error: {e}")
                else:
                    raise ValueError(f"Unsupported media format: {file_ext}. Error: {e}")
        else:
            # No ffmpeg, can't handle video or unsupported formats
            if file_ext in self.supported_video_formats:
                raise ValueError("Cannot process video files: ffmpeg is not available")
            else:
                raise ValueError(f"Unsupported media format: {file_ext}. Need ffmpeg for conversion.")
        
        return input_path, False
