import os
import json
import torch
import whisperx
from whisperx.utils import get_writer
from pathlib import Path
from typing import List, Dict
import logging
from tqdm import tqdm
import gc
import warnings
import argparse
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_transcription(result: Dict, audio_path: Path, output_dir: Path, 
                       max_line_width: int = 42, max_line_count: int = 2, 
                       highlight_words: bool = False, gpu_id: str = None):
    """Save transcription as JSON and VTT files using WhisperX writer"""
    if result is None or 'segments' not in result:
        logger.warning(f"No segments found for {audio_path}")
        return
    
    # Create json and vtts subdirectories at the ROOT of output_dir
    json_output_dir = output_dir / "json"
    vtt_output_dir = output_dir / "vtts"
    
    json_output_dir.mkdir(parents=True, exist_ok=True)
    vtt_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare file names
    base_name = audio_path.stem
    json_path = json_output_dir / f"{base_name}.json"
    
    # Extract segments with word-level timestamps for JSON
    segments = []
    for segment in result['segments']:
        seg_data = {
            'start': segment.get('start', 0.0),
            'end': segment.get('end', 0.0),
            'text': segment.get('text', '')
        }
        
        # Add word-level timestamps if available
        if 'words' in segment and segment['words']:
            seg_data['words'] = []
            for word in segment['words']:
                word_data = {
                    'word': word.get('word', ''),
                    'start': word.get('start', 0.0),
                    'end': word.get('end', 0.0),
                    'score': word.get('score', 1.0)
                }
                seg_data['words'].append(word_data)
        
        segments.append(seg_data)
    
    # Save JSON file
    json_data = {'segments': segments}
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Save VTT file using WhisperX writer with line width control
    try:
        vtt_writer = get_writer("vtt", str(vtt_output_dir))
        vtt_options = {
            "max_line_width": max_line_width,
            "max_line_count": max_line_count,
            "highlight_words": highlight_words
        }
        vtt_writer(result, str(audio_path.with_suffix('')), options=vtt_options)
        
        gpu_info = f" [GPU {gpu_id}]" if gpu_id is not None else ""
        logger.info(f"{gpu_info} Processing: {audio_path.name} -> Saved: {base_name}.json and {base_name}.vtt")
    except Exception as e:
        logger.error(f"Error saving VTT for {audio_path.name}: {str(e)}")

