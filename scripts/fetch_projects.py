#!/usr/bin/env python3
import os
import requests
import json

def fetch_projects(username="vanditsramblings"):
    url = f"https://api.github.com/users/{username}/repos"
    print(f"Fetching projects from {url}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return

    repos = response.json()
    
    # Filter or sort projects. Here we take the top 5 by stars.
    sorted_repos = sorted(repos, key=lambda r: r.get('stargazers_count', 0), reverse=True)
    top_repos = sorted_repos[:5]
    
    projects_data = []
    for r in top_repos:
        projects_data.append({
            "name": r.get("name"),
            "description": r.get("description"),
            "url": r.get("html_url"),
            "stars": r.get("stargazers_count"),
            "language": r.get("language")
        })

    data_dir = os.path.join("src", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, "projects.json")
    with open(filepath, "w") as f:
        json.dump(projects_data, f, indent=2)
        
    print(f"Successfully saved {len(projects_data)} projects to {filepath}")

if __name__ == "__main__":
    fetch_projects()
