# Component: Text Processor

## Description

The Text Processor component is responsible for cleaning, normalizing, and chunking text before it is sent to the TTS engine. It ensures that the input text is well-formed and properly segmented to produce natural-sounding speech.

## Key Classes

- **`TextProcessor`**: Located in [`vietvoicetts/core/text_processor.py`](vietvoicetts/core/text_processor.py), this class handles all text processing operations, including vocabulary mapping, text cleaning, and chunking.

## Chunking Logic

The chunking logic is designed to split long text into smaller segments that can be processed by the TTS engine without causing issues such as unnatural pauses or mispronunciations. The process is as follows:

1.  **Sentence Splitting**: The text is first split into sentences based on punctuation marks such as `.` `?` and `!`.
2.  **Sub-sentence Splitting**: Each sentence is then split by commas (`,`) to handle complex sentences.
3.  **Word-level Chunking**: If a sub-sentence is still longer than the maximum allowed characters, it is split into words using spaces. The words are then grouped into chunks that do not exceed the maximum character limit. This ensures that no words are ever split in the middle, even for Vietnamese text.
4.  **Post-processing**: Short chunks are merged with adjacent chunks to ensure that the final output does not contain unnaturally short segments.

This process ensures that the text is chunked in a linguistically-aware manner, which is crucial for generating high-quality speech. The implementation guarantees that no word is split across chunk boundaries, and the `max_chars` limit is respected as a soft constraint.

**Related tests:** See [`tests/test_text_processor.py`](tests/test_text_processor.py).
