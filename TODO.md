# TODO - End-to-end Poultry AI (dataset → training → export → FastAPI → React)

## Phase A — Fix dataset paths + training/inference correctness
- [ ] Update `ml_pipeline/train/config.yaml` dataset.root_dir to `poutry_ai/dataset`.
- [ ] Fix training script path handling so it works from any working directory.
- [ ] Fix inference script path handling (checkpoint/config) to be working-directory independent.

## Phase B — Add evaluation + best checkpoint selection
- [ ] Implement evaluation (accuracy, precision, recall, f1, confusion matrix) for the saved `best.pth`.
- [ ] Save evaluation JSON + confusion matrix artifact.

## Phase C — Export final model bundle
- [ ] Create an exported artifact (e.g. `ml_pipeline/checkpoints/final/model_bundle.pth`) containing:
  - backbone name
  - num_classes
  - class_names
  - preprocessing params
  - weights/state_dict
- [ ] Add CLI to export final model after training.

## Phase D — Build FastAPI backend
- [ ] Create `backend/` FastAPI app.
- [ ] Load exported model on startup.
- [ ] Add `POST /api/predict` for image upload and return probabilities + top class.

## Phase E — Connect React upload → backend → dashboard
- [ ] Update `poutry_ai/src/pages/ImageUpload.jsx` to call `/api/predict` instead of simulating.
- [ ] Update parent `App.jsx` to append prediction results from backend to history.
- [ ] (If needed) Add `GET /api/history` / persistence, otherwise keep localStorage and only swap prediction call.

## Phase F — Verify end-to-end
- [ ] Run training, export final model.
- [ ] Start FastAPI and validate prediction via curl.
- [ ] Start React and verify upload → dashboard flow works.
- [ ] Smoke-test failure cases (bad file upload, missing model artifact, etc.).

