# Detailed question-formation patterns

These pages expand the compact PatternBank summary for scientific reading. They describe reviewed question-forming moves; they do not establish novelty, dataset feasibility, or a scientific result.

## Pattern 001: Use population structure to discriminate computational accounts

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Collective measurements exhibit heterogeneity, correlations, dimensional structure, trajectories, or subspaces whose computational meaning is unresolved.
- The uncertainty may arise because component-level responses are difficult to interpret or because competing population-level theories predict different geometries or dynamics.
- Prior theory supplies alternative accounts linking population structure to information, readout capacity, robustness, binding, generalization, selection, or behavior, but available observations have not yet distinguished them.

### Unresolved tension

Observed population structure may be dismissed as disorder, nuisance variation, or limited sampling, interpreted as a collective computational resource, or attributed to one of several competing geometric or dynamical constraints. The unresolved tension is which interpretation makes discriminating predictions about structure under controlled variation and, where available, behavior.

### Dataset cues

- Measurements from many components across repeated conditions
- Independent variation of multiple task-relevant factors, input statistics, effective dimensionality, identities, positions, or contexts
- Contrasts or perturbations that separate candidate explanations of population geometry or dynamics
- Behavioral outcomes, errors, or transfer conditions that can test functional interpretations
- Time-resolved measurements when candidate accounts make dynamical predictions

### Question-forming move

Elevate collective structure to the level of explanation and turn it into a comparison among explicit alternatives. Depending on the starting tension, test whether heterogeneous activity preserves information, expands available readouts, or forms behavior-linked trajectories; or test which candidate geometry, dynamical account, eigenspectrum-generating constraint, or input-derived explanation best matches changes induced by controlled conditions. Require the favored account to explain observations beyond simpler component-wise, descriptive, or competing population-level alternatives.

### Scientific payoff

This move converts ambiguous population structure into a discriminating test of computational organization. It can reveal when opaque heterogeneity has collective function and when one geometric or dynamical principle better explains information, generalization, binding, robustness, selection, or behavior without assuming specialized roles for every component.

### What different outcomes would mean

- Positive: If a prespecified population account uniquely predicts the observed information, geometry, dynamics, responses to controlled variation, or behavioral patterns better than relevant alternatives, it would support that account as an organizing explanation of collective computation.
- Negative: If population structure provides no advantage or behavioral relevance beyond simpler representations, or if candidate geometries, dynamics, and generating constraints fail to make distinguishable or supported predictions, the proposed collective account would be weakened. The findings would instead favor a simpler explanation, an alternative population account, task-irrelevant variability, or the conclusion that the theoretical comparison remains unresolved.

### Common failure modes

- Treating dimensionality reduction, a fitted geometry, or an eigenspectrum as evidence of mechanism without discriminating predictions
- Equating decodability with functional use
- Comparing candidate geometries or dynamical accounts without identifying the distinct observations each predicts
- Testing only a preferred intermediate or complex geometry while omitting simpler and theoretically relevant alternatives
- Attributing population structure to an organizing constraint without separating it from input statistics, sampling limitations, or measurement noise
- Ignoring recording scale, trial count, repeated-observation reliability, or simultaneity limitations
- Selecting a geometry or dynamical description after inspecting the same outcomes used to support it
- Transferring a mathematical or mechanistic interpretation without checking the assumptions under which its predictions follow
- Failing to connect population-level structure to controlled condition changes or behavior when such validation is available

### Details that should not be transferred

- Specific cortical regions, species, and task factors used in the source studies
- Particular definitions of mixed selectivity, task axes, semi-orthogonality, binding, abstraction, or generalization
- Specific classifier, dimensionality, eigenspectrum, smoothness, or recurrent-network implementations
- Source-specific assumptions about stimulus spaces, differentiable mappings, recording simultaneity, and population coverage
- Source-specific correct-versus-error, filtering, stimulus-statistics, and risky-choice contrasts

### Source PaperCases and formation traces

