#!/usr/bin/env python3
import os
import sys
import re
from datetime import datetime

def slugify(value):
    value = str(value).lower().strip()
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value)

def create_post(title):
    date = datetime.now()
    slug = slugify(title)
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    filepath = os.path.join("src", "content", "blog", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content = f"""---
title: "{title}"
description: "A short description of {title}"
publishDate: {date.isoformat()}
tags: ["Architecture", "Engineering"]
readTime: 5
---

# {title}

Write your content here...
"""
    with open(filepath, "w") as f:
        f.write(content)
    
    print(f"Created new post at: {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_post.py 'Post Title'")
        sys.exit(1)
    create_post(sys.argv[1])
