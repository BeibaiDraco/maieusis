# Detailed Question Scientist families

This page preserves every proposed family and variant, including options that were not shortlisted for planning. Novelty and dataset leverage below are proposal-stage hypotheses, not verdicts or feasibility certifications.

- Families proposed: 6
- Authority ceiling: `verified`

## Family 001: Persistent versus sequential population dynamics during evidence accumulation

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family asking whether decision-related population activity is better understood as persistent evidence representation or as choice-selective sequential progression, while separating representational form from behavioral relevance.

### Shared scientific tension

Evidence accumulation is established as a useful account of perceptual decisions, but persistent and sequential neural implementations remain unresolved and may differ across brain populations.

### Family structure

- Semantic axes: theoretical_tension; population_scope; claim_level; outcome_meaning
- Distinctions that should not be merged: Representational form across populations and incremental behavioral prediction are different scientific claims.; A population may exhibit persistent or sequential structure without that distinction predicting trial-level behavior.
- Proposal-stage uncertainties: Whether persistent and sequential constructs can be operationalized without defining them from behavior; Whether comparable population sampling exists across relevant regions and task periods; Whether observed dynamics can be separated from movement and event locking
- Dataset assumptions: The public resource may allow later task-aligned population comparisons.; Exact simultaneous coverage, measurement quality, and usable trial structure remain for downstream testing.

### Reviewed literature context used by the family

- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Whether evidence is accumulated through persistent activity or through choice-selective sequential dynamics remains unresolved, with candidate circuit mechanisms varying across recorded brain regions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Inferences about individual neurons' contributions to perceptual decisions depend on matching neural measurements to the behavioral decision timescale and on assumptions about noise correlations.
  - Sources: [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

### Variant 001.001: Representational-form variant

- Shortlist disposition: **Active for planning**
- Distinction axes: theoretical_tension, population_scope
- Distinct from sibling variants: This variant asks what temporal population organization carries evidence across regions; it does not primarily ask which organization better predicts behavioral variation.

#### Question

Across brain populations engaged during decision formation, is accumulated evidence expressed predominantly through persistent population states or through choice-selective sequential trajectories?

#### Scientific tension and why it matters

Similar choice and response-time patterns may be compatible with persistent integration, sequential transfer of evidence, or mixtures of both population organizations.

Distinguishing these representational forms would refine claims about how distributed neural populations maintain and transform evidence without treating either form as a demonstrated circuit mechanism.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is a standardized brain-wide comparison of persistent and sequential signatures rather than another test for generic buildup or broad evidence encoding.

#### Relevant literature

- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Whether evidence is accumulated through persistent activity or through choice-selective sequential dynamics remains unresolved, with candidate circuit mechanisms varying across recorded brain regions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Closest known work

- The question of whether a neural decision-variable signal can show evidence-strength-dependent buildup and reach a stereotyped level at perceptual report has already been answered in a human dot-motion task.
  - Sources: [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Whether evidence is accumulated through persistent activity or through choice-selective sequential dynamics remains unresolved, with candidate circuit mechanisms varying across recorded brain regions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Dataset leverage hypothesis — not a feasibility certification

Coarse task-aligned neural and behavioral measurements across major brain regions may allow a later planner to compare population organizations during decision formation.

#### Competing explanations

- Apparent sequences reflect heterogeneous response latencies locked to sensory or motor events rather than evidence transfer.
- Apparent persistence is produced by averaging transient activity across neurons or trials rather than stable population representation.

#### Discriminating observation

A regionally reproducible distinction between sustained evidence-conditioned population states and orderly choice-dependent state progression that remains distinguishable when sensory timing and overt movement are considered would favor different representational accounts.

#### What different outcomes would mean

- Positive: Evidence for systematically different persistent and sequential organizations across populations would support a heterogeneous brain-wide architecture of evidence representation.
- Negative: Failure to distinguish the proposed organizations would weaken claims that persistent-versus-sequential form provides a useful taxonomy for these recordings.
- Null: Equally supported or unstable signatures would preserve the circuit tension and redirect attention toward hybrid or scale-dependent descriptions.

#### Ambiguities

- persistent activity
- choice-selective sequence
- evidence representation
- population state

#### Planning challenges

- Separating decision formation from sensory and movement timing
- Avoiding trajectory artifacts caused by temporal averaging
- Matching neural summaries to behavioral decision timescales
- Assessing sensitivity to spike-sorting limitations

#### Dataset assumptions

- Task-aligned neural activity may support later characterization of decision-period population dynamics.
- Brain-region identity may permit later comparative planning, but comparable joint coverage must be tested.


### Variant 001.002: Behavioral-prediction variant

- Shortlist disposition: **Active for planning**
- Distinction axes: claim_level, outcome_meaning, discriminating_observation
- Distinct from sibling variants: This variant evaluates predictive relevance for choices and response times rather than classifying the temporal form of population activity itself.

#### Question

Do persistent and sequential population signatures differ in how they predict trial-to-trial choice and response-time variation during evidence accumulation?

#### Scientific tension and why it matters

A neural organization can resemble an accumulation mechanism without carrying behaviorally relevant variation, while different organizations may support similar average behavior.

Relating competing population organizations to held-out behavioral variation would distinguish descriptive resemblance from predictive relevance without implying causality.

#### Proposal-stage novelty hypothesis — not a verdict

The contribution would be a direct predictive contrast between persistent and sequential descriptions at behaviorally matched timescales.

#### Relevant literature

- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Whether evidence is accumulated through persistent activity or through choice-selective sequential dynamics remains unresolved, with candidate circuit mechanisms varying across recorded brain regions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612)
- Inferences about individual neurons' contributions to perceptual decisions depend on matching neural measurements to the behavioral decision timescale and on assumptions about noise correlations.
  - Sources: [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

#### Closest known work

- The question of whether a neural decision-variable signal can show evidence-strength-dependent buildup and reach a stereotyped level at perceptual report has already been answered in a human dot-motion task.
  - Sources: [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Whether evidence is accumulated through persistent activity or through choice-selective sequential dynamics remains unresolved, with candidate circuit mechanisms varying across recorded brain regions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612)

#### Dataset leverage hypothesis — not a feasibility certification

Joint neural activity, choices, and response times may allow a later planner to compare the behavioral predictions of alternative population descriptions.

#### Competing explanations

- Both signatures predict behavior only because they track stimulus strength.
- Predictive differences arise from movement preparation or measurement timescale rather than evidence accumulation.

#### Discriminating observation

If one population description adds reproducible held-out prediction of choices or response times beyond stimulus and movement-related alternatives, it would receive stronger predictive support.

#### What different outcomes would mean

- Positive: Selective behavioral prediction would prioritize one population organization as a more consequential description of decision formation.
- Negative: No predictive advantage would argue against assigning special behavioral meaning to either signature.
- Null: Comparable weak prediction would leave open whether accumulation is distributed across hybrid dynamics or insufficiently captured by either construct.

#### Ambiguities

- behavioral relevance
- decision timescale
- persistent signature
- sequential signature

#### Planning challenges

- Preventing behavioral leakage into neural signature definition
- Separating stimulus, decision, and movement contributions
- Comparing models of unequal flexibility
- Accounting for cross-subject and cross-laboratory heterogeneity

#### Dataset assumptions

- Choices and response times may be alignable with neural activity for later predictive planning.
- Movement measurements may provide proposal-stage inspiration for alternative-explanation tests; exact availability must be checked later.

## Family 002: Temporal origin of choice-predictive population activity

- Shortlist disposition: **Not shortlisted — deferred**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family separating early sensory-linked and later decision-linked interpretations of choice-predictive neural activity, with distinct temporal-origin and spatial-distribution variants.

### Shared scientific tension

Choice-predictive activity may reflect bottom-up sensory variability, top-down decision-related feedback, movement preparation, or mixtures of these processes; choice association alone cannot adjudicate among them.

### Family structure

- Semantic axes: theoretical_tension; discriminating_observation; population_scope; target_contrast
- Distinctions that should not be merged: Temporal origin and spatial distribution are separable properties of choice-predictive activity.; A temporal shift may occur without anatomical segregation, and spatial segregation may exist without a clear temporal transition.
- Proposal-stage uncertainties: Whether temporal components are identifiable from observational data; Whether movement measurements capture the most important embodied alternatives; Whether regional comparisons are sufficiently standardized
- Dataset assumptions: The resource may support temporal and regional comparisons at proposal-stage granularity.; Exact event definitions, joint measurements, and regional coverage require downstream inspection.

### Reviewed literature context used by the family

- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)

### Variant 002.001: Temporal-origin variant

- Shortlist disposition: **Not shortlisted — deferred**
- Distinction axes: theoretical_tension, discriminating_observation
- Distinct from sibling variants: This variant asks whether the interpretation of choice-predictive activity changes over trial time, not where any surviving components are distributed.

#### Question

Does choice-predictive population activity shift over a trial from an early sensory-linked component to a later decision- or preparation-linked component?

#### Scientific tension and why it matters

Sustained choice prediction can arise from changing mixtures of bottom-up and top-down components rather than a single stable choice signal.

A temporal decomposition would clarify what choice prediction means at different decision stages while avoiding causal interpretation of observational associations.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent advance is to test a changing population-level mixture across the task rather than summarize choice prediction with one trial-wide quantity.

#### Relevant literature

- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Closest known work

- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Dataset leverage hypothesis — not a feasibility certification

Task-event alignment, population activity, decisions, and movement measures may support later planning of temporally resolved alternative-explanation tests.

#### Competing explanations

- The temporal shift reflects changing stimulus reliability rather than a bottom-up to top-down transition.
- Late choice prediction is explained by movement preparation or execution rather than decision-related feedback.

#### Discriminating observation

An early component preferentially associated with sensory variation and a later component preferentially associated with decision or preparation after accounting for measured movement would support a changing-mixture account.

#### What different outcomes would mean

- Positive: A temporal transition would show that the interpretation of choice-predictive activity depends on decision stage.
- Negative: A stable component across time would weaken the proposed changing-mixture account.
- Null: Indistinguishable or unreliable components would leave the origin of choice prediction unresolved and caution against temporal labels.

#### Ambiguities

- bottom-up component
- top-down component
- choice prediction
- decision stage

#### Planning challenges

- Avoiding circular temporal component definitions
- Separating decision-related and movement-related activity
- Matching temporal resolution to behavioral timescale
- Controlling stimulus-choice dependence

#### Dataset assumptions

- Neural activity may be alignable to sensory, decision, and movement-related periods.
- Concurrent pose or movement measurements may support later confound assessment.


### Variant 002.002: Spatial-organization variant

- Shortlist disposition: **Not shortlisted — deferred**
- Distinction axes: population_scope, target_contrast, outcome_meaning
- Distinct from sibling variants: This variant compares localized and distributed spatial organizations of temporal components rather than testing whether those components change over time.

#### Question

Are sensory-linked and later decision-linked components of choice-predictive activity spatially concentrated in different processing populations or distributed across major brain regions?

#### Scientific tension and why it matters

Temporal components with different interpretations could be anatomically segregated, broadly distributed, or appear widespread because of common inputs and movement.

The spatial organization of distinguishable components constrains descriptive accounts of brain-wide sensorimotor transformation without equating detectability with local computation.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal goes beyond asking whether a decision variable is widespread by comparing the spatial profiles of competing temporal components.

#### Relevant literature

- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The question of whether learned prior probability is represented broadly across sensory, motor, and higher-level brain regions during mouse visual decisions has already been answered in International Brain Laboratory recordings and imaging.
  - Sources: [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Closest known work

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The question of whether learned prior probability is represented broadly across sensory, motor, and higher-level brain regions during mouse visual decisions has already been answered in International Brain Laboratory recordings and imaging.
  - Sources: [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Dataset leverage hypothesis — not a feasibility certification

Broad anatomical sampling under a standardized task may allow a later planner to compare component profiles across major regions.

#### Competing explanations

- Apparent regional differences reflect unequal measurement sensitivity or sampling.
- Widespread late activity reflects common movement-related input rather than distributed decision processing.

#### Discriminating observation

Distinct and reproducible regional profiles for sensory-linked versus later decision-linked components, robust to measured movement alternatives, would favor partial spatial specialization; similar profiles would favor a distributed account.

#### What different outcomes would mean

- Positive: Spatially differentiated components would refine the architecture of the sensory-to-choice transformation.
- Negative: No spatial differentiation would support a more distributed or common-input description.
- Null: Unstable regional profiles would prevent adjudication and emphasize sampling and measurement uncertainty.

#### Ambiguities

- spatial concentration
- distributed representation
- processing population
- common input

#### Planning challenges

- Uneven anatomical sampling and registration
- Cross-region comparability of population summaries
- Separating detectability from local computation
- Cross-laboratory and cross-subject heterogeneity

#### Dataset assumptions

- Brain-region identity may permit later regional comparisons.
- Standardization may support comparability, but exact replication and usable coverage must be verified downstream.

## Family 003: Decision-related population structure after richer movement accounting

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family testing whether apparent decision-related activity survives richer embodied alternatives or is better understood as behaviorally structured activity, with target-preservation and reinterpretation variants.

### Shared scientific tension

Population activity associated with decisions may encode a latent decision construct, richer movement and posture, or inseparable mixtures; coarse motor controls may leave this ambiguity unresolved.

### Family structure

- Semantic axes: target_contrast; outcome_meaning; claim_level; discriminating_observation
- Distinctions that should not be merged: Decision-residual and embodied-representation questions assign opposite scientific roles to movement.; Absorption of a decision signal by behavior and meaningful neural representation of behavior have different interpretations and consequences.
- Proposal-stage uncertainties: Whether pose measurements capture behavior relevant to neural activity; Whether decision and movement constructs can be separated temporally or conceptually; Whether richer models can be compared without unequal flexibility
- Dataset assumptions: Joint modalities may support later alternative-explanation planning.; Exact synchronization, completeness, and quality of behavioral measurements must be tested downstream.

### Reviewed literature context used by the family

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

### Variant 003.001: Decision-residual variant

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, claim_level, discriminating_observation
- Distinct from sibling variants: This variant treats decision-related structure as the target and movement as the competing explanation; the sibling instead treats rich behavior as the target representation.

#### Question

Does population activity retain decision-related structure after accounting for richer concurrent movement and pose variation rather than only coarse behavioral covariates?

#### Scientific tension and why it matters

A decision-related signal may be genuine residual structure or a proxy for multidimensional embodied behavior omitted from conventional controls.

A stringent alternative-explanation test can strengthen a decision-representation claim or appropriately narrow it without treating prediction as causation.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent advance is to compare latent decision interpretation against a richer embodied alternative across brain populations.

#### Relevant literature

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Closest known work

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The question of whether learned prior probability is represented broadly across sensory, motor, and higher-level brain regions during mouse visual decisions has already been answered in International Brain Laboratory recordings and imaging.
  - Sources: [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Dataset leverage hypothesis — not a feasibility certification

Joint neural, decision, response-time, and pose measurements may allow a later planner to test whether decision-related structure has held-out explanatory value beyond movement.

#### Competing explanations

- The residual signal reflects unmeasured movement or internal state rather than decision formation.
- Richer behavioral models absorb genuine decision activity because movement is itself downstream of the decision.

#### Discriminating observation

Reproducible decision-related population structure that adds held-out prediction beyond richer movement descriptions, especially before overt response, would favor a distinct decision component.

#### What different outcomes would mean

- Positive: Surviving structure would strengthen an associational or predictive claim that neural populations carry decision-related information not reducible to measured movement.
- Negative: Near-complete absorption by richer behavior would weaken a distinct latent-decision interpretation.
- Null: Model-dependent residuals would leave the constructs inseparable and motivate more cautious joint sensorimotor descriptions.

#### Ambiguities

- decision-related structure
- richer movement
- internal state
- residual signal

#### Planning challenges

- Temporal leakage between decisions and movements
- Uneven pose quality
- Incomplete measurement of embodied variables
- Comparing flexible behavioral and neural models fairly

#### Dataset assumptions

- Pose and movement measurements may be sufficiently synchronized for later planning.
- Decision and neural measurements may support held-out comparative prediction, subject to exact availability checks.


### Variant 003.002: Embodied-target variant

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, outcome_meaning, claim_level
- Distinct from sibling variants: This variant makes multidimensional behavior the target and compares it with simpler state accounts, rather than asking whether a latent decision signal survives behavioral control.

#### Question

Do brain-wide populations represent multidimensional movement and pose in ways that explain decision and response-time variation better than simpler state or locomotor summaries?

#### Scientific tension and why it matters

Behavior-related neural activity may be dismissed as nuisance even when rich embodied structure is itself a meaningful component of decision behavior.

Treating multidimensional behavior as the scientific target can reveal how embodied variation participates in sensorimotor transformation rather than merely controlling it away.

#### Proposal-stage novelty hypothesis — not a verdict

The question reverses the nuisance framing by testing rich embodied representations against simpler state explanations and linking them predictively to decision outcomes.

#### Relevant literature

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Closest known work

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)

#### Dataset leverage hypothesis — not a feasibility certification

Concurrent pose, movement, neural, choice, and response-time measurements may support later comparison of rich behavioral and simple-state representations.

#### Competing explanations

- Neural prediction of pose reflects generic arousal or locomotion rather than multidimensional behavioral organization.
- Associations with decisions arise because both pose and neural activity are locked to task events.

#### Discriminating observation

Rich behavioral dimensions that reproducibly improve held-out neural and outcome prediction beyond simpler state summaries and event timing would support meaningful embodied representation.

#### What different outcomes would mean

- Positive: A positive result would elevate rich behavioral structure from nuisance to a predictive component of brain-wide decision dynamics.
- Negative: No advantage over simple summaries would weaken claims that multidimensional behavior provides distinct explanatory structure.
- Null: Unstable advantages would preserve uncertainty about behavioral dimensionality and measurement quality.

#### Ambiguities

- rich behavior
- state variable
- embodied representation
- behavioral dimensionality

#### Planning challenges

- Defining behavioral dimensions without overfitting
- Distinguishing task locking from representation
- Handling missing or uneven video measurements
- Avoiding causal language from prediction

#### Dataset assumptions

- Video-derived pose may permit later multidimensional behavioral characterization.
- Choices and response times may permit predictive outcome comparisons after feasibility review.

## Family 004: Functional geometry of shared neural variability

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family replacing correlation magnitude with structural alignment, separating sensory-information and decision-behavior meanings of shared variability.

### Shared scientific tension

Shared variability can be nuisance, information-limiting structure, or behaviorally meaningful population organization; its consequence depends on orientation relative to candidate signal dimensions rather than magnitude alone.

### Family structure

- Semantic axes: target_contrast; outcome_meaning; claim_level; discriminating_observation
- Distinctions that should not be merged: Sensory information limitation and behavioral alignment assign different meanings to the same variability geometry.; Alignment with sensory evidence need not imply alignment with decisions or movement, and their consequences differ.
- Proposal-stage uncertainties: Whether covariance geometry can be estimated reliably from available population observations; Whether candidate axes can be defined independently; Whether alignment has stable meaning across regions, subjects, or laboratories
- Dataset assumptions: Population activity and task variables may support later structural variability analysis.; Exact repeated-measure reliability and joint coverage remain unknown.

### Reviewed literature context used by the family

- The effect of noise correlations on population information is conditional on population structure, information limits, and the distinction between encoding and decoding; reduced correlations cannot be assumed to improve coding.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112); [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Inferences about individual neurons' contributions to perceptual decisions depend on matching neural measurements to the behavioral decision timescale and on assumptions about noise correlations.
  - Sources: [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

### Variant 004.001: Sensory-alignment variant

- Shortlist disposition: **Not carried into planning — bounded prior-art review found a close prior that directly recaps this variant. A content-bearing DOI-identified prior directly operationalizes and applies the proposed sensory-evidence/noise-covariance alignment test to identify differential (information-limiting) correlations in macaque V1, including an interpretation in terms of orientation-discrimination thresholds. Other content-bearing priors independently establish that small aggregate pairwise correlations can nevertheless limit information and that sensory-population information can be decomposed into information-limiting versus nonlimiting correlation components. Thus the candidate's general question and its proposed positive implication are already directly addressed within the bounded evidence pack. Compared against: https://doi.org/10.1101/842724; https://doi.org/10.1523/jneurosci.2072-19.2019; https://doi.org/10.1038/s41467-020-20722-y**
- Distinction axes: target_contrast, outcome_meaning, discriminating_observation
- Distinct from sibling variants: This variant evaluates alignment with sensory-evidence dimensions and its possible coding meaning, not alignment with decision or movement dimensions.

#### Question

Is shared population variability selectively aligned with sensory-evidence dimensions in a way that distinguishes potentially information-limiting structure from correlation magnitude alone?

#### Scientific tension and why it matters

Similar overall correlation magnitude can have different implications depending on whether variability lies along sensory-discriminating directions.

A structural characterization would avoid unsupported claims that lower correlations necessarily improve coding and could identify when variability is positioned to limit sensory discrimination.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal applies an alignment-based question to task-related brain-wide populations while retaining an associational claim ceiling.

#### Relevant literature

- The effect of noise correlations on population information is conditional on population structure, information limits, and the distinction between encoding and decoding; reduced correlations cannot be assumed to improve coding.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112); [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Inferences about individual neurons' contributions to perceptual decisions depend on matching neural measurements to the behavioral decision timescale and on assumptions about noise correlations.
  - Sources: [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)

#### Closest known work

- The effect of noise correlations on population information is conditional on population structure, information limits, and the distinction between encoding and decoding; reduced correlations cannot be assumed to improve coding.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112); [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Inferences about individual neurons' contributions to perceptual decisions depend on matching neural measurements to the behavioral decision timescale and on assumptions about noise correlations.
  - Sources: [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

#### Dataset leverage hypothesis — not a feasibility certification

Repeated neural responses under varying sensory conditions may allow a later planner to estimate variability and sensory directions separately.

#### Competing explanations

- Observed alignment is estimator circularity because variability and signal directions are learned from the same observations.
- Alignment reflects stimulus-independent global state or movement rather than sensory information limitation.

#### Discriminating observation

Selective alignment with independently defined sensory-evidence directions, beyond magnitude-matched alternatives and measured behavioral dimensions, would support a structural sensory account.

#### What different outcomes would mean

- Positive: A positive result would show that the orientation of variability provides information not captured by aggregate correlation magnitude.
- Negative: Lack of selective alignment would weaken an information-limiting interpretation in the studied populations.
- Null: Unreliable alignment estimates would leave the consequence of shared variability unresolved and highlight measurement limits.

#### Ambiguities

- shared variability
- sensory-evidence dimension
- information-limiting
- selective alignment

#### Planning challenges

- Independent estimation of signal and variability geometry
- Finite-sample and population-sampling bias
- Behavioral-timescale matching
- Spike-sorting and nonstationarity sensitivity

#### Dataset assumptions

- Repeated stimulus-linked population activity may support later geometric planning.
- A later planner must verify suitable population structure and reliability.


### Variant 004.002: Behavioral-alignment variant

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, claim_level, outcome_meaning
- Distinct from sibling variants: This variant contrasts decision and movement alignment with sensory alignment and asks about behavioral prediction; the sibling focuses on sensory coding meaning.

#### Question

Is shared population variability more selectively aligned with decision- or movement-related dimensions than with sensory-evidence dimensions, and does that alignment predict choices or response times?

#### Scientific tension and why it matters

Shared variability may reflect internal decision variation, embodied behavior, or sensory coding limits, even when its overall magnitude is similar.

Comparing candidate orientations can distinguish alternative functional meanings and test predictive relevance without treating alignment as causal readout.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is a selective comparison among sensory, decision, and movement directions tied to behavioral prediction.

#### Relevant literature

- The effect of noise correlations on population information is conditional on population structure, information limits, and the distinction between encoding and decoding; reduced correlations cannot be assumed to improve coding.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112); [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Closest known work

- The effect of noise correlations on population information is conditional on population structure, information limits, and the distinction between encoding and decoding; reduced correlations cannot be assumed to improve coding.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112); [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)

#### Dataset leverage hypothesis — not a feasibility certification

Joint neural, choice, response-time, and pose measurements may allow later planning of independently defined candidate dimensions.

#### Competing explanations

- Behavioral alignment reflects event-locked movement rather than latent decision variation.
- Apparent selectivity arises from unequal reliability of sensory, decision, and movement dimensions.

#### Discriminating observation

Preferential alignment with independently estimated decision or movement dimensions that adds held-out outcome prediction beyond sensory alignment and overall variability magnitude would favor a behavioral interpretation.

#### What different outcomes would mean

- Positive: Selective behavioral alignment would recast part of shared variability as structured population variation relevant to observed behavior.
- Negative: No selective or predictive alignment would favor a nuisance or unidentified-source interpretation.
- Null: Comparable alignment across dimensions would suggest mixed structure that cannot be assigned a unique functional meaning.

#### Ambiguities

- decision dimension
- movement dimension
- behavioral relevance
- shared variability

#### Planning challenges

- Defining independent candidate dimensions
- Avoiding temporal and outcome leakage
- Accounting for unequal measurement reliability
- Separating movement from decision formation

#### Dataset assumptions

- Behavioral outcomes and pose may support later candidate-axis construction.
- Exact synchronized coverage and sufficient repeated observations must be established later.

## Family 005: Functional forms of mixed selectivity in decision populations

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family distinguishing the representational form of mixed selectivity from its functional relationship to behavioral success and cross-condition readout.

### Shared scientific tension

Mixed responses may provide useful high-dimensional structure, reflect simpler additive mixing, or arise from correlated sensory and movement variables; identifying mixing alone does not establish function.

### Family structure

- Semantic axes: target_contrast; population_scope; claim_level; outcome_meaning; discriminating_observation
- Distinctions that should not be merged: Characterizing whether mixing is additive, nonlinear, categorical, or category-free is distinct from testing functional consequences.; A representational form can be prevalent without predicting successful behavior, and a rare form can still be functionally consequential.
- Proposal-stage uncertainties: How mixed-selectivity forms should be operationalized without post hoc categorization; Whether task conditions permit meaningful generalization contrasts; Whether apparent regional differences survive scale and measurement controls
- Dataset assumptions: Joint task, behavior, and neural measurements may support later representational planning.; Exact condition balance, population reliability, and outcome coverage require downstream testing.

### Reviewed literature context used by the family

- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

### Variant 005.001: Representational-taxonomy variant

- Shortlist disposition: **Not carried into planning — deferred: the bounded prior-art search did not return enough evidence to judge this variant. Content-bearing scholarly priors establish that nonlinear versus additive mixed selectivity and category-free versus clustered task tuning are already empirically and conceptually developed distinctions. No cited prior directly tests the proposed joint, cross-population taxonomy for sensory evidence, choice, and movement under correlated-variable controls. However, the question currently combines response-function form (additive/nonlinear) with distributional organization of tuning types (categorical/category-free) without specifying how these distinct axes will be separated; this is a consequential distinction in light of the prior category-free-selectivity result and the mechanistic definitions of linear and nonlinear mixing. Compared against: https://doi.org/10.1101/082636; https://doi.org/10.1016/j.neuron.2024.04.017; https://doi.org/10.1523/eneuro.0517-21.2022 To distinguish it: Separate two scientific axes in the target claim: whether individual or population responses contain conditional non-additive interactions among sensory evidence, choice, and movement, and whether the distribution of response profiles contains discrete clusters versus a continuum. Do not treat categorical/category-free organization as interchangeable with additive/nonlinear response form. To distinguish it: Specify a discriminating control criterion under which an apparent sensory-evidence-by-choice or sensory-evidence-by-movement interaction remains non-additive after conditioning on measured movement, choice, task-state, and other correlated variables; otherwise the comparison cannot distinguish interaction structure from covariation artifacts. To distinguish it: Define the cross-population contrast at a common level of analysis and variable set: the same joint sensory-evidence, choice, and movement representation must be assessed across populations, rather than comparing region-specific task variables or analyses. To distinguish it: State what observation would distinguish a genuinely category-free continuum of task-sensitive response profiles from a single broad mixed-selectivity cluster or from inadequate power to resolve subtypes, since the prior category-free result used a specific mixture-modeling interpretation.**
- Distinction axes: target_contrast, population_scope, outcome_meaning
- Distinct from sibling variants: This variant classifies forms of mixed selectivity across populations; it does not test whether a given form improves behavioral prediction or generalization.

#### Question

Across major brain populations, does joint representation of sensory evidence, choice, and movement exhibit additive, nonlinear, categorical, or category-free mixed selectivity?

#### Scientific tension and why it matters

Observed mixing can take scientifically different forms with different representational implications, yet apparent nonlinear structure may also arise from correlated task variables.

Characterizing form is necessary before assigning flexibility, abstraction, or computational benefit to heterogeneous population responses.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is a brain-wide comparative taxonomy of representational form under a shared decision-task context, not a generic demonstration of mixed selectivity.

#### Relevant literature

- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Closest known work

- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Dataset leverage hypothesis — not a feasibility certification

Joint sensory, decision, movement, and anatomical context may allow a later planner to compare forms of population mixing across major regions.

#### Competing explanations

- Apparent nonlinear mixing is induced by correlations among sensory, choice, and movement variables.
- Regional differences reflect sampling scale or measurement quality rather than distinct representational organization.

#### Discriminating observation

Reproducible differences among additive, nonlinear, categorical, and category-free structure under controls for correlated variables would support a meaningful taxonomy of mixing.

#### What different outcomes would mean

- Positive: Distinct forms across populations would refine how heterogeneous decision-related activity is described and compared.
- Negative: Predominantly additive or unstable structure would weaken claims of widespread nonlinear mixed selectivity.
- Null: Estimator-dependent classifications would leave the form of mixing ambiguous and caution against categorical labels.

#### Ambiguities

- nonlinear mixed selectivity
- categorical representation
- category-free representation
- representational form

#### Planning challenges

- Correlated task and movement variables
- Scale dependence of representational categories
- Estimator and regularization sensitivity
- Uneven population sampling across regions

#### Dataset assumptions

- Multiple task and behavioral variables may be jointly represented in the neural measurements.
- Regional context may permit later comparative planning after coverage checks.


### Variant 005.002: Functional-consequence variant

- Shortlist disposition: **Active for planning**
- Distinction axes: claim_level, discriminating_observation, outcome_meaning
- Distinct from sibling variants: This variant tests predictive consequences of representational form for behavior and generalization rather than establishing the taxonomy of mixing.

#### Question

Do nonlinear or higher-dimensional mixed population representations predict successful decisions and cross-condition readout better than additive or lower-dimensional alternatives?

#### Scientific tension and why it matters

High-dimensional mixing may support flexible readout, but dimensionality or decoding alone may be epiphenomenal and need not relate to behavioral success.

A functional contrast would test what population organization adds beyond descriptive heterogeneity while retaining predictive rather than causal claims.

#### Proposal-stage novelty hypothesis — not a verdict

The question links pre-specified forms of mixing to behavioral success and readout generalization rather than treating high dimensionality as intrinsically beneficial.

#### Relevant literature

- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- Sequential accumulation-to-bound models provide a supported account of perceptual decisions under uncertainty: sensory evidence can be integrated over time until a decision threshold is reached.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Closest known work

- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)

#### Dataset leverage hypothesis — not a feasibility certification

Neural populations, task conditions, and behavioral outcomes may allow later comparison of functional consequences associated with alternative representational forms.

#### Competing explanations

- Higher-dimensional representations improve prediction only because they provide more flexible models.
- Associations with successful choices reflect stimulus strength or movement consistency rather than useful mixed coding.

#### Discriminating observation

A pre-specified mixed-representation measure that reproducibly predicts held-out decision success or cross-condition readout beyond additive structure, stimulus, and movement alternatives would favor functional relevance.

#### What different outcomes would mean

- Positive: A positive result would support a predictive link between representational form and flexible or successful decision readout.
- Negative: No advantage would challenge the assumption that nonlinear or high-dimensional mixing is functionally beneficial in this setting.
- Null: Trade-offs between prediction and generalization would suggest that no single geometric regime is uniformly advantageous.

#### Ambiguities

- behavioral success
- flexible readout
- cross-condition generalization
- useful dimensionality

#### Planning challenges

- Pre-specifying geometric criteria
- Comparing models with different capacity
- Avoiding circular selection on successful trials
- Separating information amount from representational organization

#### Dataset assumptions

- Behavioral correctness or related outcome contrasts may be available for later planning.
- Task variation may support a later generalization test, but exact condition structure is unknown.

## Family 006: Population geometry of brain-wide sensorimotor transformation

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

A family asking whether sensory-to-choice transformation is organized as invariant shared geometry or region-specific transformation, with separate geometry-invariance and predictive-routing variants.

### Shared scientific tension

Brain-wide evidence and preparation signals may reflect a shared population organization propagated across regions, region-specific transformations, or common task and movement inputs; broad encoding alone does not distinguish these accounts.

### Family structure

- Semantic axes: theoretical_tension; population_scope; target_contrast; claim_level; discriminating_observation; outcome_meaning
- Distinctions that should not be merged: Cross-region geometric correspondence and temporally ordered predictive dependence are different properties.; Shared geometry can exist without routing-like prediction, while predictive dependence can occur between geometrically dissimilar populations.
- Proposal-stage uncertainties: Whether cross-region population observations permit comparable or joint geometric analysis; Whether common sensory and movement inputs can be represented adequately; Whether temporal prediction can be distinguished from event locking
- Dataset assumptions: Broad regional sampling and task standardization may support later comparative planning.; Exact simultaneous coverage, anatomical comparability, and temporal resolution remain unverified.

### Reviewed literature context used by the family

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)
- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

### Variant 006.001: Geometry-invariance variant

- Shortlist disposition: **Not carried into planning — deferred: a close prior sits near this variant and a distinguishing revision is required first. A content-bearing, DOI-identified brain-wide decision-making study substantially overlaps the proposed sensory-evidence-to-action phenomenon, cross-region scope, and population-level account. It reports distributed evidence integration, shared population patterns encoding evidence and movement preparation, and distinct execution dynamics across many regions. The candidate is not a direct recap because the cited abstract does not establish the candidate's specific invariant-versus-ordered-transformation geometry contrast, nor an adjudication against common external drive. However, the overlap is close enough that the proposal must make those distinctions scientifically explicit. Compared against: https://doi.org/10.1038/s41586-024-07908-w; https://doi.org/10.1101/2023.02.08.527772 To distinguish it: Specify the target sensorimotor pathway, region classes, and task epochs for which an ordered transformation is predicted, and distinguish this from the prior report's brain-wide parallel evidence integration and shared evidence-preparation patterns. To distinguish it: Define the scientific equivalence relation for a shared geometry versus a transformation: identify which representational relations must be preserved across regions, which changes count as an ordered transformation, and which region-by-stage pattern would falsify each account. To distinguish it: Separate geometry specifically linking sensory evidence to choice from geometry associated with movement preparation and execution, because the prior reports shared evidence-preparatory patterns together with distinct movement-execution dynamics. To distinguish it: Make the common-input alternative discriminable: the claimed cross-region relation must remain attributable to an inter-regional shared organization or transformation after accounting for stimulus-locked, choice-locked, and movement-related influences that could induce apparent similarity. To distinguish it: Distinguish the proposed account from communication-subspace alignment and routing: establish whether the intended cross-region relation concerns a stable task representation, directed transformation along sensorimotor stages, or flexible network-specific propagation.**
- Distinction axes: theoretical_tension, population_scope, target_contrast
- Distinct from sibling variants: This variant asks whether representational geometry is preserved or transformed across regions; it does not primarily test temporal routing or behavioral prediction.

#### Question

Does the population geometry linking sensory evidence to choice preserve a shared organization across major brain regions, or transform systematically along the sensorimotor pathway?

#### Scientific tension and why it matters

Similar encoded variables across regions may occupy homologous geometries, undergo region-specific transformations, or appear similar because of common external drive.

Testing geometry and its cross-region invariance would move beyond inventories of encoded variables toward a discriminating description of distributed transformation.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is an invariance-versus-transformation question across brain populations rather than another demonstration that evidence or preparation is widespread.

#### Relevant literature

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Mixed selectivity can support high-dimensional and flexibly decodable representations, but determining whether observed mixing is linear, nonlinear, categorical, or category-free remains an important analysis problem.
  - Sources: [Nonlinear mixed selectivity supports reliable neural computation (2020); 10.1371/journal.pcbi.1007544](https://doi.org/10.1371/journal.pcbi.1007544); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Closest known work

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- The question of whether learned prior probability is represented broadly across sensory, motor, and higher-level brain regions during mouse visual decisions has already been answered in International Brain Laboratory recordings and imaging.
  - Sources: [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)
- The International Brain Laboratory's public brain-wide decision-task resource has already been reused to characterize cortical representational organization and to study distributed encoding of prior information in mouse decision-making.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878); [Brain-wide representations of prior information in mouse decision-making (2025); 10.1038/s41586-025-09226-1](https://doi.org/10.1038/s41586-025-09226-1)

#### Dataset leverage hypothesis — not a feasibility certification

Standardized task measurements and broad anatomical sampling may allow a later planner to compare theory-relevant population geometry across major regions.

#### Competing explanations

- Cross-region similarity reflects common sensory, choice, or movement inputs rather than shared organizing geometry.
- Apparent transformations reflect unequal sampling, reliability, or dimensionality across regions.

#### Discriminating observation

A reproducible geometric relation that either remains invariant or changes in an ordered way across regions and task stages, beyond common-input alternatives, would distinguish shared-organization and transformation accounts.

#### What different outcomes would mean

- Positive: Systematic invariance or transformation would provide a stronger population-level description of brain-wide sensorimotor organization.
- Negative: No reproducible cross-region relation would weaken the premise of a common geometric account.
- Null: Mixed or sampling-sensitive relations would leave open a mosaic organization without a single brain-wide geometry.

#### Ambiguities

- shared geometry
- systematic transformation
- sensorimotor pathway
- geometric invariance

#### Planning challenges

- Comparing geometry across non-identical populations
- Unequal regional sampling and reliability
- Separating common inputs from intrinsic organization
- Avoiding visual-embedding interpretations

#### Dataset assumptions

- Anatomical context and standardized task structure may support later cross-region comparison.
- A later planner must test whether population observations are comparable enough for geometry estimation.


### Variant 006.002: Predictive-routing variant

- Shortlist disposition: **Active for planning**
- Distinction axes: claim_level, discriminating_observation, outcome_meaning
- Distinct from sibling variants: This variant asks whether time-varying cross-region relationships incrementally predict transformation stages; the sibling concerns cross-region geometric invariance or transformation.

#### Question

Do time-varying cross-region population relationships predict the transition from sensory evidence to movement preparation better than independent local representations or common task inputs?

#### Scientific tension and why it matters

A distributed transformation may involve temporally ordered routing among populations, independent parallel representations, or shared input that creates predictive temporal relationships without communication.

A predictive comparison can constrain distributed-routing accounts while explicitly avoiding causal claims from temporal association.

#### Proposal-stage novelty hypothesis — not a verdict

The question contrasts temporally ordered cross-region prediction with independent-local and common-input accounts rather than equating widespread activity with communication.

#### Relevant literature

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Choice probability in sensory cortex is not by itself evidence that sensory variability causes choice: it can combine an early bottom-up component with a later top-down component associated with decision build-up.
  - Sources: [Sensory integration dynamics in a hierarchical network explains choice probabilities in cortical area MT (2015); 10.1038/ncomms7177](https://doi.org/10.1038/ncomms7177)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)

#### Closest known work

- In a learned mouse visual decision task, evidence integration and movement preparation were distributed across many brain areas, with shared population patterns encoding evidence and preparation separately from movement-execution dynamics.
  - Sources: [Brain-wide dynamics linking sensation to action during decision-making (2024); 10.1038/s41586-024-07908-w](https://doi.org/10.1038/s41586-024-07908-w)
- Motor-cortical population dynamics do not generalize uniformly across movements: low-dimensional autonomous-like dynamics observed during reaching were not found during grasping, which appeared more input-driven.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848)

#### Dataset leverage hypothesis — not a feasibility certification

Time-aligned population, stimulus, choice, response-time, and movement measurements may support later planning of predictive contrasts among routing accounts.

#### Competing explanations

- Cross-region temporal prediction is generated by shared sensory or movement inputs rather than inter-population routing.
- Apparent ordering reflects differences in measurement sensitivity or event-locking across regions.

#### Discriminating observation

Cross-region population state information that adds held-out prediction of later preparation-related states beyond local history, task inputs, and measured movement would favor a routing-like predictive account.

#### What different outcomes would mean

- Positive: Incremental prediction would support a temporally organized distributed-transformation description, without establishing physical communication.
- Negative: No incremental prediction would favor independent-local or common-input explanations over routing-like organization.
- Null: Symmetric or unstable prediction would leave direction and organization unresolved.

#### Ambiguities

- routing
- population relationship
- movement preparation
- incremental prediction

#### Planning challenges

- Separating shared input from cross-region dependence
- Avoiding causal interpretation of predictive timing
- Accounting for non-simultaneous or uneven population coverage
- Matching temporal scales across regions and behavior

#### Dataset assumptions

- Task-aligned regional activity may support later predictive temporal comparison.
- Exact joint cross-region coverage and synchronization must be verified by a downstream planner.
