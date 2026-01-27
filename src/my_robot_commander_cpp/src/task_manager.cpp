#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>
#include <example_interfaces/msg/float64_multi_array.hpp>

#include <my_robot_interfaces/msg/pose_command.hpp>

using PoseCmd = my_robot_interfaces::msg::PoseCommand;
using JointCmd = example_interfaces::msg::Float64MultiArray;

enum class TaskState
{
    IDLE,
    REACH,
    APPROACH,
    REACH_POUR,
    POUR,
    PLACE,
    RETURN,
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

        joint_command_pub_ = this->create_publisher<JointCmd>(
            "/joint_command", 10);

        RCLCPP_INFO(
            this->get_logger(),
            "Task Manager (REACH → APPROACH → REACH_POUR → POUR → PLACE → RETURN → DONE) started");
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
            sendReachPourCommand();
            state_ = TaskState::REACH_POUR;
            RCLCPP_INFO(this->get_logger(), "State → REACH_POUR");
        }
        else if (state_ == TaskState::REACH_POUR)
        {
            RCLCPP_INFO(this->get_logger(), "Reach pour execution DONE");
            sendPourCommand();
            state_ = TaskState::POUR;
            RCLCPP_INFO(this->get_logger(), "State → POUR");
        }
        else if (state_ == TaskState::POUR)
        {
            RCLCPP_INFO(this->get_logger(), "Pour execution DONE");
            sendPlaceCommand();
            state_ = TaskState::PLACE;
            RCLCPP_INFO(this->get_logger(), "State → PLACE");
        }
        else if (state_ == TaskState::PLACE)
        {
            RCLCPP_INFO(this->get_logger(), "Place execution DONE");
            sendReturnCommand();
            state_ = TaskState::RETURN;
            RCLCPP_INFO(this->get_logger(), "State → RETURN");
        }
        else if (state_ == TaskState::RETURN)
        {
            RCLCPP_INFO(this->get_logger(), "Return execution DONE");
            state_ = TaskState::DONE;
            RCLCPP_INFO(this->get_logger(), "State → DONE");
        }

    }

    // ---------------- COMMANDS ----------------

    void sendApproachCommand()
    {
        approach_pose_ = target_pose_;
        approach_pose_.x += 0.05;              // 5 cm approach
        approach_pose_.cartesian_path = true;
        command_pub_->publish(approach_pose_);
    }

    void sendReachPourCommand()
    {
        JointCmd joints;
        joints.data = {
            -0.8203,
             0.7330,
             0.3840,
            -0.3316,
            -1.0472,
             0.5236,
            -1.1345
        };

        joint_command_pub_->publish(joints);
        RCLCPP_INFO(this->get_logger(), "Reach-pour joint pose sent");
    }

    void sendPourCommand()
    {
        JointCmd joints;
        joints.data = {
            -0.8203,
             0.7330,
             0.3840,
            -0.3316,
            -1.0472,
             0.5061,
            -0.0873
        };

        joint_command_pub_->publish(joints);
        RCLCPP_INFO(this->get_logger(), "Pour joint pose sent");
    }

    void sendPlaceCommand()
    {
        PoseCmd cmd = approach_pose_;
        cmd.cartesian_path = false;
        command_pub_->publish(cmd);

        RCLCPP_INFO(this->get_logger(), "Place pose sent (same as approach)");
    }
    
    void sendReturnCommand()
    {
        JointCmd joints;
        joints.data = {
            0.0,  // shoulder_pan
            0.0,  // shoulder_yaw
            0.0,  // shoulder_roll
            1.57,  // elbow
            0.0,  // wrist_yaw
            0.0,  // wrist_pitch
            0.0   // wrist_roll
        };

        joint_command_pub_->publish(joints);
        RCLCPP_INFO(this->get_logger(), "Return (zero joints) command sent");
    }
        

        // ---------------- MEMBERS ----------------

        TaskState state_;
        PoseCmd target_pose_;
        PoseCmd approach_pose_;

        rclcpp::Subscription<PoseCmd>::SharedPtr target_sub_;
        rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr execution_done_sub_;
        rclcpp::Publisher<PoseCmd>::SharedPtr command_pub_;
        rclcpp::Publisher<JointCmd>::SharedPtr joint_command_pub_;
    };

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TaskManager>());
    rclcpp::shutdown();
    return 0;
}

