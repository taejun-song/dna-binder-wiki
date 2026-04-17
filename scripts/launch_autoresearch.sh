#!/bin/bash
# Master launcher: waits for GPU, then runs autoresearch for all 9 targets in 3 waves
cd /home/taejun/workspace/dna-binder-wiki

echo "[$(date)] Waiting for GPU to free up (need <30GB used)..."
while true; do
    USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null)
    if [ -z "$USED" ]; then
        echo "[$(date)] nvidia-smi failed, retrying..."
        sleep 30
        continue
    fi
    if [ "$USED" -lt 30000 ]; then
        break
    fi
    echo "[$(date)] GPU still busy: ${USED}MB used. Waiting..."
    sleep 60
done

echo "[$(date)] GPU free (${USED}MB used). Stopping overnight runner..."
kill $(ps aux | grep overnight_runner | grep -v grep | awk '{print $2}') 2>/dev/null
sleep 5

echo "[$(date)] === WAVE 1: HD, OCT4pt1, NFKB (top priority) ==="
for TARGET in HD OCT4pt1 NFKB; do
    .venv/bin/python scripts/autoresearch_binder.py \
        --target "$TARGET" --n-designs 10 \
        --output-dir analysis_output/autoresearch \
        >> "analysis_output/autoresearch_${TARGET}.log" 2>&1 &
    echo "[$(date)] Launched $TARGET PID=$!"
    sleep 10
done
wait
echo "[$(date)] Wave 1 complete."

echo "[$(date)] === WAVE 2: PNRP1, OCT4pt2, HSTELO ==="
for TARGET in PNRP1 OCT4pt2 HSTELO; do
    .venv/bin/python scripts/autoresearch_binder.py \
        --target "$TARGET" --n-designs 10 \
        --output-dir analysis_output/autoresearch \
        >> "analysis_output/autoresearch_${TARGET}.log" 2>&1 &
    echo "[$(date)] Launched $TARGET PID=$!"
    sleep 10
done
wait
echo "[$(date)] Wave 2 complete."

echo "[$(date)] === WAVE 3: CAG, TATA, Dux4grna2 ==="
for TARGET in CAG TATA Dux4grna2; do
    .venv/bin/python scripts/autoresearch_binder.py \
        --target "$TARGET" --n-designs 10 \
        --output-dir analysis_output/autoresearch \
        >> "analysis_output/autoresearch_${TARGET}.log" 2>&1 &
    echo "[$(date)] Launched $TARGET PID=$!"
    sleep 10
done
wait
echo "[$(date)] Wave 3 complete."

echo "[$(date)] === ALL 9 TARGETS AUTORESEARCH COMPLETE ==="
echo "[$(date)] Results in analysis_output/autoresearch/*_autoresearch.tsv"
