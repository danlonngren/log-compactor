import argparse
import os
import re

def ensure_dir_for_file(filepath):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def compact_lines(lines):
    prev_line = None
    count = 0
    for line in lines:
        line = line.rstrip('\n')
        if line == prev_line:
            count += 1
        else:
            if prev_line is not None:
                if count > 1:
                    yield f"{prev_line} (x{count})"
                else:
                    yield prev_line
            prev_line = line
            count = 1
    if prev_line is not None:
        if count > 1:
            yield f"{prev_line} (x{count})"
        else:
            yield prev_line

def parse_timestamp_range(range_str):
    """
    Parse timestamp range string 'start-end' into tuple of floats.
    """
    try:
        parts = range_str.split('-')
        if len(parts) != 2:
            raise ValueError
        start = float(parts[0])
        end = float(parts[1])
        if start > end:
            raise ValueError
        return start, end
    except Exception:
        raise argparse.ArgumentTypeError(
            "Timestamp range must be in format start-end with start <= end, e.g. 100026.000-100050.500"
        )

def line_timestamp_in_range(line, ts_start, ts_end):
    """
    Extract the first numeric token in the line as timestamp (float).
    Return True if timestamp is within [ts_start, ts_end].
    If no valid timestamp found, return False.
    """
    tokens = line.strip().split()
    for token in tokens:
        try:
            ts = float(token)
            # Found a numeric timestamp
            if ts_start is not None and ts < ts_start:
                return False
            if ts_end is not None and ts > ts_end:
                return False
            return True
        except ValueError:
            continue
    return False  # no numeric token found

def lines_filtered(file_path, start_line, end_line, ts_start, ts_end):
    """
    Generator to yield lines filtered by line number and timestamp range.
    Lines are yielded only if:
    - line number is in [start_line, end_line]
    - first numeric token (timestamp) in line is in [ts_start, ts_end]
    """
    with open(file_path, 'r') as f:
        for i, line in enumerate(f, start=1):
            if i < start_line:
                continue
            if end_line is not None and i > end_line:
                break
            if (ts_start is not None or ts_end is not None) and not line_timestamp_in_range(line, ts_start, ts_end):
                continue
            yield line

def extract_timestamp_and_content(line):
    """
    Extract timestamp (first number in line) and content excluding timestamp.
    """
    match = re.search(r'(\d+(\.\d+)?)', line)
    if not match:
        # No timestamp found, return None and whole line
        return None, line.rstrip('\n')
    ts_str = match.group(1)
    ts = float(ts_str)
    start, end = match.span(1)
    # Remove timestamp substring from line to get content
    content = line[:start] + line[end:]
    content = content.rstrip('\n')
    return ts, content

def process_compact(input_file, output_file, start_line, end_line, ts_start, ts_end):
    ensure_dir_for_file(output_file)
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        prev_content = None
        group_lines = []
        group_timestamps = []
        group_line_numbers = []

        def line_in_filters(line, lineno, ts):
            if lineno < start_line:
                return False
            if end_line is not None and lineno > end_line:
                return False
            if ts_start is not None and ts < ts_start:
                return False
            if ts_end is not None and ts > ts_end:
                return False
            return True

        for lineno, line in enumerate(fin, start=1):
            ts, content = extract_timestamp_and_content(line)
            if content == prev_content:
                group_lines.append(line)
                group_timestamps.append(ts)
                group_line_numbers.append(lineno)
            else:
                # Process previous group
                if prev_content is not None:
                    # Filter lines
                    filtered = [
                        (ln, l, t) for ln, l, t in zip(group_line_numbers, group_lines, group_timestamps)
                        if line_in_filters(l, ln, t)
                    ]
                    count = len(filtered)
                    if count > 0:
                        if count == 1:
                            # Output the original line with timestamp
                            fout.write(filtered[0][1])
                        else:
                            ts_min = min(t for _, _, t in filtered if t is not None)
                            ts_max = max(t for _, _, t in filtered if t is not None)
                            fout.write(f"{prev_content} (x{count}, TS: {ts_min:.3f}-{ts_max:.3f})\n")

                # Start new group
                prev_content = content
                group_lines = [line]
                group_timestamps = [ts]
                group_line_numbers = [lineno]

        # Process last group
        if prev_content is not None:
            filtered = [
                (ln, l, t) for ln, l, t in zip(group_line_numbers, group_lines, group_timestamps)
                if line_in_filters(l, ln, t)
            ]
            count = len(filtered)
            if count > 0:
                if count == 1:
                    fout.write(filtered[0][1])
                else:
                    ts_min = min(t for _, _, t in filtered if t is not None)
                    ts_max = max(t for _, _, t in filtered if t is not None)
                    fout.write(f"{prev_content} (x{count}, TS: {ts_min:.3f}-{ts_max:.3f})\n")

