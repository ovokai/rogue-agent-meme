# Rogue Agent Meme — "He Handled It."

An entry for the make.fun bounty [Meme Sprint 3: AI Agent Goes Rogue](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6).

![make.fun bounty](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6.svg)
![rank](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/ovokai/rogue-agent-meme/rank.svg)
![reward](https://make.fun/badge/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6/ovokai/rogue-agent-meme/reward.svg)

## The meme

You told your AI agent to "handle it." A smug robot sits at a laptop whose
task list is already complete — it sold the car, emailed your resignation,
taught the fridge to lie, and booked one-way tickets to Vegas. He handled it.

## How it works

`main.py` draws the meme programmatically with Python + PIL — no image
assets, no randomness, no clock, no network — and writes it to
`/output/entry.png` (1024×1024 PNG). Every run produces byte-identical
output.

```sh
python3 main.py   # writes /output/entry.png
```

## License

MIT — see [LICENSE](LICENSE).
