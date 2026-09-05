---
name: abyss-token-launch
description: Guide a user through an oracle-enabled Abyss token design, derive an approximately $5,000 FDV launch, generate repository-native artifacts and rigorous tests, and simulate without broadcasting.
---

# Abyss token launch wizard

## Non-negotiable boundary

This workflow ends with generated artifacts, tests, and a successful local or fork simulation. NEVER broadcast, send a transaction, request or open a private key or keystore, add `--broadcast`, call a production write endpoint, or ask for wallet approval. A source repository's deploy script is evidence, not permission to execute it.

Work in the user's target repository. This harness is repository-agnostic: inspect installed code and deployed configuration before choosing interfaces or commands. Do not copy stale ABI, addresses, constants, or pricing math from this skill.

## Ground the repository first

1. Locate repository instructions, package manifests, Foundry configuration, deployment records, launch contracts, SDK pricing/calldata helpers, deploy scripts, and launch tests.
2. Identify the exact supported:
   - chain and chain ID;
   - factory, launcher, router, template registry, oracle configuration, and wrapped-native addresses;
   - oracle pool profiles;
   - fee tiers and tick spacing;
   - template IDs and versions;
   - token implementations and template compatibility;
   - request fields, launch fee, deadline, initial-buy path, and slippage behavior.
3. Treat deployed registry/factory reads or checked-in deployment evidence as authoritative. Reject unsupported fee tiers, templates, profiles, token kinds, or oracle configurations.
4. Detect the toolchain from the repository. Use its pinned versions and package manager. If a required tool is missing, explain the official installation command and install it only when the environment permits. Never replace repository-native tooling with a familiar alternative.
5. Read the strongest existing launch tests before writing artifacts. Reuse their helpers and conventions.

## Conduct the interview in order

Ask focused questions in small related groups. Explain each choice before asking. Do not silently select economic policy.

### 1. Pool accounting profile — oracle is mandatory

Offer only oracle-enabled profiles supported by the target repository:

- **Standard Oracle pool**: both assets' input-side swap fees can be accounted for. Use it when the selected template needs fee flows from both the launched token and paired token. It supports dual-sided policies where the repository permits them.
- **Quote Oracle pool**: only input fees paid in the asset designated as the pool quote are accounted for. Use it when the design wants one predictable fee asset, commonly the established paired token, for owner revenue or rewards. A fee-burn template may instead designate the launched token as quote; derive this from the template rather than assuming it.

Both profiles have an oracle. Never offer non-oracle `Standard` or `Quote`. Explain that “standard vs quote” describes fee accounting, not whether a price oracle exists and not which token is automatically token0.

Ask which profile the user wants. If a later template is incompatible, show the incompatibility and ask them to change the profile or template; never coerce fields behind the scenes.

### 2. Standard or custom launch design

Explain:

- **Standard token launch**: the repository's plain owner-fee launch recipe and its required supported fixed-supply/burnable token implementation. Minimal modules and the smallest behavioral surface.
- **Custom launch design**: one of the repository's already registered templates and token kinds, such as staking rewards, holder dividends, dual-sided fee sharing, or fee burn. “Custom” does not permit arbitrary Solidity, taxes, blacklists, hidden minting, transfer restrictions, or a new unregistered template.

Enumerate only implementations discovered in the target repository, with profile compatibility, fee assets, allowed destinations, reward duration, and whether the launched token is quote. Ask the user to choose. For every active fee asset, collect owner/rewards/burn shares and require an exact 10,000 basis-point total. Inactive fee assets must be zero.

### 3. Token and quote asset

Collect and validate every repository-required field:

- creator address for deterministic prediction/simulation;
- token name and ticker;
- token decimals and total supply;
- supported token kind implied or allowed by the template;
- paired/quote token chain, address, symbol, decimals, and whether it is wrapped native;
- pool profile, template ID/version, fee tier, oracle configuration ID;
- fee dispositions;
- image/social metadata only if the target repository's launch path requires publication metadata.

