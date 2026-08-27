# Detailed Question Scientist families

This page preserves every proposed family and variant, including options that were not shortlisted for planning. Novelty and dataset leverage below are proposal-stage hypotheses, not verdicts or feasibility certifications.

- Families proposed: 6
- Authority ceiling: `verified`

## Family 001: Functional alignment of shared variability during perceptual decisions

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Tests whether shared trial-to-trial variability is scientifically informative because of its orientation relative to sensory or choice-related population structure, rather than because of its overall magnitude.

### Shared scientific tension

Noise correlations may be largely nonspecific fluctuations, or their geometry may selectively align with population dimensions carrying sensory evidence or impending choice. These alternatives can produce similar average correlation magnitudes but different functional interpretations.

### Family structure

- Semantic axes: target_contrast: sensory evidence versus impending choice; outcome_meaning: stimulus discriminability versus behavioral prediction; discriminating_observation: selective alignment relative to different independently defined axes
- Distinctions that should not be merged: Sensory coding and choice prediction are different scientific outcomes and can dissociate even when estimated from the same task.; A covariance component can align with sensory evidence without aligning with choice, or vice versa, so combining them would obscure the central contrast.
- Proposal-stage uncertainties: Whether reliable shared-variability geometry can be estimated within relevant recordings; Whether sensory, choice, and behavioral axes can be defined independently enough to avoid circularity; Whether pose and task measurements have suitable joint availability; Whether observed alignment generalizes across populations or is region-specific
- Dataset assumptions: The released measurements may allow population-level covariance and task representation to be related at proposal-stage granularity.; Broad anatomical sampling may support comparisons, but coverage should not be treated as uniform.; A later planner must test all measurement, timing, and joint-coverage requirements.

### Reviewed literature context used by the family

- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

### Variant 001.001: Sensory-code alignment branch

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, outcome_meaning
- Distinct from sibling variants: This variant defines sensory evidence as the target axis and stimulus discriminability as the scientific outcome; it does not ask whether covariance aligns with impending choice.

#### Question

Is shared trial-to-trial variability selectively aligned with sensory-evidence representations, and does that alignment predict reduced or preserved stimulus discriminability beyond overall noise-correlation magnitude?

#### Scientific tension and why it matters

The contested effect of noise correlations on information may be resolved by their orientation relative to sensory evidence rather than by their mean strength.

A sensory-alignment result would connect the open origin and information-limitation debates to a brain-wide empirical signature without assuming that all correlations are detrimental.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is to compare sensory-aligned and non-aligned shared variability across a standardized brain-wide decision setting rather than revisit the already-answered generic encoding-versus-decoding question.

#### Relevant literature

- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Representational-geometry analyses offer an intermediate description linking population activity to cognitive or computational models, and newer two-factor cross-validation and bootstrap procedures aim to support inference that generalizes across both subjects and experimental conditions.
  - Sources: [Representational geometry: integrating cognition, computation, and the brain (2013); 10.1016/j.tics.2013.06.007](https://doi.org/10.1016/j.tics.2013.06.007); [Statistical inference on representational geometries (2023); 10.7554/elife.82566](https://doi.org/10.7554/elife.82566)
- Already answered close prior: whether noise correlations can affect population information differently for encoding and decoding has been directly analyzed in simultaneously recorded neurons; the reported effects were small in that sample, with somewhat larger effects on encoding than decoding and larger predicted effects for larger ensembles.
  - Sources: [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)

#### Closest known work

- Already answered close prior: whether noise correlations can affect population information differently for encoding and decoding has been directly analyzed in simultaneously recorded neurons; the reported effects were small in that sample, with somewhat larger effects on encoding than decoding and larger predicted effects for larger ensembles.
  - Sources: [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Dataset leverage hypothesis — not a feasibility certification

The combination of population spiking, sensory conditions, and broad anatomical sampling may allow a later planner to test whether sensory alignment has consistent or region-dependent associations with discriminability.

#### Competing explanations

- Apparent alignment reflects generic covariance or finite-sample geometry rather than a sensory-specific component.
- Alignment reflects movement, internal state, or choice-related variation correlated with sensory condition.
- Measurement and spike-sorting errors distort both covariance and the estimated sensory direction.

#### Discriminating observation

Independently estimated shared variability would show stronger alignment with sensory-evidence directions than with matched alternative directions, and the aligned component—not overall correlation magnitude—would predict held-out sensory discriminability.

#### What different outcomes would mean

- Positive: Would support a structural account in which the orientation of shared variability helps explain when noise correlations constrain sensory coding.
- Negative: Would weaken sensory-alignment accounts and shift attention toward other task dimensions, nonspecific fluctuations, or region-specific mechanisms.
- Null: Would indicate that the available observations do not distinguish sensory-aligned structure from alternatives, preserving uncertainty about whether the construct is absent or insufficiently measured.

#### Ambiguities

- noise correlation
- sensory-evidence direction
- information-limiting alignment
- stimulus discriminability

#### Planning challenges

- Estimating covariance and sensory directions without circularity
- Separating stimulus-related means from trial-to-trial variability
- Handling heterogeneous sampling and repeated-measure structure
- Assessing sensitivity to spike-sorting limitations

#### Dataset assumptions

- Repeated sensory conditions may permit proposal-stage separation of mean sensory responses from residual variability.
- Some recordings may contain populations suitable for geometric characterization; a later planner must test this.
- Anatomical labels may support coarse comparisons but do not imply uniform regional coverage.


### Variant 001.002: Choice and behavior alignment branch

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, outcome_meaning, discriminating_observation
- Distinct from sibling variants: This variant targets choice-related geometry and behavioral prediction after alternative-explanation controls, rather than sensory discriminability and sensory-axis alignment.

#### Question

Is shared trial-to-trial variability selectively aligned with choice-related population structure, and does that alignment predict choices or response-time variation after distinguishing sensory and embodied alternatives?

#### Scientific tension and why it matters

Choice-aligned covariance could reflect behaviorally relevant decision-state variation, but it could instead be inherited from sensory evidence, movement, trial history, or internal state.

Distinguishing these accounts would clarify whether choice-aligned noise is a meaningful predictive signature of decision formation or merely a correlated by-product.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is a brain-wide comparison of choice alignment against sensory and embodied alternative axes, while retaining an associational claim level.

#### Relevant literature

- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)

#### Closest known work

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Dataset leverage hypothesis — not a feasibility certification

Joint neural, choice, response-time, and pose measurements may allow later planning of held-out comparisons among choice, sensory, and behavioral alignment.

#### Competing explanations

- Choice alignment is inherited from sensory-evidence variation rather than decision formation.
- Choice alignment is generated by movement, posture, arousal, reward expectation, or trial history.
- A broad global fluctuation aligns spuriously with several task dimensions.

#### Discriminating observation

A choice-aligned covariance component would predict held-out choice or response-time variation after comparison with sensory-aligned, movement-related, and generic high-variance directions.

#### What different outcomes would mean

- Positive: Would support the predictive interpretation that covariance geometry contains choice-relevant structure beyond coarse correlation strength.
- Negative: Would favor sensory, embodied, or nonspecific explanations over a distinct choice-aligned component.
- Null: Would leave unresolved whether choice alignment is absent or cannot be separated from correlated task and behavioral variables.

#### Ambiguities

- choice-related direction
- decision-state variation
- response-time relevance
- embodied alternative

#### Planning challenges

- Avoiding choice leakage when defining population axes
- Representing high-dimensional behavior without overfitting
- Separating pre-choice from movement-related activity
- Accounting for trial history and laboratory or subject structure

#### Dataset assumptions

- Choice and response-time observations may be linkable to neural activity at suitable temporal granularity.
- Pose information may be available for at least a usable subset, which a later planner must verify.
- The observational design cannot by itself establish causal readout or decision mechanism.

## Family 002: Input-linked versus internally generated origins of correlated variability

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Uses temporal and task-condition dependence to ask whether correlated variability is primarily inherited from sensory input or sustained by internal decision and state processes.

### Shared scientific tension

Limited sensory input, circuit organization, and internal fluctuations can all generate information-limiting correlations, but they predict different changes in covariance around sensory input and decision formation.

### Family structure

- Semantic axes: theoretical_tension: inherited sensory uncertainty versus internally generated fluctuations; discriminating_observation: input-locked transformation versus post-input persistence; outcome_meaning: sensory-condition dependence versus prediction of decision timing
- Distinctions that should not be merged: Input dependence and temporal persistence make different predictions and can coexist in distinct covariance components.; Combining the branches would obscure whether sensory conditions or later behavioral variation provide the principal discriminator.
- Proposal-stage uncertainties: Whether task conditions provide sufficiently distinct sensory-drive contrasts; Whether temporal measurements separate immediate input, deliberation, and movement; Whether covariance persistence is distinguishable from recording nonstationarity; Whether trial-history and pose alternatives are jointly available
- Dataset assumptions: The task narrative suggests known sensory events and response timing but does not certify exact temporal coverage.; Repeated decision trials may support later covariance comparisons.; A later planner must determine whether the proposed contrasts are identifiable.

### Reviewed literature context used by the family

- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

### Variant 002.001: Sensory-input origin branch

- Shortlist disposition: **Active for planning**
- Distinction axes: theoretical_tension, discriminating_observation
- Distinct from sibling variants: This branch asks whether covariance transforms with external sensory drive; the sibling asks whether covariance persists and predicts later behavior beyond immediate input.

#### Question

Does correlated variability track the strength and timing of sensory drive in a manner consistent with an input-linked origin?

#### Scientific tension and why it matters

If covariance is inherited from uncertain sensory input, its structure should transform systematically with sensory evidence; internally generated fluctuations need not show the same dependence.

This would provide an observational discriminator among proposed origins of information-limiting correlations without equating correlation magnitude with mechanism.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal moves from generic correlation effects to time-resolved, condition-dependent covariance signatures in a standardized decision task.

#### Relevant literature

- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)

#### Closest known work

- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Already answered close prior: whether noise correlations can affect population information differently for encoding and decoding has been directly analyzed in simultaneously recorded neurons; the reported effects were small in that sample, with somewhat larger effects on encoding than decoding and larger predicted effects for larger ensembles.
  - Sources: [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)

#### Dataset leverage hypothesis — not a feasibility certification

Known sensory events and neural activity over task trials may allow a later planner to compare covariance structure across sensory conditions and task epochs.

#### Competing explanations

- Condition dependence reflects changes in firing statistics or estimator reliability rather than shared input.
- Movement or arousal covaries with sensory condition and produces the apparent transformation.
- Internally generated decision states are themselves modulated by sensory evidence.

#### Discriminating observation

Covariance geometry would change predictably with sensory evidence and emerge in temporal relation to input, while comparable internal-state or movement controls would not explain the pattern.

#### What different outcomes would mean

- Positive: Would support an input-linked account as a useful explanation for part of the observed correlated variability.
- Negative: Would weaken a simple inherited-input account and motivate internally generated or circuit-specific alternatives.
- Null: Would leave input-linked and internal accounts unresolved if covariance changes are weak, inconsistent, or inseparable from measurement effects.

#### Ambiguities

- sensory drive
- input-linked covariance
- information-limiting pattern
- task epoch

#### Planning challenges

- Comparing covariance across conditions with different activity levels
- Separating immediate input responses from later decisions and movements
- Establishing temporal reliability of geometric estimates
- Avoiding mechanistic overinterpretation of observational timing

#### Dataset assumptions

- Sensory conditions may vary sufficiently for coarse contrasts.
- Task timing may support separation of input-proximal and later activity, subject to planner verification.
- Repeated observations may allow covariance estimation in some populations.


### Variant 002.002: Persistent internal-state origin branch

- Shortlist disposition: **Active for planning**
- Distinction axes: theoretical_tension, outcome_meaning, discriminating_observation
- Distinct from sibling variants: This branch treats post-input persistence and response-time prediction as the discriminator for internal dynamics, rather than covariance transformation with sensory drive.

#### Question

Does correlated variability persist beyond immediate sensory drive and predict subsequent decision timing in a manner consistent with internally generated state or decision dynamics?

#### Scientific tension and why it matters

Persistent covariance may reflect endogenous decision-state dynamics, but it may also be lingering sensory activity, trial history, reward expectation, or movement preparation.

