# whisper_service.py
import os
import logging
import tempfile
import openai
import config
import subprocess

logger = logging.getLogger(__name__)

# Set up OpenAI API key
openai.api_key = config.OPENAI_API_KEY

class WhisperService:
    def __init__(self):
        self.audio_dir = config.AUDIO_DIR
        
    async def transcribe_voice_note(self, voice_note_file):
        """
        Transcribe a voice note using OpenAI's Whisper API.
        
        Args:
            voice_note_file: The path to the voice note file
            
        Returns:
            str: The transcribed text
        """
        try:
            # Convert to MP3 format using FFmpeg directly
            converted_file = await self._convert_audio_to_mp3(voice_note_file)
            
            # Transcribe the audio
            with open(converted_file, "rb") as audio_file:
                transcript = await openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            transcribed_text = transcript.text
            
            # Clean up temporary files
            if converted_file != voice_note_file:
                os.remove(converted_file)
            
            logger.info(f"Successfully transcribed voice note: {transcribed_text[:50]}...")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing voice note: {e}")
            return None
        finally:
            # Always clean up the original file to save space
            try:
                os.remove(voice_note_file)
                logger.info(f"Deleted original voice note file: {voice_note_file}")
            except Exception as e:
                logger.error(f"Error deleting voice note file: {e}")
    
    async def _convert_audio_to_mp3(self, input_file):
        """
        Convert the audio file to MP3 format using FFmpeg.
        
        Args:
            input_file: The path to the input audio file
            
        Returns:
            str: The path to the converted audio file
        """
        try:
            # Create output file path
            output_file = tempfile.NamedTemporaryFile(
                suffix=".mp3", 
                dir=self.audio_dir,
                delete=False
            ).name
            
            # Use FFmpeg to convert the file
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-acodec', 'libmp3lame',
                '-y',  # Overwrite output file if it exists
                output_file
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Converted audio file to MP3 format")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            # If conversion fails, return the original file
            return input_file
        except Exception as e:
            logger.error(f"Error converting audio file: {e}")
            return input_file