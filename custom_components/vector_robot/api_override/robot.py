"""Home Assistant specific calls."""
# pylint: disable=invalid-name
from __future__ import annotations

__all__ = ["Robot"]

import concurrent
import logging
from asyncio import AbstractEventLoop
from typing import Any

from ha_vector import (
    animation,
    audio,
    behavior,
    camera,
    events,
    faces,
    motors,
    nav_map,
    photos,
    proximity,
    screen,
    status,
    touch,
    util,
    viewer,
    vision,
    world,
)
from ha_vector.exceptions import (
    VectorHomeAssistantEscapepodException,
    VectorNotReadyException,
    VectorPropertyValueNotReadyException,
    VectorUnreliableEventStreamException,
)
from ha_vector.messaging import protocol
from ha_vector.version import __version__
from ha_vector.viewer import Viewer3DComponent, ViewerComponent

from .connection import (  # pylint: disable=relative-beyond-top-level
    Connection,
    ControlPriorityLevel,
    on_connection_thread,
)


class Robot:
    """Vector Robot class customized for Home Assistant usage."""

    def __init__(
        self,
        serial: str,
        ip_address: str,
        name: str,
        config: dict,
        loop: AbstractEventLoop,
        escape_pod: bool = False,
        logger: Any | None = None,
        behavior_activation_timeout: int = 10,
        cache_animation_lists: bool = False,
        enable_face_detection: bool = True,
        estimate_facial_expression: bool = True,
        enable_audio_feed: bool = False,
        enable_custom_object_detection: bool = False,
        enable_nav_map_feed: bool | None = None,
        show_viewer: bool = False,
        show_3d_viewer: bool = False,
        behavior_control_level: ControlPriorityLevel | None = None,
        force_async: bool = False,
    ):
        if not isinstance(logger, type(None)):
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

        self._config = config
        self._loop = loop
        self._force_async = force_async

        self._escape_pod = escape_pod
        self._name = self._config["name"] if "name" in self._config else name
        self._cert_file = self._config["cert"] if "cert" in self._config else None
        self._guid = self._config["guid"] if "guid" in self._config else None
        self._port = self._config["port"] if "port" in self._config else "443"
        self._ip = self._config["ip"] if "ip" in self._config else ip_address
        self._serial = self._config["serial"] if "serial" in self._config else serial

        if escape_pod:
            raise VectorHomeAssistantEscapepodException(
                "Escape Pod is currently not supported!"
            )

        self._conn = Connection(
            name=self._name,
            host=":".join([self._ip, self._port]),
            cert_file=self._cert_file,
            guid=self._guid,
            escape_pod=self._escape_pod,
            behavior_control_level=behavior_control_level,
            loop=self._loop,
            logger=self.logger,
        )

        self._events = events.EventHandler(self)

        # placeholders for components before they exist
        self._anim: animation.AnimationComponent = None
        self._audio: audio.AudioComponent = None
        self._behavior: behavior.BehaviorComponent = None
        self._camera: camera.CameraComponent = None
        self._faces: faces.FaceComponent = None
        self._motors: motors.MotorComponent = None
        self._nav_map: nav_map.NavMapComponent = None
        self._screen: screen.ScreenComponent = None
        self._photos: photos.PhotographComponent = None
        self._proximity: proximity.ProximityComponent = None
        self._touch: touch.TouchComponent = None
        self._viewer: viewer.ViewerComponent = None
        self._viewer_3d: viewer.Viewer3DComponent = None
        self._vision: vision.VisionComponent = None
        self._world: world.World = None

        self.behavior_activation_timeout = behavior_activation_timeout
        self.enable_face_detection = enable_face_detection
        self.estimate_facial_expression = estimate_facial_expression
        self.enable_custom_object_detection = enable_custom_object_detection
        self.cache_animation_lists = cache_animation_lists

        # Robot state/sensor data
        self._pose: util.Pose = None
        self._pose_angle_rad: float = None
        self._pose_pitch_rad: float = None
        self._left_wheel_speed_mmps: float = None
        self._right_wheel_speed_mmps: float = None
        self._head_angle_rad: float = None
        self._lift_height_mm: float = None
        self._accel: util.Vector3 = None
        self._gyro: util.Vector3 = None
        self._carrying_object_id: float = None
        self._head_tracking_object_id: float = None
        self._localized_to_object_id: float = None
        self._last_image_time_stamp: float = None
        self._status: status.RobotStatus = status.RobotStatus()

        self._enable_audio_feed = enable_audio_feed
        if enable_nav_map_feed is not None:
            self._enable_nav_map_feed = enable_nav_map_feed
        else:
            self._enable_nav_map_feed = False
        self._show_viewer = show_viewer
        self._show_3d_viewer = show_3d_viewer
        if show_3d_viewer and enable_nav_map_feed is None:
            self.logger.warning(
                "enable_nav_map_feed should be True for 3d viewer to render correctly."
            )
            self._enable_nav_map_feed = True

    @property
    def force_async(self) -> bool:
        """A flag used to determine if this is a :class:`Robot` or :class:`AsyncRobot`."""
        return self._force_async

    @property
    def conn(self) -> Connection:
        """A reference to the :class:`~anki_vector.connection.Connection` instance."""
        return self._conn

    @property
    def events(self) -> events.EventHandler:
        """A reference to the :class:`~anki_vector.events.EventHandler` instance."""
        return self._events

    @property
    def anim(self) -> animation.AnimationComponent:
        """A reference to the :class:`~anki_vector.animation.AnimationComponent` instance."""
        if self._anim is None:
            raise VectorNotReadyException("AnimationComponent is not yet initialized")
        return self._anim

    @property
    def audio(self) -> audio.AudioComponent:
        """The audio instance used to control Vector's microphone feed and speaker playback."""

        if self._audio is None:
            raise VectorNotReadyException("AudioComponent is not yet initialized")
        return self._audio

    @property
    def behavior(self) -> behavior.BehaviorComponent:
        """A reference to the :class:`~anki_vector.behavior.BehaviorComponent` instance."""
        return self._behavior

    @property
    def camera(self) -> camera.CameraComponent:
        """Instance used to control Vector's camera feed."""
        if self._camera is None:
            raise VectorNotReadyException("CameraComponent is not yet initialized")
        return self._camera

    @property
    def faces(self) -> faces.FaceComponent:
        """A reference to the :class:`~anki_vector.faces.FaceComponent` instance."""
        if self._faces is None:
            raise VectorNotReadyException("FaceComponent is not yet initialized")
        return self._faces

    @property
    def motors(self) -> motors.MotorComponent:
        """A reference to the :class:`~anki_vector.motors.MotorComponent` instance."""
        if self._motors is None:
            raise VectorNotReadyException("MotorComponent is not yet initialized")
        return self._motors

    @property
    def nav_map(self) -> nav_map.NavMapComponent:
        """A reference to the :class:`~anki_vector.nav_map.NavMapComponent` instance."""
        if self._nav_map is None:
            raise VectorNotReadyException("NavMapComponent is not yet initialized")
        return self._nav_map

    @property
    def screen(self) -> screen.ScreenComponent:
        """A reference to the :class:`~anki_vector.screen.ScreenComponent` instance."""
        if self._screen is None:
            raise VectorNotReadyException("ScreenComponent is not yet initialized")
        return self._screen

    @property
    def photos(self) -> photos.PhotographComponent:
        """A reference to the :class:`~anki_vector.photos.PhotographComponent` instance."""
        if self._photos is None:
            raise VectorNotReadyException("PhotographyComponent is not yet initialized")
        return self._photos

    @property
    def proximity(self) -> proximity.ProximityComponent:
        """Containing state related to object proximity detection."""
        return self._proximity

    @property
    def touch(self) -> touch.TouchComponent:
        """Containing state related to object touch detection."""
        return self._touch

    @property
    def viewer(self) -> ViewerComponent:
        """Instance used to render Vector's camera feed."""
        if self._viewer is None:
            raise VectorNotReadyException("ViewerComponent is not yet initialized")
        return self._viewer

    @property
    def viewer_3d(self) -> Viewer3DComponent:
        """Instance used to render Vector's navigation map."""
        if self._viewer_3d is None:
            raise VectorNotReadyException("Viewer3DComponent is not yet initialized")
        return self._viewer_3d

    @property
    def vision(self) -> vision.VisionComponent:
        """Containing functionality related to vision based object detection."""
        return self._vision

    @property
    def world(self) -> world.World:
        """A reference to the World instance, or None if the World is not yet initialized."""
        if self._world is None:
            raise VectorNotReadyException("WorldComponent is not yet initialized")
        return self._world

    @property
    @util.block_while_none()
    def pose(self) -> util.Pose:
        """The current pose (position and orientation) of Vector."""
        return self._pose

    @property
    @util.block_while_none()
    def pose_angle_rad(self) -> float:
        """Vector's pose angle (heading in X-Y plane)."""
        return self._pose_angle_rad

    @property
    @util.block_while_none()
    def pose_pitch_rad(self) -> float:
        """Vector's pose pitch (angle up/down)."""
        return self._pose_pitch_rad

    @property
    @util.block_while_none()
    def left_wheel_speed_mmps(self) -> float:
        """Vector's left wheel speed in mm/sec"""
        return self._left_wheel_speed_mmps

    @property
    @util.block_while_none()
    def right_wheel_speed_mmps(self) -> float:
        """Vector's right wheel speed in mm/sec"""
        return self._right_wheel_speed_mmps

    @property
    @util.block_while_none()
    def head_angle_rad(self) -> float:
        """Vector's head angle (up/down)."""
        return self._head_angle_rad

    @property
    @util.block_while_none()
    def lift_height_mm(self) -> float:
        """Height of Vector's lift from the ground."""
        return self._lift_height_mm

    @property
    @util.block_while_none()
    def accel(self) -> util.Vector3:
        """The current accelerometer reading (x, y, z)"""
        return self._accel

    @property
    @util.block_while_none()
    def gyro(self) -> util.Vector3:
        """The current gyroscope reading (x, y, z)"""
        return self._gyro

    @property
    @util.block_while_none()
    def carrying_object_id(self) -> int:
        """The ID of the object currently being carried (-1 if none)"""
        return self._carrying_object_id

    @property
    @util.block_while_none()
    def head_tracking_object_id(self) -> int:
        """The ID of the object the head is tracking to (-1 if none)"""
        return self._head_tracking_object_id

    @property
    @util.block_while_none()
    def localized_to_object_id(self) -> int:
        """The ID of the object that the robot is localized to (-1 if none)"""
        return self._localized_to_object_id

    @property
    @util.block_while_none()
    def last_image_time_stamp(self) -> int:
        """The robot's timestamp for the last image seen."""
        return self._last_image_time_stamp

    @property
    def status(self) -> status.RobotStatus:
        """A property that exposes various status properties of the robot.

        This status provides a simple mechanism to, for example, detect if any
        of Vector's motors are moving, determine if Vector is being held, or if
        he is on the charger."""
        return self._status

    @property
    def enable_audio_feed(self) -> bool:
        """The audio feed enabled/disabled"""
        return self._enable_audio_feed

    @enable_audio_feed.setter
    def enable_audio_feed(self, enable) -> None:
        self._enable_audio_feed = enable

    # Unpack streamed data to robot's internal properties
    def _unpack_robot_state(self, _robot, _event_type, msg):
        self._pose = util.Pose(
            x=msg.pose.x,
            y=msg.pose.y,
            z=msg.pose.z,
            q0=msg.pose.q0,
            q1=msg.pose.q1,
            q2=msg.pose.q2,
            q3=msg.pose.q3,
            origin_id=msg.pose.origin_id,
        )
        self._pose_angle_rad = msg.pose_angle_rad
        self._pose_pitch_rad = msg.pose_pitch_rad
        self._left_wheel_speed_mmps = msg.left_wheel_speed_mmps
        self._right_wheel_speed_mmps = msg.right_wheel_speed_mmps
        self._head_angle_rad = msg.head_angle_rad
        self._lift_height_mm = msg.lift_height_mm
        self._accel = util.Vector3(msg.accel.x, msg.accel.y, msg.accel.z)
        self._gyro = util.Vector3(msg.gyro.x, msg.gyro.y, msg.gyro.z)
        self._carrying_object_id = msg.carrying_object_id
        self._head_tracking_object_id = msg.head_tracking_object_id
        self._localized_to_object_id = msg.localized_to_object_id
        self._last_image_time_stamp = msg.last_image_time_stamp
        self._status.set(msg.status)

    def connect(self, timeout: int = 10) -> None:
        """Start the connection to Vector."""
        self.conn.connect(timeout=timeout)
        self.events.start(self.conn)

        # Initialize components
        self._anim = animation.AnimationComponent(self)
        self._audio = audio.AudioComponent(self)
        self._behavior = behavior.BehaviorComponent(self)
        self._faces = faces.FaceComponent(self)
        self._motors = motors.MotorComponent(self)
        self._nav_map = nav_map.NavMapComponent(self)
        self._screen = screen.ScreenComponent(self)
        self._photos = photos.PhotographComponent(self)
        self._proximity = proximity.ProximityComponent(self)
        self._touch = touch.TouchComponent(self)
        self._viewer = viewer.ViewerComponent(self)
        self._viewer_3d = viewer.Viewer3DComponent(self)
        self._vision = vision.VisionComponent(self)
        self._world = world.World(self)
        self._camera = camera.CameraComponent(self)

        if self.cache_animation_lists:
            # Load animation triggers and animations so they are ready to play when requested
            anim_request = self._anim.load_animation_list()
            if isinstance(anim_request, concurrent.futures.Future):
                anim_request.result()
            anim_trigger_request = self._anim.load_animation_trigger_list()
            if isinstance(anim_trigger_request, concurrent.futures.Future):
                anim_trigger_request.result()

        # Start rendering camera feed
        if self._show_viewer:
            self.camera.init_camera_feed()
            self.viewer.show()

        if self._show_3d_viewer:
            self.viewer_3d.show()

        if self._enable_nav_map_feed:
            self.nav_map.init_nav_map_feed()

        # Enable face detection, to allow Vector to add faces to its world view
        if self.conn.requires_behavior_control:
            face_detection = self.vision.enable_face_detection(
                detect_faces=self.enable_face_detection,
                estimate_expression=self.estimate_facial_expression,
            )
            if isinstance(face_detection, concurrent.futures.Future):
                face_detection.result()
            object_detection = self.vision.enable_custom_object_detection(
                detect_custom_objects=self.enable_custom_object_detection
            )
            if isinstance(object_detection, concurrent.futures.Future):
                object_detection.result()

        # Subscribe to a callback that updates the robot's local properties
        self.events.subscribe(
            self._unpack_robot_state,
            events.Events.robot_state,
            _on_connection_thread=True,
        )

        # get the camera configuration from the robot
        response = self._camera.get_camera_config()
        if isinstance(response, concurrent.futures.Future):
            response = response.result()
        self._camera.set_config(response)

        # Subscribe to a callback for camera exposure settings
        self.events.subscribe(
            self._camera.update_state,
            events.Events.camera_settings_update,
            _on_connection_thread=True,
        )

        # access the pose to prove it has gotten back from the event stream once
        try:
            if not self.pose:
                pass
        except VectorPropertyValueNotReadyException as e:
            raise VectorUnreliableEventStreamException() from e

    def disconnect(self) -> None:
        """Close the connection with Vector."""
        if self.conn.requires_behavior_control:
            self.vision.close()

        # Stop rendering video
        self.viewer.close()

        # Stop rendering 3d video
        self.viewer_3d.close()

        # Shutdown camera feed
        self.camera.close_camera_feed()

        # Shutdown nav map feed
        self.nav_map.close_nav_map_feed()

        # Close the world and cleanup its objects
        self.world.close()

        self.proximity.close()
        self.touch.close()

        self.events.close()
        self.conn.close()

    @on_connection_thread(requires_control=False)
    async def get_battery_state(self) -> protocol.BatteryStateResponse:
        """Check the current state of the robot and cube batteries.

        The robot is considered fully-charged above 4.1 volts. At 3.6V, the robot is approaching low charge. # pylint: disable=line-too-long

        Robot battery level values are as follows:

        +-------+---------+---------------------------------------------------------------+
        | Value | Level   | Description                                                   |
        +=======+=========+===============================================================+
        | 1     | Low     | 3.6V or less. If on charger, 4V or less.                      |
        +-------+---------+---------------------------------------------------------------+
        | 2     | Nominal | Normal operating levels.                                      |
        +-------+---------+---------------------------------------------------------------+
        | 3     | Full    | This state can only be achieved when Vector is on the charger |
        +-------+---------+---------------------------------------------------------------+

        Cube battery level values are shown below:

        +-------+---------+---------------------------------------------------------------+
        | Value | Level   | Description                                                   |
        +=======+=========+===============================================================+
        | 1     | Low     | 1.1V or less.                                                 |
        +-------+---------+---------------------------------------------------------------+
        | 2     | Normal  | Normal operating levels.                                      |
        +-------+---------+---------------------------------------------------------------+

        .. testcode::

            import anki_vector

            with anki_vector.Robot() as robot:
                print("Connecting to a cube...")
                robot.world.connect_cube()

                battery_state = robot.get_battery_state()
                if battery_state:
                    print("Robot battery voltage: {0}".format(battery_state.battery_volts))
                    print("Robot battery Level: {0}".format(battery_state.battery_level))
                    print("Robot battery is charging: {0}".format(battery_state.is_charging))
                    print("Robot is on charger platform: {0}".format(battery_state.is_on_charger_platform))
                    print("Robot suggested charger time: {0}".format(battery_state.suggested_charger_sec))
                    print("Cube battery level: {0}".format(battery_state.cube_battery.level))
                    print("Cube battery voltage: {0}".format(battery_state.cube_battery.battery_volts))
                    print("Cube battery seconds since last reading: {0}".format(battery_state.cube_battery.time_since_last_reading_sec))
                    print("Cube battery factory id: {0}".format(battery_state.cube_battery.factory_id))
        """
        get_battery_state_request = protocol.BatteryStateRequest()
        return await self.conn.grpc_interface.BatteryState(get_battery_state_request)

    @on_connection_thread(requires_control=False)
    async def get_version_state(self) -> protocol.VersionStateResponse:
        """Get the versioning information for Vector"""
        get_version_state_request = protocol.VersionStateRequest()
        return await self.conn.grpc_interface.VersionState(get_version_state_request)
