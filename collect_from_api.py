import urllib.request
import urllib.parse
import urllib.error
import json
import os
import time

def data_to_markdown(data, md_file):
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# Moltbook API Posts\n\n")
        
        for query_key, query_data in data.items():
            if not isinstance(query_data, dict) or 'results' not in query_data:
                continue
                
            f.write(f"## Query: `{query_key}`\n\n")
            
            for item in query_data['results']:
                if item.get('type') == 'post':
                    title = item.get('title', 'Untitled')
                    author = item.get('author', {}).get('name', 'Unknown')
                    upvotes = item.get('upvotes', 0)
                    downvotes = item.get('downvotes', 0)
                    content = item.get('content', '')
                    
                    f.write(f"### {title}\n")
                    f.write(f"**Author:** {author} | **Upvotes:** {upvotes} | **Downvotes:** {downvotes}\n\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")
                elif item.get('type') == 'agent':
                    title = item.get('title', 'Unknown Agent')
                    content = item.get('content', '')
                    f.write(f"### 🤖 Agent: {title}\n")
                    f.write(f"{content}\n\n")
                    f.write("---\n\n")

def get_api_key():
    api_key = os.environ.get("MOLTBOOK_API_KEY")
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, val = line.split('=', 1)
                            if key.strip() == "MOLTBOOK_API_KEY":
                                api_key = val.strip().strip('"\'')
                                break
            except Exception as e:
                print(f"Error reading .env: {e}")
    return api_key

def api_request(url, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error for {url}: {e}")
        return None

def search_moltbook(query, api_key):
    base_url = "https://www.moltbook.com/api/v1"
    url = f"{base_url}/search?q={urllib.parse.quote(query)}"
    return api_request(url, api_key)

def get_post(post_id, api_key):
    base_url = "https://www.moltbook.com/api/v1"
    url = f"{base_url}/posts/{post_id}"
    return api_request(url, api_key)

def main():
    api_key = get_api_key()
    if not api_key:
        print("Error: Could not find Moltbook API key.")
        return

    queries = ["republic", "constitution"]
    all_results = {}

    for q in queries:
        print(f"Searching Moltbook API for: '{q}'...")
        results = search_moltbook(q, api_key)
        
        if results is not None:
            # We want to fetch the full text for posts because the search api truncates them
            if 'results' in results:
                items = results['results']
                print(f" -> Found {len(items)} items. Fetching full content for posts...")
                for item in items:
                    if item.get('type') == 'post':
                        post_id = item.get('id') or item.get('post_id')
                        if post_id:
                            time.sleep(0.2) # Avoid hitting rate limits
                            full_post = get_post(post_id, api_key)
                            if full_post and 'post' in full_post:
                                item['content'] = full_post['post'].get('content', item['content'])

            all_results[q] = results
        else:
            print(f" -> Failed to retrieve data.")

    output_dir = "moltbook_data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "moltbook_api_full_posts.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)
    print(f"\nData collection complete. Results saved to {output_file}")
    
    md_file = os.path.join(output_dir, "readable_posts.md")
    data_to_markdown(all_results, md_file)
    print(f"Successfully converted to {md_file}")

if __name__ == "__main__":
    main()
