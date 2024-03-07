# hass-avpro-acmxnn
A [Home Assistant](https://www.home-assistant.io/) custom component for interacting with a [AVPro Edge](https://avproedge.com/) HDMI matrix switch in the AC-MX-nn family such as:

- [AX-MX-42](https://avproedge.com/products/ac-mx-42)
- [AX-MX-82RM](https://avproedge.com/products/ac-mx-82rm)
- [AX-MX-44](https://avproedge.com/products/ac-mx-44) (the one I own and test with)
- [AX-MX-88](https://avproedge.com/products/ac-mx-88)
- [AX-MX-1616](https://avproedge.com/products/ac-mx-1616)

## Features
- Web UI configuration
- One `media_player` entity for each configured device.
- Asynchronous updates from Matrix to Home Assistant, no polling.
- Support for the Home Assistant `media_player.select_source` service for switching inputs.
- Support for the Home Assistant `media_player.turn_on`, `media_player.turn_off`, and `media_player.toggle` services to enable or disable a given output.

![Screenshot of the custom component's attributes.](./documentation/images/device-in-ha.png)

## Before Installation
This custom component will create a Home Assistant `media_player` entity for each of your matrix outputs. Each of those `media_player` entities will have the ability to select any of your matrix's input sources for it's output. Here are some tips to save you some time and effort.
 - Configure and test your Matrix according to the manufacturers directions first.
 - This component doesn't currently support a matrix with a password protected web configuration. Open an [issue](https://github.com/toscano/hass-avpro-acmxnn/issues) and I'll look into it. Or better yet submit a [pull request](https://github.com/toscano/hass-avpro-acmxnn/pulls) with the changes.
 - You may not be using all of your matrix's inputs or outputs. This component will skip and input or output with an empty name (i.e. `""`) or a name that starts with a dot (i.e. `.OUT 4` or `.IN 1`).

## Installation via HACS
 - Install [HACS](https://hacs.xyz/) if you haven't already done so.
 - Add this repo to HACS as a custom repo.
 - Note that HACS will prompt you to restart Home Assistant. Do that.
 - Search for the `AC-MX Matrix switch` integration in the `Settings \ Integrations \ + Add Integration` Home Assistant UI. Provide the IP address of your matrix switch when prompted.

## Manual Installation
If you don't or can't use HACS then:
 - Copy the `custom_components/avpro-acmxnn` directory to your `custom_components` folder.
 - Restart Home Assistant.
 - Open your Home Assistant instance to your [integrations page.](https://my.home-assistant.io/redirect/integrations/)
 - Search for the `AC-MX Matrix switch` integration in the `Settings \ Integrations \ + Add Integration` Home Assistant UI. Provide the IP address of your matrix switch when prompted.

## Give us some Love
If you use this custom component please give it a Star :star:

## How I use this...

My matrix is set up with four inputs:
 - AppleTV
 - NVidia Shield
 - Panasonic Blu-ray player
 - HTPC (That I use for short shows prior showing guests movies. I call these PreRolls).

And three outputs:
 - A MadVR Envy Extreme video processor that feeds my Sony Laser Projector
 - An Anthem AVM 90 for my 9.4.6 audio in the main theater
 - A 65" Sony OLED for display in the lobby

 The MadVR Envy is a very powerful video processor and has separate settings for each of the separate input devices. One of the ways I automate this is via this script that ensures that the Envy is applying the correct input device profile whenever there's a change.

 I'm sure that you can find a good use yourself.

```yaml
alias: "Playhouse: Matrix Madvr source changes"
description: ""
trigger:
  - platform: state
    entity_id:
      - media_player.madvr_hdmi
    attribute: source
    to: AppleTV
    id: madvr_to_appleTv
  - platform: state
    entity_id:
      - media_player.madvr_hdmi
    attribute: source
    to: Shield
    id: madvr_to_Shield
  - platform: state
    entity_id:
      - media_player.madvr_hdmi
    attribute: source
    to: Blu-ray
    id: madvr_to_BluRay
  - platform: state
    entity_id:
      - media_player.madvr_hdmi
    attribute: source
    to: PreRoll
    id: madvr_to_PreRoll
condition: []
action:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - madvr_to_appleTv
        sequence:
          - service: remote.send_command
            target:
              entity_id: remote.envy
            data:
              command: ActivateProfile source 1
      - conditions:
          - condition: trigger
            id:
              - madvr_to_Shield
        sequence:
          - service: remote.send_command
            target:
              entity_id: remote.envy
            data:
              command: ActivateProfile source 2
      - conditions:
          - condition: trigger
            id:
              - madvr_to_BluRay
        sequence:
          - service: remote.send_command
            target:
              entity_id: remote.envy
            data:
              command: ActivateProfile source 3
      - conditions:
          - condition: trigger
            id:
              - madvr_to_PreRoll
        sequence:
          - service: remote.send_command
            target:
              entity_id: remote.envy
            data:
              command: ActivateProfile source 4
mode: queued
max: 10

```