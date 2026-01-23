#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <thread>

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);

  auto node = rclcpp::Node::make_shared("print_current_pose_node");
  node->set_parameter(rclcpp::Parameter("use_sim_time", false));

  // --- Executor (REQUIRED) ---
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);

  std::thread spinner([&executor]() {
    executor.spin();
  });

  static const std::string PLANNING_GROUP = "arm";
  moveit::planning_interface::MoveGroupInterface move_group(node, PLANNING_GROUP);

  // ---- Wait until joint states are received ----
  moveit::core::RobotStatePtr current_state;
  rclcpp::Time start = node->now();

  while (rclcpp::ok() && !current_state)
  {
    current_state = move_group.getCurrentState(1.0);

    if ((node->now() - start).seconds() > 5.0)
    {
      RCLCPP_ERROR(node->get_logger(), "Timeout waiting for robot state");
      rclcpp::shutdown();
      spinner.join();
      return 1;
    }
  }

  // ---- Get current EE pose ----
  auto pose = move_group.getCurrentPose();

  RCLCPP_INFO(node->get_logger(),
    "Current EE pose:\n"
    "Position: [%.3f, %.3f, %.3f]\n"
    "Orientation: [%.3f, %.3f, %.3f, %.3f]",
    pose.pose.position.x,
    pose.pose.position.y,
    pose.pose.position.z,
    pose.pose.orientation.x,
    pose.pose.orientation.y,
    pose.pose.orientation.z,
    pose.pose.orientation.w
  );

  rclcpp::shutdown();
  spinner.join();
  return 0;
}

