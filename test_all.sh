#!/usr/bin/env bash
#
# Create isolated venvs for several numpy versions, run a selected test and
# summarise results.  Designed to avoid contaminating the system env and to
# provide clear PASS/FAIL/ERROR reporting per numpy version.

set -u
PYTHON_BIN=${PYTHON_BIN:-/usr/bin/python3.10}
TEST_SPEC=${1:-tests/test_elmer_circuitbuilder.py::TestBasicCircuit::test_voltage_source}
NP_VERSIONS=(1.20.3 1.21.0 1.21.2 1.21.6 1.26.4 2.2.2)

declare -A STATUS_VENV
declare -A STATUS_INSTALL
declare -A STATUS_TEST
declare -A LOGFILE

mkdir -p .venv-logs

for NP in "${NP_VERSIONS[@]}"; do
  VENV=".venv-py310-np${NP//./}"
  LOG=".venv-logs/np-${NP}.log"
  LOGFILE["$NP"]="$LOG"

  rm -rf "$VENV" "$LOG"
  echo "=== numpy==$NP : venv=$VENV ===" | tee -a "$LOG"

  # create venv and verify
  if ! "$PYTHON_BIN" -m venv "$VENV" 2>>"$LOG"; then
    echo "ERROR: venv creation failed for $VENV" | tee -a "$LOG"
    # try virtualenv fallback
    echo "Attempting virtualenv fallback..." | tee -a "$LOG"
    if ! "$PYTHON_BIN" -m pip install --user virtualenv >>"$LOG" 2>&1 || \
       ! "$PYTHON_BIN" -m virtualenv -p "$PYTHON_BIN" "$VENV" >>"$LOG" 2>&1; then
      STATUS_VENV["$NP"]="VENVCREATE_FAIL"
      STATUS_INSTALL["$NP"]="SKIPPED"
      STATUS_TEST["$NP"]="SKIPPED"
      echo "VENVCREATE_FAIL" >>"$LOG"
      continue
    fi
  fi

  # activate
  # shellcheck source=/dev/null
  if ! source "$VENV/bin/activate" 2>>"$LOG"; then
    STATUS_VENV["$NP"]="ACTIVATE_FAIL"
    STATUS_INSTALL["$NP"]="SKIPPED"
    STATUS_TEST["$NP"]="SKIPPED"
    echo "ACTIVATE_FAIL" | tee -a "$LOG"
    continue
  fi
  STATUS_VENV["$NP"]="OK"

  # upgrade build tools and install precise packages
  if ! pip install -U pip setuptools wheel --no-cache-dir >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="PIP_UPGRADE_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi

  # Install exact numpy and pytest in venv, capture errors
  if ! pip install --no-cache-dir "numpy==$NP" "pytest==6.2.4" >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="INSTALL_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi
  STATUS_INSTALL["$NP"]="OK"

  # Install the local project into the venv so pytest runs against it
  echo "Installing local project into venv..." >>"$LOG"
  if ! pip install -e . >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="PROJECT_INSTALL_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi

  # verify python & numpy used inside venv
  echo "python: $(which python)" >>"$LOG"
  python -c "import sys, numpy as np; print(sys.executable, np.__version__)" >>"$LOG" 2>&1

  # run pytest for the selected test and capture exit code (append to log)
  pytest -q "$TEST_SPEC" >>"$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    STATUS_TEST["$NP"]="PASS"
  else
    STATUS_TEST["$NP"]="FAIL"
    echo "--- brief failure excerpt ---" >>"$LOG"
    tail -n 120 "$LOG" >>"$LOG" 2>&1 || true
  fi

  # preserve the venv for inspection if desired; deactivate for next iteration
  deactivate >/dev/null 2>&1 || true
done

# Print concise summary
printf "\nSummary (test: %s)\n" "$TEST_SPEC"
printf "%-10s %-14s %-14s %-8s %s\n" "numpy" "venv" "install" "result" "log"
for NP in "${NP_VERSIONS[@]}"; do
  printf "%-10s %-14s %-14s %-8s %s\n" \
    "$NP" \
    "${STATUS_VENV[$NP]:-SKIPPED}" \
    "${STATUS_INSTALL[$NP]:-SKIPPED}" \
    "${STATUS_TEST[$NP]:-SKIPPED}" \
    "${LOGFILE[$NP]:- }"
done

echo
echo "Failed runs: (see .venv-logs/*.log for details)"
for NP in "${NP_VERSIONS[@]}"; do
  if [ "${STATUS_TEST[$NP]:-SKIPPED}" = "FAIL" ]; then
    printf " - numpy %s: tail of %s\n" "$NP" "${LOGFILE[$NP]}"
    echo "-----"
    tail -n 40 "${LOGFILE[$NP]}" || true
    echo
  fi
done

