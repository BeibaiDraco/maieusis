@AGENTS.md

# Claude Code project entry point

Read and follow `AGENTS.md` before operating this Maieusis project. The runtime Dataset Planner role
is defined in `.claude/agents/dataset-planner.md`; Maieusis invokes it only after creating an
isolated QuestionFamily branch and its dialogue service. Do not invoke that role manually as a
substitute for `maieusis run` or use it to execute the scientific analysis.
