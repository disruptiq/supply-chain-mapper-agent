import yaml
import os
from typing import List, Dict, Any


class YamlParser:
    def __init__(self):
        pass

    def parse(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        filename = os.path.basename(manifest_path)

        if filename.endswith('.yml') or filename.endswith('.yaml'):
            if 'docker-compose' in filename:
                dependencies.extend(self._parse_docker_compose(manifest_path))
            elif '.github/workflows/' in manifest_path:
                dependencies.extend(self._parse_github_workflow(manifest_path))
            elif filename == '.gitlab-ci.yml':
                dependencies.extend(self._parse_gitlab_ci(manifest_path))

        return dependencies

    def _parse_docker_compose(self, manifest_path: str) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return deps

        if not content or 'services' not in content:
            return deps

        for service_name, service_config in content['services'].items():
            if 'image' in service_config:
                image = service_config['image']
                # Parse image:tag or image@digest
                if '@' in image:
                    name, digest = image.split('@', 1)
                    version = digest
                elif ':' in image:
                    name, version = image.rsplit(':', 1)
                else:
                    name = image
                    version = 'latest'

                dep_record = {
                    "ecosystem": "docker",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "docker_registry",
                        "resolved": None
                    },
                    "metadata": {
                        "dev_dependency": False,
                        "line_number": None,  # YAML doesn't have easy line numbers
                        "script_section": False,
                        "service": service_name
                    }
                }
                deps.append(dep_record)

        return deps

    def _parse_github_workflow(self, manifest_path: str) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return deps

        if not content or 'jobs' not in content:
            return deps

        for job_name, job_config in content['jobs'].items():
            if 'steps' in job_config:
                for step in job_config['steps']:
                    if 'uses' in step:
                        action_ref = step['uses']
                        # Parse owner/repo@version or owner/repo@ref
                        if '@' in action_ref:
                            name, version = action_ref.split('@', 1)
                        else:
                            name = action_ref
                            version = 'main'  # default branch

                        dep_record = {
                            "ecosystem": "github_actions",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": name,
                                "version": version,
                                "source": "github",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": False,
                                "line_number": None,
                                "script_section": False,
                                "job": job_name
                            }
                        }
                        deps.append(dep_record)

        return deps

    def _parse_gitlab_ci(self, manifest_path: str) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return deps

        if not content:
            return deps

        # GitLab CI can have global image or per-job images
        if 'image' in content:
            image = content['image']
            deps.extend(self._parse_image(image, manifest_path, "global"))

        for job_name, job_config in content.items():
            if isinstance(job_config, dict) and 'image' in job_config:
                image = job_config['image']
                deps.extend(self._parse_image(image, manifest_path, job_name))

        return deps

    def _parse_image(self, image: str, manifest_path: str, context: str) -> List[Dict[str, Any]]:
        deps = []
        if isinstance(image, str):
            # Similar to docker-compose parsing
            if '@' in image:
                name, digest = image.split('@', 1)
                version = digest
            elif ':' in image:
                name, version = image.rsplit(':', 1)
            else:
                name = image
                version = 'latest'

            dep_record = {
                "ecosystem": "docker",
                "manifest_path": os.path.relpath(manifest_path),
                "dependency": {
                    "name": name,
                    "version": version,
                    "source": "docker_registry",
                    "resolved": None
                },
                "metadata": {
                    "dev_dependency": False,
                    "line_number": None,
                    "script_section": False,
                    "context": context
                }
            }
            deps.append(dep_record)
        return deps
