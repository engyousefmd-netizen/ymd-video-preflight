# Real-world field testing — YMD Video Preflight

[العربية](#دليل-تجربة-الأداة-بالعربي)

**Status:** Public alpha, open to opt-in field testing. The published verification uses synthetic fixtures; **no independent adoption or field accuracy is verified**. This guide invites genuine tests and is not a completed field study.

## Privacy comes first

Only analyze media you own, are licensed to use, or have explicit permission to test. Files are processed locally. **Do not upload private client clips, reports containing client names, paths, contact details or commercial information to GitHub Issues.** If you need to demonstrate a defect, make a synthetic FFmpeg fixture that reproduces the behavior.

## Five-minute starting test

1. Install Python 3.10+ and FFmpeg/ffprobe, using their official installers. Verify with `python --version` (or `python3 --version` / `py --version`), `ffmpeg -version`, `ffprobe -version`.
2. Download the repository ZIP from the GitHub **Code** menu and extract it. Open a terminal in the extracted project directory.
3. Try the **included synthetic fixture**. This creates new report files but does **not** modify the original video:

macOS / Linux:

```bash
python3 -m ymd_preflight "examples/media/synthetic-review.mp4" --profile vertical-social --srt "examples/media/captions.srt" --output "reports/beta-demo" --language ar --fail-on never
```

Windows (PowerShell):

```powershell
py -m ymd_preflight "examples/media/synthetic-review.mp4" --profile vertical-social --srt "examples/media/captions.srt" --output "reports/beta-demo" --language ar --fail-on never
```

4. Open `reports/beta-demo/report.html` locally. The sample intentionally contains a black interval, an audio pause, still frames and SRT problems. Detection times may differ slightly with FFmpeg versions.
5. Optionally test one *authorized* real video using a different output directory. Judge which findings actually help and which are intentional edits. `--fail-on never` does not suppress operational errors (exit 2).

## How to report useful findings

Please share observations only if you choose to participate. **A critical or negative result is just as useful as a positive one**; do not leave stars, testimonials, or public praise as a condition of testing. A single honest report is more useful than fabricated adoption. The maintainer should independently reproduce and triage reported defects.


Open a [field-feedback issue](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/new/choose) and include:

- Operating system, Python version, FFmpeg version
- General clip type (e.g. talking head, vertical ad, long-form), approximate length and aspect ratio — **without revealing client names**
- The exact command and selected profile, with private paths replaced by placeholders
- Timecodes and which warnings were useful, false positives or missed issues
- Whether a minimal synthetic sample reproduces the problem
- Suggestions that would make the tool genuinely more useful

Do not claim a report is representative of all video formats. The current version does not score visual quality, transcribe dialogue, establish lip-sync or certify a platform delivery spec.

Project tracking: [independent field-testing issue #1](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1) and [public evidence register](ADOPTION_EVIDENCE.md).

---

## دليل تجربة الأداة بالعربي

**حالة المشروع:** نسخة Alpha تجريبية، مفتوحة لتجارب اختيارية. اختباراتنا الأولى كانت بملفات مولّدة، ولم نوثّق بعد استخدامًا من مونتيرين مستقلين. الملاحظات السلبية مهمة بقدر الملاحظات الإيجابية، ولا يُطلب من المجربين تقييم نجوم أو إشادة.

1. استخدم فيديو تملكه أو مسموح لك باختباره فقط. ممنوع رفع فيديوهات العملاء أو أي بيانات حساسة على GitHub.
2. نزّل المشروع وفك الضغط. ثبّت Python وFFmpeg/ffprobe. في Windows استخدم أمر `py`، وفي macOS/Linux استخدم `python3`.
3. شغّل أمر النسخة التجريبية بالأعلى وافتح `reports/beta-demo/report.html`.
4. التقرير المصطنع فيه سواد وصمت وثبات صورة ومشكلات ترجمة مقصودة؛ الهدف اختبار الفحوص، مش الحكم على جودة فيديو حقيقي.
5. جرّب فيديو مسموح لك باستخدامه، وقارن التنبيهات بالأحداث المقصودة في المونتاج.
6. [ابعت ملاحظاتك عبر GitHub Issues](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/new/choose): نوع الفيديو بشكل عام، نظام التشغيل، إصدار FFmpeg، التوقيتات، أي نتيجة مفيدة أو إنذار خاطئ — **من غير الفيديو الأصلي أو أسماء العملاء**.

لا تعتبر التنبيه الآلي حكمًا نهائيًا؛ راجع الفيديو بعينك قبل التسليم.
