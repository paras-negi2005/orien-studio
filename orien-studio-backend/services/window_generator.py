def create_windows(segments):

    windows = []

    i = 0

    while i < len(segments):

        start = segments[i]["start"]

        text = ""
        end = start

        collected_segments = []

        j = i

        while j < len(segments):

            text += " " + segments[j]["text"]

            end = segments[j]["end"]

            collected_segments.append(
                segments[j]
            )

            # 45-second window
            if end - start >= 45:
                break

            j += 1

        windows.append(
            {
                "start": start,
                "end": end,
                "text": text.strip(),
                "segments": collected_segments
            }
        )

        # overlap windows
        i += 5

    return windows