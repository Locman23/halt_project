"""Shared configuration values for the HALT controller modules."""

import math


class Config:
    """Central place for state names, timing values, and perception thresholds."""

    # FSM state names
    IDLE = "IDLE"
    MONITORING = "MONITORING"
    GENTLE_REMINDER = "GENTLE_REMINDER"
    ESCALATED_REMINDER = "ESCALATED_REMINDER"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    QUIET_MODE = "QUIET_MODE"
    FAIL_SAFE = "FAIL_SAFE"

    VALID_STATES = (
        IDLE,
        MONITORING,
        GENTLE_REMINDER,
        ESCALATED_REMINDER,
        ACKNOWLEDGED,
        QUIET_MODE,
        FAIL_SAFE,
    )

    # Timing / thresholds
    GENTLE_THRESHOLD_DEFAULT = 10.0
    ESCALATION_THRESHOLD_DEFAULT = 8.0
    QUIET_DURATION_DEFAULT = 15.0
    GENTLE_MIN = 5.0
    GENTLE_MAX = 20.0
    ESCALATION_MIN = 4.0
    ADAPTIVE_STEP = 1.0
    ACKNOWLEDGED_GESTURE_DURATION = 2.0
    ESCALATED_TIMEOUT = 12.0

    # Debug / console logging
    DEBUG_LOGS = True

    # Joint limits used for safety clamping in HaltRobot.
    JOINT_LIMITS = {
        "HeadYaw": (-2.0857, 2.0857),
        "HeadPitch": (-0.6720, 0.5149),
        "RShoulderPitch": (-2.0857, 2.0857),
        "RShoulderRoll": (-1.3265, 0.3142),
        "RElbowYaw": (-2.0857, 2.0857),
        "RElbowRoll": (0.0349, 1.5446),
        "RWristYaw": (-1.8238, 1.8238),
        "LShoulderPitch": (-2.0857, 2.0857),
        "LShoulderRoll": (-0.3142, 1.3265),
        "LElbowYaw": (-2.0857, 2.0857),
        "LElbowRoll": (-1.5446, -0.0349),
    }

    # Gesture tuning values.
    GENTLE_WAVE = {
        "frequency": 0.45,
        "right_shoulder_pitch": -0.85,
        "right_shoulder_roll": -0.45,
        "right_elbow_yaw": 0.75,
        "right_elbow_roll_base": 0.75,
        "right_elbow_roll_amplitude": 0.10,
        "right_wrist_yaw_amplitude": 0.45,
        "head_yaw": -0.12,
        "head_pitch": -0.08,
    }

    ESCALATED_WAVE = {
        "frequency": 1.15,
        "secondary_phase_offset": math.pi / 2,
        "right_shoulder_pitch": -1.05,
        "right_shoulder_roll_base": -0.55,
        "right_shoulder_roll_amplitude": 0.10,
        "right_elbow_yaw_base": 0.55,
        "right_elbow_yaw_amplitude": 0.20,
        "right_elbow_roll_base": 0.85,
        "right_elbow_roll_amplitude": 0.20,
        "right_wrist_yaw_amplitude": 0.85,
        "head_yaw_base": -0.12,
        "head_yaw_amplitude": 0.12,
        "head_pitch": -0.08,
    }

    # Camera-based presence detection (red marker)
    RED_MIN_R = 150
    RED_MAX_G = 100
    RED_MAX_B = 100
    RED_RATIO_THRESHOLD = 0.02
    SAMPLE_STEP = 4
    PRESENCE_LOST_DELAY = 3.0

    INTERACTION_STATES = (
        MONITORING,
        GENTLE_REMINDER,
        ESCALATED_REMINDER,
        ACKNOWLEDGED,
        QUIET_MODE,
    )

    @classmethod
    def log(cls, message):
        """Print a debug message when verbose logging is enabled."""
        if cls.DEBUG_LOGS:
            print(message)