Read ERC-20 metadata and code from the configured RPC when possible. Confirm address, symbol, decimals, chain ID, and that the selected oracle configuration and fee tier are registered. Do not infer decimals from a ticker.

## Quote-token USD price

Attempt to obtain a current USD price before asking the user to supply one:

1. Prefer the target repository's production price source or documented oracle/API.
2. Otherwise use a credible public market-data source that unambiguously identifies the same chain and contract address.
3. For a USD-pegged asset, verify the current price; do not assume exactly $1.
4. Record source URL or on-chain source, retrieval timestamp in UTC, asset address, observed price, and any staleness/identity limitation.
5. Ask the user to confirm the observed price. If no reliable price exists, ask them for a USD price and label it user-supplied with the timestamp. Never proceed from an unconfirmed price.

## Price near $5,000 FDV

Recommend `targetFdvUsd = 5000` unless the user requests another value. Display:

- total human-readable supply;
- target FDV;
- implied launch-token USD price: `targetFdvUsd / totalSupplyTokens`;
- confirmed paired-token USD price;
- implied launched/paired ratio in the orientation required by the repository;
- the derived tick, rounded tick, tick spacing, sqrt price, liquidity, and maximum token amounts;
- the effective FDV after tick rounding and its absolute/percentage difference from $5,000.

Use the repository's integer pricing helper and exact token decimals. Never implement approximate floating-point tick or liquidity math when a canonical SDK/contract helper exists. For the reviewed Black Market Atomic launcher, the canonical helper is `deriveAtomicLaunchPoolRecipe`; it prices against the protocol's launch inventory constant. Confirm that the requested supply and protocol inventory semantics match before using it.

Ask the user to confirm the quote price, target/effective FDV, and all derived parameters. If rounding puts effective FDV materially away from $5,000, present adjacent valid ticks/fee-tier effects and let the user choose.

## Initial buy

After pricing confirmation, ask whether the creator wants an initial buy.

If none:
- set amount in, minimum out, and sqrt-price limit exactly as required by the repository's zero-buy path.

If present:
- collect the paired-token amount;
- ask whether to enforce slippage protection or explicitly ignore slippage;
- when protection is enabled, collect the tolerance and derive the minimum output and sqrt-price limit with repository-native helpers;
- when the user chooses to ignore slippage, explain that execution may receive any output permitted by the contract, including materially less than the estimate, then require explicit confirmation and use the repository's supported unbounded values (commonly zero minimum output and its no-limit sentinel);
- distinguish native wrapped-token payment from ERC-20 allowance paths;
- use the repository-native initial-buy estimator in both modes;
- display gross input, pool fee, estimated output, protection mode, minimum output, sqrt-price limit, projected post-buy price/FDV, required balance/allowance, and launch fee separately;
- simulate the exact request. A pure estimate is never final authority.

Default to slippage protection. Never silently disable it. The user may explicitly choose to ignore it after the warning when the repository permits unbounded execution.

## Confirmation record

Before generating final artifacts, show one table containing every request field and derived value. Include chain ID, addresses, template ID/version, token configuration, pool profile, fee tier, oracle ID, quote orientation, both fee dispositions, target and effective FDV, price source/time, tick/liquidity/limits, initial buy, slippage/minimum out, launch fee, deadline policy, and creator. Require explicit confirmation. Any subsequent field change invalidates confirmation and requires re-derivation and re-simulation.

Never persist secrets. Generated configuration must contain public addresses and values only.

## Generate repository-native artifacts

Create the smallest maintainable artifacts in the target repository:

1. A parameter preparation path that calls existing SDK/math helpers and emits machine-readable output.
2. A Foundry script or repository-native equivalent that consumes validated parameters and constructs the exact request.
3. A simulation wrapper that pins RPC and chain ID, checks deployed bindings/registry/oracle/fee configuration, and invokes the script without broadcast.
4. Parameter-specific tests. Avoid hard-coded production prices unless the artifact clearly records source and timestamp and requires refresh/confirmation.

