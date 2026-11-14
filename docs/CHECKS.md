# Checks and limits

| Check | Method | Interpretation |
| --- | --- | --- |
| Metadata | ffprobe selected primary streams | Encoded size, displayed orientation/SAR, average frame rate, codecs and duration |
| Black | FFmpeg `blackdetect` | Mostly black pictures meeting the configured pixel/area/duration thresholds |
| Silence | FFmpeg `silencedetect` | Combined audio below the configured noise floor for the configured duration |
| Freeze | FFmpeg `freezedetect` | Picture changes below the configured threshold, including intentional stills |
| Loudness | FFmpeg `loudnorm`, **input** statistics | Integrated LUFS, true peak and loudness range; original file is not normalized |
| Captions | UTF-8 SRT parser | Syntax, interval order/overlap, video boundary, line length and approximate character rate |
| Decode | Full selected-stream decode plus recognized error messages | A useful integrity screen, not proof of flawless media |

The current version analyzes one media file per invocation. Only the selected primary audio and non-cover-art video stream are scanned. Other language tracks, embedded captions and alternate streams need separate review.

Timestamps are FFmpeg's timeline values. Rotated video and sample aspect ratio are included in the display-ratio check. Non-right-angle rotation is flagged because a precise bounding box is not modeled. Average frame rate does not establish constant frame rate. Stream-duration difference does not establish audio/video synchronization.

Silence and freeze intervals still open at EOF are closed using the available media duration. Missing duration limits end-of-file and caption-boundary checks. Very short clips, silence or noise can yield non-finite loudness values; those become explicit missing measurements rather than JSON Infinity or a pass.

SRT reading rate counts visible text characters after simple markup removal. This is not a calibrated reading model for Arabic diacritics, emoji or grapheme clusters. A caption flag is a review aid.

## Thresholds are project preferences

The bundled defaults are editable examples, not platform or accessibility standards. Use the delivery brief to set a profile. Do not claim that this report certifies a file for publication.

## Upstream documentation

- [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html): `blackdetect`, `freezedetect`, `silencedetect`, `loudnorm`.
- [ffprobe documentation](https://ffmpeg.org/ffprobe.html).
- [FFmpeg license and legal information](https://ffmpeg.org/legal.html).

The implementation invokes installed executables. No upstream binary is copied into this source package.
