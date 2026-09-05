import urllib.request
import json

def fetch_data(urls):
    results = []
    
    for url in urls:
        req = urllib.request.urlopen(url)
        data = req.read()
        results.append(json.loads(data))
        req.close()
    
    return results

def scrape_website(url):
    response = urllib.request.urlopen(url)
    content = response.read()
    # Process content
    return content.decode('utf-8')

if __name__ == "__main__":
    urls = ["http://example.com/api/1", "http://example.com/api/2"]
    data = fetch_data(urls)
    print(f"Fetched {len(data)} records")
