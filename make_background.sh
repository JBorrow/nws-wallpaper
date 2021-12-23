#!zsh

cd /Users/jborrow/Documents/Projects/weather

python3 get_image.py
python3 plot_forecast.py
python3 composit.py

# MacOS only, and only on success
if test -f "composite.jpg"; then
    cp /Users/jborrow/Pictures/forecast_image.jpg /Users/jborrow/Pictures/forecast_image_old.jpg
    cp composite.jpg /Users/jborrow/Pictures/forecast_image.jpg

    osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Users/jborrow/Pictures/forecast_image_old.jpg"'
    osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Users/jborrow/Pictures/forecast_image.jpg"'
    rm /Users/jborrow/Pictures/forecast_image_old.jpg
fi

rm composite.jpg
rm latest_weather_image.jpg
rm current_forecast.png
