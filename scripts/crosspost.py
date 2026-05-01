#!/usr/bin/env python3
import os
import sys
import frontmatter
import requests

def crosspost_to_medium(filepath, integration_token=None):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        sys.exit(1)

    with open(filepath, 'r') as f:
        post = frontmatter.load(f)

    # Note: Disabled by default for safety.
    # To enable, you would need to get an integration token from Medium,
    # fetch your author ID, and then POST the content.
    
    print(f"--- SIMULATED CROSSPOST ---")
    print(f"File: {filepath}")
    print(f"Title: {post.get('title')}")
    print(f"Tags: {post.get('tags')}")
    print(f"Content Length: {len(post.content)} characters")
    
    if not integration_token:
        print("Integration token not provided. Aborting actual POST request.")
        return

    print("Sending to Medium API... (Disabled in this script)")
    # Example logic:
    # headers = {
    #     'Authorization': f'Bearer {integration_token}',
    #     'Content-Type': 'application/json',
    #     'Accept': 'application/json',
    #     'Accept-Charset': 'utf-8'
    # }
    # data = {
    #     "title": post.get('title'),
    #     "contentFormat": "markdown",
    #     "content": post.content,
    #     "tags": post.get('tags', []),
    #     "publishStatus": "draft"
    # }
    # response = requests.post(f"https://api.medium.com/v1/users/USER_ID/posts", headers=headers, json=data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crosspost.py <path-to-markdown-file>")
        sys.exit(1)
    crosspost_to_medium(sys.argv[1])