A persistent predictive signature would narrow the open origin question toward internal processes while preserving the distinction between association and causal mechanism.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal links persistence of covariance geometry to response-time variation across brain-wide populations rather than treating pre-decision variability as undifferentiated noise.

#### Relevant literature

- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Closest known work

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Dataset leverage hypothesis — not a feasibility certification

Neural activity, response times, trial history, and pose may allow later planning of predictive contrasts between persistent internal structure and immediate-input or embodied explanations.

#### Competing explanations

- Persistent covariance is a slow sensory response rather than an internal decision state.
- Trial history, reward context, arousal, or movement preparation produces the behavioral prediction.
- Nonstationarity or recording drift creates apparent temporal persistence.

#### Discriminating observation

A covariance component would remain identifiable after the input-proximal period and predict held-out response-time variation after accounting for sensory conditions, trial history, and measured behavior.

#### What different outcomes would mean

- Positive: Would support an internally linked predictive account of a component of correlated variability.
- Negative: Would favor input-proximal, embodied, or nonspecific accounts over persistent internal-state structure.
- Null: Would preserve uncertainty if persistence cannot be distinguished from slow sensory responses, nonstationarity, or weak measurement reliability.

#### Ambiguities

- internal state
- decision dynamics
- persistence
- response-time prediction

#### Planning challenges

- Defining periods without using behavior to predetermine the answer
- Separating persistence from recording nonstationarity
- Representing trial history and movement alternatives
- Preventing response-time leakage into neural feature construction

#### Dataset assumptions

- Temporal neural and behavioral measurements may allow pre-response comparisons.
- Trial history and pose may be available at useful granularity for some recordings.
- Any result would remain predictive or associational rather than causal.

## Family 003: Embodied and internal-state explanations of apparent noise correlations

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Asks whether apparently unexplained neural covariance is better understood as rich movement-related structure or as non-motor internal-state variation.

### Shared scientific tension

Residual correlations associated with choice and response time may reflect decision computation, but conventional controls may omit multidimensional behavior or internal state. Richer alternatives can either explain away a decision interpretation or reveal scientifically meaningful embodied structure.

### Family structure

- Semantic axes: target_contrast: multidimensional embodied behavior versus residual internal state; outcome_meaning: explaining away decision covariance versus revealing residual predictive structure; discriminating_observation: held-out pose prediction versus post-pose history and response-time prediction
- Distinctions that should not be merged: Movement-related structure and residual internal state are competing but not interchangeable constructs.; One branch can be positive while the other is negative, and merging them would obscure whether behavior is the scientific target or an alternative explanation.
- Proposal-stage uncertainties: Whether pose measurements capture the relevant behavioral dimensions; Whether internal state can be distinguished from unmeasured behavior; Whether temporal alignment is sufficient for held-out prediction; Whether residual covariance is stable against preprocessing and spike-sorting uncertainty
- Dataset assumptions: Neural, task, and pose measurements may overlap for some recordings.; The released pose information may support richer alternatives than coarse movement summaries, subject to later inspection.; No measured covariate set should be treated as exhaustive.

### Reviewed literature context used by the family

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

### Variant 003.001: Rich embodied-behavior branch

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, outcome_meaning
- Distinct from sibling variants: This branch treats multidimensional pose and movement as the principal alternative and asks how they revise decision-related covariance interpretations.

#### Question

How much apparently choice- or response-time-related shared neural variability is predictively accounted for by multidimensional pose and movement structure beyond simpler behavioral summaries?

#### Scientific tension and why it matters

Movement may be an omitted explanation for decision-related covariance, yet rich behavior could itself be a distributed neural target rather than a nuisance.

The result would refine interpretation of brain-wide noise correlations and prevent residual movement structure from being mislabeled as latent decision computation.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal evaluates multidimensional pose as an alternative explanation for covariance geometry, rather than merely adding a coarse movement control.

#### Relevant literature

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Closest known work

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)

#### Dataset leverage hypothesis — not a feasibility certification

Synchronized spiking, pose, choices, and response times may allow a later planner to compare rich embodied prediction with simpler behavioral alternatives.

#### Competing explanations

- Neural covariance reflects latent decision formation that happens to correlate with movement.
- A simpler global arousal or engagement variable explains both pose and neural activity.
- Pose prediction is inflated by temporal leakage or shared task timing.

#### Discriminating observation

Rich pose structure would predict held-out shared neural variability beyond simpler behavioral summaries and substantially alter the apparent choice- or response-time association.

#### What different outcomes would mean

- Positive: Would support an embodied interpretation of a substantial component of apparent neural noise while identifying behavior-related activity as scientifically structured.
- Negative: Would strengthen the case that measured movement is not the principal explanation for the target covariance.
- Null: Would leave ambiguity because weak prediction could reflect absent embodied structure or incomplete and uneven pose measurement.

#### Ambiguities

- rich behavior
- movement-related covariance
- choice-related residual
- behavioral nuisance

#### Planning challenges

- Uneven video or pose availability
- High-dimensional prediction with leakage and overfitting risks
- Temporal alignment of pose and neural activity
- Distinguishing movement preparation from execution

#### Dataset assumptions

- Pose measurements may be synchronized with neural activity for a suitable subset.
- Simple and richer behavioral descriptions may be constructible during later planning.
- Pose does not exhaust all embodied or internal variables.


### Variant 003.002: Residual internal-state branch

- Shortlist disposition: **Active for planning**
- Distinction axes: target_contrast, discriminating_observation, outcome_meaning
- Distinct from sibling variants: This branch targets the non-motor residual after rich movement adjustment and uses history and response-time prediction as its discriminator; the sibling makes embodied structure the target explanation.

#### Question

After accounting for measured movement, does a residual shared-variability component predict response-time and choice-history effects consistent with a non-motor internal state?

#### Scientific tension and why it matters

Residual covariance could index internal engagement, expectation, or history-dependent decision state, but it could also reflect unmeasured behavior or unstable neural measurement.

This branch tests whether richer movement adjustment reveals rather than eliminates a predictive internal-state signal.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is to define internal-state evidence as residual predictive structure after rich embodied alternatives, not merely as pre-stimulus neural variation.

#### Relevant literature

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)

#### Closest known work

- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)
- A live explanation-level tension is whether information-limiting noise correlations principally arise from limited sensory input, suboptimal connectivity, or internal fluctuations; these mechanisms can all reduce asymptotic information but predict different correlation patterns.
  - Sources: [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Dataset leverage hypothesis — not a feasibility certification

Behavior, trial history, response times, pose, and neural activity may permit later planning of nested predictive comparisons.

#### Competing explanations

- The residual is unmeasured movement, posture, or physiological state rather than a decision-related internal state.
- Trial-history associations arise from sensory or reward contingencies.
- Residual covariance reflects recording drift or spike-sorting instability.

#### Discriminating observation

A reliable residual covariance component would predict held-out response-time or history-dependent choice variation after rich pose adjustment and would not be reducible to generic recording drift.

#### What different outcomes would mean

- Positive: Would support a predictive distinction between embodied behavior and a non-motor internal-state component of shared variability.
- Negative: Would favor embodied, sensory, or measurement explanations over a separable internal-state account.
- Null: Would leave the internal-state construct unresolved because absence of residual prediction may reflect inadequate measurement of either neural covariance or alternatives.

#### Ambiguities

- internal state
- engagement
- history-dependent decision state
- residual covariance

#### Planning challenges

- Internal state is latent and multiply interpretable
- Residualization can remove shared scientific signal
- Trial history may be correlated with task conditions
- Measurement drift may mimic slow state variation

#### Dataset assumptions

- Trial sequence and response times may support history-related comparisons.
- Pose may provide a partial but not exhaustive movement description.
- Only predictive or associational claims are warranted.

## Family 004: Regional organization of behaviorally relevant covariance geometry

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Tests whether behaviorally relevant covariance follows a shared brain-wide geometry or consists of regionally distinct population solutions.

### Shared scientific tension

Decision and movement signals can be distributed across the brain, but distribution does not establish a common population mechanism. Similar behavior may be associated with a recurrent geometry across regions or with distinct local geometries.

### Family structure

- Semantic axes: population_scope: cross-region commonality versus regional specialization; claim_level: recurring descriptive motif versus differential predictive associations; outcome_meaning: shared organization versus distinct task-variable relationships
- Distinctions that should not be merged: A common recurring geometry and region-specific predictive geometries are competing organizational claims.; Distributed detectability cannot adjudicate between these claims without keeping recurrence and specialization as separate branches.
- Proposal-stage uncertainties: Which regional comparisons are sufficiently and comparably sampled; How to compare geometry across non-identical neural populations; Whether apparent regional differences generalize across subjects and laboratories; Whether common task timing explains cross-region similarity
- Dataset assumptions: Broad coverage may inspire regional comparisons but does not imply uniform coverage.; Standardized task structure may support common-scale comparisons.; A later planner must test anatomical, sampling, and repeated-measure requirements.

### Reviewed literature context used by the family

- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Dataset/resource reuse precedent: the public IBL Brain-wide Map dataset has been used to characterize selectivity and representational structure across 43 cortical regions, finding scale-dependent categorical organization and broadly high linear separability across areas.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878)

### Variant 004.001: Shared brain-wide motif branch

- Shortlist disposition: **Active for planning**
- Distinction axes: population_scope, claim_level
- Distinct from sibling variants: This branch tests cross-region recurrence and generalization of a common geometry; the sibling tests whether region-specific geometries carry distinct predictive relationships.

#### Question

Does a common covariance geometry aligned with sensory-to-choice progression recur across anatomically separated populations during decision formation?

#### Scientific tension and why it matters

Brain-wide recurrence would be consistent with a shared representational organization, whereas apparent commonality may arise from common task timing or external drive.

A recurring geometry would offer a stronger population-level account of distributed decision signals than widespread detectability alone.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal asks whether covariance geometry—not merely selectivity—recurs across broad anatomical populations in a shared decision setting.

#### Relevant literature

- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Representational-geometry analyses offer an intermediate description linking population activity to cognitive or computational models, and newer two-factor cross-validation and bootstrap procedures aim to support inference that generalizes across both subjects and experimental conditions.
  - Sources: [Representational geometry: integrating cognition, computation, and the brain (2013); 10.1016/j.tics.2013.06.007](https://doi.org/10.1016/j.tics.2013.06.007); [Statistical inference on representational geometries (2023); 10.7554/elife.82566](https://doi.org/10.7554/elife.82566)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

#### Closest known work

- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Dataset/resource reuse precedent: the public IBL Brain-wide Map dataset has been used to characterize selectivity and representational structure across 43 cortical regions, finding scale-dependent categorical organization and broadly high linear separability across areas.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878)

#### Dataset leverage hypothesis — not a feasibility certification

Broad anatomical sampling under a standardized task may allow a later planner to compare representational relations across suitably sampled populations.

#### Competing explanations

- Common geometry is imposed by shared sensory and motor events rather than a shared decision organization.
- Geometry appears similar because of analysis choices or unequal sampling.
- Only a subset of interconnected regions shares the organization, making a brain-wide claim misleading.

#### Discriminating observation

A geometry defined without pooling target populations would generalize across regions or recordings and retain similarity after comparison with task-timing, sensory, and movement alternatives.

#### What different outcomes would mean

- Positive: Would support a descriptive or predictive common organizational motif for behaviorally relevant covariance.
- Negative: Would weaken a shared brain-wide motif and favor regional specialization or heterogeneous solutions.
- Null: Would leave recurrence unresolved if cross-population estimates are too uncertain or sensitive to sampling.

#### Ambiguities

- common geometry
- recurrence
- sensory-to-choice progression
- brain-wide motif

#### Planning challenges

- Comparing geometries across non-identical populations
- Avoiding claims based on visual embedding similarity
- Accounting for uneven anatomical sampling
- Generalizing across subjects and conditions

#### Dataset assumptions

- Comparable task structure may permit cross-population geometric comparisons.
- Anatomical coverage may support selected regional contrasts but is not uniform.
- A later planner must determine which populations have adequate repeated observations.


### Variant 004.002: Region-specific solutions branch

- Shortlist disposition: **Active for planning**
- Distinction axes: population_scope, target_contrast, outcome_meaning
- Distinct from sibling variants: This branch treats reproducible regional heterogeneity and differential task associations as the target, rather than cross-region recurrence of one geometry.

