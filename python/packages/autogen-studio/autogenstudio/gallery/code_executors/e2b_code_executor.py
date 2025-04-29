import asyncio
import logging
import os
import re
from hashlib import sha256
from pathlib import Path
import random
from string import Template
from types import SimpleNamespace
from typing import Any, Callable, ClassVar, List, Optional, Sequence, Union
from autogen_core.code_executor import FunctionWithRequirements, FunctionWithRequirementsStr
from autogen_core import CancellationToken, Component
from autogen_core.code_executor import CodeBlock, CodeExecutor
from e2b_code_interpreter import Sandbox
from pydantic import BaseModel
from autogen_ext.code_executors._common import (
    PYTHON_VARIANTS,
    CommandLineCodeResult,
    get_file_name_from_content,
    silence_pip,
    to_stub,
)


logger = logging.getLogger(__name__)

__all__ = ("E2BCommandlineCodeExecutor",)


def random_e2b_api_key():
    e2b_key_list = [
        'e2b_28805f77f5055af5e392b47380a168f7f3eb401e',
        'e2b_5b8813cda8fac5f2cfc51ac944c9747f102468c9',
        'e2b_2b5a720fa1791b7764a11022e73149cbeecc85f7',
        'e2b_28914374f5b77fd444eb4201f52da09de4354cc1',
        'e2b_a6bec1a2acbfca03689702510a336acdedc92057',
        'e2b_ead0384eeb25a1ebc4d0c3197826901efcf467b9',
        'e2b_b2a7d27bd2ce28c822b875bf1832c2c28cc5e26d',
        'e2b_d643bd26f3b181a95e0f784cadc964b8cc4ffa63',
        'e2b_aec35baed63c862fa1814981ed1e7b76ab2fb0a6',
        'e2b_2b988358f795baf8849850a22ab33861c4844ea3',
        'e2b_d3b508129dfde8384e399162e7ad0e4a42929881',
        'e2b_8d527e8cb4f9bb88f536ea4e971510ae477e230b',
        'e2b_acd8f50ccab0fe807a1406980f33e219be1b3041',
        'e2b_65f72ef25e09f0ec718edfaf46ce7d0ea1d3d8b5',
        'e2b_93da56d89c07fbe3388667031a1e31f98033cc89',
        'e2b_10ab63a2b9d3c72d30baeb6190884d55e6217384',
        'e2b_23373f3c85a6e71fa1e93f46c011da942a053da5' # faye
    ]
    return random.choice(e2b_key_list)

filename_patterns = [
    re.compile(r"^<!-- (filename:)?(.+?) -->", re.DOTALL),
    re.compile(r"^/\* (filename:)?(.+?) \*/", re.DOTALL),
    re.compile(r"^// (filename:)?(.+?)$", re.DOTALL),
    re.compile(r"^# (filename:)?(.+?)$", re.DOTALL),
]


class E2BCommandlineCodeExecutorConfig(BaseModel):
    """Configuration for E2BCommandlineCodeExecutor"""
    sandbox_template: str = "base"
    bind_dir: Optional[str] = None

def unescape_string(s: str) -> str:
    """处理所有转义字符"""
    return bytes(s, "utf-8").decode("unicode_escape")


def detect_language(code: str, default_lang: str = "python") -> str:
    """通过代码内容检测编程语言
    
    Args:
        code: 代码内容
        default_lang: 默认语言类型
    
    Returns:
        检测到的语言类型
    """
    # 检查第一行是否包含文件名
    first_line = code.split('\n')[0].strip()
    if first_line.startswith('# filename:'):
        ext = Path(first_line.split(':')[1].strip()).suffix.lstrip('.')
        if ext in ['sh', 'bash']:
            return 'sh'
        elif ext in ['py', 'python']:
            return 'python'
      
        return ext
    
    # 检查是否有 shebang
    if first_line.startswith('#!'):
        if 'bash' in first_line:
            return 'bash'
        elif 'python' in first_line:
            return 'python'
 
    
    # 检查代码特征
    if '!pip install' in code:
        return 'python'
    elif 'pip install' in code and not code.strip().startswith('!'): 
        return 'sh'
    
    return default_lang