- Source 1: [Rigotti, Mattia; Barak, Omri; Warden, Melissa R.; Wang, Xiao-Jing; Daw, Nathaniel D.; Miller, Earl K.; Fusi, Stefano. “The importance of mixed selectivity in complex cognitive tasks.” Nature, 2013.](papers/nature12160.md) · [Question-formation trace](formation_traces/nature12160.md)
- Source 2: [Mante, V., Sussillo, D., Shenoy, K. V. &amp; Newsome, W. T. (2013). Context-dependent computation by recurrent dynamics in prefrontal cortex.](papers/nature12742.md) · [Question-formation trace](formation_traces/nature12742.md)
- Source 3: [Stringer, Carsen; Pachitariu, Marius; Steinmetz, Nicholas; Carandini, Matteo; Harris, Kenneth D. (2019), “High-dimensional geometry of population responses in visual cortex,” Nature.](papers/s41586-019-1346-5.md) · [Question-formation trace](formation_traces/s41586-019-1346-5.md)
- Source 4: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. “Semi-orthogonal subspaces for value mediate a binding and generalization trade-off.” Nature Neuroscience, 2024. DOI: 10.1038/s41593-024-01758-5](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)

## Pattern 002: Replace an aggregate-statistic claim with a structural-alignment test

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A broad literature claim links the magnitude of an aggregate statistic to performance or information.
- Contrasting findings show that large changes in the statistic do not always produce the expected functional consequence.
- Theory suggests that alignment, configuration, or task relevance may matter more than overall magnitude.

### Unresolved tension

The same aggregate level can conceal components with different functional consequences, making a magnitude-only interpretation incompatible with observed performance or decoding results.

### Dataset cues

- Repeated population measurements that permit estimation of covariance or latent structure
- Independent estimates of signal-relevant, task-relevant, or behaviorally used directions
- Behavioral, decoding, perturbational, or information-based outcomes
- Controlled models or comparisons that hold upstream signal content approximately fixed

### Question-forming move

Decompose the aggregate phenomenon into structurally distinct components and ask whether functional consequences depend on alignment with signal- or task-relevant dimensions rather than on global magnitude. Where possible, connect analytic predictions to observable decoding, behavior, or perturbation effects.

### Scientific payoff

The pattern replaces a coarse association with a mechanistic criterion for identifying which part of a measured population statistic matters and why.

### What different outcomes would mean

- Positive: Selective effects of aligned or task-relevant structure would explain why aggregate changes can be behaviorally inconsistent and would identify a candidate circuit or coding dimension.
- Negative: If alignment or configuration adds no explanatory value and global magnitude consistently predicts outcomes, the simpler aggregate account remains viable and the proposed structural mechanism is weakened.

### Common failure modes

- Inferring alignment from the same data without out-of-sample validation
- Treating principal components as uniquely mechanistic axes
- Changing signal strength or tuning while claiming only covariance was manipulated
- Assuming a statistically detectable component is behaviorally used
- Generalizing from an idealized information measure to unrelated tasks

### Details that should not be transferred

- Tuning-curve derivative alignment and Fisher-information assumptions
- A first principal component as the operational variability axis
- Specific recurrent excitatory-inhibitory models
- Particular visual tasks, species, or perturbation methods

### Source PaperCases and formation traces

- Source 1: [Moreno-Bote et al. (2014), Information-limiting correlations](papers/nn-3807.md) · [Question-formation trace](formation_traces/nn-3807.md)
- Source 2: [The structure of correlated variability reflects task-relevant information in sensory neurons](papers/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md) · [Question-formation trace](formation_traces/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md)

## Pattern 003: Translate a mechanistic theory into a global state-space signature

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A mechanistic theory predicts a global organization of coordinated activity, such as a manifold, subspace, spectrum, trajectory, or selective mapping between populations.
- Earlier measurements or component-wise analyses could not resolve that organization.
- Alternative mechanisms may produce similar local responses, so detecting structure alone is not fully discriminating.
- The comparison axis used to distinguish mechanisms may involve altered external input, context, or stimulus structure, or may instead contrast within-population organization with across-population or across-area organization.

### Unresolved tension

A theory is plausible at the level of individual responses or pairwise relationships but remains untested at the population scale where its defining topology, geometry, spectrum, subspace, or selective cross-population mapping resides.

