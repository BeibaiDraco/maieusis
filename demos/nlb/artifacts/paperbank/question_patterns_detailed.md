# Detailed question-formation patterns

These pages expand the compact PatternBank summary for scientific reading. They describe reviewed question-forming moves; they do not establish novelty, dataset feasibility, or a scientific result.

## Pattern 001: Turn heterogeneous unit responses into a population-level functional test

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Individual measurements appear heterogeneous, mixed, or difficult to interpret using simple selectivity categories.
- Paper-local precedents suggest that distributed population structure can contain separable information or implement computations not evident at the level of individual units.
- The relationship between population organization, candidate readouts or computations, and behavior remains unresolved.

### Unresolved tension

Apparent disorder may be redundant or uninterpretable variation, or it may reflect organized population structure whose dimensions, trajectories, or subspaces enable computations unavailable from single-unit or simple-selectivity accounts alone.

### Dataset cues

- Population measurements spanning multiple task variables, contexts, conditions, or time points.
- Behavioral measurements that can distinguish choices, levels of performance, or theoretically diagnostic error types.
- Repeated observations sufficient to characterize population dimensions, trajectories, subspaces, decoding generalization, or related representational structure.
- Task variation that allows competing functional accounts of the population structure to make distinguishable neural or behavioral predictions.

### Question-forming move

Shift from classifying individual units to asking what population organization adds beyond single-unit or simple-selectivity accounts. Isolate that added structure using an analysis appropriate to the source problem—such as component control, subspace decomposition, or trajectory and geometry analysis—then test whether it supports discriminating readout or model predictions and relates to behavior through choice, performance differences, or predicted error types.

### Scientific payoff

Connects difficult-to-interpret response heterogeneity to a testable account of computation and behavior rather than merely relabeling complex activity. Population dynamics can support this move when observed trajectories are compared with competing mechanisms and a trained recurrent model is reverse-engineered as a hypothesis generator; population geometry can support it when subspace relations turn a binding-versus-abstraction trade-off into predictions about separability, generalization, and characteristic errors. These are complementary instances of testing what distributed structure contributes to readout-relevant function.

### What different outcomes would mean

- Positive: If population dimensions, trajectories, or subspace relations provide discriminating information or mechanistic predictions beyond unit-level descriptions and exhibit the predicted relationship to choice, performance, generalization, or error structure, heterogeneity gains support as functionally organized population structure.
- Negative: If the proposed population organization fails to distinguish competing mechanisms, improve or constrain readout-relevant predictions, support expected generalization, or show the predicted behavioral relationship, the specific functional interpretation is weakened; unit-level descriptions, alternative population organizations, or different mechanisms remain viable.

### Common failure modes

- Treating dimensionality, decoding accuracy, trajectory visualization, or subspace separation alone as evidence of functional use.
- Selecting a population summary without showing that it distinguishes the competing computational or representational accounts that motivated the analysis.
- Conflating reduced information with altered representational organization when interpreting performance differences or errors.
- Treating a trained dynamical model that reproduces observations as direct proof of the biological mechanism.
- Inferring binding, abstraction, or generalization from subspace geometry without testing the distinct readout and behavioral predictions implied by that geometry.
- Interpreting resampled or manipulated populations as independently observed populations.
- Assuming that a low-dimensional projection, task-related axis, or subspace is itself the biological mechanism.

### Details that should not be transferred

- The source demonstrations use particular prefrontal or reward-related systems, species, tasks, recording arrangements, and operational definitions of mixed selectivity or population structure.
- Classical-selectivity removal and correct-versus-error dimensionality comparisons are specific implementations from one source and are not required steps of the cross-paper pattern.
- Recurrent-network reverse-engineering depends on paper-specific model assumptions and serves as a mechanistic hypothesis generator rather than direct biological proof.
- The binding-versus-abstraction interpretation depends on a paper-specific subspace framework and on task manipulations capable of distinguishing generalization from characteristic misbinding errors.
- Specific dimensionality estimators, decomposition procedures, trajectory models, decoding analyses, and linear-readout assumptions do not transfer automatically.

### Source PaperCases and formation traces

