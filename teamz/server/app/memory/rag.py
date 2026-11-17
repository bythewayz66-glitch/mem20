"""RAG over git history: 'why was this function added?'"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .vector import VectorMemory, get_vector_memory
from ..config import settings


class RAGConfig(BaseModel):
    """Configuration for Git History RAG."""
    vector_config: Optional[Dict[str, Any]] = None
    repo_path: str = Field(default_factory=lambda: os.getenv("TEAMZ_REPO_PATH", "/opt/mem20"))
    max_commits: int = 1000
    max_diff_size: int = 50000
    include_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.md", "*.txt"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["*.lock", "node_modules/", ".git/", "__pycache__/", "dist/", "build/"])
    index_branches: List[str] = Field(default_factory=lambda: ["main", "master", "develop"])


@dataclass
class GitCommit:
    """A git commit with metadata."""
    hash: str
    short_hash: str
    author: str
    author_email: str
    date: float
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int
    parents: List[str] = field(default_factory=list)

    def to_search_text(self) -> str:
        return f"Commit: {self.message}\nAuthor: {self.author}\nFiles: {', '.join(self.files_changed)}"

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "hash": self.hash,
            "short_hash": self.short_hash,
            "author": self.author,
            "author_email": self.author_email,
            "date": self.date,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "parents": self.parents,
            "rag_type": "commit",
        }


@dataclass
class GitDiff:
    """A git diff for a file in a commit."""
    commit_hash: str
    file_path: str
    old_path: Optional[str]
    new_path: Optional[str]
    diff: str
    language: str
    change_type: str  # added, modified, deleted, renamed

    def to_search_text(self) -> str:
        return f"File: {self.file_path}\nChange: {self.change_type}\nDiff:\n{self.diff}"

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "file_path": self.file_path,
            "old_path": self.old_path,
            "new_path": self.new_path,
            "language": self.language,
            "change_type": self.change_type,
            "rag_type": "diff",
        }


@dataclass
class GitBlameLine:
    """A line from git blame."""
    commit_hash: str
    author: str
    date: float
    line_number: int
    content: str
    file_path: str

    def to_search_text(self) -> str:
        return f"File: {self.file_path}:{self.line_number}\nAuthor: {self.author}\nDate: {time.ctime(self.date)}\nCode: {self.content}"

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "commit_hash": self.commit_hash,
            "author": self.author,
            "date": self.date,
            "line_number": self.line_number,
            "content": self.content,
            "file_path": self.file_path,
            "rag_type": "blame",
        }


class GitHistoryRAG:
    """RAG system over git history."""

    def __init__(self, config: Optional[RAGConfig] = None) -> None:
        self.config = config or RAGConfig()
        self._vector_memory: Optional[VectorMemory] = None
        self._indexed_commits: Set[str] = set()
        self._indexed_files: Dict[str, float] = {}  # file_path -> last_indexed_commit_time

    async def initialize(self) -> None:
        if self._vector_memory is None:
            self._vector_memory = get_vector_memory()
            await self._vector_memory.initialize()

    async def close(self) -> None:
        if self._vector_memory:
            await self._vector_memory.close()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hex_digest = hash_obj.hexdigest()
        vec = []
        for i in range(1536):
            chunk_idx = (i * 2) % len(hex_digest)
            chunk = hex_digest[chunk_idx:chunk_idx+2]
            if len(chunk) == 2:
                val = int(chunk, 16) / 255.0
            else:
                val = int(chunk + hex_digest[0], 16) / 255.0
            vec.append(val)
        return vec

    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> str:
        """Run a git command."""
        cwd = cwd or self.config.repo_path
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout

    def _get_commits(self, branch: str = "HEAD", max_count: int = 100) -> List[GitCommit]:
        """Get recent commits."""
        output = self._run_git([
            "log",
            f"--max-count={max_count}",
            "--pretty=format:%H|%h|%an|%ae|%at|%s|%P",
            "--numstat",
            branch,
        ])

        commits = []
        current_commit: Optional[Dict] = None

        for line in output.strip().split("\n"):
            if "|" in line and line.count("|") >= 6:
                # Commit header
                if current_commit:
                    commits.append(self._parse_commit(current_commit))
                parts = line.split("|", 6)
                current_commit = {
                    "hash": parts[0],
                    "short_hash": parts[1],
                    "author": parts[2],
                    "author_email": parts[3],
                    "date": float(parts[4]),
                    "message": parts[5],
                    "parents": parts[6].split() if parts[6] else [],
                    "files_changed": [],
                    "insertions": 0,
                    "deletions": 0,
                }
            elif current_commit and line.strip():
                # Numstat line: insertions\tdeletions\tfile
                parts = line.split("\t")
                if len(parts) >= 3:
                    try:
                        ins = int(parts[0]) if parts[0] != "-" else 0
                        dels = int(parts[1]) if parts[1] != "-" else 0
                        current_commit["insertions"] += ins
                        current_commit["deletions"] += dels
                        current_commit["files_changed"].append(parts[2])
                    except ValueError:
                        pass

        if current_commit:
            commits.append(self._parse_commit(current_commit))

        return commits

    def _parse_commit(self, data: Dict) -> GitCommit:
        return GitCommit(
            hash=data["hash"],
            short_hash=data["short_hash"],
            author=data["author"],
            author_email=data["author_email"],
            date=data["date"],
            message=data["message"],
            files_changed=data["files_changed"],
            insertions=data["insertions"],
            deletions=data["deletions"],
            parents=data["parents"],
        )

    def _get_diff(self, commit_hash: str, file_path: str) -> Optional[GitDiff]:
        """Get diff for a file in a commit."""
        try:
            output = self._run_git(["show", f"{commit_hash}:{file_path}"])
            # This is simplified - real implementation would parse git show properly
            return None
        except RuntimeError:
            return None

    def _get_blame(self, file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> List[GitBlameLine]:
        """Get git blame for a file."""
        args = ["blame", "-L", f"{start_line},{end_line or '+'}", "--porcelain", file_path]
        output = self._run_git(args)

        lines = []
        current: Dict = {}

        for line in output.split("\n"):
            if line.startswith("^"):
                continue
            if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
                # Commit hash
                if current:
                    lines.append(GitBlameLine(
                        commit_hash=current.get("hash", ""),
                        author=current.get("author", ""),
                        date=current.get("date", 0),
                        line_number=current.get("line_number", 0),
                        content=current.get("content", ""),
                        file_path=file_path,
                    ))
                current = {"hash": line}
            elif line.startswith("author "):
                current["author"] = line[7:]
            elif line.startswith("author-time "):
                current["date"] = float(line[12:])
            elif line.startswith("\t"):
                current["content"] = line[1:]
            elif line.isdigit():
                current["line_number"] = int(line)

        if current:
            lines.append(GitBlameLine(
                commit_hash=current.get("hash", ""),
                author=current.get("author", ""),
                date=current.get("date", 0),
                line_number=current.get("line_number", 0),
                content=current.get("content", ""),
                file_path=file_path,
            ))

        return lines

    async def index_repository(self, branch: str = "HEAD", max_commits: Optional[int] = None) -> int:
        """Index the repository's git history."""
        await self.initialize()

        max_commits = max_commits or self.config.max_commits
        indexed = 0

        for branch_name in self.config.index_branches:
            try:
                commits = self._get_commits(branch_name, max_commits)

                for commit in commits:
                    if commit.hash in self._indexed_commits:
                        continue

                    # Index commit
                    search_text = commit.to_search_text()
                    embedding = self._get_embedding(search_text)
                    await self._vector_memory.add(
                        content=search_text,
                        embedding=embedding,
                        metadata=commit.to_metadata(),
                        importance=1.0,
                        id=f"commit:{commit.hash}",
                    )

                    # Index diffs for each file
                    for file_path in commit.files_changed:
                        # Skip excluded patterns
                        if any(p in file_path for p in self.config.exclude_patterns):
                            continue
                        if not any(file_path.endswith(p.replace("*", "")) for p in self.config.include_patterns if "*" in p):
                            # Check if matches include pattern
                            pass

                        diff = self._get_diff(commit.hash, file_path)
                        if diff and len(diff.diff) < self.config.max_diff_size:
                            diff_text = diff.to_search_text()
                            diff_embedding = self._get_embedding(diff_text)
                            await self._vector_memory.add(
                                content=diff_text,
                                embedding=diff_embedding,
                                metadata=diff.to_metadata(),
                                importance=0.8,
                                id=f"diff:{commit.hash}:{file_path}",
                            )

                    self._indexed_commits.add(commit.hash)
                    indexed += 1

            except RuntimeError as e:
                print(f"[GitHistoryRAG] Failed to index branch {branch_name}: {e}")

        return indexed

    async def index_file_history(self, file_path: str) -> int:
        """Index the full history of a specific file."""
        await self.initialize()

        # Get all commits that touched this file
        output = self._run_git(["log", "--follow", "--pretty=format:%H", "--", file_path])
        commits = [c for c in output.strip().split("\n") if c]

        indexed = 0
        for commit_hash in commits[:self.config.max_commits]:
            if commit_hash in self._indexed_commits:
                continue

            # Get commit details
            commit_info = self._run_git(["show", "--pretty=format:%H|%h|%an|%ae|%at|%s|%P", "--numstat", "-s", commit_hash])
            # Parse and index...

            self._indexed_commits.add(commit_hash)
            indexed += 1

        return indexed

    async def query(
        self,
        question: str,
        top_k: int = 10,
        include_commits: bool = True,
        include_diffs: bool = True,
        include_blame: bool = False,
        file_path: Optional[str] = None,
    ) -> Dict[str, List[Any]]:
        """Query git history with natural language."""
        await self.initialize()

        query_embedding = self._get_embedding(question)
        filter_metadata = {}

        results = {"commits": [], "diffs": [], "blame": []}

        if include_commits:
            filter_metadata["rag_type"] = "commit"
            commit_results = await self._vector_memory.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            for vec, score in commit_results:
                if vec.metadata.get("rag_type") == "commit":
                    results["commits"].append({
                        "commit": vec.metadata,
                        "score": score,
                    })

        if include_diffs:
            filter_metadata["rag_type"] = "diff"
            if file_path:
                filter_metadata["file_path"] = file_path
            diff_results = await self._vector_memory.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            for vec, score in diff_results:
                if vec.metadata.get("rag_type") == "diff":
                    results["diffs"].append({
                        "diff": vec.metadata,
                        "score": score,
                    })

        if include_blame and file_path:
            # Get recent blame for context
            blame_lines = self._get_blame(file_path)
            for line in blame_lines[:20]:
                blame_text = line.to_search_text()
                blame_embedding = self._get_embedding(blame_text)
                blame_results = await self._vector_memory.search(
                    query_embedding=blame_embedding,
                    top_k=5,
                    filter_metadata={"rag_type": "blame"},
                )
                for vec, score in blame_results:
                    if vec.metadata.get("rag_type") == "blame":
                        results["blame"].append({
                            "line": vec.metadata,
                            "score": score,
                        })

        return results

    async def explain_code(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
    ) -> Dict[str, Any]:
        """Explain why code was added/changed."""
        await self.initialize()

        # Get blame for the lines
        blame_lines = self._get_blame(file_path, start_line, end_line)

        # Get commits that introduced these lines
        commits = []
        for line in blame_lines:
            commit_hash = line.commit_hash
            if commit_hash not in self._indexed_commits:
                # Index this commit
                await self.index_file_history(file_path)

            commit_results = await self._vector_memory.search(
                query_embedding=self._get_embedding(f"commit {commit_hash}"),
                top_k=1,
                filter_metadata={"rag_type": "commit", "hash": commit_hash},
            )
            if commit_results:
                commits.append(commit_results[0][0].metadata)

        # Get diffs for context
        diffs = []
        for commit in commits:
            diff_results = await self._vector_memory.search(
                query_embedding=self._get_embedding(f"diff {commit['hash']} {file_path}"),
                top_k=1,
                filter_metadata={"rag_type": "diff", "commit_hash": commit["hash"], "file_path": file_path},
            )
            if diff_results:
                diffs.append(diff_results[0][0].metadata)

        return {
            "file_path": file_path,
            "lines": f"{start_line}-{end_line}",
            "blame": [bl.to_metadata() for bl in blame_lines],
            "commits": commits,
            "diffs": diffs,
        }

    async def find_related_changes(
        self,
        file_path: str,
        commit_hash: str,
    ) -> List[Dict[str, Any]]:
        """Find other files changed in the same commit."""
        await self.initialize()

        filter_metadata = {"rag_type": "commit", "hash": commit_hash}
        query_embedding = self._get_embedding(f"commit {commit_hash}")
        results = await self._vector_memory.search(
            query_embedding=query_embedding,
            top_k=1,
            filter_metadata=filter_metadata,
        )

        if not results:
            return []

        commit_meta = results[0][0].metadata
        files = commit_meta.get("files_changed", [])

        related = []
        for f in files:
            if f != file_path:
                diff_results = await self._vector_memory.search(
                    query_embedding=self._get_embedding(f"diff {commit_hash} {f}"),
                    top_k=1,
                    filter_metadata={"rag_type": "diff", "commit_hash": commit_hash, "file_path": f},
                )
                if diff_results:
                    related.append({
                        "file": f,
                        "diff": diff_results[0][0].metadata,
                        "score": diff_results[0][1],
                    })

        return related


# Global instance
_git_history_rag: Optional[GitHistoryRAG] = None


def get_git_history_rag(config: Optional[RAGConfig] = None) -> GitHistoryRAG:
    """Get global git history RAG instance."""
    global _git_history_rag
    if _git_history_rag is None:
        _git_history_rag = GitHistoryRAG(config)
    return _git_history_rag