#### Question

Do anatomically distinct populations exhibit different covariance geometries whose associations with sensory evidence, choice, movement, or response time imply region-specific computational solutions?

#### Scientific tension and why it matters

Regional differences may reflect distinct functional organizations, but they may instead arise from sampling, measurement quality, or differing mixtures of task variables.

Identifying structured regional heterogeneity would constrain claims that distributed decision signals instantiate one common mechanism.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal connects regional covariance geometry to distinct behavioral and task associations rather than cataloguing regional correlation magnitudes.

#### Relevant literature

- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Dataset/resource reuse precedent: the public IBL Brain-wide Map dataset has been used to characterize selectivity and representational structure across 43 cortical regions, finding scale-dependent categorical organization and broadly high linear separability across areas.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878)

#### Closest known work

- Dataset/resource reuse precedent: the public IBL Brain-wide Map dataset has been used to characterize selectivity and representational structure across 43 cortical regions, finding scale-dependent categorical organization and broadly high linear separability across areas.
  - Sources: [Rarely categorical and highly separable: how neural representations change along the cortical hierarchy (2024); 10.1101/2024.11.15.623878](https://doi.org/10.1101/2024.11.15.623878)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)

#### Dataset leverage hypothesis — not a feasibility certification

Broad multisite neural and behavioral measurements may allow later planning of region-sensitive comparisons under a common task framework.

#### Competing explanations

- Regional differences reflect unequal unit sampling or recording quality.
- Differences arise from varying sensory or movement mixtures rather than distinct population solutions.
- A common geometry is transformed by local readout or timing rather than replaced by region-specific mechanisms.

#### Discriminating observation

Regional geometries would differ reproducibly and show distinct held-out associations with sensory, choice, movement, or timing variables beyond what sampling-matched comparisons predict.

#### What different outcomes would mean

- Positive: Would support a descriptive or predictive account of region-specific population solutions.
- Negative: Would favor a common motif or indicate that regional distinctions do not organize behaviorally relevant covariance.
- Null: Would leave specialization unresolved if observed differences fail to generalize or cannot be separated from sampling heterogeneity.

#### Ambiguities

- region-specific solution
- functional specialization
- regional geometry
- distributed computation

#### Planning challenges

- Uneven regional coverage and population sizes
- Anatomical registration uncertainty
- Distinguishing genuine heterogeneity from measurement sensitivity
- Avoiding causal localization claims from detectability

#### Dataset assumptions

- Some regions may be sampled comparably enough for selected contrasts.
- Standardization may reduce but cannot eliminate laboratory and recording heterogeneity.
- Observed regional associations would not prove local computation.

## Family 005: Covariance geometry and alternative population accounts of evidence accumulation

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Connects noise-correlation geometry to competing temporal organizations of decision formation: a stable accumulation axis or a changing sequence of population states.

### Shared scientific tension

Behavior consistent with evidence accumulation can arise from persistent integration along a stable population direction or from sequential, time-varying population states. Shared variability may constrain these organizations differently.

### Family structure

- Semantic axes: theoretical_tension: persistent integration versus sequential state progression; discriminating_observation: stable axis over time versus reproducible information-preserving transitions; population_scope: common temporal organization versus potentially region-specific sequences
- Distinctions that should not be merged: Stable-axis and sequential accounts make incompatible predictions about temporal geometry despite potentially similar behavioral outputs.; A model averaging across time could make a sequence appear stable, so the two hypotheses require separate discriminating observations.
- Proposal-stage uncertainties: Whether the task has an identifiable decision-formation interval suitable for these contrasts; Whether temporal resolution and repeated observations distinguish stable from sequential geometry; Whether movement and event timing can be represented adequately; Whether accumulation is the appropriate behavioral construct for this task
- Dataset assumptions: Time-resolved population activity and response timing may support later comparison of temporal organizations.; Task observations may provide evidence-related contrasts, but exact operationalization belongs to planning.; Only descriptive, associational, or predictive conclusions are justified.

### Reviewed literature context used by the family

- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)

### Variant 005.001: Stable accumulation-axis branch

- Shortlist disposition: **Active for planning**
- Distinction axes: theoretical_tension, discriminating_observation, outcome_meaning
- Distinct from sibling variants: This variant predicts temporal invariance of one evidence-related direction; the sibling predicts time-varying sequential geometry that transfers evidence across states.

#### Question

Is behaviorally relevant shared variability aligned with a temporally stable evidence-accumulation direction whose state predicts choice and response time?

#### Scientific tension and why it matters

A stable direction would accord with persistent integration, but similar ramping and behavioral prediction can arise from time-varying sequences, common input, or movement preparation.

This branch tests whether covariance geometry helps distinguish a stable population decision variable from alternative temporal organizations.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal links the temporal stability of an accumulation-like direction to the orientation of shared variability across brain-wide populations.

#### Relevant literature

- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Choice-related and response-time-related neural signals are potentially confounded by internal state, reward expectation, trial history, and movement: pre-stimulus oscillatory power predicts later response time, while choice history and reward contingencies can alter fitted evidence-accumulation dynamics.
  - Sources: [The contribution of pre-stimulus neural oscillatory activity to spontaneous response time variability (2014); 10.1016/j.neuroimage.2014.11.057](https://doi.org/10.1016/j.neuroimage.2014.11.057); [Choice history biases subsequent evidence accumulation (2019); 10.7554/elife.46331](https://doi.org/10.7554/elife.46331); [Humans strategically shift decision bias by flexibly adjusting sensory evidence accumulation (2019); 10.7554/elife.37321](https://doi.org/10.7554/elife.37321)

#### Closest known work

- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Dataset leverage hypothesis — not a feasibility certification

Time-resolved neural activity, sensory evidence, choices, and response times may allow later planning of predictive tests of stable decision geometry.

#### Competing explanations

- A stable-looking direction averages over sequentially active populations.
- The direction reflects movement preparation or elapsed time rather than accumulation.
- Shared sensory drive creates both covariance alignment and choice prediction.

#### Discriminating observation

An independently estimated direction would remain geometrically stable over decision formation, track evidence in held-out observations, and predict choice or response time beyond elapsed time, sensory condition, and measured movement.

#### What different outcomes would mean

- Positive: Would support a predictive stable-axis account of evidence accumulation and specify how shared variability relates to it.
- Negative: Would weaken stable-axis interpretations and favor sequential, region-specific, or input-driven organizations.
- Null: Would leave the temporal organization unresolved if stable and sequential models are observationally indistinguishable at available resolution.

#### Ambiguities

- evidence-accumulation direction
- temporal stability
- decision variable
- persistent integration

#### Planning challenges

- Defining accumulation without assuming a fitted behavioral model is correct
- Separating elapsed time and movement preparation
- Estimating time-resolved geometry reliably
- Avoiding circular use of choice and response time

#### Dataset assumptions

- Task activity may span a period relevant to decision formation.
- Sensory, choice, and response-time observations may support predictive comparisons.
- The data cannot establish that a stable axis is a causal integrator.


### Variant 005.002: Sequential population-state branch

- Shortlist disposition: **Active for planning**
- Distinction axes: theoretical_tension, discriminating_observation, population_scope
- Distinct from sibling variants: This variant requires reproducible transitions among changing states and continuity of decision information, rather than temporal stability of a single accumulation direction.

#### Question

Is evidence accumulation associated with a sequence of changing population states whose covariance structure preserves choice-relevant information across time?

#### Scientific tension and why it matters

Sequential population activity may faithfully transfer accumulated evidence, but apparent sequences can result from heterogeneous response latencies, external events, or movement progression.

A sequence-sensitive test would distinguish changing population organization from a static decision-axis account and address whether different regions use common or distinct temporal solutions.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent contribution is to ask whether shared-variability geometry supports information continuity across changing population states in a brain-wide decision setting.

#### Relevant literature

- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Sequential evidence-accumulation models provide a core account of perceptual choice: sensory evidence is integrated over time and a decision is made when a decision variable reaches a bound; human electrophysiology has identified a supramodal signal whose buildup scales with evidence strength and predicts response time.
  - Sources: [A Role for Neural Integrators in Perceptual Decision Making (2003); 10.1093/cercor/bhg097](https://doi.org/10.1093/cercor/bhg097); [Internal and External Influences on the Rate of Sensory Evidence Accumulation in the Human Brain (2013); 10.1523/jneurosci.3355-13.2013](https://doi.org/10.1523/jneurosci.3355-13.2013)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)
- Multi-region recordings show that sensory, choice, and movement signals can be distributed brain-wide while retaining structured regional and temporal organization; in a memory-guided movement task, choice coding was concentrated in ALM-linked circuitry whereas movement representations were more broadly distributed.
  - Sources: [Brain-wide neural activity underlying memory-guided movement (2024); 10.1016/j.cell.2023.12.035](https://doi.org/10.1016/j.cell.2023.12.035)

#### Closest known work

- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

#### Dataset leverage hypothesis — not a feasibility certification

Time-resolved population activity under a common task may allow a later planner to compare sequential and stable geometric predictions across selected populations.

#### Competing explanations

- The sequence is a mixture of neurons with different event-locked latencies rather than evidence transfer.
- Movement progression or reward anticipation creates the temporal ordering.
- A stable latent accumulation direction appears sequential in observed unit coordinates.

#### Discriminating observation

Time-varying population states would preserve held-out evidence or choice information through reproducible transitions better than a stable-axis account, after comparison with event timing and pose-related sequences.

#### What different outcomes would mean

- Positive: Would support a predictive sequential organization of decision information and motivate region-sensitive hypotheses about evidence transfer.
- Negative: Would favor a stable-axis, input-driven, or non-sequential account of accumulation-related activity.
- Null: Would indicate that stable and sequential descriptions cannot be distinguished or that neither captures reliable task-related geometry.

#### Ambiguities

- choice-selective sequence
- evidence transfer
- population transition
- sequential accumulation

#### Planning challenges

- Distinguishing latent sequence from latency heterogeneity
- Separating neural transitions from task and movement events
- Comparing stable and time-varying representations fairly
- Accounting for discarded high-dimensional activity

#### Dataset assumptions

- Temporal sampling may permit characterization of changing population states.
- Pose and task events may support alternative-explanation tests where available.
- Observed temporal prediction would not demonstrate physical transfer or circuit causation.

## Family 006: Reproducibility of noise-correlation statistics and geometry across laboratories

- Shortlist disposition: **Shortlisted for planning; this is not scientific approval**
- Proposal review status: `model_generated`
- Authority ceiling: `verified`

### Scientific background

Distinguishes reproducibility of coarse correlation magnitude from reproducibility of task-aligned covariance geometry in a standardized multisite setting.

### Shared scientific tension

Standardized multisite processes may yield reproducible neural summaries, but existing process-level evidence does not establish whether noise correlations reproduce quantitatively. Coarse magnitude and functional geometry may have different reproducibility profiles.

### Family structure

- Semantic axes: outcome_meaning: reproducible aggregate magnitude versus reproducible functional geometry; claim_level: descriptive agreement versus predictive cross-laboratory generalization; discriminating_observation: matched coarse summaries versus held-out transfer of task alignment and behavioral association
- Distinctions that should not be merged: Correlation magnitude can fail to reproduce while task-aligned geometry reproduces, or the reverse.; The geometric branch requires preservation of relational and behavioral structure, a stronger and scientifically different criterion than agreement in a coarse statistic.
- Proposal-stage uncertainties: Whether sufficiently comparable populations and conditions exist across laboratories; How laboratory, subject, session, and anatomical effects can be distinguished; Whether geometric comparisons can generalize across non-identical populations; How sensitive results would be to spike-sorting and measurement-quality variation
- Dataset assumptions: The multisite design may support reproducibility questions but does not guarantee comparable question-specific coverage.; Standardized processes may reduce heterogeneity without eliminating it.; A later planner must determine the valid units and levels of cross-laboratory generalization.

### Reviewed literature context used by the family

- For cross-laboratory reproducibility, the International Brain Laboratory reports qualitative replication of a complex mouse behavior and Neuropixels recordings, supported by standardization, robust shared analysis pipelines, and collaboration infrastructure. This process-level evidence does not establish a quantitative relationship between noise correlations and either inter-laboratory variability or behavioral reproducibility.
  - Sources: [20 Lessons in Team Science: Learning from the Experience of the International Brain Laboratory (2025); 10.31234/osf.io/rfzch_v1](https://doi.org/10.31234/osf.io/rfzch_v1)
- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Representational-geometry analyses offer an intermediate description linking population activity to cognitive or computational models, and newer two-factor cross-validation and bootstrap procedures aim to support inference that generalizes across both subjects and experimental conditions.
  - Sources: [Representational geometry: integrating cognition, computation, and the brain (2013); 10.1016/j.tics.2013.06.007](https://doi.org/10.1016/j.tics.2013.06.007); [Statistical inference on representational geometries (2023); 10.7554/elife.82566](https://doi.org/10.7554/elife.82566)
- High-density extracellular recordings make spike sorting difficult because recordings can be nonstationary and electrical fields from nearby neurons can densely overlap; despite improved modern algorithms, synchronous collisions from neurons with similar extracellular signals can be missed.
  - Sources: [Spike sorting with Kilosort4 (2024); 10.1038/s41592-024-02232-7](https://doi.org/10.1038/s41592-024-02232-7); [How do spike collisions affect spike sorting performance? (2021); 10.1101/2021.11.29.470450](https://doi.org/10.1101/2021.11.29.470450)

### Variant 006.001: Coarse-statistic reproducibility branch

- Shortlist disposition: **Active for planning**
- Distinction axes: outcome_meaning, claim_level
- Distinct from sibling variants: This branch asks whether average or coarse correlation summaries reproduce; it does not require preservation of task-aligned covariance geometry.

#### Question

Are coarse summaries of noise-correlation magnitude reproducible across laboratories after accounting for subject, session, region, and behavioral-context heterogeneity?

#### Scientific tension and why it matters

Correlation magnitude may be a stable population property, or cross-laboratory variation may be dominated by biological context, sampling, and measurement differences.

This provides a necessary boundary on interpreting broad correlation-magnitude comparisons, while avoiding the unsupported assumption that process standardization guarantees quantitative neural reproducibility.

#### Proposal-stage novelty hypothesis — not a verdict

The proposal asks specifically about the reproducibility structure of noise-correlation magnitude in a multisite brain-wide resource, which the reviewed process-level evidence does not answer.

#### Relevant literature

- For cross-laboratory reproducibility, the International Brain Laboratory reports qualitative replication of a complex mouse behavior and Neuropixels recordings, supported by standardization, robust shared analysis pipelines, and collaboration infrastructure. This process-level evidence does not establish a quantitative relationship between noise correlations and either inter-laboratory variability or behavioral reproducibility.
  - Sources: [20 Lessons in Team Science: Learning from the Experience of the International Brain Laboratory (2025); 10.31234/osf.io/rfzch_v1](https://doi.org/10.31234/osf.io/rfzch_v1)
- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- High-density extracellular recordings make spike sorting difficult because recordings can be nonstationary and electrical fields from nearby neurons can densely overlap; despite improved modern algorithms, synchronous collisions from neurons with similar extracellular signals can be missed.
  - Sources: [Spike sorting with Kilosort4 (2024); 10.1038/s41592-024-02232-7](https://doi.org/10.1038/s41592-024-02232-7); [How do spike collisions affect spike sorting performance? (2021); 10.1101/2021.11.29.470450](https://doi.org/10.1101/2021.11.29.470450)
- Population-dynamic and mixed-selective coding results have important boundary conditions: motor-cortical dynamics differ between reach and grasp, mixed selectivity can vary with behavioral context and region, and estimates of neural contributions to perception depend on decision timescale and assumptions about noise correlations.
  - Sources: [Neural population dynamics in motor cortex are different for reach and grasp (2020); 10.7554/elife.58848](https://doi.org/10.7554/elife.58848); [Task-dependent mixed selectivity in the subiculum (2021); 10.1016/j.celrep.2021.109175](https://doi.org/10.1016/j.celrep.2021.109175); [Estimates of the Contribution of Single Neurons to Perception Depend on Timescale and Noise Correlation (2009); 10.1523/jneurosci.5179-08.2009](https://doi.org/10.1523/jneurosci.5179-08.2009)

#### Closest known work

- For cross-laboratory reproducibility, the International Brain Laboratory reports qualitative replication of a complex mouse behavior and Neuropixels recordings, supported by standardization, robust shared analysis pipelines, and collaboration infrastructure. This process-level evidence does not establish a quantitative relationship between noise correlations and either inter-laboratory variability or behavioral reproducibility.
  - Sources: [20 Lessons in Team Science: Learning from the Experience of the International Brain Laboratory (2025); 10.31234/osf.io/rfzch_v1](https://doi.org/10.31234/osf.io/rfzch_v1)
- Already answered close prior: whether noise correlations can affect population information differently for encoding and decoding has been directly analyzed in simultaneously recorded neurons; the reported effects were small in that sample, with somewhat larger effects on encoding than decoding and larger predicted effects for larger ensembles.
  - Sources: [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)

#### Dataset leverage hypothesis — not a feasibility certification

Multilaboratory standardized recordings may allow a later planner to partition reproducibility from subject, anatomical, and behavioral heterogeneity.

#### Competing explanations

- Laboratory differences reflect unequal anatomical or behavioral sampling rather than measurement reproducibility.
- Spike-sorting and recording-quality variation alter observed correlations.
- True biological heterogeneity across subjects or sessions exceeds laboratory effects.

#### Discriminating observation

Correlation-magnitude summaries would show consistent ordering or agreement across laboratories under sampling-matched comparisons and would remain distinguishable from subject, region, and behavioral-context variation.

#### What different outcomes would mean

- Positive: Would support the descriptive reproducibility of selected coarse correlation summaries under the studied framework.
- Negative: Would caution against treating correlation magnitude as a portable population descriptor across laboratories.
- Null: Would leave reproducibility unresolved if laboratory effects cannot be separated from biological and sampling heterogeneity.

#### Ambiguities

- reproducibility
- noise-correlation magnitude
- laboratory effect
- sampling-matched comparison

#### Planning challenges

- Separating laboratory from subject and anatomical composition
- Uneven regional and recording coverage
- Sensitivity to unit-quality and spike-sorting choices
- Defining reproducibility without post hoc thresholds

#### Dataset assumptions

- Laboratory context may be represented sufficiently for later hierarchical comparison.
- Standardization reduces some procedural differences but does not certify measurement equivalence.
- Comparable populations may exist for selected contrasts, subject to planner inspection.


### Variant 006.002: Functional-geometry reproducibility branch

- Shortlist disposition: **Active for planning**
- Distinction axes: outcome_meaning, discriminating_observation, claim_level
- Distinct from sibling variants: This branch makes cross-laboratory generalization of task-aligned geometry and behavioral association the outcome, explicitly contrasting it with reproducibility of coarse magnitude.

#### Question

Is task-aligned covariance geometry more reproducible across laboratories than coarse noise-correlation magnitude, and does any reproducible geometry retain similar behavioral associations?

#### Scientific tension and why it matters

Functional geometry might be robust despite variable correlation magnitude, but apparent geometric reproducibility could be imposed by common task structure or analysis choices.

This would test whether structural population descriptions provide a more portable scientific object than aggregate correlation strength.

#### Proposal-stage novelty hypothesis — not a verdict

The adjacent advance is a direct contrast between reproducibility of covariance magnitude and reproducibility of independently defined task alignment and behavioral association.

#### Relevant literature

- For cross-laboratory reproducibility, the International Brain Laboratory reports qualitative replication of a complex mouse behavior and Neuropixels recordings, supported by standardization, robust shared analysis pipelines, and collaboration infrastructure. This process-level evidence does not establish a quantitative relationship between noise correlations and either inter-laboratory variability or behavioral reproducibility.
  - Sources: [20 Lessons in Team Science: Learning from the Experience of the International Brain Laboratory (2025); 10.31234/osf.io/rfzch_v1](https://doi.org/10.31234/osf.io/rfzch_v1)
- Representational-geometry analyses offer an intermediate description linking population activity to cognitive or computational models, and newer two-factor cross-validation and bootstrap procedures aim to support inference that generalizes across both subjects and experimental conditions.
  - Sources: [Representational geometry: integrating cognition, computation, and the brain (2013); 10.1016/j.tics.2013.06.007](https://doi.org/10.1016/j.tics.2013.06.007); [Statistical inference on representational geometries (2023); 10.7554/elife.82566](https://doi.org/10.7554/elife.82566)
- The effect of noise correlations on population information is not determined by correlation magnitude alone: it depends on tuning heterogeneity, noise entropy, population size, and whether information is evaluated as encoding or decoding. Accordingly, reducing correlations does not necessarily improve decoding accuracy.
  - Sources: [The Effect of Noise Correlations in Populations of Diversely Tuned Neurons (2011); 10.1523/jneurosci.2539-11.2011](https://doi.org/10.1523/jneurosci.2539-11.2011); [Effects of Noise Correlations on Information Encoding and Decoding (2006); 10.1152/jn.00919.2005](https://doi.org/10.1152/jn.00919.2005)
- Open question within the recorded search scope: across tasks, regions, and recording modalities, it remains unresolved how the correlation structure, geometry, and mixed selectivity of population activity jointly constrain behaviorally relevant evidence accumulation and whether observed choice-selective sequences implement a common mechanism or region-specific circuit solutions.
  - Sources: [Neural circuit models for evidence accumulation through choice-selective sequences (2023); 10.1101/2023.09.01.555612](https://doi.org/10.1101/2023.09.01.555612); [The implications of categorical and category-free mixed selectivity on representational geometries (2022); 10.1016/j.conb.2022.102644](https://doi.org/10.1016/j.conb.2022.102644); [Origin of information-limiting noise correlations (2015); 10.1073/pnas.1508738112](https://doi.org/10.1073/pnas.1508738112)

#### Closest known work

- For cross-laboratory reproducibility, the International Brain Laboratory reports qualitative replication of a complex mouse behavior and Neuropixels recordings, supported by standardization, robust shared analysis pipelines, and collaboration infrastructure. This process-level evidence does not establish a quantitative relationship between noise correlations and either inter-laboratory variability or behavioral reproducibility.
  - Sources: [20 Lessons in Team Science: Learning from the Experience of the International Brain Laboratory (2025); 10.31234/osf.io/rfzch_v1](https://doi.org/10.31234/osf.io/rfzch_v1)
- Representational-geometry analyses offer an intermediate description linking population activity to cognitive or computational models, and newer two-factor cross-validation and bootstrap procedures aim to support inference that generalizes across both subjects and experimental conditions.
  - Sources: [Representational geometry: integrating cognition, computation, and the brain (2013); 10.1016/j.tics.2013.06.007](https://doi.org/10.1016/j.tics.2013.06.007); [Statistical inference on representational geometries (2023); 10.7554/elife.82566](https://doi.org/10.7554/elife.82566)

#### Dataset leverage hypothesis — not a feasibility certification

Standardized task observations across laboratories may allow later planning of cross-laboratory generalization tests for sensory-, choice-, or behavior-aligned covariance geometry.

#### Competing explanations

- Common task timing produces similar geometry without a shared functional organization.
- Analysis pipelines impose alignment or suppress genuine laboratory variation.
- Behavioral associations differ across laboratories even when geometry appears similar.

#### Discriminating observation

Task-aligned geometry estimated in some laboratory contexts would generalize to held-out contexts and preserve its association with behavior more consistently than coarse correlation magnitude.

#### What different outcomes would mean

- Positive: Would support task-aligned covariance geometry as a comparatively reproducible predictive population descriptor.
- Negative: Would indicate that structural geometry is no more portable than coarse magnitude or that laboratory and population context fundamentally shape it.
- Null: Would leave relative reproducibility unresolved if neither summary generalizes reliably or their uncertainty overlaps substantially.

#### Ambiguities

- geometric reproducibility
- task alignment
- cross-laboratory generalization
- portable population descriptor

#### Planning challenges

- Two-factor generalization across subjects and conditions
- Comparing geometry across non-identical neural populations
- Avoiding common-task leakage
- Separating laboratory context from anatomical composition

#### Dataset assumptions

- Shared task structure may enable cross-laboratory geometric comparison.
- Some task and behavioral conditions may recur across laboratories, subject to verification.
- The dataset narrative does not establish exact comparable joint coverage.
