# Paper — Context-dependent computation by recurrent dynamics in prefrontal cortex — Valerio Mante, David Sussillo, Krishna V. Shenoy, and William T. Newsome

- Review authority: `ai_reviewed` (automated unless expert)

## Question the system extracted

What neural mechanism in prefrontal cortex enables context-dependent selection and integration of noisy sensory inputs toward a choice, and can the mechanism account for the observed population dynamics when the same inputs are relevant in one context and irrelevant in another?

## The scientific contrast

Whether context-dependent selection occurs through early filtering or through recurrent, within-PFC dynamics that allow the same sensory inputs to be integrated differently across contexts.

Competing explanations the paper weighed:
- Early selection: irrelevant inputs are filtered out before reaching PFC, whereas relevant inputs drive PFC responses.
- Context-dependent input selection through a changing angle between the choice and sensory-input axes, while the choice axis remains fixed.
- Context-dependent output selection in which the choice axis changes between contexts while the sensory-input representation remains stable.
- A recurrent-dynamics mechanism in which both inputs reach PFC, context-dependent dynamics determine their effects, and selection and integration are aspects of one population process.

What would tell them apart: The alternatives make different predictions for the geometry and temporal trajectories of population responses. Early filtering predicts little or no PFC representation of irrelevant inputs; changing-axis models predict altered relationships among choice and sensory axes; the recurrent account predicts context-dependent deflections of population trajectories away from a stable choice axis, followed by integration toward the choice.

## Background and motivation

- Prefrontal cortex is thought to have a fundamental role in flexible, context-dependent behaviour, but the computations underlying this role remain largely unknown.
- Individual prefrontal neurons often represent several task-related signals at once, including the upcoming choice, context, and sensory evidence, making their contribution to behaviour difficult to understand at the single-neuron level.
- Context can cause identical sensory stimuli to produce different behavioural responses, while the representations of inputs and upcoming choice can be separable at the population level even though they are deeply entwined at the single-neuron level.
- Attention-related work has suggested that relevant information is selected through top-down modulation of neural activity, including modulation of firing rates or response synchrony, but the mechanism underlying selection and its relation to evidence integration remains unresolved.
- The task was designed to test the hypothesis that relevant sensory information is selected during context-dependent behaviour and to determine how selection and integration are implemented in PFC.

## Why this question mattered

Resolving the mechanism would clarify how PFC supports flexible context-dependent behaviour, explain why single neurons appear to carry multiple task-related signals, and distinguish whether selection and integration are separate operations or aspects of one dynamical process within the same circuits.

## What the dataset offered (as the paper used it)

On each trial, a contextual cue instructed the monkey to discriminate either the direction of motion or the colour of a random-dot display and report the choice with a saccade to one of two visual targets. The same visual stimuli could therefore be interpreted under different contexts.

- Population: Two trained macaque monkeys performing context-dependent perceptual discriminations.
- Measurements: choice, motion and colour evidence strength and direction, context, single-unit and multi-unit neural responses, population trajectories along choice, motion, colour, and context axes, modelled recurrent dynamics

## Key citations used in forming the question

Public citation details are represented by the paper context; internal citation identifiers are omitted from this gallery.

## Open uncertainties (unmet evidence)

- formation_trace evidence is inconsistent (e.g. binding source_span_ids outside evidence_span_ids); kept DRAFT.
- The provided source spans do not identify a parent dataset paper or establish whether this work is a secondary reuse, primary dataset release, or reuse of a named earlier dataset; verify the dataset relation from the complete paper record.
- The provided spans do not contain a complete explicit statement of the paper's original motivating background or abstract; verify the reconstructed background and question against the introduction or abstract.
- The provided spans do not establish the public/private access status of the source data beyond stating that source data are available online.
- extraction windows returned different scientific descriptions; the first is retained pending review.
- Blocking: the supplied parser spans are concentrated in later figure captions and do not state the paper's original scientific question, central contrast, or complete competing explanations.
- Blocking: the supplied spans do not support the paper's motivating literature claims, nearest prior work, or a precise unresolved theoretical tension.
- Blocking: paper type, dataset relation, parent-dataset status, and whether the data were newly collected or reused cannot be grounded by the supplied parser spans.
- Blocking: a source-backed formation_trace cannot be produced because the supplied spans do not provide a connected background-claim-to-question rationale.
- Blocking: the supplied spans do not fully support the population details, task protocol, or measurement provenance beyond the PFC population-response and model-comparison descriptions included above.
- parser-owned text was usable, but the parse completeness report recorded limitations; review before authority raise.

## If this looks wrong

Adjust the source PDF or its parse, then re-run — the gate re-judges from the paper.
