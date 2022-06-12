from typing import Iterable

from n2t.core.compiler.parser.jack_compiler import JackCompiler as DefaultJackCompiler
from n2t.core.compiler.tokenizer.tokenizer_facade import JackTokenizer
from n2t.infra.io import FileFormat


class JackCompiler:
    def get_file_format(self) -> FileFormat:
        return FileFormat.vm

    def compile(self, tokenizer: JackTokenizer) -> Iterable[str]:
        return list[str](DefaultJackCompiler(tokenizer).compile_class())
