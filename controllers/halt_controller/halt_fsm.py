"""Finite-state decision logic for HALT reminders and safety handling."""

from config import Config


# Think: HaltFSM consumes sensing and keyboard input, then decides which action state to run.
class HaltFSM:
    """Manage HALT state transitions, keyboard input, and adaptive reminder timing."""

    def __init__(self, robot, timestep, halt_robot, presence):
        self.robot = robot
        self.halt_robot = halt_robot
        self.presence = presence

        self.keyboard = self.robot.getKeyboard()
        self.keyboard.enable(timestep)

        self.current_state = Config.IDLE
        self.state_start_time = 0.0
        self.gesture_phase_start = 0.0
        self.gentle_threshold = Config.GENTLE_THRESHOLD_DEFAULT
        self.escalation_threshold = Config.ESCALATION_THRESHOLD_DEFAULT
        self.quiet_duration = Config.QUIET_DURATION_DEFAULT
        self.pending_claps = 0

    def _apply_static_pose(self, state):
        """Apply the one-off pose for states that do not animate over time."""
        if state == Config.IDLE:
            self.halt_robot.set_idle_pose()
        elif state == Config.FAIL_SAFE:
            self.halt_robot.set_fail_safe_pose()
        elif state == Config.MONITORING:
            self.halt_robot.set_monitoring_pose()
        elif state == Config.QUIET_MODE:
            self.halt_robot.set_quiet_pose()

    def enter_state(self, new_state):
        """Transition to a new FSM state and apply any immediate static pose."""
        if new_state not in Config.VALID_STATES:
            Config.log(f"[FAIL_SAFE] Invalid transition requested: {new_state}")
            new_state = Config.FAIL_SAFE

        now = self.robot.getTime()
        Config.log(f"[FSM] {self.current_state} → {new_state}  (t={now:.1f}s)")
        self.current_state = new_state
        self.state_start_time = now
        self.gesture_phase_start = now
        self._apply_static_pose(new_state)

    def update_adaptive_logic(self, response_type):
        """Adjust reminder thresholds after a quick response or a required escalation."""
        if response_type == "quick":
            self.gentle_threshold = min(
                self.gentle_threshold + Config.ADAPTIVE_STEP,
                Config.GENTLE_MAX,
            )
            Config.log(
                f"[ADAPT] Quick response — gentle_threshold increased to {self.gentle_threshold:.1f}s"
            )

        elif response_type == "escalated":
            self.escalation_threshold = max(
                self.escalation_threshold - Config.ADAPTIVE_STEP,
                Config.ESCALATION_MIN,
            )
            Config.log(
                f"[ADAPT] Escalation needed — escalation_threshold decreased to {self.escalation_threshold:.1f}s"
            )

    def handle_keyboard(self):
        """Poll the keyboard and handle manual presence, clap, and fail-safe inputs."""
        key = self.keyboard.getKey()
        while key != -1:
            char = chr(key).upper() if 0 < key < 128 else None

            if char == "P":
                self.presence.toggle_manual_mode()

            elif char == "O":
                self.presence.toggle_manual_presence()

            elif char == "1":
                self.pending_claps = 1
                Config.log("[INPUT] 1 clap detected (snooze)")

            elif char == "2":
                self.pending_claps = 2
                Config.log("[INPUT] 2 claps detected (acknowledge)")

            elif char == "3":
                self.pending_claps = 3
                Config.log("[INPUT] 3 claps detected (quiet mode)")

            elif char == "E":
                Config.log("[INPUT] Sensor fault simulated — entering FAIL_SAFE")
                self.enter_state(Config.FAIL_SAFE)

            elif char == "R":
                if self.current_state == Config.FAIL_SAFE:
                    Config.log("[INPUT] Reset from FAIL_SAFE → IDLE")
                    self.enter_state(Config.IDLE)

            key = self.keyboard.getKey()

    def update(self):
        """Evaluate the current FSM state, apply outputs, and perform any transitions."""
        now = self.robot.getTime()
        elapsed = now - self.state_start_time
        gesture_elapsed = now - self.gesture_phase_start

        claps = self.pending_claps
        self.pending_claps = 0

        if self.current_state not in Config.VALID_STATES:
            Config.log(f"[FAIL_SAFE] Invalid state detected: {self.current_state}")
            self.enter_state(Config.FAIL_SAFE)
            return

        if self.current_state == Config.FAIL_SAFE:
            return

        if not self.presence.user_present and self.current_state in Config.INTERACTION_STATES:
            Config.log("[FSM] User absent — returning to IDLE")
            self.enter_state(Config.IDLE)
            return

        if claps == 3:
            self.enter_state(Config.QUIET_MODE)
            return

        if self.current_state == Config.IDLE:
            if self.presence.user_present:
                self.enter_state(Config.MONITORING)

        elif self.current_state == Config.MONITORING:
            if elapsed >= self.gentle_threshold:
                self.enter_state(Config.GENTLE_REMINDER)

        elif self.current_state == Config.GENTLE_REMINDER:
            self.halt_robot.gentle_wave(gesture_elapsed)

            if claps == 1:
                self.update_adaptive_logic("quick")
                self.enter_state(Config.MONITORING)
            elif claps == 2:
                self.update_adaptive_logic("quick")
                self.enter_state(Config.ACKNOWLEDGED)
            elif elapsed >= self.escalation_threshold:
                self.update_adaptive_logic("escalated")
                self.enter_state(Config.ESCALATED_REMINDER)

        elif self.current_state == Config.ESCALATED_REMINDER:
            self.halt_robot.escalated_wave(gesture_elapsed)

            if claps == 1:
                self.enter_state(Config.GENTLE_REMINDER)
            elif claps == 2:
                self.enter_state(Config.ACKNOWLEDGED)
            elif elapsed >= Config.ESCALATED_TIMEOUT:
                Config.log("[FSM] Escalated reminder timed out — returning to MONITORING")
                self.enter_state(Config.MONITORING)

        elif self.current_state == Config.ACKNOWLEDGED:
            self.halt_robot.acknowledged_gesture(gesture_elapsed)

            if elapsed >= Config.ACKNOWLEDGED_GESTURE_DURATION:
                Config.log(
                    f"[FSM] Work cycle reset. Thresholds — gentle: {self.gentle_threshold:.1f}s, "
                    f"escalation: {self.escalation_threshold:.1f}s"
                )
                next_state = Config.MONITORING if self.presence.user_present else Config.IDLE
                self.enter_state(next_state)

        elif self.current_state == Config.QUIET_MODE:
            if elapsed >= self.quiet_duration:
                next_state = Config.MONITORING if self.presence.user_present else Config.IDLE
                Config.log(f"[FSM] Quiet mode expired — returning to {next_state}")
                self.enter_state(next_state)