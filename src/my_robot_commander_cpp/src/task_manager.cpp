#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>

#include <my_robot_interfaces/msg/pose_command.hpp>

using PoseCmd = my_robot_interfaces::msg::PoseCommand;

enum class TaskState
{
    IDLE,
    REACH,
    APPROACH,
    DONE
};

class TaskManager : public rclcpp::Node
{
public:
    TaskManager()
    : Node("task_manager"), state_(TaskState::IDLE)
    {
        target_sub_ = this->create_subscription<PoseCmd>(
            "/detected_target_pose", 10,
            std::bind(&TaskManager::targetCallback, this, std::placeholders::_1));

        execution_done_sub_ = this->create_subscription<std_msgs::msg::Bool>(
            "/commander/execution_done", 10,
            std::bind(&TaskManager::executionDoneCallback, this, std::placeholders::_1));

        command_pub_ = this->create_publisher<PoseCmd>(
            "/pose_command", 10);

        RCLCPP_INFO(this->get_logger(), "Task Manager (REACH → APPROACH → DONE) started");
    }

private:
    // ---------------- TARGET ----------------

    void targetCallback(const PoseCmd::SharedPtr msg)
    {
        if (state_ != TaskState::IDLE)
            return;

        target_pose_ = *msg;

        PoseCmd cmd = target_pose_;
        cmd.cartesian_path = false;
        command_pub_->publish(cmd);

        state_ = TaskState::REACH;
        RCLCPP_INFO(this->get_logger(), "State → REACH");
    }

    // ---------------- EXECUTION FEEDBACK ----------------

    void executionDoneCallback(const std_msgs::msg::Bool::SharedPtr msg)
    {
        if (!msg->data)
            return;

        if (state_ == TaskState::REACH)
        {
            RCLCPP_INFO(this->get_logger(), "Reach execution DONE");

            sendApproachCommand();

            state_ = TaskState::APPROACH;
            RCLCPP_INFO(this->get_logger(), "State → APPROACH");
        }
        else if (state_ == TaskState::APPROACH)
        {
            RCLCPP_INFO(this->get_logger(), "Approach execution DONE");

            state_ = TaskState::DONE;
            RCLCPP_INFO(this->get_logger(), "State → DONE");
        }
    }

    // ---------------- COMMANDS ----------------

    void sendApproachCommand()
    {
        PoseCmd cmd = target_pose_;
        cmd.x += 0.05;            // 5 cm approach
        cmd.cartesian_path = true;
        command_pub_->publish(cmd);
    }

    // ---------------- MEMBERS ----------------

    TaskState state_;
    PoseCmd target_pose_;

    rclcpp::Subscription<PoseCmd>::SharedPtr target_sub_;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr execution_done_sub_;
    rclcpp::Publisher<PoseCmd>::SharedPtr command_pub_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TaskManager>());
    rclcpp::shutdown();
    return 0;
}

