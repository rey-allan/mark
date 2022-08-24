# mark_app

An app for controlling and managing M.A.R.K.

## Dependencies

This app requires the [`inputs`](https://github.com/zeth/inputs) library to be installed manually. The reason is that the latest release doesn't include some important fixes present in the repository. To install manually, follow these steps:

```
git clone https://github.com/zeth/inputs.git
cd inputs
python setup.py install
```

To generate QR codes with the WiFi information of the server, we use `qrencode`. Install on Mac using `brew install qrencode` or on Linux using `apt-get install qrencode`.

## WiFi QR Code

To provide the WiFi information of the server to M.A.R.K., we encode it as a QR code than can be read by the robot's camera. Create the QR code using the following command:

```
qrencode -o wifi.png -s 10 '{"ssid":"[WIFI_NAME]","password":"[WIFI_PASSWORD]","host":"[SERVER_IP]","port":1060}'
```
