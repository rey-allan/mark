using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MarkController : MonoBehaviour
{
    public ArticulationBody leftWheel;
    public ArticulationBody rightWheel;
    public ArticulationBody cameraTilt;
    public ArticulationBody cameraPan;
    public ArticulationBody gripperLeft;
    public ArticulationBody gripperRight;
    public float drivingSpeed = 1.0F;
    public float cameraSpeed = 1.0F;
    public float gripperSpeed = 1.0F;

    // Start is called before the first frame update
    void Start()
    {
    }

    // Update is called once per frame
    void Update()
    {
        // Forward
        if (Input.GetKey(KeyCode.W))
        {
            var drive = leftWheel.xDrive;
            drive.target += drivingSpeed;
            leftWheel.xDrive = drive;

            drive = rightWheel.xDrive;
            drive.target += drivingSpeed;
            rightWheel.xDrive = drive;
        }

        // Backward
        if (Input.GetKey(KeyCode.S))
        {
            var drive = leftWheel.xDrive;
            drive.target -= drivingSpeed;
            leftWheel.xDrive = drive;

            drive = rightWheel.xDrive;
            drive.target -= drivingSpeed;
            rightWheel.xDrive = drive;
        }

        // Turn left
        if (Input.GetKey(KeyCode.A))
        {
            var drive = leftWheel.xDrive;
            drive.target += drivingSpeed;
            leftWheel.xDrive = drive;
        }

        // Turn right
        if (Input.GetKey(KeyCode.D))
        {
            var drive = rightWheel.xDrive;
            drive.target += drivingSpeed;
            rightWheel.xDrive = drive;
        }

        // Tilt up
        if (Input.GetKey(KeyCode.UpArrow))
        {
            var drive = cameraTilt.xDrive;
            drive.target -= cameraSpeed;
            cameraTilt.xDrive = drive;
        }

        // Tilt down
        if (Input.GetKey(KeyCode.DownArrow))
        {
            var drive = cameraTilt.xDrive;
            drive.target += cameraSpeed;
            cameraTilt.xDrive = drive;
        }

        // Pan left
        if (Input.GetKey(KeyCode.LeftArrow))
        {
            var drive = cameraPan.xDrive;
            drive.target += cameraSpeed;
            cameraPan.xDrive = drive;
        }

        // Pan right
        if (Input.GetKey(KeyCode.RightArrow))
        {
            var drive = cameraPan.xDrive;
            drive.target -= cameraSpeed;
            cameraPan.xDrive = drive;
        }

        // Gripper open
        if (Input.GetKey(KeyCode.O))
        {
            var drive = gripperLeft.xDrive;
            drive.target -= gripperSpeed;
            gripperLeft.xDrive = drive;

            drive = gripperRight.xDrive;
            drive.target -= gripperSpeed;
            gripperRight.xDrive = drive;
        }

        // Gripper close
        if (Input.GetKey(KeyCode.P))
        {
            var drive = gripperLeft.xDrive;
            drive.target += gripperSpeed;
            gripperLeft.xDrive = drive;

            drive = gripperRight.xDrive;
            drive.target += gripperSpeed;
            gripperRight.xDrive = drive;
        }
    }
}
