# HMM economics, configuration and operations

HMM adds a **quote-fee-funded inventory-recycling book** alongside permanently locked launch liquidity. It is not an owner token reserve, a token burn, an automatic holder payout, an LP compounding policy or a guaranteed price-support mechanism. Use [Hooks and compatibility](hooks.md) and [Token designs](token-designs.md) for the whole launch; this reference explains the additional material HMM choices, not live permission to launch.

## Evidence and offering selection

Inspected **2026-10-12** against published Node `@black-market/sdk` **0.9.0** (upstream `3f19ae3f3cfc648cad34f14ffbf897d4a63c6f21`) and Python `black-market-sdk` **0.9.0** (upstream `3146fb1c072cfe4228bfc7f1b467d6415ed10c57`), plus protocol HMM documentation/source. SDK frozen graph provenance identifies protocol source `1ca98813f7aa72393116aac4d3d791e65d4fb635` and October11 admission bundles `20261011T214314Z-hmm-fixed` / `20261011T220032Z-hmm-dynamic`. No live certification or launch simulation was performed for this reference. Public SDK links follow `main`; protocol links use the pinned commit and **may require authorized repository access**. Unauthenticated raw protocol `main` and feature-branch requests returned HTTP 404; semantics were inspected through the available checkout and matched to the pinned source, not claimed publicly accessible. Retain the installed version/source and observed canonical block for an actual launch.

| Offering | Public preset and hook selection | Trading-rate behavior | Oracle-required workflow |
| --- | --- | --- | --- |
| **HMM Fixed** | Node `KnownLifecycleProfile.V4HmmFixedPool` / `KnownLifecycleHook.HmmFixedPoolV1`; Python `V4_HMM_FIXED_POOL` / `HMM_FIXED_POOL_V1`; strings `v4-hmm-fixed-pool` / `hmm-fixed-pool-v1` | Static maximum `hookFeePips` / `hook_fee_pips`; stored minimum/sensitivity do not change it. | **Catalog only; refuse selection.** The implementation has no truncated-oracle interface/history. Registered oracle factory/config fields do not supply an oracle. |
| **HMM Dynamic** | Node `KnownLifecycleProfile.V4HmmDynamicPool` / `KnownLifecycleHook.HmmDynamicPoolV1`; Python `V4_HMM_DYNAMIC_POOL` / `HMM_DYNAMIC_POOL_V1`; strings `v4-hmm-dynamic-pool` / `hmm-dynamic-pool-v1` | Same observed upward quote-per-base tick-velocity minimum/maximum/sensitivity schedule as Dynamic Fee Hook. Warm-up/flat/falling signal uses minimum; old signal decays with idle age; rate freezes before swap observers. | Candidate with genuine truncated oracle, registered config and current exact-plan proof, **not certified by this catalog**. |

Both are distinct pool-bound topology **2**, config **6**, V2-constructor offerings with their own reviewed graph/terms, HMM collector/deployer and locker, not aliases for ordinary fixed/dynamic profiles. Both require **LP fee zero** and **developer/author rate zero**. Frozen capabilities are mask **123** (including ERC404 and multi-position); bounds allow spacing **1..32,767**, **32 positions**, oracle cardinality up to **4,096**, and **InputToken / QuoteOnly** modes. These describe construction candidates, not every token/reward combination's eligibility. One V4 market per quote and **32 total launch positions** still apply. Strategy auxiliary positions do not replace the required funded permanent tail in each market. [N-guide, N-presets, P-guide, Fixed-review, Dynamic-source]

## What the operation actually does

The bound manager is an authorized liquidity operator **after opening even when `externalLiquidityDisabled` is true**, outside fee checkpoints. That switch restricts third-party liquidity, not the HMM book; it does not freeze all auxiliary liquidity. Preserve the user's external-liquidity choice and disclose this exception rather than disabling HMM or inventing a stricter switch. [Protocol, Common-hook, Base]

