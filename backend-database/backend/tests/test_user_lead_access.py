import pytest
from app import create_app
from models.user_lead_access_model import UserLeadAccess

@pytest.fixture
def app():
    app = create_app()
    with app.app_context():
        yield app

def test_user_lead_access_creation(app):
    access = UserLeadAccess(
        user_id=1,
        lead_id="test_lead",
        access_type="view"
    )
    assert access.user_id == 1
    assert access.lead_id == "test_lead"
    assert access.access_type == "view"