# Paper — Mante, V., Sussillo, D., Shenoy, K. V. & Newsome, W. T. (2013). Context-dependent computation by recurrent dynamics in prefrontal cortex.

- Review authority: `ai_reviewed` (automated unless expert)

## Question the system extracted

What population-level neural mechanism implements context-dependent selection and integration of sensory evidence in prefrontal cortex, and can a dynamical model reproduce the observed physiological responses?

## The scientific contrast

Whether context-dependent selection occurs through early filtering or other static input transformations, versus selection and integration being implemented by recurrent population dynamics within the same prefrontal circuitry.

Competing explanations the paper weighed:
- Early selection: irrelevant sensory inputs are filtered out before reaching PFC, so only the contextually relevant input drives PFC responses.
- Context-dependent input or output geometry: context changes the direction of an input or the choice axis, altering how sensory evidence projects onto choice-related activity.
- Within-PFC recurrent selection and integration: both sensory inputs reach PFC, and recurrent population dynamics selectively integrate the contextually relevant input while maintaining decision-related activity.

What would tell them apart: The alternatives predict different population trajectories and relationships among the choice, motion, colour, and context axes. In particular, early filtering predicts that irrelevant inputs should not produce PFC population responses, whereas within-PFC selection predicts context-dependent deflections and curved trajectories produced by both relevant and irrelevant inputs.

## Background and motivation

- Prefrontal cortex has a fundamental role in flexible, context-dependent behaviour, but the computations underlying this role remain largely unknown.
- Individual prefrontal neurons often generate complex responses whose contribution to behaviour is difficult to understand.
- Context can make identical sensory inputs produce different behavioural responses because representations of inputs and the upcoming choice are separable at the population level but deeply entwined at the single-neuron level.
- Attention-related work suggests that relevant information may be selected by top-down modulation of neural activity, but the mechanisms underlying such selection and its relation to evidence integration remain unresolved.
- The observed single-neuron responses appear to represent several task-related signals simultaneously, including the upcoming choice, context, and the strength of motion and colour evidence.
- Current models of context-dependent selection and integration make distinguishable predictions about how sensory inputs should affect population activity.

## Why this question mattered

Answering the question identifies a mechanism linking context, sensory selection, evidence integration, and choice within PFC. It also provides a framework for understanding why single-neuron responses are complex and for determining whether selection and integration are separate operations or aspects of one population-level dynamical process.

## What the dataset offered (as the paper used it)

Monkeys received a contextual cue instructing them to discriminate either the motion direction or the prevalent colour of a random-dot display and reported the choice with a saccade to one of two visual targets. Motion and colour coherence were varied to manipulate evidence strength.

- Population: Two macaque monkeys trained to perform context-dependent visual discriminations.
- Measurements: Behavioral choices and psychophysical performance, Extracellular responses from neurons in and around the frontal eye field, 388 single-unit and 1,014 multi-unit responses, Population activity represented as trajectories in neural state space, Choice-, motion-, colour-, and context-related population axes

## Key citations used in forming the question

Public citation details are represented by the paper context; internal citation identifiers are omitted from this gallery.
## Open uncertainties (unmet evidence)

- The provided source spans do not identify a parent dataset paper, dataset release, or reuse relationship; verify whether the paper should be classified solely as a purpose-built primary experiment and whether any parent-dataset relation exists.
- extraction windows returned different scientific descriptions; the first is retained pending review.
- The provided parser spans do not support a complete extraction of the paper's original scientific question; provide introduction or abstract spans containing the explicit question or study aim.
- The provided parser spans do not establish the full motivating literature claims and unresolved theoretical tension; provide background and discussion spans.
- The paper type and dataset relation, including whether this is a primary dataset release, secondary reuse, or reanalysis and whether a parent dataset exists, cannot be grounded from the provided spans.
- The population, task description, and measurement details are only partially supported by the provided spans; provide methods or main-text dataset-description spans.
- A formation trace cannot be produced because the provided spans do not contain a source-backed sequence from literature background and dataset opportunity to the resulting question.
- parser-owned text was usable, but the parse completeness report recorded limitations; review before authority raise.

## If this looks wrong

Adjust the source PDF or its parse, then re-run — the gate re-judges from the paper.
