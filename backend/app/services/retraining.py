import os
import sys
import subprocess
import json
from pathlib import Path
from fastapi import HTTPException
from app.core.config import repo_root

retrain_proc = None
retrain_log_path = repo_root / "ml_pipeline" / "runs" / "retrain_live.log"

def get_retrain_status():
    global retrain_proc
    is_training = False
    if retrain_proc is not None:
        if retrain_proc.poll() is None:
            is_training = True
        else:
            retrain_proc = None
    return is_training

def start_retrain():
    global retrain_proc
    if get_retrain_status():
        raise HTTPException(status_code=400, detail="Retraining is already in progress.")

    retrain_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(retrain_log_path, "w", encoding="utf-8") as f:
        f.write("Starting AI Model Retraining...\n")

    train_script = repo_root / "ml_pipeline" / "train" / "train_classifier.py"
    log_file = open(retrain_log_path, "a", encoding="utf-8", buffering=1)

    retrain_proc = subprocess.Popen(
        [sys.executable, "-u", str(train_script)],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(repo_root),
        text=True
    )
    return str(retrain_log_path)

def read_retrain_logs():
    if not retrain_log_path.exists():
        return "No training logs found."
    try:
        with open(retrain_log_path, "r", encoding="utf-8") as f:
            logs = f.read()
        return logs
    except Exception as e:
        return f"Error reading logs: {str(e)}"

def get_dataset_statistics():
    dataset_dir = repo_root / "poutry_ai" / "dataset"
    class_counts = {}
    total_images = 0
    class_names = ["healthy", "dirty", "inflamed", "prolapse"]

    for cls in class_names:
        cdir = dataset_dir / cls
        count = 0
        if cdir.exists():
            exts = {".png", ".jpg", ".jpeg", ".webp"}
            count = len([f for f in cdir.iterdir() if f.is_file() and f.suffix.lower() in exts])
        class_counts[cls] = count
        total_images += count

    eval_path = repo_root / "ml_pipeline" / "checkpoints" / "eval" / "eval_best.json"
    metrics = {}
    if eval_path.exists():
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            pass

    return class_counts, total_images, metrics
