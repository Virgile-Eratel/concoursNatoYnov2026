"""Lit la table d'exports PE d'une DLL sans outils externes."""
import struct, sys
from pathlib import Path

def read_exports(path):
    data = Path(path).read_bytes()

    # DOS header → PE offset
    if data[:2] != b'MZ':
        return []
    pe_off = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe_off:pe_off+4] != b'PE\0\0':
        return []

    # COFF header
    machine = struct.unpack_from('<H', data, pe_off+4)[0]
    num_sections = struct.unpack_from('<H', data, pe_off+6)[0]
    opt_off = pe_off + 24
    magic = struct.unpack_from('<H', data, opt_off)[0]
    is64 = (magic == 0x20B)

    if is64:
        export_rva, export_size = struct.unpack_from('<II', data, opt_off + 112)
    else:
        export_rva, export_size = struct.unpack_from('<II', data, opt_off + 96)

    # Section headers → trouve l'export directory
    sec_off = opt_off + (112 if is64 else 96) + 8 * (16 if is64 else 16)
    # Recalcul correct : optional header size
    opt_size = struct.unpack_from('<H', data, pe_off + 20)[0]
    sec_off = pe_off + 24 + opt_size

    def rva_to_offset(rva):
        for i in range(num_sections):
            off = sec_off + i * 40
            vaddr = struct.unpack_from('<I', data, off + 12)[0]
            vsize = struct.unpack_from('<I', data, off + 16)[0]
            raw   = struct.unpack_from('<I', data, off + 20)[0]
            if vaddr <= rva < vaddr + vsize:
                return raw + (rva - vaddr)
        return None

    exp_off = rva_to_offset(export_rva)
    if exp_off is None:
        return []

    num_names = struct.unpack_from('<I', data, exp_off + 24)[0]
    names_rva  = struct.unpack_from('<I', data, exp_off + 32)[0]
    names_off  = rva_to_offset(names_rva)

    exports = []
    for i in range(num_names):
        name_rva = struct.unpack_from('<I', data, names_off + i*4)[0]
        name_off = rva_to_offset(name_rva)
        end = data.index(b'\x00', name_off)
        exports.append(data[name_off:end].decode('ascii', errors='replace'))
    return sorted(exports)

dll = r"C:\ProgramData\Facom\ScanDiag\Bin\LaserDisk_COM.dll"
names = read_exports(dll)
print(f"{len(names)} exports dans {Path(dll).name} :\n")
for n in names:
    print(" ", n)
