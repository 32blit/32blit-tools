import pathlib
import struct

from elftools.elf.elffile import ELFFile
from elftools.elf.enums import ENUM_RELOC_TYPE_ARM

from ..core.tool import Tool


class Relocs(Tool):
    command = 'relocs'
    help = 'Prepend relocations to a game binary'

    def __init__(self, parser):
        Tool.__init__(self, parser)

        self.parser.add_argument('--bin-file', type=pathlib.Path, help='Input .bin', required=True)
        self.parser.add_argument('--elf-file', type=pathlib.Path, help='Input .elf', required=True)
        self.parser.add_argument('--output', type=pathlib.Path, help='Output file', required=True)

    def run(self, args):
        with open(args.elf_file, 'rb') as f:
            elffile = ELFFile(f)

            # get addresses of GOT values that need patched
            got_offsets = self.get_flash_addr_offsets(elffile.get_section_by_name('.got'))

            # and the init/fini arrays
            init_offsets = self.get_flash_addr_offsets(elffile.get_section_by_name('.init_array'))
            fini_offsets = self.get_flash_addr_offsets(elffile.get_section_by_name('.fini_array'))

            reloc_offsets = []

            # find sidata/sdata
            sidata = 0
            sdata = 0
            relocs = elffile.get_section_by_name('.rel.text')
            symtable = elffile.get_section(relocs['sh_link'])
            for reloc in relocs.iter_relocations():
                symbol = symtable.get_symbol(reloc['r_info_sym'])
                if symbol.name == '_sidata':
                    sidata = symbol['st_value']
                elif symbol.name == '_sdata':
                    sdata = symbol['st_value']

                if sidata and sdata:
                    break

            assert(sidata != 0 and sdata != 0)

            # get all .data relocations
            relocs = elffile.get_section_by_name('.rel.data')
            symtable = elffile.get_section(relocs['sh_link'])

            for reloc in relocs.iter_relocations():
                symbol = symtable.get_symbol(reloc['r_info_sym'])

                if reloc['r_info_type'] != ENUM_RELOC_TYPE_ARM['R_ARM_ABS32']:
                    continue

                # doesn't point to flash
                if symbol['st_value'] < 0x90000000:
                    continue

                # map RAM address back to flash
                flash_offset = (reloc['r_offset'] - sdata) + sidata

                assert((flash_offset & 3) == 0)

                reloc_offsets.append(flash_offset)

            with open(args.output, 'wb') as out_f:
                all_offsets = got_offsets + init_offsets + fini_offsets + reloc_offsets
                all_offsets.sort()

                out_f.write(b"RELO")
                out_f.write(struct.pack("<L", len(all_offsets)))
                for off in all_offsets:
                    out_f.write(struct.pack("<L", off))

                out_f.write(open(args.bin_file, 'rb').read())

    def get_flash_addr_offsets(self, section):
        section_data = section.data()
        section_addrs = struct.unpack(f'<{len(section_data) // 4}I', section_data)
        section_offsets = []

        for i, addr in enumerate(section_addrs):
            # filter out non-flash
            if addr < 0x90000000:
                continue

            # offset to this address in the section
            section_offsets.append(section['sh_addr'] + i * 4)

        return section_offsets
