# Paper — Mante, Sussillo, Shenoy & Newsome (2013), “Context-dependent computation by recurrent dynamics in prefrontal cortex”

- Review authority: `ai_reviewed` (automated unless expert)

## Question the system extracted

What population-level dynamical mechanism in prefrontal cortex implements context-dependent selection and integration of sensory evidence toward a choice, and does the observed population activity support existing models or require a different mechanism?

## The scientific contrast

Early or otherwise separately configured selection and integration models versus a recurrent population-dynamics mechanism in which context-dependent selection and evidence integration occur within the same prefrontal circuitry.

Competing explanations the paper weighed:
- Early selection: irrelevant sensory inputs are filtered before reaching PFC, while relevant inputs drive PFC responses.
- Context-dependent input representation: the direction of an input axis or its overlap with the choice axis changes across contexts.
- Context-dependent output representation: the choice axis changes across contexts while the sensory-input representation remains stable.
- Recurrent dynamical selection and integration: both inputs reach the network, context changes how recurrent dynamics route them, and relevant evidence moves the population toward the choice axis while irrelevant evidence produces a transient deflection.

What would tell them apart: The models make different predictions about population trajectories, the presence of irrelevant-input signals in PFC, the stability or context dependence of choice and input axes, and the relationship between the strength of sensory evidence and movement along the choice axis.

## Background and motivation

- Prefrontal cortex contributes to flexible, context-dependent behaviour, but the computations underlying this role remain largely unknown.
- Individual prefrontal neurons often generate complex responses that are difficult to interpret in terms of their contribution to behaviour.
- Context can determine which sensory information is relevant for a choice, while task-related variables that are mixed at the single-neuron level may be separable at the population level.
- Attention-related accounts propose that relevant information is selected by top-down modulation, and observations had led to the hypothesis that early selection could explain contextually sensitive behaviour.
- The task requires integration of sensory evidence toward a visuomotor decision, making the relationship between selection and integration a central computational issue.

## Why this question mattered

Resolving the mechanism would clarify how PFC supports flexible context-dependent behaviour and would determine whether sensory selection and evidence integration are separate operations or aspects of one dynamical process within the same circuitry. The proposed population-level account also provides a framework for interpreting otherwise complex single-neuron responses.

## What the dataset offered (as the paper used it)

Monkeys were cued to discriminate either the direction of motion or the colour of a random-dot display and report the choice with a saccade. Motion and colour evidence were presented in the same trials, with context determining which input was relevant. The model received independent motion, colour and contextual inputs and was trained to make the analogous binary choice.

- Population: Two macaque monkeys performing context-dependent perceptual discriminations; extracellular responses were recorded from neurons in and around the frontal eye field, an area of prefrontal cortex.
- Measurements: Choice, Motion evidence, Colour evidence, Context, Single-neuron and multi-unit responses, Population trajectories in state space, Neural-network outputs and dynamics

## Key citations used in forming the question

Public citation details are represented by the paper context; internal citation identifiers are omitted from this gallery.

## Open uncertainties (unmet evidence)

- The provided source spans do not establish whether the paper reuses a parent dataset or whether an earlier parent-dataset paper exists; dataset relation and parent-dataset status therefore remain unsupported.
- The provided spans do not state the paper's complete original research question verbatim; the question is reconstructed from the stated aim of discovering a selective-integration mechanism and must be span-verified.
- The parser packet marks methods and references as weak or undetected, so full methodological details and a complete literature-grounding account cannot be extracted from the provided spans.
- extraction windows returned different scientific descriptions; the first is retained pending review.
- The provided source spans do not include the paper's introduction or explicit original-question statement; verify the reconstructed scientific question against parser-owned introductory spans.
- Paper type and dataset relation, including whether this is a primary dataset release, secondary reuse, or purpose-built analysis, are not explicitly grounded by the provided spans.
- The paper's full literature gap, motivating claims, and nearest prior work require introductory and reference/citation-context spans.
- The scientific significance and novelty relative to prior work are only partially supported by the provided figure-caption spans and require verification against the main text.
- parser-owned text was usable, but the parse completeness report recorded limitations; review before authority raise.

## If this looks wrong

Adjust the source PDF or its parse, then re-run — the gate re-judges from the paper.
