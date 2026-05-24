"""
halt_controller.py - HALT Project
Course: 3003ICT Programming for Robotics
Specialisation: Human-Robot Interaction
"""

from controller import Robot

from config import Config
from halt_robot import HaltRobot
from presence_detector import PresenceDetector
from halt_fsm import HaltFSM


# Module overview:
#   halt_controller.py   -> startup and main loop wiring
#   config.py            -> shared constants and timing values
#   presence_detector.py -> Sense: camera/manual presence input
#   halt_fsm.py          -> Think: FSM decisions and transitions
#   halt_robot.py        -> Act: NAO poses and gesture output
#
# Runtime flow each step:
#   HaltFSM.handle_keyboard() -> PresenceDetector.update() -> HaltFSM.update()


def main():
    """Create the HALT components and run the Webots control loop."""
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


if __name__ == "__main__":
    main()