- Source 1: [Rigotti et al., 2013, “The importance of mixed selectivity in complex cognitive tasks”](papers/nature12160.md) · [Question-formation trace](formation_traces/nature12160.md)
- Source 2: [Mante, Sussillo, Shenoy &amp; Newsome (2013), “Context-dependent computation by recurrent dynamics in prefrontal cortex”](papers/nature12742.md) · [Question-formation trace](formation_traces/nature12742.md)
- Source 3: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. (2024). Semi-orthogonal subspaces for value mediate a binding and generalization trade-off. Nature Neuroscience.](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)

## Pattern 002: Test a model-predicted latent geometry and its invariance

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A mechanistic theory predicts a specific organization of joint population states rather than only individual response patterns.
- Existing observations are compatible with the theory but do not directly identify the predicted geometry.
- Alternative mechanisms may generate a similar pattern under a single condition.

### Unresolved tension

A matching latent geometry may reflect an intrinsic organizing mechanism, inherited input statistics, or a condition-specific coincidence; geometry alone does not adjudicate among these accounts.

### Dataset cues

- Dense simultaneous population sampling sufficient to recover joint states.
- Repeated measurements under altered inputs, environments, contexts, or behavioral states.
- A theory that predicts both geometric structure and how that structure should persist or change across conditions.

### Question-forming move

Translate the theoretical geometry into a measurable population signature, recover it from joint activity, and test both its presence and its predicted invariance or transformation across conditions that alter external drive.

### Scientific payoff

Turns an abstract network or coding theory into a discriminating empirical test and uses condition dependence to distinguish intrinsic organization from input-derived structure.

### What different outcomes would mean

- Positive: Finding the predicted geometry with the expected cross-condition stability supports the proposed organizing principle and narrows the plausible mechanisms.
- Negative: Absent, unstable, or differently transformed geometry weakens the target account and favors input-dependent, lower-dimensional, feedforward, or otherwise alternative explanations.

### Common failure modes

- Treating visual resemblance in an embedding as sufficient evidence of topology or mechanism.
- Testing only the positive geometric signature without its predicted invariance.
- Ignoring sampling density, noise, repeated-measure reliability, or estimator bias.
- Claiming that a recovered geometry uniquely identifies recurrent circuitry when alternative mechanisms can produce it.

### Details that should not be transferred

- One source targets a toroidal manifold in a particular spatial-navigation system and uses topological methods.
- Another source tests eigenspectrum scaling and smoothness in a particular sensory representation.
- The relevant geometry, invariance conditions, and quantitative predictions must come from the domain-specific theory rather than being copied across systems.

### Source PaperCases and formation traces

- Source 1: [High-dimensional geometry of population responses in visual cortex — Carsen Stringer, Marius Pachitariu, Nicholas A. Steinmetz, Matteo Carandini and Kenneth D. Harris (2019)](papers/s41586-019-1346-5.md) · [Question-formation trace](formation_traces/s41586-019-1346-5.md)
- Source 2: [Gardner et al., “Toroidal topology of population activity in grid cells”](papers/s41586-021-04268-7.md) · [Question-formation trace](formation_traces/s41586-021-04268-7.md)

## Pattern 003: Use controlled inputs to distinguish competing dynamical mechanisms

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Behavior can be explained by multiple computational strategies or dynamical mechanisms.
- Paper-local theory contrasts input filtering or input-driven accumulation with selection, routing, or autonomous dynamics inside the measured circuit.
- Individual responses or aggregate behavior do not identify where or when the computation occurs.

### Unresolved tension

The same behavioral output may arise from early filtering, persistent input representation, context-dependent routing, gradual accumulation, or a later autonomous regime.

### Dataset cues

- Known, time-resolved inputs or concurrently present relevant and irrelevant inputs.
- Context or task variables that change input relevance without simply removing the alternatives.
- Simultaneous population measurements and behavioral choices.

### Question-forming move

Estimate population trajectories or flow without defining the answer from behavior alone, compare relevant and irrelevant input effects over time, and test candidate transitions or routing mechanisms against explicit behavioral consequences.

### Scientific payoff

Links flexible behavior to an interpretable population mechanism and separates the computation's timing and locus from behavioral performance alone.

### What different outcomes would mean

