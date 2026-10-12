
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

00000000000681f0 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)>:
   681f0:	a9bb7bfd 	stp	x29, x30, [sp, #-80]!
   681f4:	910003fd 	mov	x29, sp
   681f8:	a90153f3 	stp	x19, x20, [sp, #16]
   681fc:	f0000353 	adrp	x19, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   68200:	aa0003f4 	mov	x20, x0
   68204:	f9451662 	ldr	x2, [x19, #2600]
   68208:	f90013f5 	str	x21, [sp, #32]
   6820c:	aa0103f5 	mov	x21, x1
   68210:	f9400041 	ldr	x1, [x2]
   68214:	f90027e1 	str	x1, [sp, #72]
   68218:	d2800001 	mov	x1, #0x0                   	// #0
   6821c:	97ff31cd 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   68220:	91004000 	add	x0, x0, #0x10
   68224:	97ff2bdb 	bl	33190 <icraft::xir::DataType::bytes() const@plt>
   68228:	aa0003e1 	mov	x1, x0
   6822c:	d2800023 	mov	x3, #0x1                   	// #1
   68230:	aa1503e0 	mov	x0, x21
   68234:	2a0303e2 	mov	w2, w3
   68238:	9100e3e8 	add	x8, sp, #0x38
   6823c:	97ff2b45 	bl	32f50 <icraft::xrt::MemRegion::malloc(unsigned long, bool, unsigned long) const@plt>
   68240:	f9400281 	ldr	x1, [x20]
   68244:	f9401fe3 	ldr	x3, [sp, #56]
   68248:	f9001fff 	str	xzr, [sp, #56]
   6824c:	f9401020 	ldr	x0, [x1, #32]
   68250:	f9001023 	str	x3, [x1, #32]
   68254:	394103e2 	ldrb	w2, [sp, #64]
   68258:	f100001f 	cmp	x0, #0x0
   6825c:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   68260:	54000180 	b.eq	68290 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0xa0>  // b.none
   68264:	f9451673 	ldr	x19, [x19, #2600]
   68268:	f94027e0 	ldr	x0, [sp, #72]
   6826c:	f9400261 	ldr	x1, [x19]
   68270:	eb010000 	subs	x0, x0, x1
   68274:	d2800001 	mov	x1, #0x0                   	// #0
   68278:	540003c1 	b.ne	682f0 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0x100>  // b.any
   6827c:	aa1403e0 	mov	x0, x20
   68280:	a94153f3 	ldp	x19, x20, [sp, #16]
   68284:	f94013f5 	ldr	x21, [sp, #32]
   68288:	a8c57bfd 	ldp	x29, x30, [sp], #80
   6828c:	d65f03c0 	ret
   68290:	91002001 	add	x1, x0, #0x8
   68294:	885ffc22 	ldaxr	w2, [x1]
   68298:	51000442 	sub	w2, w2, #0x1
   6829c:	8803fc22 	stlxr	w3, w2, [x1]
   682a0:	35ffffa3 	cbnz	w3, 68294 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0xa4>
   682a4:	340001e2 	cbz	w2, 682e0 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0xf0>
   682a8:	f9401fe0 	ldr	x0, [sp, #56]
   682ac:	b4fffdc0 	cbz	x0, 68264 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0x74>
   682b0:	394103e1 	ldrb	w1, [sp, #64]
   682b4:	35fffd81 	cbnz	w1, 68264 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0x74>
   682b8:	91002001 	add	x1, x0, #0x8
   682bc:	885ffc22 	ldaxr	w2, [x1]
   682c0:	51000442 	sub	w2, w2, #0x1
   682c4:	8803fc22 	stlxr	w3, w2, [x1]
   682c8:	35ffffa3 	cbnz	w3, 682bc <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0xcc>
   682cc:	35fffcc2 	cbnz	w2, 68264 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0x74>
   682d0:	f9400001 	ldr	x1, [x0]
   682d4:	f9400821 	ldr	x1, [x1, #16]
   682d8:	d63f0020 	blr	x1
   682dc:	17ffffe2 	b	68264 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0x74>
   682e0:	f9400001 	ldr	x1, [x0]
   682e4:	f9400821 	ldr	x1, [x1, #16]
   682e8:	d63f0020 	blr	x1
   682ec:	17ffffef 	b	682a8 <icraft::xrt::Tensor::mallocOn(icraft::xrt::MemRegion const&)+0xb8>
   682f0:	97ff2934 	bl	327c0 <__stack_chk_fail@plt>
   682f4:	d503201f 	nop