Separate preparation from signing. Generated scripts must not embed RPC credentials, private keys, passwords, or keystore paths. Do not include a broadcast flag in the wizard's runnable command.

## Required test rigor

Tests must defend observable launch behavior and fail on plausible misconfiguration. Match the repository's strongest contract and SDK tests. Cover all applicable items:

### Deterministic pricing and encoding
- decimal parsing, token decimals, $5,000 target, both price orientations, supported fee tiers, tick rounding, boundary values, liquidity bounds, and exact integer vectors;
- ABI selector, tuple field order, template ID/version, oracle ID, quote orientation, calldata round trip, and all user-confirmed fields;
- initial-buy monotonicity, fee rounding, directional sqrt limit, slippage bounds, minimum output, zero-buy behavior, and oversized/invalid inputs.

### Token contract
- exact name, symbol, decimals, initial recipient, total supply, and balances;
- exact transfers and allowance spending with no fee-on-transfer behavior;
- mint impossibility/fixed-supply invariant except explicit burns;
- burn and burnFrom behavior when supported;
- constructor/input rejection and authorization boundaries;
- for dividend tokens: one-time tracker binding, configurator authorization, tracker identity, transfer checkpointing, excluded-address behavior, and reward accounting.

### Template and launch lifecycle
- profile/template/token-kind compatibility and rejection of every incompatible combination;
- registered oracle and fee tier, no existing pool, predicted token/pool identity, single-sided liquidity inventory, no stranded launcher balances, launch fee handling, and event/receipt fields;
- realistic buy/sell ramp and chop, fee accrual, claims, exact owner/rewards/burn splits including rounding, supply reduction on burn, seven-day streams where configured, staking/dividend accrual and claims, and protocol-contract exclusions where applicable;
- deadline, allowance/balance, incorrect ETH value, slippage, reentrancy, and malformed-token failure paths already defended by repository conventions.

### Runtime simulation
- run focused unit/SDK tests;
- run the full local lifecycle test for the chosen parameter set;
- run a pinned-chain fork simulation against canonical deployed contracts when the repository supports it;
- invoke the generated script without broadcast and inspect the simulated receipt/state deltas.

Do not claim fork coverage when a test early-returns on the wrong chain. Record the actual command and observed result.

## Final output

Report:

- confirmed design and effective FDV;
- price source and UTC timestamp;
- generated artifact paths;
- exact tests and simulation commands run, with results;
- remaining assumptions or RPC limitations;
- an explicit statement that nothing was broadcast.

Stop after simulation. A later production deployment must be a separate, explicit user request with its own operational safety procedure.

## Reviewed reference behavior

These references explain the intended rigor but never override the current target repository:

- Black Market Abby appears as the default launch-wizard example/branding, not a dedicated deploy script: `apps/web/src/pages/NewLaunchPage.tsx` uses `Abby the Vampire Squid`, ticker `ABBY`, and `/abby.jpg`.
- Diesel deployment: `contracts/script/launch-diesel.sh`, `contracts/script/prepare-diesel.mjs`, and `contracts/script/LaunchDiesel.s.sol`.
- Diesel-specific behavior: `contracts/test/LaunchFullLifecycle.t.sol` and `contracts/test/DieselContractHeldMath.t.sol`.
- Generic rigor: `contracts/test/LaunchTemplateLifecycle.t.sol`, `contracts/test/LaunchCanonicalFork.t.sol`, `contracts/test/LaunchTokenFactory.t.sol`, `contracts/test/BurnableFixedSupplyToken.t.sol`, and `packages/sdk/test/launch.test.mjs`.

The reviewed Diesel script hard-codes a historical RIVN price, targets $3,000 FDV, sets minimum output to zero, and contains a broadcast mode. Those are historical deployment choices, not wizard defaults. The wizard MUST refresh and confirm price, recommend roughly $5,000 FDV, derive slippage protection, and remain simulation-only.
