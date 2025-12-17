# coding=utf-8

import logging
from subliminal_patch.core import get_subtitle_path
from subzero.language import Language  # Add this import

from .core.translator_utils import validate_translation_params, convert_language_codes
from .services.translator_factory import TranslatorFactory
from languages.get_languages import alpha3_from_alpha2, alpha2_from_alpha3, language_from_alpha3
from app.config import settings
from app.database import TableEpisodes, TableMovies, TableShows, get_audio_profile_languages, database, select
from utilities.path_mappings import path_mappings
from utilities.post_processing import pp_replace, set_chmod
from subtitles.post_processing import postprocessing

def translate_subtitles_file(video_path, source_srt_file, from_lang, to_lang, forced, hi,
                             media_type, sonarr_series_id, sonarr_episode_id, radarr_id):
    try:
        logging.debug(f'Translation request: video={video_path}, source={source_srt_file}, from={from_lang}, to={to_lang}')

        validate_translation_params(video_path, source_srt_file, from_lang, to_lang)
        lang_obj, orig_to_lang = convert_language_codes(to_lang, forced, hi)

        logging.debug(f'BAZARR is translating in {lang_obj} this subtitles {source_srt_file}')

        dest_srt_file = get_subtitle_path(
            video_path,
            language=lang_obj if isinstance(lang_obj, Language) else lang_obj.subzero_language(),
            extension='.srt',
            forced_tag=forced,
            hi_tag=hi
        )

        translator_type = settings.translator.translator_type or 'google'
        logging.debug(f'Using translator type: {translator_type}')

        translator = TranslatorFactory.create_translator(
            translator_type,
            source_srt_file=source_srt_file,
            dest_srt_file=dest_srt_file,
            lang_obj=lang_obj,
            from_lang=from_lang,
            to_lang=alpha3_from_alpha2(to_lang),
            media_type=media_type,
            video_path=video_path,
            orig_to_lang=orig_to_lang,
            forced=forced,
            hi=hi,
            sonarr_series_id=sonarr_series_id,
            sonarr_episode_id=sonarr_episode_id,
            radarr_id=radarr_id
        )

        logging.debug(f'Created translator instance: {translator.__class__.__name__}')
        result = translator.translate()
        logging.debug(f'BAZARR saved translated subtitles to {dest_srt_file}')
        
        # Post-processing after successful translation
        if result:
            _handle_post_processing(video_path, dest_srt_file, to_lang, forced, hi, 
                                    media_type, sonarr_series_id, sonarr_episode_id, radarr_id)
        
        return result

    except Exception as e:
        logging.error(f'Translation failed: {str(e)}', exc_info=True)
        return False


def _handle_post_processing(video_path, subtitle_path, language_code2, forced, hi, 
                            media_type, sonarr_series_id, sonarr_episode_id, radarr_id):
    """Handle post-processing for translated subtitles"""
    try:
        use_postprocessing = settings.general.use_postprocessing
        postprocessing_cmd = settings.general.postprocessing_cmd
        
        if not use_postprocessing:
            return
            
        # Calculate score from translator default_score setting (percentage)
        default_score_percentage = int(settings.translator.default_score or 50)
        if media_type == 'series':
            # Series max score is 360
            percent_score = default_score_percentage
            max_score = 360
        else:
            # Movies max score is 120
            percent_score = default_score_percentage
            max_score = 120
        
        # Get language information
        language_code3 = alpha3_from_alpha2(language_code2)
        if hi:
            modifier_string = " HI"
            modifier_code = ":hi"
        elif forced:
            modifier_string = " forced"
            modifier_code = ":forced"
        else:
            modifier_string = ""
            modifier_code = ""
        
        downloaded_language = language_from_alpha3(language_code3) + modifier_string
        downloaded_language_code2 = language_code2 + modifier_code
        downloaded_language_code3 = language_code3 + modifier_code
        
        # Get audio language from database
        audio_language = None
        audio_language_code2 = None
        audio_language_code3 = None
        
        if media_type == 'series':
            episode_metadata = database.execute(
                select(TableEpisodes.audio_language, TableEpisodes.sonarrSeriesId, TableEpisodes.sonarrEpisodeId)
                    .where(TableEpisodes.path == path_mappings.path_replace_reverse(video_path))
            ).first()
            
            if episode_metadata:
                audio_language_list = get_audio_profile_languages(episode_metadata.audio_language)
                if len(audio_language_list) > 0:
                    audio_language = audio_language_list[0]['name']
                    audio_language_code2 = audio_language_list[0].get('code2', '')
                    audio_language_code3 = audio_language_list[0].get('code3', '')
                series_id = episode_metadata.sonarrSeriesId
                episode_id = episode_metadata.sonarrEpisodeId
            else:
                series_id = sonarr_series_id or ""
                episode_id = sonarr_episode_id or ""
        else:
            movie_metadata = database.execute(
                select(TableMovies.audio_language, TableMovies.radarrId)
                    .where(TableMovies.path == path_mappings.path_replace_reverse_movie(video_path))
            ).first()
            
            if movie_metadata:
                audio_language_list = get_audio_profile_languages(movie_metadata.audio_language)
                if len(audio_language_list) > 0:
                    audio_language = audio_language_list[0]['name']
                    audio_language_code2 = audio_language_list[0].get('code2', '')
                    audio_language_code3 = audio_language_list[0].get('code3', '')
                series_id = ""
                episode_id = movie_metadata.radarrId
            else:
                series_id = ""
                episode_id = radarr_id or ""
        
        # Default audio language if not found
        if not audio_language:
            audio_language = "Unknown"
            audio_language_code2 = ""
            audio_language_code3 = ""
        
        # Build post-processing command
        command = pp_replace(
            postprocessing_cmd,
            video_path,
            subtitle_path,
            downloaded_language,
            downloaded_language_code2,
            downloaded_language_code3,
            audio_language,
            audio_language_code2,
            audio_language_code3,
            percent_score,
            "translator",  # subtitle_id - use "translator" as identifier
            "translator",  # provider - set to "translator" for translated subtitles
            None,  # uploader
            None,  # release_info
            series_id,
            episode_id
        )
        
        # Apply threshold checks
        if media_type == 'series':
            use_pp_threshold = settings.general.use_postprocessing_threshold
            pp_threshold = int(settings.general.postprocessing_threshold)
        else:
            use_pp_threshold = settings.general.use_postprocessing_threshold_movie
            pp_threshold = int(settings.general.postprocessing_threshold_movie)
        
        # Execute post-processing if threshold conditions are met
        if not use_pp_threshold or (use_pp_threshold and percent_score < pp_threshold):
            logging.debug(f"BAZARR Using post-processing command for translated subtitle: {command}")
            postprocessing(command, video_path)
            set_chmod(subtitles_path=subtitle_path)
        else:
            logging.debug(f"BAZARR post-processing skipped for translated subtitle because score isn't below "
                         f"threshold value: {pp_threshold}%")
            
    except Exception as e:
        logging.error(f'BAZARR Post-processing failed for translated subtitle {subtitle_path}: {repr(e)}')