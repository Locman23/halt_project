"""
halt_controller.py - HALT Project
NAO Desk Companion: Break Reminder Robot
Course: 3003ICT Programming for Robotics
Specialisation: Human-Robot Interaction

Uses a Finite State Machine (FSM) to monitor user presence and
remind them to take breaks. Inputs are simulated via keyboard.
"""

from controller import Robot

from config import Config
from halt_robot import HaltRobot
from presence_detector import PresenceDetector
from halt_fsm import HaltFSM


# Module diagram for report/video:
#   halt_controller.py   -> startup and main loop wiring
#   config.py            -> shared constants and timing values
#   presence_detector.py -> Sense: camera/manual presence input
#   halt_fsm.py          -> Think: FSM decisions and transitions
#   halt_robot.py        -> Act: NAO poses and gesture output
#
# Runtime flow each step:
#   PresenceDetector.update() -> HaltFSM.update() -> HaltRobot pose/gesture methods


robot = Robot()
timestep = int(robot.getBasicTimeStep())

halt_robot = HaltRobot(robot)
presence = PresenceDetector(robot, timestep)
fsm = HaltFSM(robot, timestep, halt_robot, presence)


print("=" * 60)
print(" HALT Controller started")
print(
    f" Thresholds — gentle: {Config.GENTLE_THRESHOLD_DEFAULT}s | "
    f"escalation: {Config.ESCALATION_THRESHOLD_DEFAULT}s | "
    f"quiet: {Config.QUIET_DURATION_DEFAULT}s"
)
print(" Keys: P=toggle manual presence mode")
print("       O=toggle manual present/absent while manual mode is active")
print("       1=snooze  2=acknowledge  3=quiet  E=fault  R=reset")
print("=" * 60)

fsm.enter_state(Config.IDLE)


while robot.step(timestep) != -1:
    fsm.handle_keyboard()
    presence.update()
    fsm.update()
