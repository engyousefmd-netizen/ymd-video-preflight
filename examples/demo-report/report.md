# تقرير فحص الفيديو

**synthetic-review.mp4** — يحتاج إلى مراجعة

> **تظل المراجعة البشرية ضرورية.** رصد الإطارات السوداء والصمت وثبات الصورة يعتمد على مؤشرات آلية، وقد تكون هذه المقاطع مقصودة. راجع التوقيتات المحددة قبل اتخاذ قرار تحريري؛ هذا التقرير لا يمثل اعتمادًا إبداعيًا أو موافقة على التسليم.

## نظرة عامة

- **وقت الإنشاء:** 2026-11-14T08:38:26.968832+00:00
- **ملف الإعدادات:** vertical-social
- **المدة:** 00:00:08.000
- **حجم الملف:** 932.61 KiB
- **نطاق الفحص:** فحص كامل

اجتاز: **10** · مراجعة: **6** · لم يجتز: **0** · معلومة: **0**

## الفحوص

| الحالة | الفحص | النتيجة |
| --- | --- | --- |
| مراجعة | Resolution | Encoded short edge 360px; house minimum 720px. |
| مراجعة | Black segments | 1 interval(s) above the configured threshold. Review intentional pauses, fades and stills. |
| مراجعة | Silence segments | 1 interval(s) above the configured threshold. Review intentional pauses, fades and stills. |
| مراجعة | Static/frozen segments | 2 interval(s) above the configured threshold. Review intentional pauses, fades and stills. |
| مراجعة | Integrated loudness | Measured -25.69 LUFS; house target -16 ± 2 LU. |
| مراجعة | SRT captions | 3 cues; 5 issue(s). |

## الفيديو

- **الترميز:** h264
- **أبعاد العرض:** 360 × 640
- **الأبعاد المخزنة:** 360 × 640
- **معدل الإطارات:** 25 fps
- **تنسيق البكسل:** yuv420p
- **الدوران:** 0 °

## الصوت

- **الترميز:** aac
- **معدل أخذ العينات:** 48000 Hz
- **القنوات:** 1
- **جهارة الصوت المتكاملة:** -25.69 LUFS
- **الذروة الحقيقية:** -19.54 dBFS
- **نطاق الجهارة:** 2.2 LU

## الأحداث المرصودة

| الحدث | البداية | النهاية | المدة |
| --- | --- | --- | --- |
| إطارات سوداء | 00:00:02.000 | 00:00:03.200 | 00:00:01.200 |
| ثبات الصورة | 00:00:02.000 | 00:00:03.200 | 00:00:01.200 |
| صمت | 00:00:02.005 | 00:00:03.221 | 00:00:01.216 |
| ثبات الصورة | 00:00:03.200 | 00:00:05.200 | 00:00:02.000 |

## الترجمة النصية

الملف: **captions.srt** · المقاطع النصية: **3**

- **مراجعة · المقطع 2:** Text line 1 has approximately 53 characters; the configured limit is 42.
- **مراجعة · المقطع 2:** Reading speed is approximately 40.8 characters/second; the configured limit is 20.
- **مراجعة · المقطع 3:** Cue ends at 9.000s, beyond the video duration of 8.000s.
- **مراجعة · المقطع 3:** Reading speed is approximately 20.7 characters/second; the configured limit is 20.
- **مراجعة · المقطع 2:** Cue overlaps cue 1.

## ملاحظات التحليل

- **حدود التحليل:** House profiles are editable preferences, not official platform requirements.
- **حدود التحليل:** Black, silence and freeze detections are review cues; intentional stills, fades and pauses can trigger them.
- **حدود التحليل:** Only the selected primary video/audio streams are scanned. Captions are checked from an optional external SRT.
- **حدود التحليل:** No aesthetic, factual, legal, lip-sync, speech-recognition or caption-meaning verification is performed.
- **حدود التحليل:** A pass means configured checks completed without a flag; a person must review the delivery.
