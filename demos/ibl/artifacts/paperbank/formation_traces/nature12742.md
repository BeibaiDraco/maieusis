# Question-formation trace

- Review status: `ai_reviewed`

## Starting background

- Prefrontal cortex is associated with flexible, context-dependent behaviour, but the computations producing that flexibility remain unresolved; heterogeneous single-neuron responses make the underlying circuit contribution difficult to interpret.
- Prior work provides two relevant strands of precedent: recurrent-circuit models explain slow sensory integration and categorical choice, while population analyses show that mixed or complex single-neuron responses can preserve task-relevant information in distributed neural activity.
- Population-level neural dynamics can therefore provide a level of description at which competing mechanistic accounts of selection and integration make distinguishable predictions.

## Unresolved gap

It remained unclear whether context-dependent behaviour is produced by filtering irrelevant sensory information before it reaches PFC, by changing the relationship between sensory and choice representations within PFC, or by recurrent PFC dynamics that allow the same sensory inputs to be integrated differently across contexts. The observed complexity of individual responses did not by itself resolve these alternatives.

## Dataset opportunity

The task presents the same broad visual stimulus structure under different contextual instructions: motion is relevant in one context and colour in the other. Behavioural choices, sensory-evidence variation, and PFC recordings can be examined jointly as population responses and trajectories.

Because the contextual cue changes the behavioural relevance of otherwise available sensory inputs, the data provide within-task contrasts between relevant and irrelevant evidence. Population trajectories can then be compared with the distinct geometric and temporal predictions of early-filtering, selective-integration, and recurrent-dynamics accounts, while a task-matched recurrent model can be used to identify a mechanism consistent with the observed trajectories.

## Resulting question

What neural mechanism in prefrontal cortex enables context-dependent selection and integration of noisy sensory inputs toward a choice, and do population-level dynamics support early filtering or a recurrent within-PFC process in which selection and integration are coupled aspects of the same computation?

## Scientific consequence

Evidence for early filtering would imply that irrelevant inputs are excluded before entering the PFC decision process, whereas persistent representations of irrelevant inputs together with context-dependent trajectory deflections would favour selection within a recurrent population process. Different relationships among sensory, context, and choice dimensions would also discriminate alternative selective-integration mechanisms. A mechanism that reproduces the data in a trained recurrent network would provide a computational account of how the same input can guide choice in one context and be ignored in another, although it would remain a model-based mechanistic interpretation rather than a direct demonstration of every circuit implementation detail.

The question links flexible behaviour to an interpretable population-level mechanism rather than treating mixed single-neuron responses as isolated signals. Resolving it can clarify how PFC maintains separable representations while flexibly linking them to behaviour, and whether selection and evidence integration should be understood as separate operations or as aspects of one dynamical process. This makes the case valuable as a pattern for turning apparently confounded neural measurements into tests of competing mechanistic theories.
