"""Code execution service with Docker sandbox"""
import docker
import subprocess
import tempfile
import os
import shutil
from typing import Dict, Any
from datetime import datetime

class CodeExecutor:
    """Execute code in various languages"""
    
    def __init__(self):
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except:
            print("⚠️ Docker not available, using local execution")
    
    def execute(self, code: str, language: str, use_sandbox: bool = True) -> Dict[str, Any]:
        """Execute code with optional Docker sandbox"""
        if use_sandbox and self.docker_client:
            return self._execute_docker(code, language)
        else:
            return self._execute_local(code, language)
    
    def _execute_docker(self, code: str, language: str) -> Dict[str, Any]:
        """Execute code in Docker container"""
        try:
            image_map = {
                "python": "python:3.11-alpine",
                "java": "openjdk:17-alpine",
                "javascript": "node:18-alpine",
                "c": "gcc:alpine"
            }
            
            image = image_map.get(language.lower())
            if not image:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}",
                    "sandboxed": False
                }
            
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                code_file = os.path.join(tmpdir, self._get_filename(language))
                
                with open(code_file, 'w') as f:
                    f.write(code)
                
                # Run in container
                container = self.docker_client.containers.run(
                    image,
                    command=self._get_docker_command(language, code_file),
                    volumes={tmpdir: {'bind': '/code', 'mode': 'ro'}},
                    working_dir='/code',
                    mem_limit='100m',
                    cpu_period=100000,
                    cpu_quota=50000,
                    network_mode='none',
                    remove=True,
                    stdout=True,
                    stderr=True,
                    timeout=10
                )
                
                output = container.decode('utf-8') if isinstance(container, bytes) else str(container)
                
                return {
                    "success": True,
                    "output": output,
                    "sandboxed": True,
                    "execution_time": 0.0  # Would calculate actual time
                }
                
        except docker.errors.ContainerError as e:
            return {
                "success": False,
                "error": str(e.stderr.decode('utf-8') if hasattr(e, 'stderr') else str(e)),
                "sandboxed": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Docker execution failed: {str(e)}",
                "sandboxed": True
            }
    
    def _execute_local(self, code: str, language: str) -> Dict[str, Any]:
        """Execute code locally (fallback)"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_suffix(language), delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            start_time = datetime.now()
            
            if language == "python":
                result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)
            elif language == "java":
                # Java requires compilation
                compile_result = subprocess.run(['javac', temp_file], capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": compile_result.stderr,
                        "sandboxed": False
                    }
                class_file = temp_file.replace('.java', '.class')
                result = subprocess.run(['java', '-cp', os.path.dirname(temp_file), 'Main'], 
                                      capture_output=True, text=True, timeout=10)
            elif language == "javascript":
                result = subprocess.run(['node', temp_file], capture_output=True, text=True, timeout=10)
            elif language == "c":
                compile_result = subprocess.run(['gcc', temp_file, '-o', temp_file + '.out'], 
                                              capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": compile_result.stderr,
                        "sandboxed": False
                    }
                result = subprocess.run([temp_file + '.out'], capture_output=True, text=True, timeout=10)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}",
                    "sandboxed": False
                }
            
            exec_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "sandboxed": False,
                "execution_time": exec_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timed out (10 seconds)",
                "sandboxed": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sandboxed": False
            }
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
                if language == "java":
                    class_file = temp_file.replace('.java', '.class')
                    if os.path.exists(class_file):
                        os.unlink(class_file)
                elif language == "c":
                    exe_file = temp_file + '.out'
                    if os.path.exists(exe_file):
                        os.unlink(exe_file)
            except:
                pass
    
    def _get_filename(self, language: str) -> str:
        """Get filename for code"""
        extensions = {
            "python": "code.py",
            "java": "Main.java",
            "javascript": "code.js",
            "c": "code.c"
        }
        return extensions.get(language, "code.txt")
    
    def _get_suffix(self, language: str) -> str:
        """Get file suffix for code"""
        suffixes = {
            "python": ".py",
            "java": ".java",
            "javascript": ".js",
            "c": ".c"
        }
        return suffixes.get(language, ".txt")
    
    def _get_docker_command(self, language: str, code_file: str) -> str:
        """Get Docker command for language"""
        commands = {
            "python": ["python", "/code/code.py"],
            "java": ["sh", "-c", "javac /code/Main.java && java -cp /code Main"],
            "javascript": ["node", "/code/code.js"],
            "c": ["sh", "-c", "gcc /code/code.c -o /code/program && /code/program"]
        }
        return commands.get(language, ["echo", "Unsupported language"])