### Dataset cues

- Sufficiently large simultaneous or coordinated population measurements
- Repeated observations supporting reliable state-space or cross-population structure estimation
- Discriminating comparisons that either alter external input, context, or stimulus structure or contrast within-population organization with across-population or across-area organization
- A theory-derived prediction about topology, dimensionality, invariance, mapping, or selective subspace structure

### Question-forming move

Express the mechanism as a population-level structural prediction, measure that structure at the relevant scale, and test its mapping, invariance, or selectivity using comparisons chosen to separate the focal mechanism from plausible alternatives. Depending on the theory, those comparisons may span external conditions or contrast within-population with across-population organization.

### Scientific payoff

This pattern turns an abstract model into a falsifiable population-level signature and clarifies which observations constrain mechanism rather than merely describe activity.

### What different outcomes would mean

- Positive: Recovery of the predicted structure together with its expected mapping, invariance, or selectivity across the relevant comparison would strengthen the mechanistic account and constrain how population organization relates to external inputs, internal organization, or interactions between systems.
- Negative: Absent, unstable, nonselective, or incorrectly mapped structure would weaken the proposed mechanism and preserve alternatives based on different organizing principles, broadly distributed interactions, condition-specific geometry, or insufficiently resolved population structure.

### Common failure modes

- Declaring mechanism proven from structural detection alone
- Testing a topology, geometry, or subspace selected after viewing the data
- Ignoring sample-size and noise sensitivity of structural estimators
- Confusing low-dimensional visualization with intrinsic dimensionality
- Using conditions or within-versus-across comparisons that do not actually distinguish the competing mechanisms

### Details that should not be transferred

- A torus as the predicted topology for a particular spatial code
- Specific power-law and smoothness assumptions for visual representations
- Specific cortical communication or value-coding subspaces
- Particular topology, eigenspectrum, dimensionality, or predictive-subspace estimators

### Source PaperCases and formation traces

- Source 1: [Gardner et al., “Toroidal topology of population activity in grid cells,” Nature, 2022.](papers/s41586-021-04268-7.md) · [Question-formation trace](formation_traces/s41586-021-04268-7.md)
- Source 2: [Stringer, Carsen; Pachitariu, Marius; Steinmetz, Nicholas; Carandini, Matteo; Harris, Kenneth D. (2019), “High-dimensional geometry of population responses in visual cortex,” Nature.](papers/s41586-019-1346-5.md) · [Question-formation trace](formation_traces/s41586-019-1346-5.md)
- Source 3: [Semedo et al., 2019, “Cortical Areas Interact through a Communication Subspace”](papers/1-s2-0-s0896627319300534-main.md) · [Question-formation trace](formation_traces/1-s2-0-s0896627319300534-main.md)
- Source 4: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. “Semi-orthogonal subspaces for value mediate a binding and generalization trade-off.” Nature Neuroscience, 2024. DOI: 10.1038/s41593-024-01758-5](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)

## Pattern 004: Use coordinated common-design measurements to resolve the organization of cross-system signals

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Prior evidence establishes that a signal or interaction exists across relevant units or systems, but its population- or system-level organization remains unresolved.
- Earlier studies or analyses use incomparable sampling or lower-level summaries that cannot distinguish broad involvement from selective organization.
- Competing accounts predict that the relevant signal or interaction is broadly expressed across available units or dimensions versus concentrated in particular units, stages, or subspaces.

### Unresolved tension

Observed signals or interactions may reflect broad participation of the measured system or selective organization within it, but differences in sampling, conditions, or analytical scale leave these alternatives underdetermined.

### Dataset cues

- Coordinated measurements from the relevant units, populations, regions, or systems under a common design
- Repeated or matched observations that support comparisons of shared variation or interaction structure
- Coverage at the population or system scale needed to distinguish broad from selective organization
- An internal reference, comparator, or alternative measurement that helps determine whether the inferred organization is specific to the interaction of interest

### Question-forming move

Use coordinated common-design measurements to compare broad and selective accounts of where a signal is expressed or which activity dimensions participate in an interaction, then evaluate the inferred structure against an internal reference or supported alternative explanation.

