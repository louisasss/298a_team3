# Manual Canary Rollout Guide

The application uses Argo Rollouts with a manual canary deployment strategy.

The rollout progresses through the following stages:

- 10% canary traffic
- pause
- 25% canary traffic
- pause
- 50% canary traffic
- pause
- 100% canary traffic

Each pause is indefinite. The rollout will not continue to the next stage until a manual action is performed.

This allows the team to inspect the canary version before increasing its exposure. If the canary appears healthy, the rollout can be promoted. If a problem is detected, the rollout can be aborted and traffic can return to the stable version.

## Check Rollout Status

Use the following command to inspect the current rollout:

```bash
kubectl argo rollouts get rollout app
```

The output shows information such as:

- current rollout status
- current canary step
- configured traffic weight
- stable and canary images
- ReplicaSet status
- pod readiness

During a normal manual rollout, the rollout should enter a paused state at the configured checkpoints.

For example:

```text
Status:          Paused
Message:         CanaryPauseStep
SetWeight:       10
```

This means the rollout reached the 10% canary stage and is waiting for a manual decision.

## Promote a Rollout

If the canary is healthy, promote the rollout to the next stage:

```bash
kubectl argo rollouts promote app
```

After promoting, check the rollout again:

```bash
kubectl argo rollouts get rollout app
```

The rollout should advance to the next configured step.

For this rollout strategy, the progression is:

```text
10% -> pause
25% -> pause
50% -> pause
100%
```

Because there are pauses after 10%, 25%, and 50%, three manual promote actions are required to move the rollout from the first pause to 100%.

Once the rollout reaches 100%, the canary becomes the new stable version and the rollout should return to a Healthy state.

## Abort a Rollout

If the canary is unhealthy, unwanted, or should not continue, abort the rollout:

```bash
kubectl argo rollouts abort app
```

Then check the rollout status:

```bash
kubectl argo rollouts get rollout app
```

After an abort:

- the rollout stops progressing
- the canary ReplicaSet is scaled down
- the previous stable version continues serving traffic
- the configured canary weight returns to 0
- the Rollout enters a Degraded state because the attempted update did not complete

An aborted rollout may show output similar to:

```text
Status:          Degraded
Message:         RolloutAborted