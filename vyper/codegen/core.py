from vyper import ast as vy_ast
from vyper.address_space import CALLDATA, DATA, IMMUTABLES, MEMORY, STORAGE
from vyper.codegen.ir_node import Encoding, IRnode
from vyper.codegen.types import (
    DYNAMIC_ARRAY_OVERHEAD,
    ArrayLike,
    BaseType,
    ByteArrayLike,
    DArrayType,
    MappingType,
    SArrayType,
    StructType,
    TupleLike,
    TupleType,
    ceil32,
    is_bytes_m_type,
    is_decimal_type,
    is_integer_type,
)
from vyper.evm.opcodes import version_check
from vyper.exceptions import CompilerPanic, StructureException, TypeCheckFailure, TypeMismatch
from vyper.utils import GAS_CALLDATACOPY_WORD, GAS_CODECOPY_WORD, GAS_IDENTITY, GAS_IDENTITYWORD


# propagate revert message when calls to external contracts fail
def check_external_call(call_ir):
    copy_revertdata = ["returndatacopy", 0, 0, "returndatasize"]
    revert = ["revert", 0, "returndatasize"]

    propagate_revert_ir = ["seq", copy_revertdata, revert]
    return ["if", ["iszero", call_ir], propagate_revert_ir]


# cost per byte of the identity precompile
def _identity_gas_bound(num_bytes):
    return GAS_IDENTITY + GAS_IDENTITYWORD * (ceil32(num_bytes) // 32)


def _calldatacopy_gas_bound(num_bytes):
    return GAS_CALLDATACOPY_WORD * ceil32(num_bytes) // 32


def _codecopy_gas_bound(num_bytes):
    return GAS_CODECOPY_WORD * ceil32(num_bytes) // 32


# Copy byte array word-for-word (including layout)
def make_byte_array_copier(dst, src):
    assert isinstance(src.typ, ByteArrayLike)
    assert isinstance(dst.typ, ByteArrayLike)

    if src.typ.maxlen > dst.typ.maxlen:
        raise TypeMismatch(f"Cannot cast from {src.typ} to {dst.typ}")
    # stricter check for zeroing a byte array.
    if src.value == "~empty" and src.typ.maxlen != dst.typ.maxlen:
        raise TypeMismatch(
            f"Bad type for clearing bytes: expected {dst.typ} but got {src.typ}"
        )  # pragma: notest

    if src.value == "~empty":
        # set length word to 0.
        return STORE(dst, 0)

    with src.cache_when_complex("src") as (b1, src):
        with get_bytearray_length(src).cache_when_complex("len") as (b2, len_):

            max_bytes = src.typ.maxlen

            ret = ["seq"]
            # store length
            ret.append(STORE(dst, len_))

            dst = bytes_data_ptr(dst)
            src = bytes_data_ptr(src)

            ret.append(copy_bytes(dst, src, len_, max_bytes))
            return b1.resolve(b2.resolve(ret))


def bytes_data_ptr(ptr):
    if ptr.location is None:
        raise CompilerPanic("tried to modify non-pointer type")
    assert isinstance(ptr.typ, ByteArrayLike)
    return add_ofst(ptr, ptr.location.word_scale)


def dynarray_data_ptr(ptr):
    if ptr.location is None:
        raise CompilerPanic("tried to modify non-pointer type")
    assert isinstance(ptr.typ, DArrayType)
    return add_ofst(ptr, ptr.location.word_scale)














# TODO simplify this code, especially the ABI decoding



def has_length_word(typ):
    return isinstance(typ, (DArrayType, ByteArrayLike))














# sanity check an assignment
# typechecking source code is done at an earlier phase
# this function is more of a sanity check for typechecking internally
# generated assignments
def check_assign(left, right):
    def FAIL():  # pragma: nocover
        raise TypeCheckFailure(f"assigning {right.typ} to {left.typ} {left} {right}")

    if isinstance(left.typ, ByteArrayLike):
        _check_assign_bytes(left, right)
    elif isinstance(left.typ, ArrayLike):
        _check_assign_list(left, right)
    elif isinstance(left.typ, TupleLike):
        _check_assign_tuple(left, right)

    elif isinstance(left.typ, BaseType):
        # TODO once we propagate types from typechecker, introduce this check:
        # if left.typ != right.typ:
        #    FAIL()  # pragma: notest
        pass

    else:  # pragma: nocover
        FAIL()


_label = 0


# TODO might want to coalesce with Context.fresh_varname and compile_ir.mksymbol
def _freshname(name):
    global _label
    _label += 1
    return f"{name}{_label}"