- Positive: Model-specific trajectories or a transition that predicts a change in later input influence would support a particular routing, accumulation, or commitment mechanism.
- Negative: Continued behavioral influence after a proposed transition, or trajectories inconsistent with the predicted mechanism, would reject that interpretation and preserve competing accounts.

### Common failure modes

- Imposing the favored dynamical model during discovery and then treating the fit as independent validation.
- Confounding a neural transition with movement, reward, or another task event.
- Inferring physical causality from predictive temporal relationships alone.
- Using low-dimensional trajectories without checking whether discarded activity changes the conclusion.

### Details that should not be transferred

- The source tasks use specific sensory modalities, contexts, choice reports, and timing structures.
- One source relies on a trained recurrent model as a hypothesis generator; another uses a paper-specific flow-field and transition framework.
- Exact transition definitions and neural modes are not transferable without validation in the new system.

### Source PaperCases and formation traces

- Source 1: [Mante, Sussillo, Shenoy &amp; Newsome (2013), “Context-dependent computation by recurrent dynamics in prefrontal cortex”](papers/nature12742.md) · [Question-formation trace](formation_traces/nature12742.md)
- Source 2: [Luo et al., “Transitions in dynamical regime and neural mode during perceptual decisions”](papers/s41586-025-09528-4-1.md) · [Question-formation trace](formation_traces/s41586-025-09528-4-1.md)

## Pattern 004: Disambiguate target-specific structure from competing explanations with standardized joint measurement

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- Paper-local studies disagree about whether a measured pattern reflects a target construct, a simpler state variable, immediate external input, or another correlated process.
- Comparisons are fragmented because prior work used non-comparable tasks, samples, regions, measurement settings, or external-input conditions.
- Broad spatial extent may be scientifically important in some applications, but in others the primary issue is whether apparently noisy or ambiguous variation contains structured information.
- The identity of the target and the competing variable differs by application: rich behavior may itself be the target rather than a nuisance.

### Unresolved tension

An observed pattern may contain structure specific to the scientific target or may instead be explained by a simpler competing variable, immediate external input, or another correlated process. Standardized comparisons across input conditions and jointly measured alternatives can distinguish these interpretations. Where broad comparable sampling is available and spatial organization is theoretically relevant, the same move can additionally test whether target-specific structure is localized or distributed, but spatial extent need not be the primary tension.

### Dataset cues

- A shared task or measurement framework that permits comparable assessment of the target across sites, processing levels, or conditions relevant to the application.
- Controlled contrasts that reduce or remove immediate external evidence, including comparisons between spontaneous no-stimulus periods and stimulus-driven periods where available.
- Concurrent measurements that distinguish the target construct from plausible alternatives; depending on the application, these may contrast a latent computation with embodied variables or a rich multidimensional behavioral representation with simpler arousal or state measures such as pupil or locomotion.
- Broad comparable sampling when localized-versus-distributed organization is an independently motivated part of the application.

### Question-forming move

First specify which measured construct is the scientific target and which variables represent competing explanations; the primary goal is to test target specificity, not necessarily to resolve spatial placement. Compare target-related structure under a shared design, use reduced- or no-external-input conditions alongside input-driven conditions to distinguish ongoing structure from immediate evidence, and test whether the pattern remains after accounting for application-specific alternatives. When broad comparable sampling and a spatial hypothesis are available, additionally ask whether the surviving target-specific structure is concentrated or distributed across processing levels. When rich behavior is the target, compare it against simpler arousal or state variables rather than treating behavior itself as a nuisance.

### Scientific payoff

Converts ambiguous or fragmented observations into a common-scale test of whether measured variation contains target-specific structure rather than reflecting immediate input or a competing variable. Where justified, it also clarifies spatial extent without assuming in advance that localization is the central scientific issue.

### What different outcomes would mean

- Positive: Structure that remains associated with the target after comparison with competing variables supports a target-specific interpretation. Persistence across reduced- or no-input and input-driven conditions further clarifies whether the structure depends on immediate external evidence. In applications with a spatial hypothesis, structure extending across processing levels supports a distributed account, whereas concentration in specialized stages supports a more localized account.
- Negative: If target-related structure is absent, fails to persist when immediate external input is reduced, or is accounted for by a competing variable, then a broad target-specific interpretation is weakened. This instead supports an input-dependent, low-dimensional state, alternative-variable, noise-like, or otherwise restricted account according to which contrast fails. Where spatial extent is being tested, absence outside limited stages specifically favors a localized over a distributed interpretation.

