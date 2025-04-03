import os
import requests
import yaml
import base64
import time
from pathlib import Path

# --- Configuration ---
GITHUB_API_URL = "https://api.github.com"
PYPI_API_URL = "https://pypi.org/pypi"
SEARCH_QUERY = "LitePolis- in:name fork:false" # Search for repos starting with LitePolis-, excluding forks
OUTPUT_DIR = Path("_data")
OUTPUT_FILE = OUTPUT_DIR / "repositories.yml"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # Optional: Use for higher rate limits

# --- Helper Functions ---

def make_request(url, headers=None):
    """Makes a GET request and handles potential errors."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        # Check rate limit
        remaining = int(response.headers.get('X-RateLimit-Remaining', 10))
        if remaining < 5:
            print("Approaching GitHub rate limit, sleeping...")
            time.sleep(60)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for {url}: {e}")
        return None

def get_github_readme(repo_full_name, headers):
    """Fetches and decodes the README content from GitHub."""
    readme_url = f"{GITHUB_API_URL}/repos/{repo_full_name}/readme"
    readme_data = make_request(readme_url, headers=headers)
    if readme_data and 'content' in readme_data:
        try:
            # Decode base64 content
            decoded_content = base64.b64decode(readme_data['content']).decode('utf-8')
            return decoded_content
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            print(f"Error decoding README for {repo_full_name}: {e}")
            return "Error decoding README."
        except Exception as e:
            print(f"An unexpected error occurred decoding README for {repo_full_name}: {e}")
            return "Error processing README."
    return None

def get_github_license(repo_full_name, headers):
    """Fetches the license information from GitHub."""
    license_url = f"{GITHUB_API_URL}/repos/{repo_full_name}/license"
    license_data = make_request(license_url, headers=headers)
    if license_data and 'license' in license_data and license_data['license']:
        return license_data['license'].get('name', 'License info unavailable')
    return None # No license file found or API error

def check_pypi(package_name):
    """Checks if a package exists on PyPI."""
    pypi_url = f"{PYPI_API_URL}/{package_name}/json"
    try:
        response = requests.get(pypi_url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking PyPI for {package_name}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred checking PyPI for {package_name}: {e}")
        return False

# --- Main Script ---

def main():
    print("Fetching repositories from GitHub...")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
        print("Using GitHub token for authentication.")

    search_url = f"{GITHUB_API_URL}/search/repositories?q={SEARCH_QUERY}&sort=updated&order=desc&per_page=100"
    search_results = make_request(search_url, headers=headers)

    if not search_results or 'items' not in search_results:
        print("Failed to fetch repositories or no repositories found.")
        return

    repositories_data = []
    print(f"Found {search_results.get('total_count', 0)} repositories. Processing...")

    for item in search_results['items']:
        repo_name = item['name']
        repo_full_name = item['full_name']
        print(f"Processing: {repo_full_name}")

        # Basic repo info
        repo_info = {
            "name": repo_name,
            "url": item['html_url'],
            "description": item.get('description', ''),
            "stars": item.get('stargazers_count', 0),
            "last_updated": item.get('updated_at', '')
        }

        # Check PyPI (assuming package name matches repo name, might need adjustment)
        # Example: LitePolis-Core -> litepolis-core
        pypi_package_name = repo_name.lower()
        if check_pypi(pypi_package_name):
            repo_info["install_command"] = f"litepolis-cli deploy add {pypi_package_name}"
            print(f"  Found on PyPI: {pypi_package_name}")
        else:
            repo_info["install_command"] = None
            print(f"  Not found on PyPI: {pypi_package_name}")

        # Get README
        readme_content = get_github_readme(repo_full_name, headers)
        repo_info["readme"] = readme_content
        if readme_content:
             print(f"  Fetched README.")
        else:
             print(f"  README not found or error fetching.")


        # Get License
        license_name = get_github_license(repo_full_name, headers)
        repo_info["license"] = license_name
        if license_name:
            print(f"  Fetched License: {license_name}")
        else:
            print(f"  License not found or error fetching.")

        repositories_data.append(repo_info)
        time.sleep(0.5) # Small delay to avoid hitting secondary rate limits

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write data to YAML file
    print(f"\nWriting data for {len(repositories_data)} repositories to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(repositories_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print("Successfully wrote data.")
    except IOError as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")
    except yaml.YAMLError as e:
        print(f"Error formatting data to YAML: {e}")
    except Exception as e:
        print(f"An unexpected error occurred writing YAML: {e}")


if __name__ == "__main__":
    main()