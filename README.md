# os-reticulum — OPNsense Reticulum Plugin

 **This is a work in progress and does not work yet**

An OPNsense plugin intends to turns your firewall into a fully managed [Reticulum](https://reticulum.network/) transport node and [LXMF](https://github.com/markqvist/LXMF) propagation node, with complete GUI configuration, automatic firewall rules, and real-time diagnostics.

## Overview

[Reticulum](https://reticulum.network/) is a cryptography-based networking stack for building resilient, self-organizing local and wide-area networks. It uses X25519/Ed25519 elliptic curve cryptography for all communication and operates over diverse physical mediums — from Ethernet and WiFi to LoRa radio, packet radio, serial modems, and the I2P anonymous network.

This plugin is planned to integrate Reticulum into OPNsense's standard MVC framework, giving full control through the web GUI without touching a config file.