### Common failure modes

- Equating detectability in many sites with local computation in every site.
- Making spatial extent the primary question when the application's central tension concerns target specificity or structured variation instead.
- Calling predictive temporal relations communication or causation without stronger evidence.
- Ignoring uneven sampling, registration quality, or measurement sensitivity across sites.
- Treating reduced- or no-input conditions as if they perfectly isolate the target construct.
- Failing to define whether behavioral measurements are the target representation or an alternative explanation before applying controls.
- Assuming that richer multidimensional behavior and simpler arousal or state measures are interchangeable constructs.

### Details that should not be transferred

- The source cases use mouse neural recordings, particular decision and visual paradigms, and specific behavioral-video measurements.
- The target-versus-confound assignment is source-specific: embodied movement, posture, or eye variables are alternatives to a prior representation in one case, whereas multidimensional behavior is the target and simpler pupil or locomotion measures are competing state explanations in the other.
- The localized-versus-distributed dimension is central in one source but secondary to the noise-versus-structured-representation tension in the other; it should therefore be included only when independently motivated by an application.
- The availability and quality of behavioral measurements and broad recording coverage vary across sessions.
- The exact manipulations or periods used to reduce immediate sensory evidence—low- or zero-contrast trials versus spontaneous no-stimulus periods—are paradigm-specific.

### Source PaperCases and formation traces

- Source 1: [Brain-wide representations of prior information in mouse decision-making](papers/ibl-s41586-025-09226-1.md) · [Question-formation trace](formation_traces/ibl-s41586-025-09226-1.md)
- Source 2: [C. Stringer et al., Science 364, eaav7893 (2019)](papers/science-aav7893.md) · [Question-formation trace](formation_traces/science-aav7893.md)

## Pattern 005: Reframe nuisance variability through selective geometric alignment

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A population-level variable is commonly summarized by its magnitude and treated as noise or nuisance variation.
- Available evidence suggests that the variable may contain structured components related to represented signals, behavior, or coding limits.
- The scientific interpretation therefore depends on where the variability lies relative to candidate signal dimensions, not merely on how much variability exists.

### Unresolved tension

Shared variability may be a generic fluctuation that obscures coding, or its geometry may identify dimensions associated with represented information, ongoing behavior, or information-limiting structure; these possibilities require comparisons tailored to the evidence available in each setting.

### Dataset cues

- Population measurements or purpose-built models that permit shared variability or covariance structure to be estimated separately from the candidate signal dimensions being compared.
- Representational, stimulus-related, behavioral, or tuning-derived directions against which variability geometry can be evaluated.
- Where available, relevant and irrelevant features, multiple contexts, behavioral outcomes, or causal manipulations that can test whether an observed alignment is selective and functionally consequential; these extensions are not required in every application.
- For analytical or simulation cases, control over covariance structure, signal direction, and system size sufficient to distinguish alignment-dependent effects from effects of overall correlation magnitude.

### Question-forming move

Replace a coarse question about the amount of population variability with a structural question about its orientation relative to independently defined candidate signal dimensions. The basic move is to compare variability geometry with represented, behavioral, or tuning-derived directions and ask whether alignment distinguishes competing functional and nuisance accounts. When the evidence permits, strengthen this move by contrasting task-relevant with task-irrelevant axes, testing recurrence across contexts, and relating alignment to behavior or causal effects; these are extensions of the shared move rather than requirements instantiated by every cited case.

### Scientific payoff

Distinguishes explanations that predict different geometric relationships even when they permit similar overall variability. Across the cited cases, the common payoff is to determine whether structure relative to a signal direction—not variability magnitude alone—clarifies behavioral prediction, coexistence with sensory representations, or information limitation. Selective relevant-versus-irrelevant alignment, cross-task recurrence, and behavioral or causal validation provide a stronger functional interpretation only where those evidence types are available.

