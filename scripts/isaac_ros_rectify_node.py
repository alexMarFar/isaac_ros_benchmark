# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2021-2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
"""
Performance test for the Isaac ROS rectify node.

The graph consists of the following:
- Preprocessors:
    None
- Graph under Test:
    1. RectifyNode: rectifies images

Required:
- Packages:
    - isaac_ros_image_proc
- Datasets:
    - assets/datasets/r2b_dataset/r2b_storage
"""

from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

from ros2_benchmark import ImageResolution
from ros2_benchmark import ROS2BenchmarkConfig, ROS2BenchmarkTest

IMAGE_RESOLUTION = ImageResolution.FULL_HD
ROSBAG_PATH = 'datasets/r2b_dataset/r2b_storage'

def launch_setup(container_prefix, container_sigterm_timeout):
    """Generate launch description for isaac rectify node."""
    rectify_node = ComposableNode(
        name='RectifyNode',
        namespace=TestIsaacROSRectifyNode.generate_namespace(),
        package='isaac_ros_image_proc',
        plugin='nvidia::isaac_ros::image_proc::RectifyNode',
        parameters=[{
            'output_width': IMAGE_RESOLUTION['width'],
            'output_height': IMAGE_RESOLUTION['height'],
        }],
        remappings=[('image_raw', 'image')]
    )

    data_loader_node = ComposableNode(
        name='DataLoaderNode',
        namespace=TestIsaacROSRectifyNode.generate_namespace(),
        package='ros2_benchmark',
        plugin='ros2_benchmark::DataLoaderNode',
        remappings=[('hawk_0_left_rgb_image', 'buffer/image'),
                    ('hawk_0_left_rgb_camera_info', 'buffer/camera_info')]
    )

    playback_node = ComposableNode(
        name='PlaybackNode',
        namespace=TestIsaacROSRectifyNode.generate_namespace(),
        package='isaac_ros_benchmark',
        plugin='isaac_ros_benchmark::NitrosPlaybackNode',
        parameters=[{
            'data_formats': ['nitros_image_bgr8', 'nitros_camera_info'],
        }],
        remappings=[('buffer/input0', 'buffer/image'),
                    ('input0', 'image'),
                    ('buffer/input1', 'buffer/camera_info'),
                    ('input1', 'camera_info')],
    )

    monitor_node = ComposableNode(
        name='MonitorNode',
        namespace=TestIsaacROSRectifyNode.generate_namespace(),
        package='isaac_ros_benchmark',
        plugin='isaac_ros_benchmark::NitrosMonitorNode',
        parameters=[{
            'monitor_data_format': 'nitros_image_bgr8',
            'use_nitros_type_monitor_sub': True,
        }],
        remappings=[
            ('output', 'image_rect')],
    )

    composable_node_container = ComposableNodeContainer(
        name='rectify_container',
        namespace=TestIsaacROSRectifyNode.generate_namespace(),
        package='rclcpp_components',
        executable='component_container_mt',
        prefix=container_prefix,
        sigterm_timeout=container_sigterm_timeout,
        composable_node_descriptions=[
            data_loader_node,
            rectify_node,
            playback_node,
            monitor_node,
        ],
        output='screen',
    )

    return [composable_node_container]

def generate_test_description():
    return TestIsaacROSRectifyNode.generate_test_description_with_nsys(launch_setup)


class TestIsaacROSRectifyNode(ROS2BenchmarkTest):
    """Performance test for the Isaac ROS rectify node."""

    # Custom configurations
    config = ROS2BenchmarkConfig(
        benchmark_name='Isaac ROS RectifyNode Benchmark',
        input_data_path=ROSBAG_PATH,
        # Upper and lower bounds of peak throughput search window
        publisher_upper_frequency=2500.0,
        publisher_lower_frequency=10.0,
        # The number of frames to be buffered
        playback_message_buffer_size=10,
        custom_report_info={'data_resolution': IMAGE_RESOLUTION}
    )

    def test_benchmark(self):
        self.run_benchmark()
