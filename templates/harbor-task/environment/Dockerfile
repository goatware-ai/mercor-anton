# Agent image. Nothing from solution/ may ever be copied in here.
#
# Both rollouts must start from the same frozen state, so the base is pinned by
# digest. To re-pin after changing the tag:
#   docker buildx imagetools inspect python:<tag>
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

# Rollouts have no internet, so anything the verifier needs at trial time must be
# baked in here. pytest is also available to the agent, which the prompt allows.
RUN pip install --no-cache-dir pytest==9.1.1

# This task has the agent create its own starting file, so /workspace ships empty.
# A task over an existing repository copies that snapshot in at its base commit.
WORKDIR /workspace