### Scientific payoff

This move elevates evidence from isolated signals or pairwise relationships to a discriminating account of system-level organization, clarifying whether apparent breadth or selectivity reflects the phenomenon of interest, limited sampling, or structure shared with a reference condition.

### What different outcomes would mean

- Positive: A reproducible distinction between broad and selective organization, relative to the available reference, would favor the account matching that structure and clarify how earlier partial or lower-level observations fit together.
- Negative: If the alternatives cannot be distinguished, the inferred structure is unstable, or it resembles the reference comparison, claims of specifically broad or selective organization would be weakened and the existing evidence would remain compatible with more generic shared activity or sampling-dependent explanations.

### Common failure modes

- Treating the measured coverage as complete or uniformly informative
- Comparing units, populations, or systems without accounting for differences in measurement quality or dimensionality
- Inferring mechanistic transmission or anatomical causation from predictive association alone
- Using a reference comparison that does not address the alternative explanation it is meant to exclude
- Equating a compact or widespread statistical representation with a uniquely identified biological mechanism

### Details that should not be transferred

- The brain-wide public-dataset setting, common anatomical registration, multimodal coverage, and literature-wide localization dispute in the first source
- The first source's behavioral, movement, reward, trial-history, and embodied controls, including its task-specific low-evidence conditions
- The two-area source-target design, repeated visual stimuli, trial-to-trial spike-count fluctuations, and held-out within-area comparator in the second source
- The particular species, sensory tasks, anatomical systems, recording modalities, and directional or dimensional analysis methods used by either source
- Claims about complete anatomical coverage, synaptic direction, or causal transmission that are not established by the observational measurements

### Source PaperCases and formation traces

- Source 1: [Brain-wide representations of prior information in mouse decision-making](papers/ibl-s41586-025-09226-1.md) · [Question-formation trace](formation_traces/ibl-s41586-025-09226-1.md)
- Source 2: [Semedo et al., 2019, “Cortical Areas Interact through a Communication Subspace”](papers/1-s2-0-s0896627319300534-main.md) · [Question-formation trace](formation_traces/1-s2-0-s0896627319300534-main.md)

## Pattern 005: Use controlled within-task contrasts to test latent population-dynamics mechanisms

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Competing mechanistic accounts can explain similar behavior while predicting different population dynamics, such as one versus sequential processing regimes or early filtering versus context-dependent selection within the measured population.
- Complex, heterogeneous time-varying responses make isolated-unit or predefined single-trajectory interpretations inadequate.
- The task contains a controlled within-task contrast that changes either when an input should matter or which concurrently available input should matter.

### Unresolved tension

Similar behavioral outcomes can arise from different latent dynamics, leaving it unclear whether population activity reflects a mechanistically meaningful change in input processing or only a descriptive trajectory that does not distinguish the competing accounts.

### Dataset cues

- Time-resolved measurements that support population-level trajectory or task-related-dimension analysis; simultaneous recordings may be required for trial-resolved transition claims, whereas pooled recordings can support condition-level population contrasts.
- Timing-based cue from source paper 1: precisely timed, variable sensory inputs and trial-level choices permit comparison of input influence before versus after an inferred within-trial transition.
- Context-based cue from source paper 2: the same concurrently available sensory dimensions are paired with different contextual rules, permitting comparison of relevant and irrelevant input representations across conditions.
- Behavioral or physiological observations that provide an external criterion for comparing the alternative dynamical mechanisms.

### Question-forming move

Characterize time-varying population activity without assuming that one candidate mechanism is correct, then use a controlled within-task contrast to test whether the observed dynamics and their relation to behavior change as competing accounts predict. The contrast may be timing-based, testing input influence around an inferred transition, or context-based, testing how the relevance of concurrently available inputs alters their population-level representation or integration.

### Scientific payoff

This pattern connects population dynamics to an experimentally controlled criterion and distinguishes mechanisms that can produce similar choices but differ in when inputs influence behavior, which inputs are selected or integrated, or where that selection occurs. Timing-based evidence can evaluate sequential versus single-regime accounts, whereas context-based evidence can evaluate early-filtering versus within-population selection accounts.

