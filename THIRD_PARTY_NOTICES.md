# Attribution and third-party notices

## itlwm / AirportItlwm

The patch targets [laobamac/itlwm](https://github.com/laobamac/itlwm) commit `f26a3afc8a0eecd6995ebdba48498f36bac107ad`, a fork of [OpenIntelWireless/itlwm](https://github.com/OpenIntelWireless/itlwm). The pinned repository provides a GNU GPL version 2 license, copied as this repository's `LICENSE`.

Original file notices remain intact after applying the patch:

- `AirportItlwmSkywalkInterface.cpp` and `.hpp`: Created by qcwap, copyright © 2023 钟先耀.
- `AirportItlwm/WCL/WCL.cpp`: Created by laobamac, copyright © 2026 laobamac.

These are required public upstream credits, not the device owner's identity. Original header notices are not removed or replaced. This repository claims authorship only for its additions and research records.

The scan-cursor investigation was informed by [OpenIntelWireless/itlwm PR #1069 by gargamel778](https://github.com/OpenIntelWireless/itlwm/pull/1069). The local implementation adds gate serialization, ordering-key traversal, tests and diagnostic instrumentation against the pinned Sequoia source. The PR is a proposed upstream change, not asserted here as a shipped fix.

## OpenBSD components

The host tests obtain `tree.h` and `_null.h` from the user's separate upstream source checkout at runtime. Their original BSD / public-domain notices must remain in that checkout and in any redistributed copies. This repository does not replace those licenses with its own.

## Build dependencies and firmware

[MacKernelSDK](https://github.com/acidanthera/MacKernelSDK), Apple Command Line Tools and macOS system components are external dependencies, not bundled here. Their respective terms continue to apply.

The experimental build uses upstream Intel firmware during source generation. Firmware is not included in this publication. Redistribution of a future compiled product requires a separate corresponding-source, firmware-license and dependency review, including upstream `iwlwifi-firmware-license`.

## Protocol research

OWL, OpenDrop, omdrop-owl and other linked projects are references. Their code is not bundled or relicensed. Any future adaptation must preserve its applicable license and attribution.

## Repository additions

Copyright (C) 2026 INEEDBUG. Original additions, documentation and experimental changes in this repository are provided under GPL-2.0-only; see `LICENSE`.
