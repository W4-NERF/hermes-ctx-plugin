# CTX Memory Provider (`ctx`)

Hermes Agent memory provider for [CTX](https://github.com/GottZ/ctx), a self-hosted
knowledge store: semantic recall before each turn, explicit `ctx_query` / `ctx_store` /
`ctx_search` / `ctx_get` tools, a mirror of `MEMORY.md` / `USER.md` writes, a transcript
checkpoint chain and fact extraction before compactions, and per-segment session digests.

This directory is installed as `$HERMES_HOME/plugins/ctx/`:

```bash
hermes plugins install W4-NERF/hermes-ctx-plugin/plugin
hermes memory setup          # pick "ctx" — prompts for CTX_BASE_URL and CTX_KEY
hermes ctx status
```

Optional settings live in `$HERMES_HOME/ctx.json`. Full documentation (configuration
reference, CLI, internals): <https://github.com/W4-NERF/hermes-ctx-plugin#readme>.

License: MPL-2.0. `checkpoint.py` is a modified port of GottZ/ctx
`integrations/hermes/plugin/ctx_checkpoint` (© Jan-Stefan Janetzky, MPL-2.0).
