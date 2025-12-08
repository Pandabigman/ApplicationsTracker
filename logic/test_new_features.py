"""
Quick test script for new features: Deadlines and AI Thoughts
Run this after starting the server to verify the new endpoints work
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_scraping_with_ai():
    """Test that scraping includes AI thoughts"""
    print("\n=== Testing Scraping with AI Thoughts ===")

    # Note: This will make an actual API call to OpenAI
    # You need a valid OPENAI_API_KEY in .env
    test_url = input("Enter a job posting URL to test (or press Enter to skip): ").strip()

    if not test_url:
        print("Skipped scraping test")
        return None

    response = requests.post(f"{BASE_URL}/scrape", json={"url": test_url})

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Company: {data.get('company_name')}")
        print(f"✓ Position: {data.get('position_title')}")
        print(f"✓ Application Deadline: {data.get('application_deadline')}")
        print(f"✓ AI Thoughts: {data.get('ai_thoughts')[:100]}..." if data.get('ai_thoughts') else "✗ No AI thoughts")
        return data
    else:
        print(f"✗ Scraping failed: {response.text}")
        return None

def test_application_creation():
    """Test creating an application"""
    print("\n=== Testing Application Creation ===")

    app_data = {
        "company_name": "Test Company",
        "position_title": "Software Engineer",
        "location": "Remote",
        "salary": "$100k - $150k",
        "status": "Applied"
    }

    response = requests.post(f"{BASE_URL}/applications", json=app_data)

    if response.status_code == 201:
        app = response.json()
        print(f"✓ Created application ID: {app['id']}")
        return app['id']
    else:
        print(f"✗ Application creation failed: {response.text}")
        return None

def test_deadline_management(app_id):
    """Test deadline CRUD operations"""
    print(f"\n=== Testing Deadline Management for Application {app_id} ===")

    # Create deadlines
    deadlines = [
        {
            "deadline_type": "application",
            "deadline_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "description": "Submit application online",
            "is_completed": False
        },
        {
            "deadline_type": "interview",
            "deadline_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "description": "Phone screen with recruiter",
            "is_completed": False
        },
        {
            "deadline_type": "assessment",
            "deadline_date": (datetime.now() + timedelta(days=21)).isoformat(),
            "description": "Complete coding challenge",
            "is_completed": False
        }
    ]

    created_deadline_ids = []

    for deadline in deadlines:
        response = requests.post(
            f"{BASE_URL}/applications/{app_id}/deadlines",
            json=deadline
        )

        if response.status_code == 201:
            created = response.json()
            created_deadline_ids.append(created['id'])
            print(f"✓ Created {deadline['deadline_type']} deadline (ID: {created['id']})")
        else:
            print(f"✗ Failed to create deadline: {response.text}")

    # Get all deadlines
    response = requests.get(f"{BASE_URL}/applications/{app_id}/deadlines")
    if response.status_code == 200:
        deadlines = response.json()
        print(f"✓ Retrieved {len(deadlines)} deadlines")
    else:
        print(f"✗ Failed to get deadlines: {response.text}")

    # Mark first deadline as completed
    if created_deadline_ids:
        deadline_id = created_deadline_ids[0]
        response = requests.put(
            f"{BASE_URL}/deadlines/{deadline_id}",
            json={"is_completed": True}
        )

        if response.status_code == 200:
            print(f"✓ Marked deadline {deadline_id} as completed")
        else:
            print(f"✗ Failed to update deadline: {response.text}")

    return created_deadline_ids

def test_job_details_with_ai(app_id):
    """Test creating job details with AI thoughts"""
    print(f"\n=== Testing Job Details with AI Thoughts for Application {app_id} ===")

    job_details = {
        "application_id": app_id,
        "description": "We are looking for a talented software engineer...",
        "requirements": "3+ years experience, Python, React",
        "clean_text_content": "Full job posting text here...",
        "ai_thoughts": "To stand out for this role, emphasize your full-stack experience. The company values candidates who can work independently and take ownership. Highlight projects where you've built features end-to-end."
    }

    response = requests.post(
        f"{BASE_URL}/applications/{app_id}/job-details",
        json=job_details
    )

    if response.status_code == 201:
        details = response.json()
        print(f"✓ Created job details with AI thoughts")
        print(f"  AI Thoughts: {details['ai_thoughts'][:80]}...")
        return True
    else:
        print(f"✗ Failed to create job details: {response.text}")
        return False

def test_activity_log(app_id):
    """Test activity log retrieval"""
    print(f"\n=== Testing Activity Log for Application {app_id} ===")

    response = requests.get(f"{BASE_URL}/applications/{app_id}/activities")

    if response.status_code == 200:
        activities = response.json()
        print(f"✓ Retrieved {len(activities)} activities:")
        for activity in activities[:5]:  # Show first 5
            print(f"  - [{activity['activity_type']}] {activity['description']}")
        return True
    else:
        print(f"✗ Failed to get activities: {response.text}")
        return False

def test_full_application_retrieval(app_id):
    """Test getting full application with all related data"""
    print(f"\n=== Testing Full Application Retrieval (ID: {app_id}) ===")

    response = requests.get(f"{BASE_URL}/applications/{app_id}")

    if response.status_code == 200:
        app = response.json()
        print(f"✓ Retrieved full application")
        print(f"  - Company: {app['company_name']}")
        print(f"  - Position: {app['position_title']}")
        print(f"  - Deadlines: {len(app.get('deadlines', []))}")
        print(f"  - Notes: {len(app.get('notes', []))}")
        print(f"  - Activities: {len(app.get('activities', []))}")
        print(f"  - Has Job Details: {app.get('job_details') is not None}")
        if app.get('job_details'):
            print(f"  - Has AI Thoughts: {app['job_details'].get('ai_thoughts') is not None}")
        return True
    else:
        print(f"✗ Failed to retrieve application: {response.text}")
        return False

def cleanup(app_id):
    """Clean up test data"""
    print(f"\n=== Cleaning Up ===")

    response = input(f"Delete test application {app_id}? (y/n): ").strip().lower()

    if response == 'y':
        response = requests.delete(f"{BASE_URL}/applications/{app_id}")
        if response.status_code == 204:
            print("✓ Test application deleted")
        else:
            print(f"✗ Failed to delete: {response.text}")

def main():
    print("=" * 60)
    print("Testing New Features: Deadlines & AI Thoughts")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()

    try:
        # Test server health
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("✗ Server not responding. Is it running?")
            return
        print("✓ Server is running")

        # Run tests
        scrape_data = test_scraping_with_ai()
        app_id = test_application_creation()

        if app_id:
            deadline_ids = test_deadline_management(app_id)
            test_job_details_with_ai(app_id)
            test_activity_log(app_id)
            test_full_application_retrieval(app_id)

            print("\n" + "=" * 60)
            print("All Tests Completed!")
            print("=" * 60)

            cleanup(app_id)
        else:
            print("\n✗ Tests failed - could not create application")

    except KeyboardInterrupt:
        print("\n\nTests cancelled")
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()
