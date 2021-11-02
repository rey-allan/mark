using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraManager : MonoBehaviour
{
    public Camera topDownCamera;
    public Camera markCamera;

    // Start is called before the first frame update
    void Start()
    {
        topDownCamera.enabled = true;
        markCamera.enabled = false;
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1))
        {
            topDownCamera.enabled = true;
            markCamera.enabled = false;
        }

        if (Input.GetKeyDown(KeyCode.Alpha2))
        {
            topDownCamera.enabled = false;
            markCamera.enabled = true;
        }
    }
}