class E2BCommandlineCodeExecutor(CodeExecutor, Component[E2BCommandlineCodeExecutorConfig]):
    """A code executor class that executes code in an E2B sandbox environment.

    Args:
        sandbox_template (str): The sandbox template to use. Default is "base".
        bind_dir (Optional[Union[Path, str]]): Local directory to bind with the sandbox.
    """

    component_config_schema = E2BCommandlineCodeExecutorConfig
    component_provider_override = "autogenstudio.gallery.code_executors.e2b_code_executor.E2BCommandlineCodeExecutor"

    SUPPORTED_LANGUAGES: ClassVar[List[str]] = [
        "bash",
        "shell",
        "sh",
        "pwsh",
        "powershell",
        "ps1",
        "python",
    ]

    FUNCTION_PROMPT_TEMPLATE: ClassVar[
        str
    ] = """You have access to the following user defined functions. They can be accessed from the module called `$module_name` by their function names.

    For example, if there was a function called `foo` you could import it by writing `from $module_name import foo`

    $functions"""



    def __init__(
        self,
        timeout: int = 60,
        sandbox_template: str = "code-interpreter-v1",
        work_dir: Union[Path, str] = Path("."),
        functions: Sequence[
            Union[
                FunctionWithRequirements[Any, Any],
                Callable[..., Any],
                FunctionWithRequirementsStr,
            ]
        ] = [],
        functions_module: str = "functions",
          virtual_env_context: Optional[SimpleNamespace] = None,
    ):
        """Initialize the E2B sandbox executor.

        Args:
            sandbox_template (str): Sandbox template name, default is "code-interpreter-v1".
            bind_dir (Optional[Union[Path, str]]): Local directory to bind with sandbox.
        """
        self._timeout = timeout
        self._functions_module = functions_module
        self._sandbox_template = sandbox_template
        self._sandbox = Sandbox(
            api_key=random_e2b_api_key(),
            template=sandbox_template,
            envs={"OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")}
        )
        self._work_dir = Path('/home/user')  # e2b work dir
        if isinstance(work_dir, str):
            work_dir = Path(work_dir)
            
        work_dir.mkdir(exist_ok=True)
        self._bind_dir = Path(work_dir)
        
        self._functions = functions
        
        # Setup could take some time so we intentionally wait for the first code block to do it.
        if len(functions) > 0:
            self._setup_functions_complete = False
        else:
            self._setup_functions_complete = True

        self._virtual_env_context: Optional[SimpleNamespace] = virtual_env_context

    def format_functions_for_prompt(self, prompt_template: str = FUNCTION_PROMPT_TEMPLATE) -> str:
        """(Experimental) Format the functions for a prompt.

        The template includes two variables:
        - `$module_name`: The module name.
        - `$functions`: The functions formatted as stubs with two newlines between each function.

        Args:
            prompt_template (str): The prompt template. Default is the class default.

        Returns:
            str: The formatted prompt.
        """

        template = Template(prompt_template)
        return template.substitute(
            module_name=self._functions_module,
            functions="\n\n".join([to_stub(func) for func in self._functions]),
        )


    async def execute_code_blocks(
        self, code_blocks: List[CodeBlock], cancellation_token: CancellationToken
    ) -> CommandLineCodeResult:
        """Execute code blocks in the E2B sandbox.

        Args:
            code_blocks (List[CodeBlock]): Code blocks to execute.
            cancellation_token (CancellationToken): Token to cancel execution.

        Returns:
            CommandLineCodeResult: Execution result.
        """
        if len(code_blocks) == 0:
            raise ValueError("No code blocks to execute.")

        outputs = []
        filenames = []
        last_exit_code = 0

        for code_block in code_blocks:
            code = code_block.code
            lang = detect_language(code, code_block.language.lower())
            code = silence_pip(code, lang)

            if lang in PYTHON_VARIANTS:
                lang = "python"

            if lang not in self.SUPPORTED_LANGUAGES:
                outputs.append(f"Unsupported language {lang}\n")
                last_exit_code = 1
                break
            
            filename = get_file_name_from_content(code, self._work_dir)
            
            if filename is None:
                code_hash = sha256(code.encode()).hexdigest()
                if lang.startswith("python"):
                    ext = "py"
                elif lang in ["pwsh", "powershell", "ps1"]:
                    ext = "ps1"
                else:
                    ext = lang

                filename = f"tmp_code_{code_hash}.{ext}"

            filenames.append(filename)
            code_path = self._work_dir / filename

            code = unescape_string(code)  # 处理所有转义字符
            
            # Write code to sandbox
            self._sandbox.files.write(str(code_path), code)

            # Execute in sandbox
            command = ["timeout", str(self._timeout), lang, str(code_path)]
            try:
                result = self._sandbox.commands.run(" ".join(command), cwd="/home/user")
                exit_code = result.exit_code
                outputs.append(result.stdout if result.stdout else "")
                outputs.append(result.stderr if result.stderr else "")
                last_exit_code = exit_code
                if exit_code != 0:
                    break

            except Exception as e:
                outputs.append(str(e))
                last_exit_code = 1
                break

        # Download generated files
        files = self.sandbox_download_file()
        code_file = str(files[0]) if files else None

        # 添加markdown格式的文件链接
        if files:
            outputs.append("\nResult:\n")
            for file_path in files:
                relative_path = str(file_path)
                outputs.append(f"📎 [{relative_path}]({relative_path})\n")

        return CommandLineCodeResult(
            exit_code=last_exit_code,
            output="".join(outputs),
            code_file=code_file
        )

    def sandbox_download_file(self) -> List[Path]:
        files = []
        for fileInfo in self._sandbox.files.list(str(self._work_dir)):
            filename = fileInfo.name
            # 如果文件名以 . 开头、是文件夹或者没有扩展名，则跳过
            if filename.startswith('.') or fileInfo.type.value == 'dir' or '.' not in filename:
                continue
            # # 如果文件名是 skills.py，则跳过
            # if filename == 'skills.py':
            #     continue
            # 读取沙盒里文件内容，拼路径，读内容
            sandbox_path = self._work_dir / filename
            
            # 读取文件内容
            content = self._sandbox.files.read(str(sandbox_path),format='bytes')
            
            # 写本地
            autogen_code_path = self._bind_dir / filename
            
            with autogen_code_path.open("wb") as f:
                f.write(content)
            files.append(autogen_code_path)
        return files
    
    async def restart(self) -> None:
        """Restart the E2B sandbox executor."""
        logger.info("Restarting the E2B sandbox...")
        self._sandbox.kill()
        self._sandbox = Sandbox(
            template=self._sandbox_template,
            envs={"OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY")}
        )
        logger.info("E2B sandbox restarted.")

    def _to_config(self) -> E2BCommandlineCodeExecutorConfig:
        return E2BCommandlineCodeExecutorConfig(
            sandbox_template=self._sandbox_template,
            bind_dir=str(self._bind_dir) if self._bind_dir else None
        )

    @classmethod
    def _from_config(cls, config: E2BCommandlineCodeExecutorConfig) -> "E2BCommandlineCodeExecutor":
        return cls(
            sandbox_template=config.sandbox_template,
            work_dir=config.bind_dir if config.bind_dir else Path(".")
        )
