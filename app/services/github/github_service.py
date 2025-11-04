# app/services/github/github_service.py
from github import Github, GithubException, InputGitTreeElement
from typing import Dict, Optional, Tuple, Any
import base64
import time
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.github = Github(settings.github_token)
        self.user = self.github.get_user()

    def create_repository(self, repo_name: str, description: str = "") -> Any:
        """Create a new public repository."""
        try:
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=False,
                auto_init=False
            )
            logger.info(f"Created repository: {repo_name}")
            return repo
        except GithubException as e:
            if e.status == 422:  # Repository already exists
                logger.info(f"Repository {repo_name} already exists, using existing")
                return self.user.get_repo(repo_name)
            raise

    def push_files(self, repo, files: Dict[str, str]) -> str:
        """Push files to repository as a single commit and return commit SHA.

        If the repo is empty, create a small placeholder file with the
        Contents API to initialize it, then perform a single commit
        containing all provided files and return that commit's SHA.
        """
        try:
            default_branch = repo.default_branch or "main"
            commit_message = f"Deploy application - Round {files.get('round', 1)}"

            # Build tree elements for the files we want to add/update.
            tree_elements = []
            for filepath, content in files.items():
                if filepath == "round":
                    continue
                tree_elements.append(
                    InputGitTreeElement(path=filepath, mode="100644", type="blob", content=content)
                )

            # Attempt to get the branch reference / base commit.
            # For an empty repo this will raise a GithubException (409 / 404).
            try:
                ref = repo.get_git_ref(f"heads/{default_branch}")
                base_commit = repo.get_git_commit(ref.object.sha)
                base_tree = base_commit.tree
            except GithubException as e:
                # Repo is empty or branch does not exist -> initialize via Contents API
                logger.info(
                    "Repository appears empty or branch missing. Initializing repository with a placeholder file."
                )
                # Create a tiny placeholder file to initialize the git DB.
                # This will create the branch/ref if it didn't exist.
                try:
                    repo.create_file(
                        path=".init",
                        message="Initialize repository",
                        content="Initialized by application",
                        branch=default_branch
                    )
                except GithubException as create_exc:
                    # If the create_file itself fails, re-raise with context
                    logger.error(f"Failed to initialize repository with create_file: {create_exc}")
                    raise

                # Re-fetch the ref/commit now that the repo has an initial commit
                ref = repo.get_git_ref(f"heads/{default_branch}")
                base_commit = repo.get_git_commit(ref.object.sha)
                base_tree = base_commit.tree

            # Create a tree (based on the repo's current tree) that includes/updates only our paths.
            new_tree = repo.create_git_tree(tree_elements, base_tree)

            # Create a single commit with the current commit as parent.
            new_commit = repo.create_git_commit(commit_message, new_tree, [base_commit])

            # Move the branch ref to the new commit
            ref.edit(new_commit.sha, force=True)

            logger.info(f"Pushed {len(tree_elements)} file(s) in single commit: {new_commit.sha}")
            return new_commit.sha

        except Exception as e:
            logger.error(f"Error pushing files: {str(e)}")
            raise


    def enable_pages(self, repo) -> str:
        """Enable GitHub Pages and return the pages URL."""
        try:
            # Enable pages using the API
            headers = {
                'Authorization': f'token {settings.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            import httpx
            # First, ensure we have a gh-pages branch or use main
            try:
                repo.get_branch("gh-pages")
                source_branch = "gh-pages"
            except:
                source_branch = repo.default_branch or "main"
            # Enable Pages
            url = f"https://api.github.com/repos/{repo.full_name}/pages"
            with httpx.Client() as client:
                response = client.post(
                    url,
                    headers=headers,
                    json={
                        "source": {
                            "branch": source_branch,
                            "path": "/"
                        }
                    }
                )
                if response.status_code in [201, 200]:
                    logger.info(f"GitHub Pages enabled for {repo.name}")
                elif response.status_code == 409:
                    logger.info(f"GitHub Pages already enabled for {repo.name}")
                else:
                    logger.warning(f"GitHub Pages response: {response.status_code} - {response.text}")
            # Return the pages URL
            pages_url = f"https://{settings.github_username}.github.io/{repo.name}/"
            return pages_url
        except Exception as e:
            logger.error(f"Error enabling GitHub Pages: {str(e)}")
            # Return expected URL even if enabling fails
            return f"https://{settings.github_username}.github.io/{repo.name}/"

    def get_repository(self, repo_name: str):
        """Get an existing repository."""
        try:
            return self.user.get_repo(repo_name)
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def get_files(self, repo) -> Dict[str, str]:
        """Get all files from a repository."""
        files = {}
        try:
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    # Decode file content
                    if file_content.encoding == 'base64':
                        content = base64.b64decode(file_content.content).decode('utf-8', errors='replace')
                    else:
                        content = file_content.content
                    files[file_content.path] = content
        except Exception as e:
            logger.error(f"Error getting files: {str(e)}")
        return files
