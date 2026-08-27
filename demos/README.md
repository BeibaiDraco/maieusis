# What is in this folder

Four complete runs of Maieusis over three real datasets. Nothing here is a summary written for
publication: every page is the run's own record, including the questions it stopped.

**→ [Every question in one table](ALL_QUESTIONS.md)** — start here. One row per question, what
happened to it, and a link into the run that produced it.

Then, if you want one run in depth:

| Run | What it was pointed at |
| --- | --- |
| [`ibl/`](ibl/README.md) | Mouse decision-making recordings, told to think about noise correlations |
| [`ibl-open/`](ibl-open/README.md) | The same recordings, told nothing — it chose its own scope |
| [`nlb/`](nlb/README.md) | A monkey reaching around obstacles |
| [`climate/`](climate/README.md) | Reanalysis of the Arctic polar stratosphere |

Inside each run, `artifacts/` holds the full chain: the record extracted from each paper it read,
the patterns drawn from those papers, every question proposed, what the planner found when it opened
the data, and the reviewed outcome for each. [`PAPER_SOURCES.md`](PAPER_SOURCES.md) lists the
literature the runs drew on.

Source PDFs, raw model payloads, credentials, and private runtime state are not published here.
