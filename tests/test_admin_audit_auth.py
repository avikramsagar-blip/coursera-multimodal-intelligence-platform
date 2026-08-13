import os
import unittest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Base, get_db
import backend.models as models
import backend.security as security

# Import routers directly to avoid heavy main imports
from backend.evidence_api import router as evidence_router
from backend.metrics_api import router as metrics_router
from backend.admin_api import router as admin_router


def create_test_app(session_local):
    app = FastAPI()
    app.include_router(evidence_router, prefix="/api")
    app.include_router(metrics_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")

    # override get_db
    def _override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    return app


class AuthAuditTests(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite DB
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db_local = TestingSessionLocal

        # create users
        db = TestingSessionLocal()
        admin = models.User(full_name="Admin", email="admin@example.com", password="x", role="admin")
        reviewer = models.User(full_name="Reviewer", email="rev@example.com", password="x", role="reviewer")
        ops = models.User(full_name="Ops", email="ops@example.com", password="x", role="ops")
        student = models.User(full_name="Student", email="stu@example.com", password="x", role="student")
        db.add_all([admin, reviewer, ops, student])
        db.commit()
        db.refresh(admin); db.refresh(reviewer); db.refresh(ops); db.refresh(student)
        db.close()

        # create some metrics rows
        db = TestingSessionLocal()
        gm = models.GenerationMetric(model_name="gemini-test", prompt_hash="h", tokens_in=10, tokens_out=20, latency_ms=100.0, success=True)
        db.add(gm)
        db.commit()
        db.close()

        # create an insight to review
        db = TestingSessionLocal()
        ins = models.Insight(title="T", summary="S", created_by=admin.user_id)
        db.add(ins);
        db.commit(); db.refresh(ins)
        self.insight_id = ins.insight_id
        db.close()

        # prepare app
        self.app = create_test_app(TestingSessionLocal)
        self.client = TestClient(self.app)

        # ensure SECRET_KEY exists for tokens
        os.environ['SECRET_KEY'] = os.getenv('SECRET_KEY', 'testsecret')

        # build tokens
        self.admin_token = security.create_access_token({"sub": "admin@example.com"})
        self.reviewer_token = security.create_access_token({"sub": "rev@example.com"})
        self.ops_token = security.create_access_token({"sub": "ops@example.com"})
        self.student_token = security.create_access_token({"sub": "stu@example.com"})

    def test_admin_can_change_role_and_audit_is_recorded(self):
        # change student's role to reviewer
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = self.client.post(f"/api/admin/users/4/role", json={"role": "reviewer"}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('role'), 'reviewer')

        # now audit should have an entry (via admin_api.record_audit)
        resp2 = self.client.get('/api/admin/audits', headers=headers)
        self.assertEqual(resp2.status_code, 200)
        audits = resp2.json().get('audits')
        self.assertTrue(any(a.get('action_type') == 'role_change' for a in audits))

    def test_reviewer_can_review_and_audit_logged_but_student_cannot(self):
        # reviewer reviews insight
        headers = {"Authorization": f"Bearer {self.reviewer_token}"}
        resp = self.client.post(f"/api/insights/{self.insight_id}/review", json={"action": "approve"}, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # check audit exists (admin list)
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp2 = self.client.get('/api/admin/audits', headers=admin_headers)
        self.assertEqual(resp2.status_code, 200)
        audits = resp2.json().get('audits')
        self.assertTrue(any(a.get('action_type') == 'insight_review' for a in audits))

        # student cannot review
        sh = {"Authorization": f"Bearer {self.student_token}"}
        resp3 = self.client.post(f"/api/insights/{self.insight_id}/review", json={"action": "approve"}, headers=sh)
        self.assertIn(resp3.status_code, (401, 403))

    def test_ops_can_view_dashboard_but_student_cannot(self):
        headers_ops = {"Authorization": f"Bearer {self.ops_token}"}
        resp = self.client.get('/api/metrics/dashboard', headers=headers_ops)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('models', data)

        headers_student = {"Authorization": f"Bearer {self.student_token}"}
        resp2 = self.client.get('/api/metrics/dashboard', headers=headers_student)
        self.assertIn(resp2.status_code, (401, 403))


if __name__ == '__main__':
    unittest.main()
