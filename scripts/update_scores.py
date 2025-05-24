
import os
import requests
import json
from datetime import datetime

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

HEADERS = {
    "Accept": "application/json"
}

AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
PROJECT_KEY = "CLP"
SPRINT_FIELD = "customfield_10119"

# Determine which sprint to report
def determine_sprint_name():
    today = datetime.utcnow().date()
    if today < datetime(2025, 6, 4).date():
        return "Sprint 6"
    elif today < datetime(2025, 6, 18).date():
        return "Sprint 7"
    else:
        return "Sprint 8"

def fetch_issues(jql):
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {
        "jql": jql,
        "maxResults": 1000,
        "fields": ["status", SPRINT_FIELD]
    }
    response = requests.get(url, headers=HEADERS, auth=AUTH, params=params)
    response.raise_for_status()
    return response.json().get("issues", [])

def calculate_scores():
    sprint_name = determine_sprint_name()

    # Readiness: To Do or Ready for Development in current sprint
    readiness_jql = f'project = {PROJECT_KEY} AND "{SPRINT_FIELD}" ~ "{sprint_name}"'
    sprint_issues = fetch_issues(readiness_jql)
    readiness_ready = [i for i in sprint_issues if i['fields']['status']['name'].lower() in ['to do', 'ready for development']]
    readiness_score = round((len(readiness_ready) / len(sprint_issues)) * 100, 1) if sprint_issues else 0.0

    # Backlog: New or Grooming not in any sprint
    backlog_jql = f'project = {PROJECT_KEY} AND "{SPRINT_FIELD}" is EMPTY'
    backlog_issues = fetch_issues(backlog_jql)
    backlog_refined = [i for i in backlog_issues if i['fields']['status']['name'].lower() in ['new', 'grooming']]
    backlog_score = round((len(backlog_refined) / len(backlog_issues)) * 100, 1) if backlog_issues else 0.0

    return {
        "sprint_readiness": readiness_score,
        "backlog_health": backlog_score
    }

def save_to_json(scores, path="data/sitrep_scores.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(scores, f, indent=2)

if __name__ == "__main__":
    scores = calculate_scores()
    save_to_json(scores)
    print("Updated sitrep_scores.json:", scores)
