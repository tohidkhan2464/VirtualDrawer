import time


class FPSCounter:

    def __init__(self):
        self.prev_time = 0

    def get_fps(self):

        current_time = time.time()

        fps = 0

        if self.prev_time != 0:
            fps = 1 / (current_time - self.prev_time)

        self.prev_time = current_time

        return int(fps)