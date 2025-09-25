# log-compactor
A lightweight Python tool to compact, filter, and split log files by content and timestamp ranges. It merges consecutive log lines ignoring timestamps, counts repeated entries, and supports splitting logs by keywords with flexible timestamp and line range filters.

# Options:
- -c, --compact: Enable compacting repeated lines (ignores timestamps when comparing lines)
- -s, --split: Comma-separated keywords to split log into multiple files (e.g., ERROR,WARNING,INFO)
- -t, --time-range: Line number range to process, format start-end (e.g., 100-200)
- --timestamp-range: Timestamp range to process, format start-end (e.g., 100000.000-100100.000)

# Example usage:
python log_compactor.py <log_file> -o <output_file_or_base> [options]

# Example output:
(python3 ./compactLog.py ./logs/repeatlog.log -o ./out/compact.log -c)
```bash
TS: INFO Starting the service (x3, TS: 100000.000-100002.000)
TS: WARNING Low disk space (x2, TS: 100003.000-100004.000)
TS: ERROR Failed to connect to database (x3, TS: 100005.000-100007.000)
TS: INFO Retrying connection (x3, TS: 100008.000-100010.000)
TS: INFO Service started successfully (x2, TS: 100011.000-100012.000)
TS: WARNING High memory usage (x3, TS: 100013.000-100015.000)
TS: ERROR Timeout while reading response (x2, TS: 100016.000-100017.000)
TS: INFO Cleanup started (x2, TS: 100018.000-100019.000)
```
