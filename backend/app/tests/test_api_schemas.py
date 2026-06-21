import sys
import unittest
from pathlib import Path
from pydantic import ValidationError
from fastapi import HTTPException

# Adjust path to import app modules
repo_root = Path(__file__).resolve().parents[3]
sys.path.append(str(repo_root / "backend"))

from app.schemas import (
    PredictionCorrection,
    PredictionReview,
    PredictionFlag,
    NotificationRead,
    PredictionResponse,
    NotificationResponse
)
from app.api.endpoints.predictions import update_reviewed, update_flagged, correct_prediction
from app.api.endpoints.notifications import update_notif_read
from app.api.endpoints.health import health
from app.api.endpoints.model import model_status

class TestAPISchemas(unittest.TestCase):
    def test_schemas_validation(self):
        # 1. PredictionCorrection validation
        valid_corr = PredictionCorrection(correctedStatus="dirty")
        self.assertEqual(valid_corr.correctedStatus, "dirty")
        with self.assertRaises(ValidationError):
            PredictionCorrection()

        # 2. PredictionReview validation
        valid_rev = PredictionReview(reviewed=True)
        self.assertTrue(valid_rev.reviewed)
        with self.assertRaises(ValidationError):
            PredictionReview()

        # 3. PredictionFlag validation
        valid_flag = PredictionFlag(flagged=False)
        self.assertFalse(valid_flag.flagged)
        with self.assertRaises(ValidationError):
            PredictionFlag()

        # 4. NotificationRead validation
        valid_read = NotificationRead(read=True)
        self.assertTrue(valid_read.read)
        with self.assertRaises(ValidationError):
            NotificationRead()

    def test_endpoint_responses_and_exceptions(self):
        # Calling endpoints directly with mock inputs to test business logic and response mapping
        
        # 1. Test update_reviewed with nonexistent prediction (should execute DB query and return successfully or raise if db connection fails, but here sqlite is local, so it updates 0 rows and returns)
        res_rev = update_reviewed("nonexistent-id-123", PredictionReview(reviewed=True))
        self.assertEqual(res_rev.status, "ok")
        self.assertEqual(res_rev.id, "nonexistent-id-123")
        self.assertTrue(res_rev.reviewed)

        # 2. Test update_flagged with nonexistent prediction
        res_flag = update_flagged("nonexistent-id-456", PredictionFlag(flagged=True))
        self.assertEqual(res_flag.status, "ok")
        self.assertEqual(res_flag.id, "nonexistent-id-456")
        self.assertTrue(res_flag.flagged)

        # 3. Test correct_prediction with nonexistent prediction (should raise 404 HTTPException)
        with self.assertRaises(HTTPException) as ctx:
            import asyncio
            asyncio.run(correct_prediction("nonexistent-id-789", PredictionCorrection(correctedStatus="inflamed")))
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Prediction not found")

        # 4. Test correct_prediction with invalid status (should raise 400 HTTPException)
        with self.assertRaises(HTTPException) as ctx:
            import asyncio
            asyncio.run(correct_prediction("nonexistent-id-789", PredictionCorrection(correctedStatus="invalid_status")))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid corrected status", ctx.exception.detail)

        # 5. Test update_notif_read with nonexistent notification
        res_notif = update_notif_read("notif-abc", NotificationRead(read=True))
        self.assertEqual(res_notif.status, "ok")
        self.assertEqual(res_notif.id, "notif-abc")
        self.assertTrue(res_notif.read)

    def test_health_check_endpoint(self):
        # Health check should return HealthSuccessResponse (since model bundle was successfully trained and exported)
        res = health()
        self.assertEqual(res.status, "ok")
        self.assertIsNotNone(res.device)
        self.assertIn("healthy", res.class_names)

    def test_model_status_endpoint(self):
        res = model_status()
        self.assertIsNotNone(res.dataset_counts)
        self.assertGreaterEqual(res.total_images, 0)
        self.assertFalse(res.is_training)

if __name__ == "__main__":
    unittest.main()
