import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load PAT
load_dotenv()
PAT = os.getenv("PAT_tsc")  # make sure this env var exists

if not PAT:
    raise Exception("PAT_tsc not found in .env")

auth = HTTPBasicAuth("", PAT)

ORG = "ab-inbev"
BASE_DEV = f"https://dev.azure.com/{ORG}"

# Step 1: Get all projects
projects_url = f"{BASE_DEV}/_apis/projects?api-version=7.0"
projects_response = requests.get(projects_url, auth=auth)
projects_response.raise_for_status()

projects = projects_response.json()["value"]

print(f"\nTotal Projects: {len(projects)}\n")

# Step 2: Loop projects → fetch teams
for project in projects:
    project_name = project["name"]
    project_id = project["id"]

    print(f"\n=== Project: {project_name} ===")

    teams_url = f"{BASE_DEV}/_apis/projects/{project_id}/teams?api-version=7.0"
    teams_response = requests.get(teams_url, auth=auth)

    if teams_response.status_code != 200:
        print("  Failed to fetch teams")
        continue

    teams = teams_response.json()["value"]

    if not teams:
        print("  No teams found")
        continue

    for team in teams:
        print(f"  - {team['name']}")

print("\nDone.")