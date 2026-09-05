# Abyss Black Market Launch

Claude Code and Codex harness for designing and simulating oracle-enabled Abyss token launches.

The wizard walks users through:

- Standard Oracle versus Quote Oracle pool accounting
- Standard versus supported custom launch templates
- Token name, ticker, supply, decimals, quote asset, fee tier, and fee distribution
- Current quote-token USD price confirmation
- Launch pricing near a recommended $5,000 fully diluted valuation
- Optional initial buy with protected or explicitly unbounded slippage
- Repository-native launch artifacts and rigorous contract, SDK, lifecycle, and fork tests

## Safety boundary

This harness generates, tests, and simulates launches. It never broadcasts transactions, requests private keys, opens keystores, or asks for wallet approval.

## Use with Codex

Clone the repository and start Codex from its root. `AGENTS.md` directs Codex to the canonical skill at:

```text
.agents/skills/abyss-token-launch/SKILL.md
```

Ask it to guide a token launch against a local Abyss-compatible repository. Provide that repository's path when requested.

Example:

```text
Guide me through designing and simulating an Abyss token launch using the repository at /path/to/repository.
```

## Use with Claude Code

Start Claude Code from the repository root. `CLAUDE.md` loads the shared instructions, and the Claude skill is available at:

```text
.claude/skills/abyss-token-launch/SKILL.md
```

Use the same launch request shown above.

## Workflow

The harness instructs the agent to:

1. Inspect the target repository's contracts, SDK, deployment records, registered templates, fee tiers, oracle configuration, and toolchain.
2. Explain the supported design choices and collect every required launch parameter.
3. Retrieve and confirm the quote token's current USD price, or request a user-supplied price when no reliable source exists.
4. Derive the launch tick, liquidity, effective FDV, initial-buy estimate, and execution limits using repository-native integer math.
5. Present one complete confirmation record.
6. Generate parameter preparation, launch simulation, and test artifacts in the target repository.
7. Run focused tests, a full local lifecycle, and a canonical fork simulation where supported.
8. Stop without broadcasting.

The target repository remains authoritative. The harness does not hard-code a particular deployment, ABI, address set, or toolchain.

## Slippage

Slippage protection is the default for a nonzero initial buy. A user may explicitly ignore it after acknowledging that execution can receive materially less than the estimate. The generated request uses unbounded values only when the target contracts support them and the user confirms the choice.
