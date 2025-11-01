# Skyblock-Farm-Automation
A programmatic approach to farm in minecraft hypixel skyblock without real user intervention

Uses windows api to simulate user key presses, along with random movements for anticheat, mouse movement behaviour was removed due to sporadic movements

Monitors the games audio for when the farming has stopped, kills the loop and uses a discord API to send the user direct messages that they are potentially being checked by the administration team, requires game audio to be set to only "Blocks"

Also uses threads for movement and breaking
