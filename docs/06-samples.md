# Samples

> **Samples** — These samples demonstrate the expected quality of a task prompt. A prompt is reviewed together with its frozen repository, environment, tests, golden solution, and verification assets. A good prompt does not need to explain the implementation, but it must define enough observable behavior and scope for an expert and an agent to determine what success means.

## Good Samples

### Sample 1: Coordinated Graceful Shutdown

**Task category:** feature_implementation

**Approved Harbor task:** SWE Trajectory QC Good Samples

#### prompt:

hloop_stop_graceful(loop, drain_timeout_ms=3000) returns int, mirroring hloop_stop (0 ok, -1 null loop, -2 already stopped); 0 stops now, else HLOOP_STATUS_DRAINING: ios finish their write or close if idle, timers keep their own schedule but fire at most once more, then it stops when idle or timed out.\
stopGraceful(drain_timeout_ms=3000) on EventLoop and HttpServer; stopGraceful(drain_timeout_ms=3000, wait=false) on EventLoopThread and EventLoopThreadPool; stopGraceful(drain_timeout_ms=3000, wait=true) on TcpServer, TcpClient, UdpServer, UdpClient; all share one deadline; HttpServer's worker-thread mode also waits for in-flight requests. Channel gains DRAINING (between DISCONNECTED and CLOSED); isOpened() is false while draining.

#### Why this is a good task

- Defines observable shutdown behavior, return values, defaults, and state transitions.
- Requires coordinated changes across multiple related components.
- Introduces concurrency, timing, resource-lifecycle, and compatibility considerations.
- Leaves the internal implementation to the agent.
- Supports deterministic verification while still requiring engineering judgment about safe shutdown behavior.

### Sample 2: Event Batching for a Subscription Engine

**Task category:** feature_implementation

**Approved Harbor task:** SWE Trajectory QC Good Samples

#### Complete prompt

Add event batching functionality to the subscription engine.

The tests expect the following new interface and class structure:

Patchlevel\EventSourcing\Subscription\Subscriber\BatchableSubscriber:

beginBatch(): void

commitBatch(): void

rollbackBatch(): void

forceCommit(): bool

Patchlevel\EventSourcing\Subscription\Subscriber\RealSubscriberAccessor:

realSubscriber(): object (Update MetadataSubscriberAccessor to implement this interface).

Patchlevel\EventSourcing\Subscription\Engine\SubscriptionManager (internal):

\_\_construct(SubscriptionStore $subscriptionStore)

findForUpdate(SubscriptionCriteria $criteria, \Closure $closure): mixed

find(SubscriptionCriteria $criteria): array

add(Subscription ...$subscriptions): void

update(Subscription ...$subscriptions): void

remove(Subscription ...$subscriptions): void

flush(): void

Update DefaultSubscriptionEngine to use SubscriptionManager for all store interactions. The engine must trigger batch lifecycle methods on BatchableSubscriber instances: beginBatch when handling the first event of a batch, commitBatch and position updates only when the batch finishes (loop end, limit reached, or forceCommit returning true), and rollbackBatch if an error occurs.

Verify implementation with tests/Unit/Subscription/Engine/DefaultSubscriptionEngineTest.php, tests/Unit/Subscription/Engine/SubscriptionManagerTest.php, and tests/Unit/Subscription/Subscriber/MetadataSubscriberAccessorTest.php.

#### Why this is a good task

- States the required public contracts and lifecycle behavior precisely.
- Covers normal completion, forced completion, position updates, and rollback.
- Requires state management and coordinated changes across interfaces, storage, and engine behavior.
- Names the verification surface without supplying the implementation.
- Allows trajectory review to distinguish a robust lifecycle implementation from one that only handles the happy path.

### Sample 3: Multiple Rules in a textX Abstract-Rule Alternative

**Task category:** bug_fix_deterministic

**Approved Harbor task:** SWE Trajectory QC Good Samples

#### Complete prompt

The textX parser currently prohibits referencing more than one rule in a single alternative of an abstract rule, raising a TextXSemanticError during metamodel construction. We want to remove this restriction and properly handle the results when such an alternative is matched.

If an abstract rule matches multiple sub-nodes:

If all nodes are "match rules" (rules with no assignments), their string values should be concatenated into a single result.

If there are "common rules" (object-generating rules), the result should be the first instance created.

For example, in a grammar like BaseCommand: (Require | Group) '.'?, matching Require and a dot should return a string, while matching Group should return its object instance.

#### Why this is a good task

- Identifies the current failure and the desired observable behavior.
- Defines separate semantics for two meaningful result shapes.
- Includes a concrete example that clarifies the requirement.
- Requires understanding parser behavior and the repository's rule model.
- Does not prescribe which parser internals must be changed.

