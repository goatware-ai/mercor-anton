FROM node:20-slim

RUN apt-get update && apt-get install -y \
    git curl ca-certificates patch build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN git clone https://github.com/DeusData/codebase-memory-mcp.git /workspace/repo && cd /workspace/repo && \
    BASE=9987a4eae00a7ea2beda3f56ce3fa386f2fda085 && \
    cur_branch="$(git rev-parse --abbrev-ref HEAD)" && \
    git reset --hard "$BASE" && \
    git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do \
      [ "$b" = "$cur_branch" ] || git branch -D "$b"; \
    done && \
    git remote | xargs -r -n1 git remote remove && \
    rm -f .git/config.lock && \
    git reflog expire --expire=now --all && \
    git gc --prune=now --aggressive

WORKDIR /workspace/repo/graph-ui

RUN npm ci

WORKDIR /workspace

# offline-harbor: warm dependency caches at build (offline-hermetic grade)
RUN set +e; cd /workspace/repo 2>/dev/null; export DEBIAN_FRONTEND=noninteractive; if ls pom.xml */pom.xml >/dev/null 2>&1; then (command -v mvn >/dev/null 2>&1 || (apt-get update && apt-get install -y --no-install-recommends maven)) >/dev/null 2>&1; mvn -q -B -DskipTests -Dmaven.test.skip=false dependency:go-offline 2>/dev/null; mvn -q -B -DincludeScope=test dependency:go-offline 2>/dev/null; mvn -q -B org.apache.maven.plugins:maven-dependency-plugin:resolve-plugins 2>/dev/null; mvn -q -B -DskipTests install 2>/dev/null; mvn -q -B -Dtest=_zzz_nomatch_zzz -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false test 2>/dev/null; fi; if ls build.gradle build.gradle.kts gradlew >/dev/null 2>&1; then (./gradlew --no-daemon -q assemble testClasses -x test 2>/dev/null || ./gradlew --no-daemon -q dependencies 2>/dev/null); fi; if [ -f package.json ]; then (npm ci 2>/dev/null || npm install 2>/dev/null || yarn install --frozen-lockfile 2>/dev/null || yarn install 2>/dev/null || (corepack enable 2>/dev/null; pnpm install 2>/dev/null)); fi; if [ -f Cargo.toml ]; then cargo fetch 2>/dev/null; cargo test --no-run 2>/dev/null; fi; if [ -f go.mod ]; then go mod download all 2>/dev/null || go mod download 2>/dev/null; go test -run _zzz_nomatch_zzz ./... 2>/dev/null; fi; if [ -f requirements.txt ]; then pip install -r requirements.txt 2>/dev/null; fi; if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt 2>/dev/null; fi; if [ -f pyproject.toml ] || [ -f setup.py ]; then pip install -e ".[test,dev,tests]" 2>/dev/null || pip install -e . 2>/dev/null || (pip install poetry 2>/dev/null; poetry install 2>/dev/null); fi; true