- Each market has one separate `HMMLiquidityManagerV1`. It owns **one auxiliary quote bid**, up to **eight auxiliary resale asks**, and ERC6909 inventory claims, including a **claims-only reserve lot**. The original launch positions remain in the sealed permanent locker; the manager never owns, resizes, removes or transfers them.
- Collected quote funding is first an ERC20 transfer to the manager, **not an immediate market buy or liquidity addition**. A later successful maintenance pass deposits physical quote only when the PoolManager has no synced currency, closes deltas into claims, and deploys available quote subject to thresholds, inventory capacity, valid range and rounding constraints. Otherwise funding/placement may wait.
- A bid sits below the local placement anchor. Fills acquire launched tokens; resale asks place acquired stock above spot and no lower than their effective realized-cost-plus-premium floor and anchor/gap constraint. Returned quote can fund further bids. Unplaced inventory remains claims-backed, sometimes in the reserve; a valid config does not promise prompt placement, sale or a complete recycling cycle.
- Maintenance performs mandatory ask harvests in slot order, then mandatory bid harvest; it refreshes retained fill checkpoints, optionally removes **at most one stale position** (asks first, then bid), deposits quote/closes claims, promotes reserve inventory and places/reinforces auxiliary positions. Completed passes net both currency deltas to zero.
- The **local anchor is not an oracle/TWAP**. It may fall on any maintenance pass and rises only on a priced two-sided swap ending with active liquidity. Ending-composition checkpoints refresh meaningful-fill age only when net observed token movement meets the minimum token harvest; an intra-swap round trip returning to the checkpoint is intentionally invisible. These rules are not manipulation-resistance guarantees.
- Strategy ticks treat the launched token as synthetic token0, independent of address ordering. When the token is actual currency1, strategy spot is `-poolTick - 1` and strategy interval `[L,U)` maps to pool `[-U,-L)`. Use contract/SDK orientation logic rather than display-price inversions; widths, gap and displacement are **tick spacings**, not raw ticks.

There is **no manager owner-redemption, seed, recipient-share or fee-charging path**. Transferring quote directly to the manager is not an owner deposit with a promised withdrawal. Inventory cost floors discipline auxiliary placements, **not the public market price**, and do not guarantee profit, fills or protection against an adverse market. [Protocol, Manager]

## Quote-fee diversion and exact precedence

The chosen strategy share is a share of **newly collected quote fee proceeds**, not a trading tax or a percentage of supply. `InputToken` can produce both quote and token fees across directions; `QuoteOnly` produces quote hook fees in both directions. Both HMM offerings have zero LP fee. HMM never diverts token-side fees, preexisting collector balances or arbitrary donations to the collector. [Collector]

The source and hub order is explicit:

1. **Protocol treasury first.** The hook accrues its separately rounded treasury liability and sweeps it on redemption before forwarding net hook fees to the collector. Its source arithmetic is zero treasury for denominator zero, otherwise integer division by the denominator followed by the documented `125 / 100` adjustment; the frozen HMM denominator is **6**, not a hardcoded flat trade percentage. Verify actual selected terms. PoolManager protocol-fee handling is a separate concrete-hook restriction, not an additional percentage to guess.
2. **Strategy next.** The collector combines newly claimed liquidity/hook proceeds, identifies the actual quote as the asset opposite the launched token, sends `floor(newQuoteCollected × strategyShareBps / 10,000)` to its bound manager, and forwards the remaining quote plus **all token proceeds** to the hub. Strategy funding occurs **before** the hub bounty and owner/reward/burn split, not solely out of the owner's share.
3. **Hub executor bounty next.** `claimAndSplit()` pays its bounty based on the asset's **actual newly received, post-diversion proceeds**. Other sources may contribute to the same asset. Preexisting unreserved hub inventory follows its disposition policy separately and does not acquire a newly-collected-fee bounty or author allocation.
4. **Normal disposition next.** After bounty, the hub applies the committed owner/rewards/burn split totaling **10,000 bps**. It floors destinations then assigns the remainder to owner if active, otherwise rewards if active, otherwise burn. Reward modules remain unchanged, but their quote funding base is smaller after diversion.
5. **Author allocation comes from attributed owner proceeds**, after bounty/disposition; it does not surcharge trading or take reward/burn proceeds. HMM's selected author rate must be **0**, regardless of the larger protocol ceiling, so these HMM sources owe no author royalty.