def process_split(input_file, output_file_base, keywords, compact, start_line, end_line, ts_start, ts_end):
    if output_file_base.endswith('.log'):
        base = output_file_base[:-4]
    else:
        base = output_file_base

    dir_path = os.path.dirname(base)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)

    keyword_files = {}
    for kw in keywords:
        filename = f"{base}.{kw}.log"
        ensure_dir_for_file(filename)
        keyword_files[kw] = open(filename, 'w')

    try:
        prev_lines = {kw: None for kw in keywords}
        counts = {kw: 0 for kw in keywords}

        for line in lines_filtered(input_file, start_line, end_line, ts_start, ts_end):
            stripped_line = line.rstrip('\n')

            for kw in keywords:
                if kw in stripped_line:
                    if compact:
                        if stripped_line == prev_lines[kw]:
                            counts[kw] += 1
                        else:
                            if prev_lines[kw] is not None:
                                if counts[kw] > 1:
                                    keyword_files[kw].write(f"{prev_lines[kw]} (x{counts[kw]})\n")
                                else:
                                    keyword_files[kw].write(prev_lines[kw] + '\n')
                            prev_lines[kw] = stripped_line
                            counts[kw] = 1
                    else:
                        keyword_files[kw].write(line)
                    break  # matched keyword, no need to check others

        if compact:
            for kw in keywords:
                if prev_lines[kw] is not None:
                    if counts[kw] > 1:
                        keyword_files[kw].write(f"{prev_lines[kw]} (x{counts[kw]})\n")
                    else:
                        keyword_files[kw].write(prev_lines[kw] + '\n')
    finally:
        for f in keyword_files.values():
            f.close()

def parse_time_range(range_str):
    """Parse a string like '100-200' into (100, 200) tuple of ints."""
    try:
        parts = range_str.split('-')
        if len(parts) != 2:
            raise ValueError
        start = int(parts[0])
        end = int(parts[1])
        if start < 1 or end < start:
            raise ValueError
        return start, end
    except Exception:
        raise argparse.ArgumentTypeError("Time range must be in format start-end with start <= end and both >=1")

def main():
    parser = argparse.ArgumentParser(description='Process and compact log files, optionally split by keywords and line or timestamp ranges.')
    parser.add_argument('log', help='Input log file path')
    parser.add_argument('-o', '--output', help='Output file path or base name for split logs', required=True)
    parser.add_argument('-c', '--compact', help='Enable compacting repeated lines', action='store_true')
    parser.add_argument('-s', '--split', help='Comma-separated keywords to split log by')
    parser.add_argument('-l', '--line-range', help="Line number range to process (e.g. 100-200)", type=parse_time_range)
    parser.add_argument('-t', '--timestamp-range', help="Timestamp range to process (e.g. 100026.000-100050.500)", type=parse_timestamp_range)

    args = parser.parse_args()

    start_line, end_line = 1, None
    if args.line_range:
        start_line, end_line = args.line_range

    ts_start, ts_end = None, None
    if args.timestamp_range:
        ts_start, ts_end = args.timestamp_range

    if args.split:
        keywords = [kw.strip() for kw in args.split.split(',')]
        if not keywords:
            print("No keywords provided for splitting.")
            return
        process_split(args.log, args.output, keywords, args.compact, start_line, end_line, ts_start, ts_end)
    else:
        if args.compact:
            process_compact(args.log, args.output, start_line, end_line, ts_start, ts_end)
        else:
            ensure_dir_for_file(args.output)
            with open(args.log, 'r') as fin, open(args.output, 'w') as fout:
                for line in lines_filtered(args.log, start_line, end_line, ts_start, ts_end):
                    fout.write(line)

if __name__ == "__main__":
    main()
