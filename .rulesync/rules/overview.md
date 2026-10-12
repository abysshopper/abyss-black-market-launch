---
root: true
targets: ["*"]
description: "One SDK-driven, conversational token launch workflow for Node and Python"
---
# Abyss guided token launches

For token design, pricing, preparation, simulation, execution, or recovery, read and follow the `abyss-token-launch` skill before choosing parameters or changing launch files. The canonical source is `.rulesync/skills/abyss-token-launch/SKILL.md`; rulesync generates the agent-specific skill paths.

Do not ask users to choose a programming language for a token-design or launch request. Honor an explicit Node/TypeScript or Python preference; otherwise reuse the workspace's installed SDK (`@black-market/sdk` or `black_market_sdk`). For a fresh workspace with no preference, use Node/TypeScript when its supported runtime is available, otherwise Python when available; state the selection briefly, without making it an interview question. Ask only about a material unresolved workspace/runtime constraint. Use the installed SDK's current public APIs, deployed-profile discovery, integer pricing helpers, admission and receipt recovery. Do not duplicate ABIs, deployment addresses, or pricing math here.

Planning is unsigned by default. Real execution and resumption need explicit user authorization after economic review. Secrets belong only in the user's own local terminal: never ask for a password or private key in chat, read secret files with agent tools, capture secret prompts in an agent PTY, or commit secret/recovery artifacts. Prefer a password-protected V3 keystore and `scripts/run-launch.py`.

Generate launch files in the user's SDK/workspace, not in this skill repository. Preserve economic guards, stateful proof, slippage protection, metadata integrity and canonical receipt/reorg checks. A failed or unavailable proof is not permission to send.

Maintain guidance in `.rulesync/`, not generated `AGENTS.md`, `CLAUDE.md`, `.agents/`, or `.claude/`. Run `pnpm dlx rulesync@27.0.0 generate` after edits; generated agent files remain local and ignored. No funded broadcasts are part of repository maintenance verification.