Consequences the user must review:

- **100% share is valid** and routes all this source's newly collected **net quote** to the manager. It leaves **zero quote hub receipts from this source** for bounty/owner/rewards/burn, but does **not** erase protocol treasury payment. Token-side fees, other sources, existing hub inventory or prior owner credits are separate; do not promise that the entire launch has no rewards or owner revenue.
- **0% share is valid** and diverts nothing from new fees. It does **not** disable/remove the manager, unwind existing bids/asks, refund inventory, erase cost floors or prevent previously funded/directly transferred quote from being maintained. It does not remove hook-to-manager gas/callback behavior.
- **50% is the helper default, not user approval.** Review the revenue tradeoff together with the normal fee split: e.g. a reward allocation applies to the smaller post-strategy/post-bounty base, not to gross trading input or gross quote fees.
- Only the launch's **current fee owner**, resolved through the hub fee-owner registry, may call `HMMFeeCollectorV1.setStrategyShareBps(uint16)` within **0..10,000**. The new share affects the **next collection, including already-accrued unharvested fees**. It does not change strategy geometry. Authors/keepers have no authority from those roles alone. This mutability must be disclosed; the initial plan hash is not a promise of an immutable lifetime share.
- The current fee owner's existing hub `setExecutorFeeBps(uint16)` is a different control, bounded **0..1,000 bps**; owner pull credits and author payout authority are separate too. Do not conflate them with strategy share.

Evidence: [Collector] `collect` / `setStrategyShareBps`; [Base] `_accrue` / `_redeem`; [Hub] `_collectSource`, `_reserveAsset`, `_reserveDeveloperFees`, `_splitAmounts`; [Protocol] collector split and fee-owner controls. These are source-described economics, not observed live payouts here.

## Strategy controls and calibration

Fields below use Node camelCase; Python uses the corresponding snake_case fields in `HmmStrategyConfig` / `HmmLaunchConfig`. **All helper values are proposed model calibrations, not an investment recommendation or approved economic policy.** Share is mutable after launch; strategy fields are constructor-fixed in this manager implementation, not owner-tunable post-launch settings. [N-helpers, P-helpers, Manager]

| Field | Meaning / user-choice consequence | SDK helper default |
| --- | --- | --- |
| `strategyShareBps` | Net quote fees diverted upstream of hub bounty/disposition. More funding reduces this source's immediate quote distributions. | **5,000 bps (50%)** |
| `bidWidth`, `askWidth` | Auxiliary bid/ask range widths in multiples of market spacing. Alter deployment geometry and inventory exposure. | **5 / 5** |
| `gap` | Spacing-count separation used by bid/ask target ranges around the local anchor. Not a raw-tick or fixed-dollar spread. | **1** |
| `staleAfterSeconds` | No-meaningful-net-fill age gate for optional relocation, not a timer guaranteeing movement. | **86,400 seconds (24h)** |
| `staleDisplacement` | Minimum target displacement in tick spacings, normally required **together with** stale age. | **5** |
| `minQuoteDeploy` | Raw quote-claims threshold for bid deployment/reinforcement; passing it does not guarantee a valid/capacity-funded placement. Zero is allowed. | Quote-specific below |
| `minQuoteHarvest` | Raw quote-content threshold for harvesting a mixed resale ask; fully sold asks harvest independently. | Quote-specific below |
| `minTokenHarvest` | Raw token threshold for mixed bid harvesting, stock/residual handling and meaningful net-composition age refresh; fully converted bids harvest independently. | Integer **market token budget / 100,000** |
| `resalePremiumBps` | Premium added to realized acquisition cost for the stored ask floor; not the hook trading fee or guaranteed return. | **500 bps (5%)** |
| `maxAsks` | Maximum used ask slots, not permanent launch position count. More slots subdivide the offered cap. | **4** |
| `maxAskTokenExposure` | Raw-token offered cap; each ask placement is capped by integer cap / ask count as well as stock and available claims. | Integer **market token budget / 10** |
| `maxAcquiredInventory` | Raw-token inventory cap; each bid is sized so full token conversion fits remaining acquired-inventory allowance. Not extra minted allocation. | **market token budget** |
| `premiumDecaySeconds` | Ask/reserve premium-floor decay duration; **0 disables decay**. Decay relaxes placement premium, not acquisition cost, and does not itself move a live ask. | **0 (off)** |