### What different outcomes would mean

- Positive: A reproducible correspondence between population dynamics and the controlled contrast would support the mechanism making that prediction: for a timing-based contrast, a transition accompanied by the predicted change in later input sensitivity would support sequential regimes; for a context-based contrast, predicted context-dependent effects of relevant and irrelevant inputs would support the corresponding selection-and-integration account.
- Negative: Failure of population dynamics or behavior to vary as predicted by the controlled contrast would weaken the proposed mechanism without presuming a common temporal transition across cases. Stable input influence across an inferred transition could favor a single-regime account or undermine the transition's behavioral interpretation, while absent or mismatched context effects could favor an alternative filtering or geometrical account or leave the mechanism unresolved.

### Common failure modes

- Overfitting population trajectories, task-related dimensions, or regime transitions with an overly flexible model.
- Using the same observations to define a dynamical feature and validate its interpretation without safeguards.
- Ignoring sensory, motor, timing, contextual, or choice-related covariates.
- Assuming a model-derived state change or population axis is automatically a cognitive mechanism.
- Treating a context-dependent relevance contrast as evidence for a within-trial temporal regime switch.
- Treating pooled, separately recorded units as if they supported the same trial-resolved claims as simultaneous population recordings.
- Using timing or contextual manipulations that do not sufficiently distinguish the competing mechanistic predictions.
- Treating a fitted dynamical model as a replacement for correspondence with observed physiological and behavioral patterns.

### Details that should not be transferred

- The timing-based transition interpretation depends on the source-specific auditory pulse-counting task, precisely timed evidence sequences, simultaneous recordings, and a choice readout that supports pre-versus-post-transition sensitivity tests.
- The context-based selection interpretation depends on the source-specific motion-versus-colour task and contextual rules governing which concurrently available sensory dimension is relevant.
- Source-specific frontal, striatal, prefrontal, or frontal-eye-field recordings cannot establish the same dynamics in other regions, species, or task designs.
- Particular deep-learning flow-field and recurrent-network models are source-specific implementations rather than required components of the shared move.
- Trial-resolved commitment and context-dependent relevance are distinct source-specific interpretations and should not be treated as interchangeable.
- Most units in the context-based source were recorded separately, and one colour-related comparison was equivocal for one animal, limiting transfer of simultaneous or uniformly supported population claims.

### Source PaperCases and formation traces

- Source 1: [Transitions in dynamical regime and neural mode during perceptual decisions](papers/s41586-025-09528-4-1.md) · [Question-formation trace](formation_traces/s41586-025-09528-4-1.md)
- Source 2: [Mante, V., Sussillo, D., Shenoy, K. V. &amp; Newsome, W. T. (2013). Context-dependent computation by recurrent dynamics in prefrontal cortex.](papers/nature12742.md) · [Question-formation trace](formation_traces/nature12742.md)

## Pattern 006: Turn ambiguous population structure into discriminating task contrasts and functional predictions

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Population activity contains heterogeneous, mixed, or geometrically structured responses whose computational role is unresolved.
- Competing accounts attribute the observed activity to different mechanisms, such as upstream filtering versus within-population selection, specialized representations versus distributed computational capacity, or separation versus reuse of information.
- A dataset varies task-relevant inputs, identities, relations, or contextual rules and includes neural population measurements together with behavioral outcomes.
- Descriptive decoding or single-neuron selectivity alone cannot distinguish the competing accounts.

### Unresolved tension

The same complex population activity may be incidental or reducible to a simpler mechanism, or it may be structured in a way that performs a task-relevant computation. The shared unresolved issue is not whether one particular intermediate geometry exists, but whether population organization makes discriminating neural and behavioral predictions beyond simpler filtering, specialized-code, or task-irrelevant alternatives.

### Dataset cues

- Independent or contextual variation of multiple task-relevant factors within a common paradigm
- Population measurements across conditions that place different computational demands on the same inputs
- Behavioral outcomes, including choices, characteristic errors, or correct-versus-error trials, that can constrain functional interpretation
- A basis for comparing population-level accounts with simpler alternatives or with a constrained mechanistic model

### Question-forming move

