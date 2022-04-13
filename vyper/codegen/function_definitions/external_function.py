from typing import Any, List

import vyper.utils as util
from vyper.address_space import CALLDATA, DATA, MEMORY
from vyper.ast.signatures.function_signature import FunctionSignature, VariableRecord
from vyper.codegen.context import Context
from vyper.codegen.core import get_element_ptr, getpos, make_setter
from vyper.codegen.expr import Expr
from vyper.codegen.function_definitions.utils import get_nonreentrant_lock
from vyper.codegen.ir_node import Encoding, IRnode
from vyper.codegen.stmt import parse_body
from vyper.codegen.types.types import (
    BaseType,
    ByteArrayLike,
    DArrayType,
    SArrayType,
    TupleLike,
    TupleType,
)
from vyper.exceptions import CompilerPanic














