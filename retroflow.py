import requests
from requests.auth import HTTPBasicAuth
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()
OUTPUT_FOLDER="/media/bhargav/OS1/Users/Bhargav/Downloads/Retro files"
ORG = "ab-inbev-DSCOE"
PAT = os.getenv("PAT")

auth = HTTPBasicAuth("", PAT)

BASE_DEV = f"https://dev.azure.com/{ORG}"
BASE_EXT = f"https://extmgmt.dev.azure.com/{ORG}"
projects_url = f"{BASE_DEV}/_apis/projects?api-version=7.0"
projects_response = requests.get(projects_url, auth=auth)
projects_response.raise_for_status()

projects = projects_response.json()["value"]

print(f"Found {len(projects)} projects")
for project in projects:

    project_name = project["name"]
    project_id = project["id"]

    print(f"\nProcessing Project: {project_name}")

    teams_url = f"{BASE_DEV}/_apis/projects/{project_id}/teams?$mine=false&$top=100&$skip=0&$expandIdentity=true&api-version=7.0"

    teams_response = requests.get(teams_url, auth=auth)

    if teams_response.status_code != 200:
        print(f"Failed to fetch teams for {project_name}")
        continue

    teams = teams_response.json()["value"]

    print(f"  Found {len(teams)} teams")
    for team in teams:

        team_id = team["id"]
        team_name = team["name"]

        print(f"    Processing Team: {team_name}")

        retro_url = f"{BASE_EXT}/_apis/ExtensionManagement/InstalledExtensions/ms-devlabs/team-retrospectives/Data/Scopes/Default/Current/Collections/{team_id}/Documents?api-version=7.0-preview.1"

        retro_response = requests.get(retro_url, auth=auth)

        if retro_response.status_code != 200:
            print(f"      No retros found")
            continue

        retros = retro_response.json()

        if not retros:
            print(f"      No retrospective documents")
            continue

        team_export = {
            "team": team,
            "retrospectives": retros
        }

        safe_team_name = re.sub(r'[\\/*?:"<>|]', "_", team_name)
        safe_project_name = re.sub(r'[\\/*?:"<>|]', "_", project_name)

        filename = f"{safe_project_name}__{safe_team_name}.json"
        full_path = os.path.join(OUTPUT_FOLDER, filename)
        with open(full_path, "w") as f:
            json.dump([team_export], f, indent=2)

        print(f"      Saved: {filename}")

print("\nDone. All teams processed.")