### What different outcomes would mean

- Positive: Alignment that selectively tracks an independently defined signal, predicts an associated outcome, or explains a limiting coding effect would support the claim that variability geometry carries scientifically meaningful structure beyond its overall magnitude; stronger functional conclusions would require the corresponding behavioral, cross-context, or causal evidence.
- Negative: Absent or nonselective alignment, alignment confined to broad state dimensions, or failure of the proposed geometry to explain behavioral or coding outcomes would favor a nuisance, generic-state, or correlation-magnitude account and would limit claims that variability identifies functionally used dimensions.

### Common failure modes

- Estimating variability and comparison axes from the same observations without safeguards against circularity or overfitting.
- Treating any subspace overlap as selective alignment without suitable alternative axes, non-limiting covariance structures, or other comparison conditions.
- Requiring behavioral or perturbation evidence in analytical, simulation, or observational settings that do not contain it, or implying that its absence invalidates the narrower geometric test.
- Equating geometric alignment with causal readout, recurrent mechanism, or behavioral use when the available evidence is associational or theoretical.
- Assuming a single leading component captures all meaningful shared variability or that overall correlation magnitude determines its consequences.
- Generalizing relevant-versus-irrelevant contrasts or cross-context recurrence from one empirical instantiation to all applications of the pattern.

### Details that should not be transferred

- In source paper 1, the supported sub-move is multidimensional behavior prediction plus comparison of behavioral and sensory population subspaces. It does not include an explicit task-relevant-versus-task-irrelevant axis contrast, cross-task recurrence test, or perturbation evidence, and its conclusions are associational.
- In srinath-et-al-2026, the fuller instantiation includes independently estimating a shared-variability axis, contrasting task-relevant and task-irrelevant representations, examining recurrence across tasks or areas, and relating alignment to behavioral and causal evidence. Those extensions should not be attributed to the other cited cases.
- In source paper 3, the alignment move is an analytical and simulation-based analogue: differential correlations aligned with the tuning-curve-derivative direction are contrasted with non-limiting correlation structure. It does not empirically compare task-relevant and task-irrelevant representational axes or test cross-task recurrence, behavioral prediction, or perturbation effects.
- The operationalization of shared variability by a particular principal component is specific to one source and is not required by the cross-paper abstraction.
- The recurrent-circuit interpretation depends on model-specific connectivity, input, and readout assumptions; the analytical information-limitation result likewise depends on its stated covariance and population-code framework.
- Species, sensory modality, task demands, behavioral measurements, information measures, and availability of cross-context or causal evidence constrain generalization.

### Source PaperCases and formation traces

- Source 1: [C. Stringer et al., Science 364, eaav7893 (2019)](papers/science-aav7893.md) · [Question-formation trace](formation_traces/science-aav7893.md)
- Source 2: [The structure of correlated variability reflects task-relevant information in sensory neurons](papers/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md) · [Question-formation trace](formation_traces/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md)
- Source 3: [Information-limiting correlations](papers/nn-3807.md) · [Question-formation trace](formation_traces/nn-3807.md)

## Pattern 006: Replace a coarse association with a task-aligned structural characterization

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A broad population statistic is widely associated with a limiting or beneficial outcome.
- Prior observations show that changing the statistic's overall magnitude does not consistently change performance or information.
- Theory suggests that only a component aligned with the task-relevant signal determines the limiting behavior.

### Unresolved tension

The outcome may depend on the amount of a population feature in general, or on a small, potentially masked structural component with a particular orientation relative to the signal.

### Dataset cues

- Analytical, simulated, or empirical systems in which overall magnitude and structure can be separated.
- A task-relevant direction, representation, or derivative against which alignment can be defined.
- Measurements across population size, task conditions, or contexts that expose limiting behavior.

### Question-forming move

Decompose the coarse statistic into task-aligned and non-aligned components, manipulate or compare them separately, and ask which component explains performance, information scaling, or behavioral readout.

### Scientific payoff

Prevents misleading conclusions from aggregate statistics and identifies the mechanistic structure that determines whether additional measurements contribute useful information.

### What different outcomes would mean

