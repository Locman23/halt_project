"""NAO actuation helpers for HALT poses and gesture output."""

import math

from config import Config


# Act: HaltRobot owns NAO devices and turns FSM decisions into joint movement.
class HaltRobot:
    """Wrap NAO device access and expose the movement API used by the FSM."""

    def __init__(self, robot):
        self.robot = robot
        self._motor_names = {}

        self.head_yaw = self._get_motor("HeadYaw")
        self.head_pitch = self._get_motor("HeadPitch")

        self.r_shoulder_pitch = self._get_motor("RShoulderPitch")
        self.r_shoulder_roll = self._get_motor("RShoulderRoll")
        self.r_elbow_yaw = self._get_motor("RElbowYaw")
        self.r_elbow_roll = self._get_motor("RElbowRoll")
        self.r_wrist_yaw = self._get_motor("RWristYaw")

        self.l_shoulder_pitch = self._get_motor("LShoulderPitch")
        self.l_shoulder_roll = self._get_motor("LShoulderRoll")
        self.l_elbow_yaw = self._get_motor("LElbowYaw")
        self.l_elbow_roll = self._get_motor("LElbowRoll")

        all_motors = [
            self.head_yaw,
            self.head_pitch,
            self.r_shoulder_pitch,
            self.r_shoulder_roll,
            self.r_elbow_yaw,
            self.r_elbow_roll,
            self.r_wrist_yaw,
            self.l_shoulder_pitch,
            self.l_shoulder_roll,
            self.l_elbow_yaw,
            self.l_elbow_roll,
        ]
        for motor in all_motors:
            if motor is not None:
                motor.setVelocity(1.0)

    def _get_motor(self, name):
        """Return a motor device by name, or None if the device does not exist."""
        try:
            motor = self.robot.getDevice(name)
            if motor is None:
                print(f"[WARN] Motor not found: {name}")
            else:
                self._motor_names[id(motor)] = name
            return motor
        except Exception as error:
            print(f"[WARN] Error getting motor '{name}': {error}")
            return None

    def _clamp_angle(self, motor_name, angle):
        """Clamp a target angle to the configured joint limits when available."""
        limits = Config.JOINT_LIMITS.get(motor_name)
        if limits is None:
            return angle

        min_angle, max_angle = limits
        clamped_angle = min(max(angle, min_angle), max_angle)
        if abs(clamped_angle - angle) > 1e-9:
            Config.log(f"[SAFETY] Clamped {motor_name} from {angle:.3f} to {clamped_angle:.3f}")
        return clamped_angle

    def _set(self, motor, angle):
        """Safely command a motor to a target angle."""
        if motor is not None:
            motor_name = self._motor_names.get(id(motor))
            if motor_name is not None:
                angle = self._clamp_angle(motor_name, angle)
            motor.setPosition(angle)

    def _set_head(self, yaw, pitch):
        """Set the head joints together for readability and consistency."""
        self._set(self.head_yaw, yaw)
        self._set(self.head_pitch, pitch)

    def _set_right_arm(self, shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll, wrist_yaw):
        """Set the right arm joints together."""
        self._set(self.r_shoulder_pitch, shoulder_pitch)
        self._set(self.r_shoulder_roll, shoulder_roll)
        self._set(self.r_elbow_yaw, elbow_yaw)
        self._set(self.r_elbow_roll, elbow_roll)
        self._set(self.r_wrist_yaw, wrist_yaw)

    def _set_left_arm(self, shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll):
        """Set the left arm joints together."""
        self._set(self.l_shoulder_pitch, shoulder_pitch)
        self._set(self.l_shoulder_roll, shoulder_roll)
        self._set(self.l_elbow_yaw, elbow_yaw)
        self._set(self.l_elbow_roll, elbow_roll)

    def _set_relaxed_left_arm(self):
        """Apply the standard relaxed left arm pose used in several states."""
        self._set_left_arm(1.4, 0.2, -1.2, -0.2)

    def _set_neutral_right_arm(self):
        """Apply the standard neutral right arm pose used by monitoring and fail-safe."""
        self._set_right_arm(1.4, -0.2, 1.2, 0.4, 0.0)

    def set_idle_pose(self):
        """Slumped/resting pose - head bowed, arms hanging low, robot appears inactive."""
        self._set_head(0.0, 0.5)
        self._set_right_arm(1.5, -0.1, 1.2, 0.3, 0.0)
        self._set_left_arm(1.5, 0.1, -1.2, -0.3)

    def set_monitoring_pose(self):
        """Upright attentive pose - arms at sides, head level. Used in MONITORING."""
        self._set_head(0.0, 0.0)
        self._set_neutral_right_arm()
        self._set_relaxed_left_arm()

    def gentle_wave(self, t):
        """Slow, friendly wave above the head using mostly wrist/elbow movement."""
        settings = Config.GENTLE_WAVE
        frequency = settings["frequency"]
        wave = math.sin(2 * math.pi * frequency * t)

        self._set_right_arm(
            settings["right_shoulder_pitch"],
            settings["right_shoulder_roll"],
            settings["right_elbow_yaw"],
            settings["right_elbow_roll_base"] + settings["right_elbow_roll_amplitude"] * wave,
            settings["right_wrist_yaw_amplitude"] * wave,
        )
        self._set_relaxed_left_arm()
        self._set_head(settings["head_yaw"], settings["head_pitch"])

    def escalated_wave(self, t):
        """More urgent wave above the head, with stronger wrist/elbow motion but safe shoulders."""
        settings = Config.ESCALATED_WAVE
        frequency = settings["frequency"]

        wave = math.sin(2 * math.pi * frequency * t)
        secondary_wave = math.sin(2 * math.pi * frequency * t + settings["secondary_phase_offset"])

        self._set_right_arm(
            settings["right_shoulder_pitch"],
            settings["right_shoulder_roll_base"] + settings["right_shoulder_roll_amplitude"] * wave,
            settings["right_elbow_yaw_base"] + settings["right_elbow_yaw_amplitude"] * secondary_wave,
            settings["right_elbow_roll_base"] + settings["right_elbow_roll_amplitude"] * wave,
            settings["right_wrist_yaw_amplitude"] * wave,
        )
        self._set_relaxed_left_arm()
        self._set_head(
            settings["head_yaw_base"] + settings["head_yaw_amplitude"] * wave,
            settings["head_pitch"],
        )

    def acknowledged_gesture(self, t):
        """Small downward head nod to confirm acknowledgement."""
        progress = min(t, Config.ACKNOWLEDGED_GESTURE_DURATION) / Config.ACKNOWLEDGED_GESTURE_DURATION
        nod = 0.2 * math.sin(math.pi * progress)
        self.set_monitoring_pose()
        self._set_head(0.0, nod)

    def set_quiet_pose(self):
        """Hands raised near the face for a quiet/do-not-disturb pose."""
        self._set_head(0.0, 0.1)
        self._set_right_arm(0.5, -0.1, 0.5, 1.2, 0.0)
        self._set_left_arm(0.5, 0.1, -0.5, -1.2)

    def set_fail_safe_pose(self):
        """Neutral safe pose - no animated movement."""
        self._set_head(0.0, 0.0)
        self._set_neutral_right_arm()
        self._set_relaxed_left_arm()