Use within-task contrasts to identify predictions that differ across candidate accounts of population computation, then test whether population organization explains both condition-dependent neural structure and task-relevant behavioral outcomes. The concrete contrast may concern preserved identity alongside reuse, upstream filtering versus context-dependent integration, or specialized coding versus distributed representational capacity; an intermediate geometry, cross-condition transfer, or characteristic error pattern should be required only when the source-specific theory supports it. When a mechanistic model is available, ask whether it jointly reproduces the relevant behavioral and physiological patterns rather than treating model fit or decoding alone as sufficient.

### Scientific payoff

This pattern converts difficult-to-interpret population activity into a test of computational function by requiring competing accounts to make distinct predictions across controlled task conditions and behavioral outcomes. It supports mechanistic interpretation without assuming that every source shares the same representational trade-off or geometry.

### What different outcomes would mean

- Positive: If the proposed population account uniquely explains condition-dependent neural organization and the associated behavioral pattern—and, where applicable, a constrained model reproduces both—it would support that organization as a functional computational mechanism rather than incidental heterogeneity or a merely descriptive code.
- Negative: If the predicted neural contrasts, behavioral associations, transfer patterns, or model correspondences fail, the proposed population-level account would be weakened. Depending on the source-specific alternatives, the evidence could instead favor upstream filtering, simpler or more specialized representations, one extreme of a separation–reuse trade-off, or task-irrelevant heterogeneity; it could also leave the alternatives unresolved.

### Common failure modes

- Treating decoding accuracy, representational similarity, or dimensionality alone as evidence of mechanism
- Assuming that all sources instantiate an intermediate binding–abstraction geometry
- Failing to vary the factors or contextual demands needed to distinguish competing accounts
- Defining candidate mechanisms too loosely to yield different neural and behavioral predictions
- Using a model as a substitute for physiological observations rather than requiring correspondence with both physiology and behavior
- Interpreting behavioral errors or correct-versus-error differences without considering alternative causes
- Inferring shared downstream readout or functional capacity directly from population structure

### Details that should not be transferred

- The binding-versus-generalization framing, semi-orthogonal subspaces, and predictions about transfer and misbinding are specific to source paper 1; they instantiate the broader move through competing geometries linked to characteristic choice errors.
- The early-filtering-versus-within-prefrontal-selection contrast and recurrent-network reproduction of behavioral and physiological patterns are specific to source paper 2; they instantiate the broader move through contextual contrasts and model-constrained population dynamics, not through an intermediate binding geometry.
- Residual information after removal of classical selectivity, expanded readout diversity, high dimensionality, and comparison of correct with error trials are specific to source paper 3; they instantiate the broader move by testing mixed selectivity as a population resource, not by requiring cross-condition transfer or binding errors.
- The particular species, cortical regions, sensory or memory tasks, response modalities, recording arrangements, model architectures, and population-analysis choices of the source papers
- Any claim that factorial variation, an intermediate geometry, transfer testing, recurrent modeling, or dimensionality analysis is mandatory in every application

### Source PaperCases and formation traces

- Source 1: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. “Semi-orthogonal subspaces for value mediate a binding and generalization trade-off.” Nature Neuroscience, 2024. DOI: 10.1038/s41593-024-01758-5](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)
- Source 2: [Mante, V., Sussillo, D., Shenoy, K. V. &amp; Newsome, W. T. (2013). Context-dependent computation by recurrent dynamics in prefrontal cortex.](papers/nature12742.md) · [Question-formation trace](formation_traces/nature12742.md)
- Source 3: [Rigotti, Mattia; Barak, Omri; Warden, Melissa R.; Wang, Xiao-Jing; Daw, Nathaniel D.; Miller, Earl K.; Fusi, Stefano. “The importance of mixed selectivity in complex cognitive tasks.” Nature, 2013.](papers/nature12160.md) · [Question-formation trace](formation_traces/nature12160.md)

## Pattern 007: Use an empirical comparator or theoretical anchor to interpret observed structure

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A compact, low-dimensional, aligned, or intermediate structure is observed or theoretically expected.
- Generic dimensionality, shared complexity, measurement artifacts, or multiple functionally distinct geometries could produce superficially similar observations.
- The scientific claim depends on showing either that the structure is specific to an interaction or task role, or that it occupies a meaningful position between competing theoretical extremes.