### Sample 4: Decimal and Fraction Support in a Solver

**Task category:** bug_fix_deterministic

**Approved Harbor task:** SWE Trajectory QC Good Samples

#### Complete prompt

LP problem definitions and result evaluations currently fail when using Decimal or Fraction numeric types instead of floats. Please update the solver framework to support these types in variable bounds, objectives, and constraints, and ensure they are handled correctly during expression evaluation in solver results.

#### Why this is a good task

- Describes a real compatibility failure rather than prescribing a patch.
- Identifies every major behavior surface that must support the new numeric types.
- Requires tracing values through problem construction and result evaluation.
- Allows multiple valid implementations consistent with repository conventions.
- Is concise while remaining bounded and objectively verifiable against the supplied repository and tests.

### Sample 5: Remove a Redundant Import Utility

**Task category:** refactor

**Approved Harbor task:** SWE Trajectory QC Good Samples

#### Complete prompt

The fancyImport utility is redundant and overcomplicates our module loading and testing. Please remove it from the codebase, refactor all its callsites to use standard imports, and simplify the associated tests.

#### Why this is a good task

- States the refactor's motivation, scope, and intended end state.
- Requires finding and updating all affected callsites and tests.
- Makes removal of the obsolete path part of completion.
- Preserves flexibility in how standard imports are introduced.
- Allows reviewers to assess completeness, behavioral preservation, and whether unnecessary complexity was actually removed.

## Bad Samples

### Sample 1: Vague Feature Request

**Intended category:** feature_implementation

#### Complete prompt

Add graceful shutdown support to the networking library. Connections should finish properly before the application exits, and the shutdown process should be safe and efficient. Update anything necessary and add tests.

#### Why this is a bad task

- “Finish properly,” “safe,” and “efficient” are undefined.
- The affected APIs, resources, states, timeout behavior, and compatibility requirements are missing.
- There is no deterministic completion condition.
- Different implementations could satisfy completely different interpretations of the request.

### Sample 2: Solution-Leaking Bug Fix

**Intended category:** bug_fix_deterministic

#### Complete prompt

Fix the parser failure by opening src/parser/abstract.py, removing the len(nodes) > 1 error check, and changing process_abstract_result() to join every string node with "". If any node is not a string, return nodes[0]. Add exactly two tests in tests/test_abstract.py using the names test_multiple_match_rules and test_multiple_common_rules.

#### Why this is a bad task

- Supplies the target files, condition, algorithm, return logic, and test structure.
- Converts the task into patch transcription rather than engineering work.
- May force an incorrect implementation, such as returning the first node instead of the first object-generating result.
- Rejects valid alternative solutions without expressing a product or compatibility reason.

### Sample 3: Artificially Trivial Change

**Intended category:** refactor

#### Complete prompt

Rename the local variable tmp to temporaryValue in src/helpers.js. Update the one reference in the following line and run the formatter. Do not make any other changes.

#### Why this is a bad task

- Requires no meaningful investigation or engineering judgment.
- Has one obvious mechanical solution.
- Produces no useful trajectory or artifact-quality comparison.
- Artificially labels a cosmetic edit as a software-engineering refactor.

### Sample 4: Unbounded Migration

**Intended category:** codebase_migration

#### Complete prompt

Replace the application's current SQL persistence layer with a modern NoSQL database. Migrate all existing data and update the entire codebase to use the new system. The application must remain reliable, scalable, and backward compatible. Choose whichever database and migration strategy you think is best.

#### Why this is a bad task

- Does not select a target system or define the source schema and supported data.
- Has no bounded scope, rollout sequence, rollback requirement, or compatibility period.
- “Reliable” and “scalable” have no measurable definitions.
- Likely exceeds the available task time and resources.
- Cannot be reproduced or verified from a frozen package as written.

### Sample 5: Unverifiable Performance Request

**Intended category:** performance_optimization

#### Complete prompt

Make the parser at least ten times faster for real customers without increasing memory usage. Test it against current production traffic and optimize whichever parts appear slow. The optimized version must feel instantaneous under heavy load.

#### Why this is a bad task

- Does not provide a frozen benchmark, workload, baseline, hardware allocation, or measurement method.
- Depends on inaccessible and changing production traffic.
- “Feel instantaneous” and “heavy load” are subjective.
- The ten-times target cannot be reproduced fairly across environments.
- It provides no correctness or regression requirements while encouraging arbitrary optimization.

## Creator Takeaway

A strong prompt defines the requested outcome, observable behavior, boundaries, and important constraints while leaving implementation decisions to the agent. It must work with a frozen Harbor package to support reproducible verification. Reject prompts that are vague, trivial, solution-leaking, unbounded, dependent on unavailable systems, or impossible to verify deterministically.
