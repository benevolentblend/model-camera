# model-camera
Code for a model camera project

This repo is setup to hold the source code and configuration for setting up a model camera. This model is shaped to be an "old timey" camera, but has the ability to record videos with a view preview behind a finder.

Hardware:
- Pi 4 (running raspberry pi bookworm)

- Camera: https://www.amazon.com/dp/B0C9PYCV9S?ref=ppx_yo2ov_dt_b_fed_asin_title
- Display: https://www.waveshare.com/2inch-lcd-module.htm


In order to setup the display, you need to copy the [config.txt](config/config.txt) to /boot/firmware/config.txt

You will also need to create a firmware file for the display using [mipi-dbi-cmd](https://github.com/notro/panel-mipi-dbi/blob/main/mipi-dbi-cmd) and the wavesku17344.txt file

```
python mipi-dbi-cmd wavesku17344.bin wavesku17344.txt
sudo mv wavesku17344.bin /lib/firmware
```

In order to fix the display orientation, you can create a profile at `~/.config/kanshi/config` using the provided [kanshi config](config/kanshi/config)


To get the application to start on boot, you can can leverage autostart:

Run `mkdir /home/pi/.config/autostart/` and use the [autostart config](config/autostart/model-camera.desktop)