- Positive: If only the task-aligned component predicts the limit, global reduction or amplification of the statistic is not a general intervention principle; interpretation must focus on structure.
- Negative: If overall magnitude predicts outcomes independently of alignment, the proposed structural account is insufficient and a broader mechanism remains plausible.

### Common failure modes

- Conflating pairwise magnitude with population covariance structure.
- Using finite populations to make unsupported asymptotic claims.
- Assuming one information or performance measure generalizes to every task.
- Failing to test whether the proposed aligned component can be reliably estimated.

### Details that should not be transferred

- The analytical source focuses on covariance structure, population scaling, and a particular information measure.
- The empirical reuse source defines a dominant shared axis with a specific dimensionality-reduction choice.
- Model architectures, tuning assumptions, and decoder restrictions are source-specific.

### Source PaperCases and formation traces

- Source 1: [Information-limiting correlations](papers/nn-3807.md) · [Question-formation trace](formation_traces/nn-3807.md)
- Source 2: [The structure of correlated variability reflects task-relevant information in sensory neurons](papers/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md) · [Question-formation trace](formation_traces/srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.md)

## Pattern 007: Convert a representational trade-off into a population-geometry test

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A representational property may support one function while limiting another, but the relevant property differs by problem: subspace overlap can mediate binding versus abstraction, eigenspectrum decay can mediate expressivity versus smoothness, and population dimensionality can relate representational capacity to behavioral success.
- Competing accounts predict distinguishable population structures or different relationships between a geometric statistic and an experimentally varied condition.
- Paper-local precedents provide ways to measure subspace overlap, population dimensionality, readout-relevant structure, or eigenspectrum scaling.

### Unresolved tension

The shared tension is not a single overlap-based mechanism but uncertainty about whether measurable population geometry resolves a functional coding trade-off. This can appear as partial subspace separation balancing binding and abstraction, eigenspectrum structure balancing expressive dimensionality and smoothness, or population dimensionality distinguishing functionally useful mixed representations from structure that does not support successful behavior.

### Dataset cues

- Population measurements broad and repeated enough to estimate a theory-relevant geometric statistic such as subspace overlap, dimensionality, or eigenspectrum structure.
- Variation in inputs, task-relevant features, experimental conditions, or behavioral correctness that permits competing geometric predictions to be compared.
- A source-appropriate functional criterion or proxy, which may be neural discrimination and cross-condition generalization, dependence on manipulated input dimensionality, readout-relevant information, or behavior; direct behavioral and transfer outcomes are not required in every application.

### Question-forming move

Translate a functional coding tension into competing predictions for a population-geometric statistic, then test whether that statistic changes with or explains a source-appropriate contrast—such as feature binding versus cross-condition generalization, eigenspectrum scaling across input dimensionalities, or dimensionality and readout structure across successful and unsuccessful behavior. Treat intermediate geometry as one possible prediction when theory motivates it, not as a universal requirement.

### Scientific payoff

Turns an abstract coding trade-off into a falsifiable relationship between population structure and an experimentally distinguishable condition or functional consequence, while allowing the relevant geometric statistic and validation criterion to differ across scientific settings.

### What different outcomes would mean

- Positive: A population-geometric statistic that follows the predicted condition dependence or relationship to a relevant neural or behavioral outcome would support the proposed account of how representational structure addresses the functional tension.
- Negative: Failure of the predicted geometric relationship, persistence under conditions expected to alter it, or dissociation from the relevant neural or behavioral outcome would weaken that account and favor an alternative geometry, an input-driven explanation, or a different mechanism linking representation to function.

### Common failure modes

- Assuming that every representational trade-off requires an intermediate geometry rather than deriving source-specific competing predictions.
- Selecting the geometric statistic or defining a favorable regime only after inspecting the data.
- Inferring functional benefit from population geometry without a source-appropriate manipulation, readout comparison, generalization test, or behavioral contrast.
- Treating orthogonality in a reduced projection as complete independence or treating dimensionality and eigenspectrum measures as interchangeable.
- Generalizing beyond the sampled inputs, task conditions, positions, times, populations, or behavioral outcomes.

### Details that should not be transferred