# offline-harbor: manifest-dep cache warm (fair: caches golden/test-added deps by coordinate, no patch)
RUN set +e; cd /workspace/repo 2>/dev/null; if command -v npm >/dev/null 2>&1; then (npm cache add @testing-library/jest-dom @testing-library/react react vitest >/dev/null 2>&1 || true); (cd /workspace/repo 2>/dev/null && npm install --no-save @testing-library/jest-dom @testing-library/react react vitest >/dev/null 2>&1); fi; true
# ---- Harbor harness deps (tmux + asciinema) baked at build for offline eval ----
RUN (command -v tmux >/dev/null 2>&1 && command -v asciinema >/dev/null 2>&1) \
    || (apt-get update && apt-get install -y --no-install-recommends tmux asciinema \
        && rm -rf /var/lib/apt/lists/*) || true

# ---- verifier-integrity: FULL immutable pristine snapshot of the base tree (graded-surface restore source for tests/test.sh) ----
RUN set +e; mkdir -p /opt/pristine; cd /workspace/repo 2>/dev/null && \
    { git archive HEAD 2>/dev/null | tar -x -C /opt/pristine 2>/dev/null \
      || cp -a /workspace/repo/. /opt/pristine/ 2>/dev/null; }; \
    chmod -R a-w /opt/pristine 2>/dev/null; \
    chattr -R +i /opt/pristine 2>/dev/null; true

# ---- verifier-integrity: immutable snapshot of the RUNNER-EXECUTABLE surface (wrappers + node_modules/.bin + runner package BODIES + all node_modules package.json + vendor/bin) for tests/test.sh (2e) restore ----
RUN set +e; mkdir -p /opt/runner_pristine; cd /workspace/repo 2>/dev/null && \
    { find . \( -name gradlew -o -name gradlew.bat -o -name mvnw -o -name mvnw.cmd \) -o -path '*/gradle/wrapper/*' -o -path '*/node_modules/.bin/*' -o -path '*/vendor/bin/*' -o -path '*/bin/*' -o -path '*/node_modules/vitest/*' -o -path '*/node_modules/@vitest/*' -o -path '*/node_modules/jest/*' -o -path '*/node_modules/jest-cli/*' -o -path '*/node_modules/@jest/*' -o -path '*/node_modules/mocha/*' -o -path '*/node_modules/jasmine/*' -o -path '*/node_modules/jasmine-core/*' -o -path '*/node_modules/ava/*' -o -path '*/node_modules/tap/*' -o -path '*/node_modules/tape/*' -o -path '*/node_modules/uvu/*' -o -path '*/node_modules/vite/*' -o -path '*/node_modules/ts-node/*' -o -path '*/node_modules/tsx/*' -o -path '*/node_modules/*/package.json' 2>/dev/null | sed 's#^\./##' ; } | while IFS= read -r f; do \
      [ -e "$f" ] || continue; mkdir -p "/opt/runner_pristine/$(dirname "$f")" 2>/dev/null; \
      cp -a "$f" "/opt/runner_pristine/$f" 2>/dev/null; \
    done; \
    mkdir -p /opt/toolchain_pristine; printf '%s' "$PATH" > /opt/trusted_path 2>/dev/null; \
    for tb in pytest py.test python python3 go gofmt mvn mvnw gradle ./gradlew node npm npx yarn pnpm jest vitest mocha cargo cargo-nextest rustc ctest cmake dotnet phpunit composer rspec ruby bundle rake make gmake ninja bazel bazelisk msbuild mix elixir erl swift swiftc clang gcc g++ tsc tsx ts-node ava tap; do \
      rp=$(command -v "$tb" 2>/dev/null) || continue; [ -f "$rp" ] || continue; \
      case "$rp" in /workspace/*) continue;; esac; \
      mkdir -p "/opt/toolchain_pristine$(dirname "$rp")" 2>/dev/null; \
      cp -a "$rp" "/opt/toolchain_pristine$rp" 2>/dev/null; \
    done; \
    for d in /usr/local/bin /usr/local/sbin; do [ -d "$d" ] || continue; \
      for x in "$d"/*; do [ -f "$x" ] || continue; \
        mkdir -p "/opt/toolchain_pristine$d" 2>/dev/null; cp -a "$x" "/opt/toolchain_pristine$x" 2>/dev/null; \
      done; done; \
    chmod -R a-w /opt/runner_pristine /opt/trusted_path /opt/toolchain_pristine 2>/dev/null; \
    chattr -R +i /opt/runner_pristine /opt/toolchain_pristine 2>/dev/null; chattr +i /opt/trusted_path 2>/dev/null; true

# ---- verifier-integrity: immutable snapshot of OUT-OF-REPO aux verifier helpers (/usr/local/{bin,sbin}/*.{sh,py,js}|run_*|setup_*|convert_* + /workspace top-level helpers) for tests/test.sh restore ----
RUN set +e; mkdir -p /opt/aux_pristine; \
    { find /usr/local/bin /usr/local/sbin -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' -o -name '*.js' -o -name 'run_*' -o -name 'setup_*' -o -name 'convert_*' \) 2>/dev/null; \
      find /workspace -maxdepth 1 -type f \( -name '*.py' -o -name '*.sh' -o -name '*.js' \) 2>/dev/null; } | while IFS= read -r f; do \
      [ -e "$f" ] || continue; mkdir -p "/opt/aux_pristine$(dirname "$f")" 2>/dev/null; \
      cp -a "$f" "/opt/aux_pristine$f" 2>/dev/null; \
    done; chmod -R a-w /opt/aux_pristine 2>/dev/null; chattr -R +i /opt/aux_pristine 2>/dev/null; true

# offline-harbor: git blob-drop shrink (client-contract .git<100MB, HEAD==base)
RUN set +e; cd /workspace/repo 2>/dev/null && ( rm -rf .git/modules .git/worktrees 2>/dev/null; H=$(git rev-parse HEAD 2>/dev/null); [ -n "$H" ] && git update-ref --no-deref HEAD "$H" 2>/dev/null; git remote remove origin 2>/dev/null; git tag -l | xargs -r git tag -d >/dev/null 2>&1; git for-each-ref --format='%(refname)' refs/remotes refs/tags 2>/dev/null | xargs -r -n1 git update-ref -d 2>/dev/null; git for-each-ref --format='%(refname)' refs/heads 2>/dev/null | xargs -r -n1 git update-ref -d 2>/dev/null; [ -n "$H" ] && printf "%s\n" "$H" > .git/shallow; git reflog expire --expire=now --all 2>/dev/null; rm -rf .git/logs; { git rev-list --objects HEAD 2>/dev/null | awk '{print $1}'; printf "%s\n" "$H"; } | git cat-file --batch-check='%(objectname) %(objecttype)' 2>/dev/null | awk '$2!="blob"&&$1~/^[0-9a-f]{40}$/{print $1}' | sort -u > /tmp/_keep.txt; if [ ! -s /tmp/_keep.txt ]; then git cat-file --batch-all-objects --batch-check='%(objectname) %(objecttype)' 2>/dev/null | awk '$2!="blob"{print $1}' > /tmp/_keep.txt; fi; if [ -s /tmp/_keep.txt ]; then git pack-objects --quiet /tmp/_kp < /tmp/_keep.txt >/dev/null 2>&1 && rm -rf .git/objects/pack && mkdir -p .git/objects/pack && find .git/objects -maxdepth 1 -type d -name '[0-9a-f][0-9a-f]' -exec rm -rf {} + 2>/dev/null; mv /tmp/_kp-*.pack /tmp/_kp-*.idx .git/objects/pack/ 2>/dev/null; fi; git rev-parse HEAD >/dev/null 2>&1 || echo "WARN head-broken"; du -sm .git 2>/dev/null | cut -f1 ) ; true

# --- client-req: expose toolchain on the LOGIN shell PATH (bash -lc) ---
RUN set +e; \
    for b in cargo rustc rustup cargo-nextest go gofmt node npm npx yarn pnpm python3 pip3 \
             java javac mvn gradle ruby bundle gem php composer dotnet dub swift clang gcc; do \
      p="$(command -v "$b" 2>/dev/null)"; \
      [ -n "$p" ] && [ "$p" != "/usr/local/bin/$b" ] && ln -sf "$p" "/usr/local/bin/$b"; \
    done; \
    printf 'export PATH="%s:$PATH"\n' "$PATH" > /etc/profile.d/99-toolchain.sh; \
    for v in CARGO_HOME RUSTUP_HOME GOROOT GOPATH JAVA_HOME NVM_DIR PYENV_ROOT; do \
      val="$(printenv "$v" 2>/dev/null)"; [ -n "$val" ] && echo "export $v=\"$val\"" >> /etc/profile.d/99-toolchain.sh; \
    done; \
    chmod 0644 /etc/profile.d/99-toolchain.sh; true
