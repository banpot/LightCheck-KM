# Rebuild every number and figure from scratch:  make all
PY ?= python3
all: bias sim figures twin fwtest stats
bias:    ; cd calibration && $(PY) expected_bias_from_datasheet.py
sim:     ; cd calibration && $(PY) simulate_calibration.py --n 5000 --seed 2569
figures: ; cd calibration && $(PY) make_figures.py
twin:    ; cd tools/survey && $(PY) office_lighting_sim.py
fwtest:  ; bash tools/fw_sim/run.sh | tee tools/fw_sim/results.txt
stats:   ; $(PY) tools/repo_stats.py
.PHONY: all bias sim figures twin fwtest stats
