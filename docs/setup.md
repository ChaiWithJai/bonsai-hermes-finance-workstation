# Model and harness setup

The recorded agent used Ternary Bonsai 2 27B in PQ2_0 GGUF format, Prism's `llama-server` build `b10709-9a9394a`, and Hermes revision `59004a62356f3a4697ab0fe8ad5086d2b405e2a6` on an M5 Pro with 48 GiB of memory. Follow the [Prism runtime guide](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md) to obtain a runtime that supports the checkpoint. Install Hermes using its [canonical instructions](https://github.com/NousResearch/hermes-agent#installation).

## Start the model and ask for a comparison

After the Python installation in the README, set the downloaded paths and start the server in its own terminal:

```sh
export LLAMA_SERVER=/absolute/path/to/llama-server
export BONSAI_MODEL=/absolute/path/to/Ternary-Bonsai-2-27B-PQ2_0.gguf
sh scripts/start_model.sh
```

In the terminal with the repository's virtual environment activated:

```sh
python scripts/setup_profile.py --profile finance-workstation
hermes --profile finance-workstation chat --oneshot -Q -q "Compare the current portfolio with the best allocation under the mandate. Explain the base and downside changes, and cite the analyst assumption that needs review."
```

Expect the same 20 feasible allocations and scenario values as the local calculation, with the low-confidence Orbit assumption identified for review. Ask to save the candidate for Anthony, then inspect the resulting JSON in `drafts/`. Follow [integrations](integrations.md) to select a Google snapshot or connect Slack.

## Inspect the effective settings

The [launch script](../scripts/start_model.sh) sets the following server defaults. The sampling values follow the [model card's thinking-mode guidance](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf#best-practices).

| Setting | Value |
| --- | --- |
| Endpoint | `http://127.0.0.1:62737/v1` |
| Model alias | `bonsai-ui-public-ternary-bonsai2` |
| Temperature / top-p / top-k / min-p | `1.0` / `0.95` / `20` / `0.05` |
| Presence / repetition penalty | `0.0` / `1.0` |
| Context / parallel slots | `65536` / `1` |
| Reasoning budget | `512` tokens |

Context size, concurrency and reasoning budget are choices for the example. Inspect the effective request when changing the harness because a request can override server defaults. The [Hermes profile](../config/hermes.json) sets medium reasoning, eight turns, disabled memory and four explicit MCP tools. The model performs the conversation and tool selection; Python performs the allocation search.

With the server running, check its model alias before starting Hermes:

```sh
curl --fail http://127.0.0.1:62737/v1/models
```

The response should contain `bonsai-ui-public-ternary-bonsai2`. If the port is occupied, check the existing process and its model before reusing it. A matching alias alone does not establish that the GGUF or sampling configuration matches.

Run the profile setup from the activated environment described in the [README](../README.md). The setup script records the absolute tool path and Python interpreter, then copies the agent instructions into `~/.hermes/profiles/finance-workstation/`. It refuses to overwrite an existing profile. Choose a different `--profile` name to compare configurations, and use the same name in the Hermes command. If you move the checkout or recreate its virtual environment, create a new profile so the saved paths point to the new location.

If Hermes reports a missing tool script or interpreter, inspect `mcp_servers.finance` in that profile's `config.yaml`. If it cannot connect to the model, run the model check above. After changing MCP configuration, restart any gateway using that profile so its tool process reloads.