### Unresolved tension

Detection of structure alone does not determine whether it is specifically tied to the focal mechanism, reflects generic properties of the system or measurement process, or lies between theoretical extremes that support competing functions such as abstraction and feature binding. Resolving this ambiguity requires either an empirically matched comparator or theoretically defined baseline geometries that serve as classification anchors.

### Dataset cues

- An empirically matched internal comparator, such as a held-out within-system population or a task-irrelevant representation
- A theoretically defined baseline or extreme structure against which the observation can be classified
- Relevant-versus-irrelevant task dimensions or other matched functional contrasts
- Competing candidate geometries or representations with distinct functional implications
- Repeated observations enabling matched predictive, representational, or behavioral comparisons

### Question-forming move

Place the focal structure against an appropriate reference: either compare it with an empirically matched internal alternative or classify it relative to theoretically defined baseline and extreme geometries. Ask whether it differs in compactness, alignment, mapping, or behavioral consequence from the empirical comparator, or whether its position between theoretical anchors resolves a functional trade-off rather than merely reproducing one endpoint.

### Scientific payoff

A comparator or classification anchor converts a descriptive structural finding into a discriminating test. It can reveal whether an observation is specific rather than generic, or whether an intermediate organization reconciles competing functional demands that neither theoretical extreme satisfies alone.

### What different outcomes would mean

- Positive: A focal structure that differs meaningfully from an empirical reference would support interaction-specific routing, task-organized variability, or another specialized representational role. An observed structure that occupies a functionally consequential position between theoretical extremes would instead support a trade-off account, such as preserving feature binding while retaining some abstraction or generalization.
- Negative: Similarity to an empirical reference would weaken claims of specialization and favor explanations based on generic shared activity, common dimensionality, or target complexity. Placement near a theoretical endpoint, absence of the predicted intermediate organization, or failure to relate geometry to the expected functional consequences would weaken the proposed trade-off mechanism and favor the function associated with one extreme or leave the structure mechanistically unresolved.

### Common failure modes

- Choosing an empirical comparator that differs in data quality or sample size
- Treating a theoretical anchor as though it were a separately observed control
- Interpreting any numerical difference or intermediate value as mechanistic specificity
- Failing to match prediction targets or nuisance variables across empirical comparisons
- Using a reference contaminated by the focal interaction
- Ignoring uncertainty in subspace, alignment, or geometric classification estimates
- Assigning functional meaning to geometry without checking its predicted behavioral or representational consequences

### Details that should not be transferred

- The held-out within-area comparator from the inter-system recording study
- Specific relevant-versus-irrelevant visual features
- Paper-specific definitions of parallel, orthogonal, and intermediate value-position geometries and their error consequences
- Exact source and target anatomical assignments

### Source PaperCases and formation traces

- Source 1: [Semedo et al., 2019, “Cortical Areas Interact through a Communication Subspace”](papers/1-s2-0-s0896627319300534-main.md) · [Question-formation trace](formation_traces/1-s2-0-s0896627319300534-main.md)
- Source 2: [The structure of correlated variability reflects task-relevant information in sensory neurons](papers/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md) · [Question-formation trace](formation_traces/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md)
- Source 3: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. “Semi-orthogonal subspaces for value mediate a binding and generalization trade-off.” Nature Neuroscience, 2024. DOI: 10.1038/s41593-024-01758-5](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)

## Pattern 008: Separate input-bound structure from model-predicted internal organization

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A measured system-level pattern could reflect current input statistics, environmental context, or embodied behavior rather than internal organization.
- Competing models predict different internal signatures, such as a constrained population geometry, persistence across contexts, or distributed versus localized representation and inter-area interaction.
- A dataset combines coordinated system-wide measurements with contrasts in input statistics, effective dimensionality, environment, or sensory availability and, where relevant, measurements of plausible behavioral confounds.

### Unresolved tension