exit 0
```// filepath: /home/mjfwest/repositories/elmer_circuitbuilder/test_all.sh
#!/usr/bin/env bash
#
# Create isolated venvs for several numpy versions, run a selected test and
# summarise results.  Designed to avoid contaminating the system env and to
# provide clear PASS/FAIL/ERROR reporting per numpy version.

set -u
PYTHON_BIN=${PYTHON_BIN:-/usr/bin/python3.9}
TEST_SPEC=${1:-tests/test_elmer_circuitbuilder.py::TestBasicCircuit::test_voltage_source}
NP_VERSIONS=(1.20.3 1.21.0 1.21.2 1.21.6 1.26.4)

declare -A STATUS_VENV
declare -A STATUS_INSTALL
declare -A STATUS_TEST
declare -A LOGFILE

mkdir -p .venv-logs

for NP in "${NP_VERSIONS[@]}"; do
  VENV=".venv-py39-np${NP//./}"
  LOG=".venv-logs/np-${NP}.log"
  LOGFILE["$NP"]="$LOG"

  rm -rf "$VENV" "$LOG"
  echo "=== numpy==$NP : venv=$VENV ===" | tee -a "$LOG"

  # create venv and verify
  if ! "$PYTHON_BIN" -m venv "$VENV" 2>>"$LOG"; then
    echo "ERROR: venv creation failed for $VENV" | tee -a "$LOG"
    # try virtualenv fallback
    echo "Attempting virtualenv fallback..." | tee -a "$LOG"
    if ! "$PYTHON_BIN" -m pip install --user virtualenv >>"$LOG" 2>&1 || \
       ! "$PYTHON_BIN" -m virtualenv -p "$PYTHON_BIN" "$VENV" >>"$LOG" 2>&1; then
      STATUS_VENV["$NP"]="VENVCREATE_FAIL"
      STATUS_INSTALL["$NP"]="SKIPPED"
      STATUS_TEST["$NP"]="SKIPPED"
      echo "VENVCREATE_FAIL" >>"$LOG"
      continue
    fi
  fi

  # activate
  # shellcheck source=/dev/null
  if ! source "$VENV/bin/activate" 2>>"$LOG"; then
    STATUS_VENV["$NP"]="ACTIVATE_FAIL"
    STATUS_INSTALL["$NP"]="SKIPPED"
    STATUS_TEST["$NP"]="SKIPPED"
    echo "ACTIVATE_FAIL" | tee -a "$LOG"
    continue
  fi
  STATUS_VENV["$NP"]="OK"

  # upgrade build tools and install precise packages
  if ! pip install -U pip setuptools wheel --no-cache-dir >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="PIP_UPGRADE_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi

  # Install exact numpy and pytest in venv, capture errors
  if ! pip install --no-cache-dir "numpy==$NP" "pytest==6.2.4" >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="INSTALL_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi
  STATUS_INSTALL["$NP"]="OK"

  # Install the local project into the venv so pytest runs against it
  echo "Installing local project into venv..." >>"$LOG"
  if ! pip install -e . >>"$LOG" 2>&1; then
    STATUS_INSTALL["$NP"]="PROJECT_INSTALL_FAIL"
    STATUS_TEST["$NP"]="SKIPPED"
    deactivate >/dev/null 2>&1 || true
    continue
  fi

  # verify python & numpy used inside venv
  echo "python: $(which python)" >>"$LOG"
  python -c "import sys, numpy as np; print(sys.executable, np.__version__)" >>"$LOG" 2>&1

  # run pytest for the selected test and capture exit code (append to log)
  pytest -q "$TEST_SPEC" >>"$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    STATUS_TEST["$NP"]="PASS"
  else
    STATUS_TEST["$NP"]="FAIL"
    echo "--- brief failure excerpt ---" >>"$LOG"
    tail -n 120 "$LOG" >>"$LOG" 2>&1 || true
  fi

  # preserve the venv for inspection if desired; deactivate for next iteration
  deactivate >/dev/null 2>&1 || true
done

# Print concise summary
printf "\nSummary (test: %s)\n" "$TEST_SPEC"
printf "%-10s %-14s %-14s %-8s %s\n" "numpy" "venv" "install" "result" "log"
for NP in "${NP_VERSIONS[@]}"; do
  printf "%-10s %-14s %-14s %-8s %s\n" \
    "$NP" \
    "${STATUS_VENV[$NP]:-SKIPPED}" \
    "${STATUS_INSTALL[$NP]:-SKIPPED}" \
    "${STATUS_TEST[$NP]:-SKIPPED}" \
    "${LOGFILE[$NP]:- }"
done

echo
echo "Failed runs: (see .venv-logs/*.log for details)"
for NP in "${NP_VERSIONS[@]}"; do
  if [ "${STATUS_TEST[$NP]:-SKIPPED}" = "FAIL" ]; then
    printf " - numpy %s: tail of %s\n" "$NP" "${LOGFILE[$NP]}"
    echo "-----"
    tail -n 40 "${LOGFILE[$NP]}" || true
    echo
  fi
done

exit 0