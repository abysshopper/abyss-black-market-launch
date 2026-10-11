![Abyss](assets/abyss-ziggurat-v3-pale-text-1500x500.png)

# Abyss Black Market Launch

One conversational launch skill for **Node/TypeScript or Python**. Your agent walks
you through token design, quote pricing, liquidity, fees, opening buys, unsigned
planning, and—only when you authorize it—execution and recovery with the Abyss SDK.

## Install locally

Keep this as a separate checkout. Generate your agent's instructions here, then
point the skill at your SDK checkout or application workspace. You do not need
the Solidity repository just to use the SDK, and this avoids overwriting an
application's existing agent rules.

Requires Node 24+, pnpm, Python 3.10+ for the local signing helper, and Claude Code
or Codex. Install your chosen SDK using its README:
[Node](https://github.com/abysshopper/black-market-node-sdk)
· [Python](https://github.com/abysshopper/black-market-python-sdk).

```sh
git clone https://github.com/abysshopper/abyss-black-market-launch.git
cd abyss-black-market-launch
pnpm dlx rulesync@27.0.0 generate
claude
# Or start: codex
```

Paste this, replacing the workspace path:

```text
Use the abyss-token-launch skill with /absolute/path/to/my/sdk-or-app.
Ask whether I want Node or Python. Walk me through the supported token and
reward designs, markets, quotes, fees, and opening buys. Fetch and explain
quote pricing, derive exact liquidity near a $5,000 starting valuation,
and let me confirm the economics. Prepare an unsigned plan first.
If I choose to launch, prepare a locally reviewed execution runner and a
password-protected keystore command I can run in my own terminal.
Never ask for passwords or private keys in chat.
```

## What the skill does

1. Uses the selected SDK's current profiles, public APIs, and integer pricing
   helpers—not copied ABIs or addresses.
2. Asks for design choices in small groups and explains quote-price provenance,
   token allocation, rounded opening valuation, fee splits, buy protection, and gas.
3. Builds and proves the exact launch; unavailable or failed proof stops execution.
4. Presents the final economics for confirmation before signing. SDK example
   `--broadcast` commands skip this prompt, so the skill adds a pre-signature
   review gate to your runner rather than treating a prior dry-run as approval.
5. Executes only with authorization, records receipts, verifies activation and
   metadata, and resumes the original launch after interruption instead of relaunching.

## Signing in your own terminal

Prefer a **password-protected V3 keystore**, stored outside the repository with
owner-only permissions (`chmod 600`). Configure non-secret RPC/API settings in your
workspace; leave signer keys/passwords out of `.env`. Review the skill-generated
runner before supplying a signer: it receives the ability to spend your wallet.

From your workspace, use the helper's absolute path and your reviewed runner:

```sh
python /path/to/abyss-black-market-launch/scripts/run-launch.py \
  --sdk node --script examples/launch-my-token.ts \
  --keystore /path/to/wallet.json
```

For Python, activate the SDK's virtual environment and use `--sdk python` with a
`.py` runner. No mode flag means **unsigned dry-run**. After final review, add
`--broadcast`; after interruption, use `--resume "launch-results/<original-run>"`
instead. Both write modes require local confirmation and may spend real funds.

The helper prompts without echo for the password and passes signer settings only
to the local SDK process. Run it yourself, **not inside an agent-controlled terminal**.
`--private-key` replaces `--keystore` with hidden local key entry when necessary;
never paste the key into chat or put it in command arguments. Process environments
are not a vault: trust the runner and machine, and use a dedicated funded wallet.
Keep private recovery files; never commit or share them.

## Maintain the skill

Edit `.rulesync/rules/` and `.rulesync/skills/`, then regenerate with the pinned
command above. `AGENTS.md`, `CLAUDE.md`, `.agents/`, and `.claude/` are generated
locally and ignored, not separate maintained sources. To update an existing
checkout, run `git pull --ff-only` and regenerate. Run helper checks with
`python -m unittest discover -s tests`.