Use the **actual market's raw token budget**, not whole supply or omitted example inventory, for calibration. Exact integer truncation is material. A budget below **100,000 raw units** yields zero default token harvest and fails; caps above `uint128.max` fail rather than clamp. Review human-unit equivalents using real token/quote decimals, then retain exact integers in the plan.

Default quote calibration resolves SDK catalog symbols or canonical catalog addresses:

- **WETH:** minimum quote deploy / harvest **0.0005 / 0.005 WETH** (the guide calls these ETH units). These are asset-unit thresholds, not USD valuations or a new native-funding route.
- **SDK USD-pegged quote calibration (documented USDG):** **1 / 10 quote units**; USDG uses its catalogued six decimals. A catalog `usdPeg` flag is a calibration assumption, **not a measured current $1 price**.
- **Other quotes:** both minimum quote deployment and harvest must be explicitly supplied in raw quote units. Decimals alone do not infer a peg or price. Verify actual chain/address/decimals and do not substitute a familiar symbol on another deployment.

The SDK helper implementations differ in input guards: Node checks supplied decimals against known catalog decimals and requires input budget within uint128; Python accepts an optional decimal override and checks input budget as uint256 before strategy-cap validation. Do not treat an accepted override as verified asset metadata; read actual decimals and require equality yourself. A successful default helper/encoder is only local validation, never admission. [N-helpers, P-helpers]

### Premium decay and stale behavior

A **nonzero** `premiumDecaySeconds` causes the effective ask/reserve floor to decline linearly in **tick distance**, rounded up to a whole spacing, toward the zero-premium realized-cost floor. It never decays below **current allocated realized cost**; rounding can raise that current unit cost above the original stored premium floor. Unrepresentable floors defer placement and sentinel floors never decay. **259,200 seconds (72h)** in SDK examples is an optional illustration, not an approved/recommended choice.

The stored floor remains unchanged. New acquired inventory begins its clock at acquisition; promotion and partial-placement/harvest residuals retain lot age, and nonempty reserve folds use a token-weighted average clock rounded down, so a small arrival cannot renew the whole reserve age. Normal stale relocation requires **both** no-meaningful-fill age and displacement. Once fully decayed, an ask above its final target can relocate downward after the age gate without the normal displacement threshold; bids retain the original rules. Decay alone does not place/sell/move an ask, force a fill or guarantee profit. [Protocol, Manager]

## Launch tail and exact validation

Supply an explicit typed `hmmLaunchConfig` / `hmm_launch_config` on the selected HMM **config6** market. The public market codec emits a canonical V6 prefix, including its complete dynamic positions array, followed by **exactly 448 bytes (14 static ABI words)** for the HMM launch configuration. Use public codecs, not copied ABIs or manual tuple construction. `abi.encode(v6, hmm)` is **not** equivalent to concatenating the two canonical encodings; it changes the V6 dynamic offset. [N-guide, P-guide, Factory]

Exact local checks, mirroring the factory and Solidity widths:

