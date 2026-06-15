#!/usr/bin/env python3
"""
Workspace calibration script for Isaac Lab Bridge.

Calibrates workspace bounds, camera poses, and safety limits
for a specific robot setup.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import time

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calibrate_workspace_bounds(robot_ip: str | None = None, num_samples: int = 100):
    """
    Calibrate workspace bounds by sampling reachable positions.
    
    For sim: uses forward kinematics
    For real: commands robot to sample positions
    """
    logger.info("Calibrating workspace bounds...")
    
    # Simulated calibration (replace with real robot commands)
    # Franka reachable workspace (approximate)
    bounds = {
        "min": [-0.6, -0.6, 0.02],
        "max": [0.6, 0.6, 1.0],
        "reachable_volume": 0.432,  # m^3
        "notes": "Franka Panda approximate reachable workspace",
    }
    
    logger.info(f"Workspace bounds: {bounds}")
    return bounds


def calibrate_camera(camera_name: str, num_poses: int = 20):
    """
    Calibrate camera extrinsics by observing fiducial markers.
    """
    logger.info(f"Calibrating camera: {camera_name}")
    
    # Placeholder - would use OpenCV + ArUco/Charuco board
    calibration = {
        "camera_name": camera_name,
        "intrinsics": {
            "width": 640,
            "height": 480,
            "fx": 525.0,
            "fy": 525.0,
            "cx": 320.0,
            "cy": 240.0,
        },
        "extrinsics": {
            "position": [0.5, 0.0, 1.0],
            "orientation": [0.707, 0, 0.707, 0],  # quaternion x,y,z,w
        },
        "distortion": [0.0, 0.0, 0.0, 0.0, 0.0],
    }
    
    return calibration


def calibrate_force_sensor(sensor_name: str, known_masses: list[float] = None):
    """
    Calibrate force/torque sensor using known masses.
    """
    if known_masses is None:
        known_masses = [0.5, 1.0, 2.0, 5.0]  # kg
    
    logger.info(f"Calibrating force sensor: {sensor_name}")
    
    # Placeholder - would command robot to hold masses
    calibration = {
        "sensor_name": sensor_name,
        "force_scale": [1.0, 1.0, 1.0],
        "force_offset": [0.0, 0.0, -5.0],  # Gravity compensation
        "torque_scale": [1.0, 1.0, 1.0],
        "torque_offset": [0.0, 0.0, 0.0],
    }
    
    return calibration


def calibrate_joint_limits(robot_type: str = "franka"):
    """
    Get joint limits for robot type.
    """
    limits = {
        "franka": {
            "joint_names": [
                "panda_joint1", "panda_joint2", "panda_joint3",
                "panda_joint4", "panda_joint5", "panda_joint6", "panda_joint7",
                "panda_finger_joint1", "panda_finger_joint2",
            ],
            "lower": [-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973, 0.0, 0.0],
            "upper": [2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973, 0.04, 0.04],
            "velocity": [2.1750, 2.1750, 2.1750, 2.1750, 2.6100, 2.6100, 2.6100, 0.1, 0.1],
            "effort": [87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0, 10.0, 10.0],
        },
        "ur5e": {
            "joint_names": [
                "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
                "wrist_1_joint", "wrist_2_joint", "wrist_3_joint",
            ],
            "lower": [-6.283, -6.283, -3.141, -6.283, -6.283, -6.283],
            "upper": [6.283, 6.283, 3.141, 6.283, 6.283, 6.283],
            "velocity": [3.14] * 6,
            "effort": [150.0] * 6,
        },
    }
    
    return limits.get(robot_type, limits["franka"])


def generate_registry_updates(
    workspace_bounds: dict,
    camera_calibrations: list[dict],
    force_calibrations: list[dict],
    joint_limits: dict,
    output_path: str,
):
    """Generate registry.yaml updates from calibration data."""
    
    updates = {
        "global": {
            "workspace_bounds": workspace_bounds,
            "joint_limits": joint_limits,
        },
        "cameras": {c["camera_name"]: c for c in camera_calibrations},
        "force_sensors": {f["sensor_name"]: f for f in force_calibrations},
    }
    
    with open(output_path, 'w') as f:
        json.dump(updates, f, indent=2)
    
    logger.info(f"Calibration data saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate Isaac Lab Bridge")
    parser.add_argument("--robot", choices=["franka", "ur5e", "go1", "g1"], default="franka")
    parser.add_argument("--robot-ip", help="Robot IP for real calibration")
    parser.add_argument("--output", default="calibration_output.json")
    parser.add_argument("--workspace", action="store_true", help="Calibrate workspace")
    parser.add_argument("--cameras", action="store_true", help="Calibrate cameras")
    parser.add_argument("--force", action="store_true", help="Calibrate force sensors")
    parser.add_argument("--all", action="store_true", help="Run all calibrations")
    
    args = parser.parse_args()
    
    run_all = args.all or not (args.workspace or args.cameras or args.force)
    
    results = {}
    
    if run_all or args.workspace:
        results["workspace"] = calibrate_workspace_bounds(args.robot_ip)
    
    if run_all or args.cameras:
        results["cameras"] = [
            calibrate_camera("wrist"),
            calibrate_camera("overhead"),
        ]
    
    if run_all or args.force:
        results["force"] = [
            calibrate_force_sensor("wrist_ft"),
        ]
    
    results["joint_limits"] = calibrate_joint_limits(args.robot)
    
    generate_registry_updates(
        results.get("workspace", {}),
        results.get("cameras", []),
        results.get("force", []),
        results.get("joint_limits", {}),
        args.output,
    )
    
    logger.info("Calibration complete!")


if __name__ == "__main__":
    main()