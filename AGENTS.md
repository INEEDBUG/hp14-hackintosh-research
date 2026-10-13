# Public research repository

- Preserve the distinction between user-reported results, offline tests, compiled products and verified physical behavior.
- The owner's current priority is native Wi-Fi stability, followed by macOS sleep/wake and AirDrop.
- Driver development is authorized offline. Live activation, EFI changes, network changes and power operations require the applicable test-batch authorization.
- Commit and push each verified substantive milestone with changed code, tests, sanitized evidence, remaining limitations and acceptance status. Routine monitoring is not a milestone.
- Use the existing repository and non-force pushes. Do not create duplicate repositories or change upstream repositories.
- Review every staged file and outgoing commit for credentials, device identities, personal paths, network identifiers, private endpoints and raw diagnostic data. Keep private operational checkpoints outside this repository.
- Preserve upstream attribution and license terms. Do not redistribute Apple system binaries, raw disassembly or third-party firmware as project artifacts.
- No automatic releases, deployment or recurring quota-consuming monitoring. Research artifacts do not imply a production-ready driver.