def find_audio_files(root_dir: Path, extensions: List[str] = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']) -> List[Path]:
    """Recursively find all audio files in directory"""
    audio_files = []
    for ext in extensions:
        audio_files.extend(root_dir.rglob(f"*{ext}"))
    return sorted(audio_files)

def transcribe_with_whisperx(
    audio_path: str,
    model,
    align_model,
    metadata,
    device: str,
    batch_size: int,
    compute_type: str,
    language: str = None
) -> Dict:
    """Transcribe a single audio file with WhisperX"""
    try:
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Transcribe with Whisper
        result = model.transcribe(audio, batch_size=batch_size, language=language)
        
        # Store the detected language before alignment
        detected_language = result.get("language", language or "en")
        
        # Align whisper output for word-level timestamps
        if align_model is not None:
            aligned_result = whisperx.align(
                result["segments"], 
                align_model, 
                metadata, 
                audio, 
                device, 
                return_char_alignments=False
            )
            # Preserve the language field in the aligned result
            aligned_result["language"] = detected_language
            result = aligned_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error transcribing {audio_path}: {str(e)}")
        return None

def transcribe_directory(
    input_dir: str,
    output_dir: str,
    model_name: str = "large-v2",
    batch_size: int = 16,
    compute_type: str = "float16",
    language: str = None,
    align: bool = True,
    model_dir: str = None,
    max_line_width: int = 42,
    max_line_count: int = 2,
    highlight_words: bool = False
):
    """
    Transcribe all audio files in a directory structure using WhisperX
    
    Args:
        input_dir: Root directory containing audio files
        output_dir: Directory to save transcriptions
        model_name: WhisperX model name (tiny, base, small, medium, large-v2, large-v3, turbo)
        batch_size: Batch size for transcription (default: 16)
        compute_type: Compute type for model (float16, int8, float32)
        language: Language code (e.g., 'en', 'es'). If None, auto-detect
        align: Whether to perform alignment for accurate word timestamps
        model_dir: Local directory path to the downloaded model (for offline use)
        max_line_width: Maximum characters per line in VTT (default: 42)
        max_line_count: Maximum lines per subtitle (default: 2)
        highlight_words: Whether to highlight words in VTT (default: False)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Setup device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_id = "0" if device == "cuda" else "CPU"
    
    # Adjust compute type for CPU
    if device == "cpu":
        compute_type = "float32"
        logger.warning("CPU detected, using float32 compute type")
    
    logger.info(f"Using device: {device}")
    logger.info(f"Using compute type: {compute_type}")
    logger.info(f"VTT format: max_line_width={max_line_width}, max_line_count={max_line_count}")
    
    # Determine model path
    if model_dir:
        model_path = model_dir
        logger.info(f"Using local model from: {model_path}")
    else:
        model_path = model_name
        logger.info(f"Using model: {model_name}")
    
    # Find all audio files
    logger.info("Scanning for audio files...")
    audio_files = find_audio_files(input_path)
    logger.info(f"Found {len(audio_files)} audio files")
    
    if not audio_files:
        logger.warning("No audio files found!")
        return
    
    # Load WhisperX model
    logger.info(f"Loading WhisperX model...")
    model = whisperx.load_model(
        model_path, 
        device, 
        compute_type=compute_type,
        language=language
    )
    
    # Load alignment model if needed
    align_model = None
    metadata = None
    if align:
        logger.info("Loading alignment model for word-level timestamps...")
        try:
            if language:
                align_model, metadata = whisperx.load_align_model(
                    language_code=language, 
                    device=device
                )
            else:
                logger.info("Language not specified, will load alignment model after detecting language")
        except Exception as e:
            logger.warning(f"Could not load alignment model: {str(e)}")
            logger.warning("Continuing without word-level alignment")
    
    # Process files
    successful = 0
    failed = 0
    detected_language = language
    
    logger.info(f"Processing {len(audio_files)} files...")
    
    for audio_file in tqdm(audio_files, desc="Transcribing"):
        try:
            # Load alignment model for detected language if not already loaded
            if align and align_model is None:
                audio = whisperx.load_audio(str(audio_file))
                temp_result = model.transcribe(audio, batch_size=batch_size)
                detected_language = temp_result.get("language", "en")
                
                try:
                    align_model, metadata = whisperx.load_align_model(
                        language_code=detected_language, 
                        device=device
                    )
                    logger.info(f"Loaded alignment model for language: {detected_language}")
                except Exception as e:
                    logger.warning(f"Could not load alignment model for {detected_language}: {str(e)}")
                    align = False
            
            # Transcribe
            result = transcribe_with_whisperx(
                str(audio_file),
                model,
                align_model,
                metadata,
                device,
                batch_size,
                compute_type,
                language=detected_language
            )
            
            if result:
                save_transcription(
                    result, audio_file, output_path, 
                    max_line_width, max_line_count, highlight_words, gpu_id
                )
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Failed to process {audio_file}: {str(e)}")
            failed += 1
        
        # Cleanup to prevent memory issues
        if (successful + failed) % 10 == 0:
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()
    
    logger.info(f"Transcription complete! Successful: {successful}, Failed: {failed}")
    
    # Cleanup models
            batch_size=args.batch_size,
            compute_type=args.compute_type,
            language=args.language,
            num_gpus=args.num_gpus,
            model_dir=args.model_dir,
            max_line_width=args.max_line_width,
            max_line_count=args.max_line_count,
            highlight_words=args.highlight_words
        )
    else:
        transcribe_directory(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            model_name=args.model,
            batch_size=args.batch_size,
            compute_type=args.compute_type,
            language=args.language,
            align=not args.no_align,
            model_dir=args.model_dir,
            max_line_width=args.max_line_width,
            max_line_count=args.max_line_count,
            highlight_words=args.highlight_words
        )