#!/bin/bash
# Verifier entrypoint. Harbor copies tests/ to /tests and runs this in the agent's
# container after the rollout ends. Nothing may be installed here: rollouts have
# no internet, so pytest is baked into environment/Dockerfile.
#
# Deliberately NOT `set -e`: a failing pytest must still reach the reward write.
set -uo pipefail

mkdir -p /logs/verifier

python3 -m pytest -p no:cacheprovider --rootdir=/tests -rA /tests/test_outputs.py
rc=$?

if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
