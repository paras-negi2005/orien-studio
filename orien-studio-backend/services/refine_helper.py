def get_window_by_timestamp(
    windows,
    start_time,
    end_time=None
):
    """
    Find the window corresponding to a highlight.

    We use a tolerance because floating-point
    timestamps are rarely identical.
    """

    for window in windows:

        if abs(
            window["start"] - start_time
        ) < 1:

            return window

    return None