- The intermediate parallel-versus-orthogonal subspace framing, decoding generalization, and spatial or temporal behavioral-error predictions belong specifically to the binding-versus-abstraction source.
- The smoothness source tests eigenspectrum scaling against manipulated sensory-input dimensionality and reports no direct behavioral or transfer outcome in its formation trace; its interpretation depends on mathematical assumptions linking input dimensionality, eigenspectrum decay, and smoothness.
- The mixed-selectivity source relates dimensionality and readout-relevant population structure to correct-versus-error trials without an explicit overlap or extremes-versus-intermediate test.
- The binding source concerns value representations associated with a limited set of positions and presentation times.
- Subjective-value models, particular error categories, component-removal procedures, stimulus ensembles, and specific geometry estimators remain source-bound.

### Source PaperCases and formation traces

- Source 1: [Johnston, W. Jeffrey; Fine, Justin M.; Yoo, Seng Bum Michael; Ebitz, R. Becket; Hayden, Benjamin Y. (2024). Semi-orthogonal subspaces for value mediate a binding and generalization trade-off. Nature Neuroscience.](papers/s41593-024-01758-5.md) · [Question-formation trace](formation_traces/s41593-024-01758-5.md)
- Source 2: [High-dimensional geometry of population responses in visual cortex — Carsen Stringer, Marius Pachitariu, Nicholas A. Steinmetz, Matteo Carandini and Kenneth D. Harris (2019)](papers/s41586-019-1346-5.md) · [Question-formation trace](formation_traces/s41586-019-1346-5.md)
- Source 3: [Rigotti et al., 2013, “The importance of mixed selectivity in complex cognitive tasks”](papers/nature12160.md) · [Question-formation trace](formation_traces/nature12160.md)

## Pattern 008: Use richer concurrent measurements to adjudicate alternative explanations

- Review authority: `ai_reviewed`
- Transfer scope: `cross_paper`

### Starting scientific state

- A target signal is observed in population measurements but may reflect unmeasured behavior, arousal, posture, movement, or another correlated process.
- Existing studies often use only coarse covariates, leaving residual ambiguity.
- Paper-local methodological precedents show that richer naturalistic measurements can recover multiple behavioral dimensions.

### Unresolved tension

The target signal may encode the scientific construct of interest, or it may be a proxy for a richer behavioral or state process omitted from conventional controls.

### Dataset cues

- Synchronized population measurements and high-dimensional behavioral or state observations.
- Periods or task conditions that vary the target construct independently of immediate external input.
- Held-out data suitable for comparing predictive contributions rather than only in-sample correlation.

### Question-forming move

Represent the alternative explanation at multiple dimensions, test its held-out prediction of the target population signal, compare it with simpler covariates, and reassess the target interpretation after accounting for the richer measurements.

### Scientific payoff

Makes confound analysis part of question formation and can either strengthen a latent-representation claim or reveal that apparently unexplained activity has meaningful behavioral structure.

### What different outcomes would mean

- Positive: If the target signal survives rich alternative-explanation controls, its construct interpretation is strengthened; if rich covariates explain substantial activity, variability previously labeled noise gains a structured behavioral interpretation.
- Negative: Failure of richer measurements to predict the signal preserves non-behavioral explanations, while complete explanation by those measurements weakens claims of an independent latent representation.

### Common failure modes

- Treating prediction as proof that behavior causes neural activity.
- Assuming recorded behavior exhausts all relevant internal or motor variables.
- Using high-dimensional covariates without cross-validation or leakage controls.
- Discarding behavior-related signals as nuisance even when they are themselves scientifically meaningful.

### Details that should not be transferred

- The source cases use species-specific facial, postural, ocular, and movement measurements.
- Video availability and measurement quality are uneven in some recordings.
- Specific pose-estimation, reduced-rank prediction, and subspace procedures are implementations rather than universal requirements.

### Source PaperCases and formation traces

- Source 1: [Brain-wide representations of prior information in mouse decision-making](papers/ibl-s41586-025-09226-1.md) · [Question-formation trace](formation_traces/ibl-s41586-025-09226-1.md)
- Source 2: [C. Stringer et al., Science 364, eaav7893 (2019)](papers/science-aav7893.md) · [Question-formation trace](formation_traces/science-aav7893.md)
