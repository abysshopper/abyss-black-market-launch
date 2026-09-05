# Abyss guided token launches

When the user asks to design, prepare, test, or simulate an Abyss token launch, you MUST read and follow `.agents/skills/abyss-token-launch/SKILL.md` before changing files or recommending parameters.

The launch workflow is simulation-only. NEVER broadcast a transaction, request a private key, inspect a keystore, print a secret, or add `--broadcast`. Generate repository-native artifacts and tests in the user's target repository, not in this harness.
