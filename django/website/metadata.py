import http.client
import json

from datetime import datetime

class GithubUserData:
    login: str
    id: int
    type: str

    def __init__(self, data: dict):
        self.login = data['login']
        self.id = data['id']
        self.type = data['type']

class GithubLicenseData:
    key: str
    name: str
    spdx_id: str
    url: str

    def __init__(self, data: dict):
        self.key = data['key']
        self.name = data['name']
        self.spdx_id = data['spdx_id']
        self.url = data['url']

class GithubRepoData:
    id: int
    name: str
    full_name: str
    private: bool
    owner: GithubUserData
    html_url: str
    description: str
    collaborators_url: str
    teams_url: str
    git_commits_url: str
    downloads_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    homepage: str | None
    language: str
    license: GithubLicenseData

    def __init__(self, data: dict):
        self.id = data['id']
        self.name = data['name']
        self.full_name = data['full_name']
        self.private = data['private']
        self.html_url = data['html_url']
        self.description = data['description']
        self.collaborators_url = data['collaborators_url']
        self.teams_url = data['teams_url']
        self.git_commits_url = data['git_commits_url']
        self.downloads_url = data['downloads_url']
        self.releases_url = data['releases_url']
        self.deployments_url = data['deployments_url']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.pushed_at = data['pushed_at']
        self.homepage = data['homepage']
        self.language = data['language']

        if data['owner'] is None:
            self.owner = None
        else:
            self.owner = GithubUserData(data['owner'])
        
        if data['license'] is None:
            self.license = None
        else:
            self.license = GithubLicenseData(data['license'])

class RepoData:
    name: str = ""
    owner: str = ""
    description: str = ""
    homepage: str = ""
    repo_url: str = ""
    created_date: datetime | None = None
    updated_date: datetime | None = None
    publish_date: datetime | None = None
    credits: list[str] = []
    languages: list[str] = []
    version: str = ""

    def __init__(self):
        pass

    @staticmethod
    def from_github_data(data: GithubRepoData) -> 'RepoData':
        fmt_str = "%Y-%m-%dT%H:%M:%SZ"

        if data is None:
            return None

        repodata = RepoData()
        repodata.name = data.name
        repodata.owner = data.owner.login
        repodata.description = data.description
        repodata.homepage = data.homepage or ""
        repodata.repo_url = data.html_url
        repodata.created_date = datetime.strptime(data.created_at, fmt_str)
        repodata.updated_date = datetime.strptime(data.updated_at, fmt_str)
        repodata.publish_date = None # TODO get publish date from release url
        repodata.credits = [data.owner.login] # TODO get credits from contributors url
        repodata.languages = [data.language] # TODO get languages from languages url
        repodata.version = "" # TODO get version from release url

        return repodata

    def from_gitlab_data(data: dict) -> 'RepoData':
        print("Gitlab metadata retrieval not implemented")
        return None

def get_metadata(repo_url: str) -> RepoData | None:

    # get repo data from appropriate web api
    if "github.com" in repo_url:
        return RepoData.from_github_data(github_metadata(repo_url))
    elif "gitlab.com" in repo_url:
        return RepoData.from_gitlab_data(gitlab_metadata(repo_url))
    
    # if no match, return None
    return None

def gitlab_metadata(url: str) -> dict:
    # TODO
    print("Gitlab metadata retrieval not implemented")
    return None

def github_metadata(url: str) -> GithubRepoData | None:

    # Extract the owner and repo names from the URL
    url_post_domain = url.split("github.com/")[1]
    owner = url_post_domain.split("/")[0]
    repo = url_post_domain.split("/")[1]

    # Set up the connection to the GitHub API
    host = "api.github.com"
    conn = http.client.HTTPSConnection(host)
    
    # Define the API endpoint
    endpoint = f"/repos/{owner}/{repo}"
    print(f"attempting to get repo metadata from {host + endpoint}")

    # Make the GET request
    conn.request(
        "GET", 
        endpoint, 
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Python-requests/2.26.0)"
        }
    )
    
    # Get the response
    response = conn.getresponse()

    # Check if the request was successful
    if response.status == 200:
        # Read and decode the response data
        data = response.read().decode("utf-8")
        
        # Parse the JSON response
        repo_metadata = json.loads(data)
        
        # Close the connection
        conn.close()
        
        # print the retrieved metadata
        # print(f"Repository: {repo_metadata['full_name']}:")
        # for key, value in repo_metadata.items():
        #     print(f"  {key}: {value}")

        return GithubRepoData(repo_metadata)
    else:
        # Handle errors
        print(f"Error: {response.status} - {response.reason}")
        conn.close()
        return None