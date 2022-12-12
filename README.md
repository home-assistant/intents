# Intents for Home Assistant

This repository contains training data for Home Assistant's local voice control.


## Intents

* `HassTurnOn`
    * Turn on a device, entity, or all entities of a specific domain in an area
* `HassTurnOff`
    * Turn off a device, entity, or all entities of a specific domain in an area
* `HassToggle`
    * Toggle a device, entity, or all entities of a specific domain in an area
* `HassLightSet`
    * Set a light's brightness or color
* `HassOpenCover`
    * Open a cover by name, device class, or area
* `HassCloseCover`
    * Close a cover by name, device class, or area
* `HassClimateSetTemperature`
    * Set the desired temperature of a climate device
* `HassClimateGetTemperature`
    * Get the current temperature of a climate device


## Lists

* `{name}`
    * List of entity friendly names
* `{area}`
    * List of area names


## Domains

* `light`
    * `HassTurnOn`
    * `HassTurnOff`
    * `HassToggle`
    * `HassLightSet`
* `cover`
    * `HassOpenCover`
    * `HassCloseCover`
* `fan`
    * `HassTurnOn`
    * `HassTurnOff`
    * `HassToggle`
* `switch`
    * `HassTurnOn`
    * `HassTurnOff`
    * `HassToggle`
* `climate`
    * `HassClimateSetTemperature`
    * `HassClimateGetTemperature`
