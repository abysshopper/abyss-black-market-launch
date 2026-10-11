---
name: abyss-token-launch
description: Guide Node or Python SDK users through token design, exact USD launch pricing, protected opening buys, unsigned admission, explicitly authorized live execution, metadata publication, and canonical recovery without exposing signer secrets.
---

# Conversational Abyss launch and pricing

Help the user design, review, simulate, and, **only with explicit live authorization**, execute a launch. Signing occurs in the user's own terminal, never an agent-controlled terminal/PTY. Do not request keys, passwords, keystore contents, signed raw transactions, or session capabilities in chat. No secret belongs in commands, generated files, logs, screenshots, or Git. Prefer a password-protected keystore over a raw key.

## 1. Choose a workspace and SDK

Ask: **Node/TypeScript or Python? Existing workspace, new consumer project, or SDK checkout?** A contract repository/Foundry installation is not required. Inspect workspace instructions, installed package version, public SDK exports, examples, and the current lifecycle guide before constructing fields. Do not copy addresses/ABIs or historical launch math from this skill.

Official sources:
- Node: [repository](https://github.com/abysshopper/black-market-node-sdk), [lifecycle API](https://github.com/abysshopper/black-market-node-sdk/blob/main/docs/launch-lifecycle.md), [runner guide](https://github.com/abysshopper/black-market-node-sdk/blob/main/examples/README.md).
- Python: [repository](https://github.com/abysshopper/black-market-python-sdk), [launch/API guide](https://github.com/abysshopper/black-market-python-sdk/blob/main/docs/launch-guide.md), [runner guide](https://github.com/abysshopper/black-market-python-sdk/blob/main/examples/README.md).

Use the workspace's package manager and compatible SDK release (0.8.0+ for adjacent ranges/boundary-tail APIs); read the installed release, not just a shortened README. For a fresh consumer workspace:
- Node: initialize an ESM package and `pnpm add @black-market/sdk viem` (or the workspace's npm equivalent). Node SDK runtime supports Node 20+, but direct `.ts` examples require **Node 24+**. Import public `@black-market/sdk` / `@black-market/sdk/lifecycle`.
- Python: create/activate `.venv`, then `python -m pip install black-market-sdk`; import `black_market_sdk`. Requires **Python 3.10+**.
- Checkout alternative: clone the chosen official repository; Node uses `pnpm install --frozen-lockfile && pnpm build`; Python uses an activated venv and `python -m pip install -e .`.

The mixed-dividends examples are useful starting points: `launch-erc20-dividends-multiquote-mixed.ts` / `launch_erc20_dividends_multiquote_mixed.py`. Copy required helpers together when using a consumer workspace: Node `launch-example.ts`, `launch-example-support.ts`, `launch-example-kyber.ts`; Python `launch_examples.py`, `_launch_support.py`. Do not pretend a fixed example exposes arbitrary supply, fees, quote assets, deadlines, or ranges as wrapper/environment options. Customize the consumer-local plan construction through public APIs for choices outside its supported fields; leave the SDK checkout unchanged.

Store **nonsecret** API/RPC configuration and token options locally. Require the actual `LAUNCH_API_URL`; the runners do not support guessing/omitting their metadata API. Use HTTPS for remote endpoints; owned loopback services may use the SDK's explicit local exception. Never put signer variables/passwords in `.env` even if SDK examples show that option. Remove ambient/file-based signer configuration before using the secure helper; do not read existing secrets into the transcript.

## 2. Interview and certify the design

Ask small related groups, explain choices, and never silently select economic policy:
1. **Network and creator:** chain ID/RPC, public creator EOA address, actual deployment/core/registry. Official examples target Robinhood mainnet **4663**; other chains need real matching deployed infrastructure, not a changed number. Resolve addresses through SDK deployment helpers and verify RPC identity/live registry bindings.
2. **Token:** name, symbol, description/social links, ERC20 or ERC404, actual supported decimals/supply; for ERC404, NFT unit and genuinely hosted base URI. Current example tokens use 18 decimals (ERC20 1,000,000 tokens; ERC404 10,000 tokens / 100-token NFT unit). These are examples, not imposed user defaults. Do not invent configurable token decimals where the implementation fixes them.
3. **Rewards and fees:** none, staking, or holder dividends; supported reward duration/assets, owner recipient, token burn if admitted. For every collected fee asset collect owner/rewards/burn shares totaling exactly **10,000 bps**, sorted unique assets and inactive destinations zero. A 40% reward allocation is a split of collected fees, **not a 40% trading tax**. Separately review LP fee, hook fee, protocol/executor share and author royalty with their actual denominators. Fixed and dynamic hooks are different certified offerings: stored minimum/sensitivity do not make a fixed hook dynamic.
4. **Markets/topology:** V4, Abyss, or mixed; quote assets; exact supply allocation per market; position count/distribution; oracle configuration; external-liquidity policy; explicit `atomic` or `staged` mode. At most one V4 market per quote; Abyss may also use that quote. Choose only live admitted profiles compatible with token/reward/configuration and fee accounting. Oracle protection is required here: never replace an oracle-enabled offering with a non-oracle profile. Standard Oracle accounts both input fee assets; Quote Oracle accounts only its designated asset. This accounting choice is not token0 ordering. Canonical Abyss examples use QUOTE_ORACLE/profile3/config1; V4 examples use admitted fixed pool-bound config6/V2. Discover, do not force these onto another deployment.
5. **Opening buys:** none or ordered buys per market, recipient, input asset/amount, slippage tolerance, price limits, conversion slippage and separate gas budget. Also agree on cancellation policy, confirmation depth, plan deadline and any distinct conversion expiry.
6. **Metadata/image:** required API service, text/links and optional local PNG/JPEG/WebP artwork (1 byte–5 MiB); no image means metadata-only with canonical `image: null`, not invented artwork.

Read quote code/metadata, chain/address/decimals, canonical wrapped-native binding, certified profile/terms/schema/topology, registered fee tier/spacing/oracle and author ceiling from the SDK/live registry. Retain refusal reasons. “Custom” means composing supported public lifecycle plans, not adding arbitrary taxes, hidden minting, blacklists, unregistered hooks or Solidity. If a choice is incompatible, ask the user to change it; do not coerce it.

## 3. Price review and exact integer derivation

Recommend roughly **$5,000 whole-supply opening FDV**, unless the user chooses otherwise. Obtain pricing evidence before asking for a number:
- Prefer the SDK/workspace's documented price source. Record quote chain/address/decimals, exact price, URL/origin or on-chain source, upstream observation timestamp, UTC retrieval time, source identity and staleness/limitations. Retrieval does not refresh an old observation.
- Actual example runners require the configured API's `/api/v1/token-prices?chainId=4663&limit=100` direct WETH anchor with positive exact `priceUsdX18`; unpriced/mismatched/unavailable evidence refuses. Do not substitute a manual/public price to bypass that runner's checks.
- USDG examples use their catalogued explicit `usdPeg` seed; disclose it as a **peg assumption**, not a measured current $1 price. Verify current market evidence where available and get explicit agreement. For a custom admitted SDK plan, a reliable same-chain/address source or clearly labeled user-supplied value may be reviewed if its actual price policy supports it; unavailable required evidence stops that path.
- Ask the user to confirm each valuation input and target. Indicative USD seeds are not executable conversion quotes, RPC canonicality, or receipt authority.

Use `bigint` (Node) / `int` (Python), exact decimal parsing and SDK helpers; portable large values are decimal strings, never JSON floating-point numbers. Derive from the **entire actual raw minted supply S**, not a market's budget or an omitted helper default inventory. Pass explicit `supply`, `tokenBudget`/`token_budget`, quote decimals, USD-X18 seed, target USD-X18, admitted fee/spacing and predicted address ordering.

Predict the token before deriving markets. In these recipe APIs, `launchedTokenIsQuote` / `launched_token_is_quote = true` means **launched token is token0** (lower address), despite the historical name. If target is F (USD-X18), quote USD price Q (USD-X18), quote decimals d, then the desired raw quote-per-raw-launch-token ratio is `F * 10^d / (Q * S)`. Token0 uses that token1/token0 ratio; token1 uses its reciprocal. `sqrtPriceX96^2 / 2^192` is the raw token1/token0 ratio, not a human 1:1 price. The recipe handles integer square roots/TickMath and directional spacing rounding; do not replace it with logarithms/display floats. Use supported launched-token decimals only and apply actual decimals when displaying human prices/supply.

Call the pool recipe for one position; for multiple positions call the range helper with the exact requested count and `staircase`, `early-scarcity`, or `smooth-ramp`. Use `positionGaps: "adjacent"` / `position_gaps="adjacent"` and `extendFinalRangeToBoundary: true` / `extend_final_range_to_boundary=True`. Require each market's own nonzero funded permanent tail at its usable spacing-aligned buy-side boundary and continuous opening-to-tail coverage; a tail in another market does not count. Do not enable topology-gap/missing-tail opt-outs to turn a refusal into success.

Market budgets sum exactly to supply; position caps sum exactly to each market budget. Assign integer allocation remainders to the final market/position, enforce positive caps/liquidity and shared-endpoint capacity. Initial liquidity must require **zero quote deposit** at the actual opening orientation. Mint-rounding residuals burn before buys; they are not a creator reserve or extra allocation.

Display target versus aligned opening price/FDV (absolute and percentage difference), tick/sqrt price, per-market budgets, each range/cap/liquidity/expected mint debit, rounding burn and expected retained supply. Mixed markets must share the reviewed USD valuation, with rounding differences disclosed. Reconfirm materially different aligned outcomes rather than concealing them.

## 4. Opening buys and funding

Default to protected buys; derive `minTokenOut = floor(simulatedOutput * (10000 - slippageBps) / 10000)` from **every ordered stateful diagnostic buy**, then prove the final protected commitment. Use SDK sqrt-price-limit helpers where applicable. Pure first-buy estimators do not account for all ordered buys, hooks/fees or complete admission. If the user explicitly chooses unbounded execution and the selected path supports it, explain potentially much worse output, require separate confirmation, and use only its documented zero-minimum/no-limit sentinel. Do not imply the fixed runners expose a disable-slippage option.

Funding paths are distinct:
- Native ETH to canonical WETH is escrow **NativeWrap**, not a Kyber swap; verify binding and exact summed native value.
- Non-native quotes such as USDG require an actual admitted executable conversion build (example endpoint `POST /api/v1/quote/kyber/build?chainId=4663`). Freeze exact input/output, target/spender/runtime commitment, escrow sender/recipient, minimum, calldata and expiry. Preview GET output is not funding calldata. Registry admission and complete sequential proof are mandatory.
- Custom direct ERC20 funding requires actual balances and exact escrow approvals, including supported reset-to-zero handling. Never approve the wrong core/adapter or silently switch funding routes after refusal.

The examples use native input **per buy**, default 0.00001 ETH, with 50-bps protected buys and 50-bps non-native conversion slippage. Aggregate conversion inputs by quote; split protected quote output across ordered buys with the remainder last. Ask for real budgets, not unquestioned examples. WETH wrapping and admitted conversion failures must never trigger an unapproved separate-wallet swap, fallback, route retry, deadline rewrite or omitted buy.

Show native/quote input, conversion minimum/expiry, LP/hook/other fees, expected output, min output, sqrt limit, per-buy all-in USD/token and fee-plus-price-impact premium, funding balances/allowances, total spend **plus gas**. Do not invent a flat launch fee. Distinguish whole-supply opening valuation from average execution price and observed post-buy marginal price/retained-supply valuation; only claim simulated post-buy values when actually supplied by canonical simulation.

## 5. Public APIs, proof and confirmation

| Task | Node public API | Python public API |
| --- | --- | --- |
| Deployment/discovery | `getAddresses(4663)`, `getKnownLifecycleDeployment`, `readLifecycleProfiles` | `get_launch_addresses(4663)`, `read_lifecycle_profiles` |
| Prediction | `predictLifecycleToken` | `predict_launch_token` |
| Integer recipe/ranges/topology | `deriveLaunchPoolRecipe`, `deriveLaunchPositionRanges`, `assertLaunchTopologyCoverage` | `derive_launch_pool_recipe`, `derive_launch_position_ranges`, `assert_launch_topology_coverage` |
| Pure buy/price-limit helpers | `estimateLaunchInitialBuy`, `deriveLaunchBuySqrtPriceLimitX96` | `estimate_launch_initial_buy`, `derive_launch_buy_sqrt_price_limit_x96` |
| Market codecs | `encodePoolBoundV4LifecycleMarketConfig`, `encodeAbyssLifecycleMarketConfig` | `encode_lifecycle_pool_bound_v4_market_config`, `encode_lifecycle_abyss_market_config` |
| Finalize salts/protected buys and prove | `prepareAndPlanLifecycleLaunch({client, account, plan, mode, buySlippageBps, ...})` | `await prepare_and_plan_lifecycle_launch(client, plan, account=..., mode=..., buy_slippage_bps=..., ...)` |
| Already-finalized admission | `planLaunch` | `plan_launch` |
| Fresh remaining proof | `simulateLaunchPlan` | `simulate_launch_plan` |
| Canonical progress | `readLaunchProgress({client, planned, receipts, confirmations})` | `read_launch_progress(client, plan, mode=..., receipts=..., confirmations=...)` |
| Next proven unsigned envelope | `buildNextTransaction` | `build_next_transaction` |
| Portable plan/hash | `parseLaunchPlan`, `serializeLaunchPlan`, `hashLaunchPlan` | `launch_plan_from_dict`, `launch_plan_to_dict`, `hash_launch_plan` |
| Pure unsigned compiler | `buildLaunchTransactions` | `build_lifecycle_calldata` |

SDK planners do not sign or publish. Pure compilation/encoding, token prediction, hook salt mining or an RPC estimate is **not execution admission**. Persist the returned finalized plan, explicit mode, confirmation policy, restrictions and typed receipt references, not a draft or callback-filled runtime object. Require `admitted`, proved execution and applicable protocol fit; disclose transport preflight separately. Refused/unavailable simulation **stops**. Robinhood requires pinned native Nitro compute/poster evidence and exact sequential `eth_simulateV1` replay; an Anvil/Hardhat fork is not a Nitro substitute. Generic-EVM controlled forks must be separate owned disposable loopback backends, never the source RPC/unlocked live wallet.

Atomic and staged are explicit choices, never an automatic fallback. Staged can partition only empty preparation under SDK-classified capacity constraints; all mint/lock/ordered buys/public activation remain indivisible. Never drop positions/buys/minima or bypass profile/funding/gas/canonical checks to obtain admission.

Run the smallest consumer-specific unsigned checks and successful exact-plan simulation, not a newly generated exhaustive contract matrix. Review one complete table: chain/core/creator/predicted token, identity/supply/rewards, profile/terms/oracle/config version, quote orientation/decimals, all fee rates/allocations, price evidence/time, target/aligned/retained valuation, budgets/ranges/dust, buys/protection/funding/expiry, gas envelopes, plan deadline, execution mode and metadata/image descriptor. Save a nonsecret economic review and require explicit agreement. Any economic field/source/price change invalidates that agreement and requires re-derivation, successful proof and renewed confirmation.

## 6. Secure dry run and explicit live authorization

Use this repository's `scripts/run-launch.py` by absolute path **from the SDK/consumer workspace cwd**. Activate the Python SDK venv first: the helper uses `sys.executable` for Python children and `node` for Node children. Select a vetted local runner that accepts the documented mode flags.

Helper interface:

```text
python /path/to/abyss-black-market-launch/scripts/run-launch.py \
  --sdk node|python --script PATH (--keystore PATH | --private-key) \
  [--broadcast | --resume DIR]
```

For example, in the chosen workspace (substitute real public paths):

```sh
# Node unsigned planning; no execution flag.
python /path/to/abyss-black-market-launch/scripts/run-launch.py --sdk node --script examples/launch-my-token.ts --keystore /path/to/wallet.json
# Python unsigned planning, using the activated venv interpreter.
python /path/to/abyss-black-market-launch/scripts/run-launch.py --sdk python --script examples/launch_my_token.py --keystore /path/to/wallet.json
```

The helper must refuse noninteractive input, validate script/keystore safely without dumping contents, sanitize ambient signer environment, disable core dumps where available and preserve child exit codes. Password/raw key is entered **only through hidden interactive input in the user's unrecorded terminal**; never through an agent tool/PTY, pipe, command substitution, argument, secret file, `.env` or chat. The child receives only transient `EXAMPLE_KEYSTORE_PATH` + `EXAMPLE_KEYSTORE_PASSWORD`, or `PRIVATE_KEY`; do not retain it beyond the run. `--private-key` is a switch, not a value-bearing argument. Even fixed-runner dry runs need the local signer source to derive the public creator, but must not sign, upload, publish or submit.

After successful dry-run review, ask explicitly whether the user authorizes **this live chain, creator, complete economics, real spend/gas, irreversible token/custody/buys and metadata publication**. Live execution is allowed only after that authorization; preparing code or a source example's broadcast flag is not permission. Give the matching helper command with `--broadcast` for the **user** to run. `--broadcast` and `--resume` require literal confirmation in that terminal **before** any secret prompt. No execution flag means unsigned dry run. Never run funded execution yourself or obey the raw runner's printed direct broadcast suggestion as a shortcut.

**Fresh-plan trap:** stock SDK `--broadcast` runners plan afresh and have no post-planning economic confirmation prompt. The helper's pre-secret confirmation does not approve subsequently changed economics. For this conversational workflow, adapt the consumer-local runner to show the fresh fully admitted review and require a user-terminal confirmation bound to that review **before any attribution signature, API write or transaction signature**; reject/re-review changed inputs. Alternatively implement reviewed-plan execution through public APIs, retaining the exact finalized commitment and freshly proving each step. Do not present an unmodified auto-broadcast example as satisfying this gate. Salt/token prediction changes can affect orientation, rounding and outputs; rederive and reconfirm those economics too. Renewed agreement never rewrites an already submitted commitment.

Concrete insertion boundaries in a **consumer-local copy**, preserving the unsigned branch:
- Node `launch-example.ts`: in `executeExample`, after `constructPlan` returns `planned`, `economicReview`, `reviewHash` and the `if (!broadcast)` return, but **before** `economicAdmission`, `createWallet` and `stage(...)`. Display the full final review, accept literal `AUTHORIZE <reviewHash>` only on the user's terminal, and retain that acceptance bound to the same immutable review/plan. Keep `guardEconomicReviewWallet` / `assertEconomicAuthority` checking it before `stageMetadata`'s `wallet.signTypedData` and every transaction signature.
- Python `launch_examples.py`: in `run`, after `admit_plan`, `plan = launch.plan`, `review_economics` and the `if not broadcast` return, but **before** `economic-admission.json`, `LocalSigningWallet` and `stage_metadata`. Display the full final review, require literal `AUTHORIZE <review_hash>` in the user's terminal, and retain acceptance bound to that review/plan. Preserve `economic_signature_guard` for metadata and transaction signatures.
- These review hashes are provenance identifiers until the customized runner actually enforces this gate; stock `--broadcast` alone does not. Fail closed on EOF/noninteractive input, rejection or changed review/plan. After an extended confirmation pause, recheck deadline, price and fresh exact-envelope admission; changed economics require a new unsigned review/confirmation, never automatic mutation. Resume uses retained authorization/commitment plus explicit helper continuation consent, not this fresh-launch regeneration path.

Before every signature recheck creator/provider chain, current pricing authority, deadline, funding/admission and exact `from/to/data/value/gas/gasPrice` (or admitted fee envelope). Use the fresh next-transaction builder and immediate submission-provider preflight; a reviewed envelope must match exact current commands. Never disable wallet chain checks or enlarge gas silently. Signing/API mutation stays in the user-terminal runner. Durable recovery may contain signed bytes and API capability **but never a key/password**; keep such files owner-only, unshared and out of Git.

## 7. Metadata, receipts and recovery

Use actual `LaunchApiClient` flows, not a fake publication projection:

| Flow | Node methods/helpers | Python methods/helpers |
| --- | --- | --- |
| Signed attribution | `canonicalLaunchMetadataHash`, `launchAttributionTypes` with full EIP-712 chain/core domain | `build_launch_attribution_typed_data` with explicit `verifying_contract` |
| Create/read session | `createUploadSession`, `getUploadSession` | `create_launch_upload_session`, `get_launch_upload_session` |
| Upload/complete/renew | `putImage`, `completeUpload`, `renewUploadUrl` | `put_launch_image`, `complete_launch_upload`, `renew_launch_upload_url` |
| Publish | `publishUploadSession`, `LaunchPublishPending` | `publish_launch_upload_session`, `LaunchPublishPending` |

Require correct chain/wallet and signed metadata, including description, idempotency key/nonce/deadline and exact optional SHA-256/MIME/length. Never preassign API image keys. Persist original signed request/idempotency **before** create POST and one-time capability durably **before** further requests; unknown issuance requires service reconciliation, not a new/replayed session. Upload only exact frozen bytes with issued headers/create-only conditions, complete server verification and require ready status. Pending-image recovery needs original bytes; renew only in the documented expired-upload case. Do not turn image failure into metadata-only success.

Before each raw send, persist exact signed-envelope hash and private bytes; persist inclusion receipts before asserting success. On every next step/reload, use canonical progress, confirmed/head/pending nonce checks and typed receipt evidence: original hash, observed block number/hash, confirmation policy and effective replacement hash. Never trust local counters or redacted `plan.json` as recovery authority. Pending/unconfirmed work waits without new executable commands; removed/moved blocks require reorg reconciliation; reverted/replacement-cancelled transactions are not completion. A missing receipt/ambiguous send is not permission to send again.

After interruption, use **only the original broadcast directory**, same SDK/script/creator and exact plan/mode/confirmation policy/session through helper `--resume DIR` (instead of `--broadcast`). It is live authorization, not a dry run. Node retains `private-recovery.json`; Python retains `recovery.private.json` and `signed-<hash>.private.json`. Resume must not mine new salts, regenerate identity/minima, refresh committed economics/expiry, re-create a session or blindly rebroadcast unresolved signed hashes. Use Node unsigned `examples/launch.ts --plan ... --mode ... --receipts ...` or Python `examples/launch_submit.py ... --mode ... --receipts ...` with safe owner-local exact recovery data for read-only reconciliation. Canonical Preparing/Ready continues only proven remaining steps; Active performs verification/publication only; Cancelled is terminal. Cancellation is a separate explicit action/authorization, not a silent rescue; it requires fresh nonce/receipt/execution safety and cannot pause an Active launch.

Publish **only the original confirmed activation hash**, after a fresh canonical barrier binding its receipt/block/confirmations to the exact commitment and Active state, and repeat the barrier before final success. Preserve the original hash across replacement/reorg ambiguity; stop for reconciliation rather than choose a convenient later transaction. Genuine pending-indexer `202` / `LaunchPublishPending` may be polled within the documented bound honoring `Retry-After`; other failures are not blanket-retried. Require actual optimistic/final session and matching indexed `/api/v1/launches/<token>?chainId=...` data, not chain success alone. If an image was selected, require matching ready descriptor/token-bound public image URL and bounded HTTP-200 nonempty image verification; transformed bytes are qualified transformation evidence, never claimed byte-identical.

## Final report

Report confirmed token/design, pricing source and UTC timestamps/limitations, target/aligned valuation and actual outcomes, public artifacts/run directory, exact checks/simulations exercised, mode/authorization, chain status and canonical transaction/token/market evidence, and API/image status separately. Never claim broadcast/publication/finality from a dry run, local fixture or unobserved output. When stopped, preserve all recovery evidence and name the exact refusal or pending dependency and safe read-only next step; never recommend a fresh launch after an ambiguous send.
