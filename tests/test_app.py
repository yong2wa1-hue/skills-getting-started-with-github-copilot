import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 9  # 9 activities in total
    
    def test_get_activities_includes_activity_details(self, client):
        """Test that activity data includes all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        new_email = "newstudent@mergington.edu"
        
        # Signup
        client.post(f"/activities/Chess Club/signup?email={new_email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        chess_club_participants = activities["Chess Club"]["participants"]
        
        assert new_email in chess_club_participants
    
    def test_signup_duplicate_returns_400(self, client):
        """Test that signing up twice for same activity returns 400 error"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "Already signed up for this activity" in data["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404 error"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_students_different_activities(self, client):
        """Test that multiple students can sign up for different activities"""
        # Signup for different activities
        client.post("/activities/Chess Club/signup?email=alice@mergington.edu")
        client.post("/activities/Programming Class/signup?email=bob@mergington.edu")
        
        # Verify both signups succeeded
        response = client.get("/activities")
        activities = response.json()
        
        assert "alice@mergington.edu" in activities["Chess Club"]["participants"]
        assert "bob@mergington.edu" in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert f"Unregistered {email} from Chess Club" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify participant is in activity before unregister
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client):
        """Test that unregistering non-existent participant returns 400 error"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notaparticipant@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Participant not found in this activity" in data["detail"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404 error"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_after_unregister(self, client):
        """Test that student can signup again after unregistering"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        # Signup again
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 200
        
        # Verify signup succeeded
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_full_signup_flow(self, client):
        """Test complete flow: get activities -> signup -> verify -> unregister -> verify"""
        new_email = "integration_test@mergington.edu"
        activity_name = "Art Studio"
        
        # Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Signup
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert response.json()[activity_name]["participants"].count(new_email) == 1
        assert len(response.json()[activity_name]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.delete(f"/activities/{activity_name}/unregister?email={new_email}")
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert new_email not in response.json()[activity_name]["participants"]
        assert len(response.json()[activity_name]["participants"]) == initial_count

    def test_activities_isolation_between_tests(self, client):
        """Test that each test gets fresh activities data"""
        # This test runs independently, so it should have original participants
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Verify original participants are present
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
