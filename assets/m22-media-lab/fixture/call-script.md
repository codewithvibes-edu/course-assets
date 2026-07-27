# The fixture: a scripted, synthetic support call

`maple-finch-support-call.mp4` is 73 seconds of a fake customer-support call at a
fictional company, Maple + Finch Garden Supply. Both voices are macOS text-to-speech
voices reading the script below, which was written for this course. No real person
appears in the audio or on the screen-share video. The company, the order, and the
planter box are all invented.

That is the consent story for THIS recording: it is synthetic, so there is nobody to
ask. Your own recordings do not get that shortcut. Before your media enters this
pipeline, every recorded person has agreed to the use, and lesson 2 makes you write
that down before any tool runs.

The video track is a staged screen share: an order-status page, a hold screen, an
order-detail page, a fulfillment-timeline chart, and a resolution screen. It exists so
the frame-sampling and OCR lessons have real slides, a real chart, and real scene
changes to work with.

`source-record.json` records how the fixture was generated, by what tool versions, on
what date, with SHA-256 hashes of the frozen files. `scripts/generate_fixture.py` is
the generator itself and doubles as the source record for lesson 2. `timeline.json` is
generation ground truth (exact line timings, the hold silence, the overlap region, and
scene boundaries). Use it to CHECK your review work in lessons 4 through 7. Do not feed
it to your pipeline tools; a real recording never comes with one.

## The script

Speakers below are named only as agent and caller. When your diarization step runs in
lesson 5, it produces anonymous labels like `speaker_00` and `speaker_01`. Deciding
that `speaker_00` "is Riley" is a claim about identity, and this course does not make
identity claims from voices.

| # | Speaker | Line |
|---|---------|------|
| 0 | agent | Thanks for calling Maple and Finch Garden Supply, this is Riley. What can I help you with today? |
| 1 | caller | Hi Riley. I placed an order last week, order four two one seven, and the status page still says processing. |
| 2 | agent | Let me pull that up. One moment. |
| | | *3.5 seconds of hold silence. The video cuts to the hold screen.* |
| 3 | agent | Okay, I see it. Order four two one seven, one cedar planter box, placed July fourteenth. |
| 4 | caller | Right. |
| 5 | agent | The warehouse shows it packed, but the carrier never picked it up. That is why the status is stuck. |
| 6 | caller | So is it lost, or... |
| 7 | agent | No, no, it is still on the shelf. *(starts about one second before line 6 ends; the two voices overlap)* |
| 8 | caller | Okay. So what happens now? |
| 9 | agent | Two options. I can reship it tomorrow with two day shipping at no charge, or refund the whole order today. |
| 10 | caller | Hmm. |
| 11 | caller | Reship it. I still want the planter. |
| 12 | agent | Done. The new tracking number goes out to your email tonight. Anything else? |
| 13 | caller | No, that covers it. Thanks. |
| 14 | agent | Thanks for calling Maple and Finch. Have a good one. |

## Why the script is shaped this way

Every awkward moment above is there on purpose, because each one gives a lesson something to work on:

- The spoken digits in lines 1 and 3 ("four two one seven") come back from
  transcription as "4217". The connecting word inside the company name is what scores
  low (0.167 on one pass), while the real error, cedar heard as -seater, scores 0.743
  and never reaches the review queue. Lesson 4 works both cases.
- The 3.5 second hold silence separates voice-activity segmentation from fixed
  windows in lesson 3.
- The overlap at lines 6 and 7, the one-word turns at 4 and 10, and the caller
  speaking twice in a row at 10 and 11 are the classic diarization review cases in
  lesson 5.
- The slide text, the timeline chart, and the hard cut to the hold screen give
  lesson 6 frames worth sampling and OCR text worth checking.
