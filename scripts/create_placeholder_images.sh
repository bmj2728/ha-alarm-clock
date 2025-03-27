#!/bin/bash

# Create placeholder images for documentation
echo "Creating placeholder images for documentation..."
convert -size 800x600 -background lightblue -fill navy -gravity center -font Arial label:"Dashboard View" /home/ubuntu/ha-alarm-enhancements/docs/images/dashboard.png
convert -size 800x600 -background lightgreen -fill darkgreen -gravity center -font Arial label:"Alarm Detail View" /home/ubuntu/ha-alarm-enhancements/docs/images/alarm_detail.png
convert -size 800x600 -background lightyellow -fill brown -gravity center -font Arial label:"Settings View" /home/ubuntu/ha-alarm-enhancements/docs/images/settings.png

echo "Placeholder images created successfully."
