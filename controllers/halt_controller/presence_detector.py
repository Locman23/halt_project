"""Presence sensing for HALT using CameraTop and manual override input."""

from controller import Camera

from config import Config


# Sense: PresenceDetector turns CameraTop input or manual overrides into user_present.
class PresenceDetector:
    """Convert camera frames or manual override input into a stable presence signal."""

    def __init__(self, robot, timestep):
        self.robot = robot
        self.camera_top = None
        self.user_present = False
        self.camera_presence = False
        self.last_seen_user_time = 0.0
        self.manual_presence_override = False
        self.manual_user_present = False

        try:
            self.camera_top = self.robot.getDevice("CameraTop")
            if self.camera_top is not None:
                self.camera_top.enable(timestep)
            else:
                Config.log("[WARN] CameraTop not found")
        except Exception as error:
            self.camera_top = None
            Config.log(f"[WARN] Error getting CameraTop: {error}")

    def toggle_manual_mode(self):
        self.manual_presence_override = not self.manual_presence_override
        if self.manual_presence_override:
            self.manual_user_present = True
            self.user_present = self.manual_user_present
            Config.log("[INPUT] Presence mode -> MANUAL")
            Config.log("[INPUT] Manual presence state -> PRESENT")
        else:
            Config.log("[INPUT] Presence mode -> CAMERA")

    def toggle_manual_presence(self):
        if self.manual_presence_override:
            self.manual_user_present = not self.manual_user_present
            self.user_present = self.manual_user_present
            state = "PRESENT" if self.manual_user_present else "ABSENT"
            Config.log(f"[INPUT] Manual presence state -> {state}")
        else:
            Config.log("[INPUT] O ignored (manual mode is OFF)")

    def is_red_pixel(self, r, g, b):
        """Return True if RGB values match the configured red marker thresholds."""
        return r >= Config.RED_MIN_R and g <= Config.RED_MAX_G and b <= Config.RED_MAX_B

    def detect_red_presence(self):
        """Return the ratio of sampled pixels that match the red marker."""
        if self.camera_top is None:
            return 0.0

        image = self.camera_top.getImage()
        if image is None:
            return 0.0

        width = self.camera_top.getWidth()
        height = self.camera_top.getHeight()
        red_count = 0
        sampled_count = 0

        for y in range(0, height, Config.SAMPLE_STEP):
            for x in range(0, width, Config.SAMPLE_STEP):
                red = Camera.imageGetRed(image, width, x, y)
                green = Camera.imageGetGreen(image, width, x, y)
                blue = Camera.imageGetBlue(image, width, x, y)
                sampled_count += 1
                if self.is_red_pixel(red, green, blue):
                    red_count += 1

        if sampled_count == 0:
            return 0.0

        return red_count / sampled_count

    def update(self):
        """Update the public presence state using camera input and the loss delay rule."""
        if self.manual_presence_override:
            self.user_present = self.manual_user_present
            return

        red_ratio = self.detect_red_presence()
        now = self.robot.getTime()
        previous_user_present = self.user_present
        previous_camera_presence = self.camera_presence

        if red_ratio >= Config.RED_RATIO_THRESHOLD:
            self.camera_presence = True
            self.user_present = True
            self.last_seen_user_time = now
        elif now - self.last_seen_user_time > Config.PRESENCE_LOST_DELAY:
            self.camera_presence = False
            self.user_present = False

        if (
            self.camera_presence != previous_camera_presence
            or self.user_present != previous_user_present
        ):
            status = "PRESENT" if self.user_present else "ABSENT"
            Config.log(f"[PERCEPTION] Camera presence changed -> {status} (red_ratio={red_ratio:.3f})")