| Field/check | Required bound |
| --- | --- |
| Strategy share | Integer **0..10,000 bps** (`uint16`) |
| Bid width, ask width, stale displacement | Integer **1..8,388,607** (positive `int24`) |
| Gap | Integer **0..8,388,607** (`int24`) |
| Stale seconds | Integer **1..4,294,967,295** (`uint32`) |
| Premium decay seconds | Integer **0..4,294,967,295** (`uint32`) |
| Minimum quote deployment | Integer **0..uint256.max** |
| Minimum quote/token harvest | Integer **1..uint256.max** each |
| Resale premium | Integer **0..5,000 bps** (`uint16`) |
| Ask count | Integer **1..8** (`uint8`) |
| Offered exposure | **At least ask count and minimum token harvest**, at most **uint128.max**, despite ABI `uint256` |
| Acquired inventory | **At least minimum token harvest**, at most **uint128.max**, despite ABI `uint256` |
| Market wire/economics | Matching inner/outer profile/version, **config6**, canonical V6 prefix, exactly canonical 448-byte tail, **LP fee 0 / author rate 0**, selected profile's own terms/graph/bounds |

There is no factory guard requiring acquired cap ≥ offered cap or harvest ≥ deployment threshold; do not invent such limits, or invent automatic clamps for invalid inputs. ABI/range validation does not prove execution capacity or economic suitability.

Missing/short/extra tails, noncanonical offsets/prefixes/tails, tails on non-HMM profiles and historical versions fail. Decoding, salt mining, finalized-plan serialization and recovery must retain the typed tail. **The full plan hash commits every tail byte. The hook constructor's market-economics commitment excludes the auxiliary tail and hashes only the canonical V6 prefix with zero hook salt**, matching the factory. Therefore identical constructor commitment or a mined salt does not independently authenticate the strategy choice; bind the complete finalized plan/review hash. Tail changes require renewed economic review and exact proof even if hook constructor identity is unchanged. [N-markets, P-guide, Factory]

## SDK construction versus contract-only operations

| Surface | Node public API | Python public API / boundary |
| --- | --- | --- |
| Typed strategy/launch configuration | `HmmStrategyConfig`, `HmmLaunchConfig` | `HmmStrategyConfig`, `HmmLaunchConfig` |
| Local calibration/guards/tail codecs | `defaultHmmLaunchConfig`, `validateHmmLaunchConfig`, `encodeHmmLaunchTail`, `decodeHmmLaunchTail`, `isHmmProfile` | `default_hmm_launch_config`, `validate_hmm_launch_config`, `encode_hmm_launch_tail`, `decode_hmm_launch_tail`, `is_hmm_profile` |
| Integrated market codec | `encodePoolBoundV4LifecycleMarketConfig` / matching decoder with `hmmLaunchConfig` | `encode_lifecycle_pool_bound_v4_market_config` / matching decoder with `hmm_launch_config` |
| Discovery, salts and exact launch proof | Existing `readLifecycleProfiles`, `prepareAndPlanLifecycleLaunch`, `planLaunch`, `simulateLaunchPlan` | Existing `read_lifecycle_profiles`, `prepare_and_plan_lifecycle_launch`, `plan_launch`, `simulate_launch_plan` |
| Later strategy share, maintenance and state inspection | **Contract-only operation surface**, not a dedicated 0.9.0 HMM SDK management wrapper | Same boundary; do not invent convenience methods or signing support |

Contract-level operations include current fee-owner `collector.setStrategyShareBps`, permissionless hub `claimAndSplit`, manager `maintain`, and manager state/effective-floor/fill-state getters. Hook-only `onOpened`, `onSwap`, `onDonate` are **not user maintenance calls**. Use verified deployed bindings and authoritative contract ABI for any separately authorized operation; this reference does not supply transaction calldata or authorize writes.

