# CTX Memory Provider (`ctx`) — DEPRECATED

> [!WARNING]
> **Deprecated.** This standalone plugin is no longer maintained. Its engine was
> contributed upstream to [GottZ/ctx](https://github.com/GottZ/ctx) and lives there as
> the memory layer of `ctx_checkpoint` (ctx v5.29.0 / plugin 0.6.0 and later).
>
> Use the catalog entry instead:
>
> ```bash
> hermes plugins install ctx_checkpoint
> hermes memory setup ctx_checkpoint
> ```
>
> Catalog page: <https://hermes-agent.nousresearch.com/docs/plugins/ctx_checkpoint> ·
> Full guide: <https://github.com/GottZ/ctx/blob/root/integrations/hermes/README.md>

Hermes Agent memory provider for [CTX](https://github.com/GottZ/ctx), a self-hosted
knowledge store: semantic recall before each turn, explicit `ctx_query` / `ctx_store` /
`ctx_search` / `ctx_get` tools, a mirror of `MEMORY.md` / `USER.md` writes, a transcript
checkpoint chain and fact extraction before compactions, and per-segment session digests.

Historical install path (retired, kept for reference) — this directory was installed as
`$HERMES_HOME/plugins/ctx/`:

```bash
hermes plugins install W4-NERF/hermes-ctx-plugin/plugin   # deprecated — do not use
hermes memory setup          # pick "ctx" — prompts for CTX_BASE_URL and CTX_KEY
hermes ctx status
```

Optional settings lived in `$HERMES_HOME/ctx.json`. Full documentation (configuration
reference, CLI, internals): <https://github.com/W4-NERF/hermes-ctx-plugin#readme>.

License: MPL-2.0. `checkpoint.py` is a modified port of GottZ/ctx
`integrations/hermes/plugin/ctx_checkpoint` (© Jan-Stefan Janetzky, MPL-2.0).
