# Copyright 2023 BentoML Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""OCI-related utilities for OpenLLM. This module is considered to be internal and API are subjected to change."""
from __future__ import annotations
import pathlib
import subprocess
import typing as t

from git.exc import InvalidGitRepositoryError
from git.repo import Repo

import bentoml

from ...exceptions import Error
from ...utils import apply
from ...utils import device_count
from ...utils import generate_hash_from_file
from ...utils import pkg

_BUILDER = bentoml.container.get_backend("buildx")
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

LiteralContainerRegistry = t.Literal["docker", "gh", "quay"]

_CONTAINER_REGISTRY: dict[LiteralContainerRegistry, str] = {"docker": "docker.io", "gh": "ghcr.io", "quay":"quay.io"}

@apply(str.lower)
def get_container_name() -> str:
    try:
        repo = Repo(pkg.source_locations("openllm"), search_parent_directories=True)
        url = repo.remotes.origin.url
        is_http_url = url.startswith("https://")
        parts = url.split("/") if is_http_url else url.split(":")
        return f"{parts[-2]}/{parts[-1].rstrip('.git')}" if is_http_url else parts[-1]
    except InvalidGitRepositoryError: return "openllm"

def get_container_tag() -> str:
    # To work with bare setup
    try: return Repo(pkg.source_locations("openllm"), search_parent_directories=True).head.commit.hexsha
    # in this case, not a repo, then just generate GIT_SHA-like hash
    # from the root directory of openllm from this file
    except InvalidGitRepositoryError: return generate_hash_from_file(ROOT_DIR.resolve().__fspath__())

def build_container(registries: t.Literal["local"] | LiteralContainerRegistry | t.Sequence[LiteralContainerRegistry] | None = None, push: bool = False):
    try:
        if not _BUILDER.health(): raise Error
    except (Error, subprocess.CalledProcessError): raise RuntimeError("Building base container requires BuildKit (via Buildx) to be installed. See https://docs.docker.com/build/buildx/install/ for instalation instruction.") from None
    if device_count() == 0: raise RuntimeError("Building base container requires GPUs (None available)")
