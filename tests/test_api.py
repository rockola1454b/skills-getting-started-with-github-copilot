"""
FastAPI Backend Tests
Tests are structured using the AAA (Arrange-Act-Assert) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Store original activities state for reset between tests
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Arrange: Reset activities to original state before each test.
    This ensures tests don't interfere with each other.
    """
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    """Arrange: Create a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns the full activity dictionary"""
        # Arrange: (already done by fixtures)
        
        # Act: Make GET request
        response = client.get("/activities")
        
        # Assert: Check response status and content
        assert response.status_code == 200
        activities_data = response.json()
        assert isinstance(activities_data, dict)
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
        assert "Science Olympiad" in activities_data

    def test_get_activities_includes_participants(self, client):
        """Test that activity data includes participants list"""
        # Arrange: (none needed)
        
        # Act: Get activities
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert: Verify structure
        chess_club = activities_data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success_new_participant(self, client):
        """Test successful signup of a new student"""
        # Arrange: Prepare test data
        activity_name = "Science Olympiad"
        email = "newabc@mergington.edu"
        
        # Act: Send signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Verify success response and state change
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]

    def test_signup_duplicate_returns_400(self, client):
        """Test that signing up twice returns 400 error"""
        # Arrange: Student already exists in activity
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act: Attempt to sign up with duplicate email
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 400 error and message
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up for this activity"

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test signup to non-existent activity returns 404"""
        # Arrange: Use fake activity name
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        
        # Act: Try to sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_multiple_students_same_activity(self, client):
        """Test multiple different students can sign up for same activity"""
        # Arrange: Prepare multiple emails
        activity_name = "Art Studio"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act: Sign up first student
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        
        # Act: Sign up second student
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert: Both succeed and are added
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 2
        assert email1 in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # Arrange: Identify existing participant
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        assert email in activities[activity_name]["participants"]
        
        # Act: Remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert: Verify removal succeeded and state changed
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_returns_404(self, client):
        """Test removing a participant not in activity returns 404"""
        # Arrange: Use email not in activity
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"
        
        # Act: Try to remove
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in activity"

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Test removing from non-existent activity returns 404"""
        # Arrange: Use fake activity and email
        activity_name = "Fake Club"
        email = "test@mergington.edu"
        
        # Act: Try to remove
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_and_signup_again(self, client):
        """Test that a removed participant can sign up again"""
        # Arrange: Start with existing participant
        activity_name = "Drama Club"
        email = "isabella@mergington.edu"
        
        # Act: Remove participant
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        assert email not in activities[activity_name]["participants"]
        
        # Act: Sign up again
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Signup succeeds and participant is back
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
