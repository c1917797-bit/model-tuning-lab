# Forward Tests

These cases validate the Humanize-first workflow against raw parsed sources.

## Cases

- `tidar-paper-deck/`: raw paper XML + extracted figures. Expected mode: `Deck`.
- `rtx-spark-agent-pc-report/`: raw web evidence package. Expected mode: `Report`.

Each case keeps only source artifacts and a minimal prompt. The agent must not rely on any prewritten brief.