The same observed structure can be attributed to inherited input statistics, environment-specific or feedforward construction, embodied covariates, or a model-predicted internal organization expressed through population geometry, persistence, anatomical distribution, or directed inter-component dynamics.

### Dataset cues

- Controlled contrasts in input statistics, effective dimensionality, environment, or sensory availability, including conditions with weak or absent task-relevant input
- Repeated or coordinated measurements that make the focal population structure reliable and comparable across conditions
- Broad coverage at the spatial or population scale needed to distinguish localized from distributed organization
- Measurements of movement, posture, or other embodied variables that could mimic the focal representation
- Temporal measurements suitable for assessing directed statistical information between system components when interaction patterns discriminate competing models

### Question-forming move

Translate competing explanations into distinct predictions for an observable system-level signature, then use selective contrasts in input statistics, dimensionality, context, or availability to ask whether that signature tracks external conditions or instead exhibits the geometry, persistence, anatomical distribution, or inter-component dynamics predicted by an internal model. When sensory evidence is reduced or absent, use behavioral measurements to test embodied alternatives; when the internal account predicts distributed recurrent organization rather than a mathematical invariant, compare broad spatial representation and directed statistical information against a localized late-stage account.

### Scientific payoff

This move goes beyond detecting correspondence between inputs and measured activity by determining whether the structure is input-bound, behaviorally confounded, localized to a late processing stage, or consistent with a broader model-predicted internal organization. It also clarifies which aspects of internal organization remain supported across geometric, contextual, anatomical, and dynamical tests.

### What different outcomes would mean

- Positive: A signature that remains detectable under altered or reduced input and matches the relevant model prediction—whether a dimensionality-dependent geometry, cross-context population organization, or distributed representation with compatible inter-component dynamics—would strengthen the corresponding internal-organization account, provided behavioral alternatives are not sufficient to explain it.
- Negative: A signature that follows specific input statistics, changes only with the original environment, localizes to the predicted late processing stage, lacks the model-predicted geometry or interactions, or is explained by embodied variables would weaken the proposed broader internal organization and favor input-bound, feedforward, localized, context-specific, or behavioral alternatives.

### Common failure modes

- Changing several input or contextual properties at once and losing the ability to attribute the observed change
- Calling persistence invariance without testing whether the representation or mapping remains comparable across conditions
- Ignoring differences in sampling, state, coverage, or measurement reliability across conditions or system components
- Treating weak or absent task-relevant input as absence of all external or embodied influence
- Failing to test movement, posture, reward history, or other behavioral variables that could mimic an internally maintained signal
- Inferring distributed organization from broad coverage without accounting for uneven sampling or common task covariates
- Treating directed statistical information as proof of anatomical causation or a uniquely recurrent mechanism
- Assuming persistence, topology, or distributed decoding uniquely identifies one mechanism
- Applying a mathematical, geometric, or network-model prediction outside its stated assumptions

### Details that should not be transferred

- Specific natural-image manipulations, visual response spectra, and smooth differentiable mapping assumptions
- The source-specific spatial environments, sleep states, and particular toroidal topology prediction
- The specific trial-history prior, zero-contrast condition, visual decision task, and localized-versus-brain-wide anatomical alternatives
- Source-specific decoding, Granger-causality, video-feature, and pose-estimation implementations
- Exact species, recording technologies, sensory modalities, anatomical registration, and coverage

### Source PaperCases and formation traces

- Source 1: [Stringer, Carsen; Pachitariu, Marius; Steinmetz, Nicholas; Carandini, Matteo; Harris, Kenneth D. (2019), “High-dimensional geometry of population responses in visual cortex,” Nature.](papers/s41586-019-1346-5.md) · [Question-formation trace](formation_traces/s41586-019-1346-5.md)
- Source 2: [Gardner et al., “Toroidal topology of population activity in grid cells,” Nature, 2022.](papers/s41586-021-04268-7.md) · [Question-formation trace](formation_traces/s41586-021-04268-7.md)
- Source 3: [Brain-wide representations of prior information in mouse decision-making](papers/ibl-s41586-025-09226-1.md) · [Question-formation trace](formation_traces/ibl-s41586-025-09226-1.md)
