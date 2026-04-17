import requests
from requests.auth import HTTPBasicAuth
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FOLDER = "/home/bhargav/Downloads/Retro_files"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def fetch_retro_data(org, pat_env_var, needed_projects=None, needed_teams=None):
    PAT = os.getenv(pat_env_var)
    if not PAT:
        print(f"PAT not found for {org}")
        return

    auth = HTTPBasicAuth("", PAT)
    BASE_DEV = f"https://dev.azure.com/{org}"
    BASE_EXT = f"https://extmgmt.dev.azure.com/{org}"

    print(f"\n===== Processing ORG: {org} =====")

    projects_url = f"{BASE_DEV}/_apis/projects?api-version=7.0"
    projects_response = requests.get(projects_url, auth=auth)
    projects_response.raise_for_status()
    projects = projects_response.json()["value"]

    print(f"Found {len(projects)} projects")

    for project in projects:
        project_name = project["name"]
        project_id = project["id"]

        if needed_projects and project_name not in needed_projects:
            continue

        print(f"\nProcessing Project: {project_name}")

        teams_url = f"{BASE_DEV}/_apis/projects/{project_id}/teams?$mine=false&$top=100&$skip=0&$expandIdentity=true&api-version=7.0"
        teams_response = requests.get(teams_url, auth=auth)

        if teams_response.status_code != 200:
            print(f"  Failed to fetch teams for {project_name}")
            continue

        teams = teams_response.json()["value"]
        print(f"  Found {len(teams)} teams")

        for team in teams:
            team_id = team["id"]
            team_name = team["name"]

            if needed_teams and team_name not in needed_teams:
                continue

            team_obj = {"id": team_id, "name": team_name}
            print(f"    Processing Team: {team_name}")

            # Step 1: boards
            boards_url = f"{BASE_EXT}/_apis/ExtensionManagement/InstalledExtensions/ms-devlabs/team-retrospectives/Data/Scopes/Default/Current/Collections/{team_id}/Documents?api-version=7.0-preview.1"
            boards_response = requests.get(boards_url, auth=auth)

            if boards_response.status_code != 200:
                print(f"      No retros found")
                continue

            boards = boards_response.json()
            if not boards:
                print(f"      No retrospective documents")
                continue

            full_retros = []

            for board in boards:
                board_id = board.get("id")
                if not board_id:
                    continue

                # Step 2: items
                items_url = f"{BASE_EXT}/_apis/ExtensionManagement/InstalledExtensions/ms-devlabs/team-retrospectives/Data/Scopes/Default/Current/Collections/{board_id}/Documents?api-version=7.0-preview.1"
                items_response = requests.get(items_url, auth=auth)

                items = []
                if items_response.status_code == 200:
                    items = items_response.json()
                else:
                    print(f"        Failed to fetch items for board {board_id}")

                # Step 3: assemble
                full_retros.append({
                    "team": team_obj,
                    "board": board,
                    "items": items
                })

            if not full_retros:
                print(f"      No valid retros retrieved")
                continue

            safe_team_name = re.sub(r'[\\/*?:"<>|]', "_", team_name)
            safe_project_name = re.sub(r'[\\/*?:"<>|]', "_", project_name)

            filename = f"{org}__{safe_project_name}__{safe_team_name}.json"
            full_path = os.path.join(OUTPUT_FOLDER, filename)

            with open(full_path, "w") as f:
                json.dump(full_retros, f)

            print(f"      Saved: {filename} ({len(full_retros)} boards)")


# ===== RUN FOR BOTH ORGS =====

# ORG 1 → Full dump
fetch_retro_data(
    org="ab-inbev-command-center",
    pat_env_var="PAT"
)

# ORG 2 → Filtered
fetch_retro_data(
    org="ab-inbev",
    pat_env_var="PAT_tsc",
    needed_projects=["ABI-SupplyChain-GlobalTechHub"],
    needed_teams=[
        "BrewHub Squad",
        "Data Management Systems and DVPO SQUAD",
        "DATA Omnia SQUAD",
        "Data Reliability SQUAD"
    ]
)

print("\nDone. All orgs processed.")
