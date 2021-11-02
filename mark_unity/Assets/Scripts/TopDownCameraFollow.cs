using UnityEngine;

namespace UnityStandardAssets.Utility
{
    public class TopDownCameraFollow : MonoBehaviour
    {
        // The target we are following
        [SerializeField]
        private Transform target;

        // Use this for initialization
        void Start() { }

        // Update is called once per frame
        void LateUpdate()
        {
            // Early out if we don't have a target
            if (!target)
                return;

            var currentHeight = transform.position.y;

            // Set the position of the camera to the position of the target
            transform.position = target.position;
            // Maintain the height of the camera
            transform.position = new Vector3(transform.position.x, currentHeight, transform.position.z);
        }
    }
}