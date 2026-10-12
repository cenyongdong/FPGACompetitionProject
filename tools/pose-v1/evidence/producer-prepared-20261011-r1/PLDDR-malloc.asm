
/usr/lib/aarch64-linux-gnu/libaxizg330aiu.so:     file format elf64-littleaarch64


Disassembly of section .text:

000000000002b2c8 <AXIZG330AIPLDDRMemRegionNode::malloc(unsigned long, bool, unsigned long) const>:
   2b2c8:	a9bd7bfd 	stp	x29, x30, [sp, #-48]!
   2b2cc:	91006000 	add	x0, x0, #0x18
   2b2d0:	910003fd 	mov	x29, sp
   2b2d4:	a90153f3 	stp	x19, x20, [sp, #16]
   2b2d8:	b0000253 	adrp	x19, 74000 <spdlog::details::elapsed_formatter<spdlog::details::scoped_padder, std::chrono::duration<long, std::ratio<1l, 1l> > >::format(spdlog::details::log_msg const&, tm const&, fmt::v8::basic_memory_buffer<char, 250ul, std::allocator<char> >&)@@Base+0x3dda8>
   2b2dc:	aa0803f4 	mov	x20, x8
   2b2e0:	f9454e73 	ldr	x19, [x19, #2712]
   2b2e4:	f9400264 	ldr	x4, [x19]
   2b2e8:	f90017e4 	str	x4, [sp, #40]
   2b2ec:	d2800004 	mov	x4, #0x0                   	// #0
   2b2f0:	97fff09c 	bl	27560 <icraft::xrt::MemManager::malloc(unsigned long, bool, unsigned long)@plt>
   2b2f4:	f94017e0 	ldr	x0, [sp, #40]
   2b2f8:	f9400261 	ldr	x1, [x19]
   2b2fc:	eb010000 	subs	x0, x0, x1
   2b300:	d2800001 	mov	x1, #0x0                   	// #0
   2b304:	540000a1 	b.ne	2b318 <AXIZG330AIPLDDRMemRegionNode::malloc(unsigned long, bool, unsigned long) const+0x50>  // b.any
   2b308:	aa1403e0 	mov	x0, x20
   2b30c:	a94153f3 	ldp	x19, x20, [sp, #16]
   2b310:	a8c37bfd 	ldp	x29, x30, [sp], #48
   2b314:	d65f03c0 	ret
   2b318:	97fff046 	bl	27430 <__stack_chk_fail@plt>
   2b31c:	d503201f 	nop
