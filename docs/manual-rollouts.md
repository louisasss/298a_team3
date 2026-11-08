# Manual Canary Rollout Guide

The application uses Argo Rollouts with the following canary progression:

- 10%
- pause
- 25%
- pause
- 50%
- pause
- 100%

Each pause is indefinite and requires a manual action before the rollout continues.

## Check Rollout Status

```bash
kubectl argo rollouts get rollout app
```

## Promote a Rollout

To advance the rollout from its current paused step:

```bash
kubectl argo rollouts promote app
```

Run the status command again to confirm the rollout advanced:

```bash
kubectl argo rollouts get rollout app
```

## Abort a Rollout

To stop an unhealthy or unwanted rollout:

```bash
kubectl argo rollouts abort app
```

Check the rollout status afterward:

```bash
kubectl argo rollouts get rollout app
```

Traffic should return to the stable version.

## Recover After an Abort

Recovery can be performed by reverting to the previous working image or retrying with a corrected image.

After updating the image, verify the new rollout with:

```bash
kubectl argo rollouts get rollout app
```