Callbacks and risk: opening, swaps and donations notify the bound manager. The hook reserves **3,000,000 gas** per manager call and requires at least **3,057,619 gas remaining at that call site**, otherwise the entire operation reverts. With sufficient gas, a manager revert is isolated and emits `LiquidityManagerCallFailed(bytes4)`; the market operation can succeed without strategy maintenance. This threshold is not total transaction gas or a universal gas bound. A failed opening notification is not automatically retried by the hook. Check manager `opened()` and failure events rather than infer strategy readiness from token activation or successful trades. Direct `maintain()` is permissionless but cannot substitute for hook-only opening initialization. [Fixed-review, Common-hook, Manager-interface]

## Required consumer review and proof

Record each material HMM field as supplied, verified, proposed, unresolved or conflicting alongside the ordinary token/price/fee review. Resolve SDK/deployment/registry facts with tools, not user guesses. Obtain agreement on **proposed** strategy share, diversion precedence/revenue effect, fee-owner mutability, widths/gap, stale gates, exact thresholds/caps, premium/decay and the absence of guarantees/owner redemption. A supplied decision need not be asked again, and agreeing to economics is not live authorization.

Before execution retain current paginated profile discovery and canonical block, genuine oracle behavior/config, complete artifact/graph/manager provenance, zero LP/author restrictions, token/reward/fee-asset compatibility, full-key orientation, funded permanent tail/continuous coverage per market, zero quote initial mint, exact supply budgets, protected ordered buys/funding, explicit mode and successful **complete exact-plan** proof. Refused/unavailable simulation stops; Robinhood requires its real Nitro/exact sequential evidence, not generic fork substitution. Preserve refusal reasons. Never silently switch HMM Fixed to Dynamic, reduce strategy share, remove rewards, change decay or accept an oracle-free implementation to obtain admission. Current admission alone does not establish these user-specific choices or authorize execution.

## Official sources

- **[N-guide]** [Node 0.9.0 HMM release](https://github.com/abysshopper/black-market-node-sdk/blob/main/docs/launch-lifecycle.md#090-release-hmm-pool-hooks); **[N-presets]** [frozen profile selectors](https://github.com/abysshopper/black-market-node-sdk/blob/main/src/lifecycle/presets.ts).
- **[N-helpers]** [Node HMM helpers](https://github.com/abysshopper/black-market-node-sdk/blob/main/src/lifecycle/hmm.ts); **[N-markets]** [market codec/commitment](https://github.com/abysshopper/black-market-node-sdk/blob/main/src/lifecycle/markets.ts).
- **[P-guide]** [Python HMM launch guide](https://github.com/abysshopper/black-market-python-sdk/blob/main/docs/launch-guide.md#hmm-launch-configuration); **[P-helpers]** [Python helpers](https://github.com/abysshopper/black-market-python-sdk/blob/main/black_market_sdk/hmm.py).
- **[Protocol]** [HMM architecture, config, fee-owner controls and decay](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/docs/third-party-launch-hooks.md#hmm-pool-bound-templates).
- **[Collector]** [HMM fee collector](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/src/launch/hmm/HMMFeeCollectorV1.sol); **[Factory]** [canonical tail/constructor validation](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/src/launch/hmm/HMMFeeCollectorFactoryV1.sol); **[Hub]** [hub bounty/disposition/author accounting](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/src/launch/fees/v3/LaunchFeeHubV3.sol).
- **[Base]** [bound base oracle/treasury accounting](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-authoring/PoolBoundLaunchHookBaseV3.sol); **[Common-hook]** [manager callbacks and liquidity-operator seam](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-authoring/HMMLiquidityHookV1.sol).
- **[Fixed-review]** [HMM Fixed source review: no oracle](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-fixed/review.md); **[Dynamic-source]** [HMM Dynamic truncated-oracle composition](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-dynamic/HMMDynamicHook.sol).
- **[Manager]** [inventory book, controls, floors and claims](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-manager/src/HMMLiquidityManagerV1.sol); **[Manager-interface]** [hook-only/permissionless operation boundary](https://github.com/okjintao/black-market/blob/1ca98813f7aa72393116aac4d3d791e65d4fb635/contracts/hooks/hmm-manager/src/interfaces/IHMMLiquidityManagerV1.sol).
