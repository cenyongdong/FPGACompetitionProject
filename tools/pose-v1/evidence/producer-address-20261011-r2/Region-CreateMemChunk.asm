
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000036ef0 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)>:
   36ef0:	a9b77bfd 	stp	x29, x30, [sp, #-144]!
   36ef4:	910003fd 	mov	x29, sp
   36ef8:	a90153f3 	stp	x19, x20, [sp, #16]
   36efc:	b00004f4 	adrp	x20, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   36f00:	aa0303f3 	mov	x19, x3
   36f04:	f9451686 	ldr	x6, [x20, #2600]
   36f08:	a9025bf5 	stp	x21, x22, [sp, #32]
   36f0c:	aa0803f5 	mov	x21, x8
   36f10:	f9400005 	ldr	x5, [x0]
   36f14:	f94000c7 	ldr	x7, [x6]
   36f18:	f90047e7 	str	x7, [sp, #136]
   36f1c:	d2800007 	mov	x7, #0x0                   	// #0
   36f20:	39402000 	ldrb	w0, [x0, #8]
   36f24:	aa0103f6 	mov	x22, x1
   36f28:	a90363f7 	stp	x23, x24, [sp, #48]
   36f2c:	f10000bf 	cmp	x5, #0x0
   36f30:	12001c97 	and	w23, w4, #0xff
   36f34:	f90023e5 	str	x5, [sp, #64]
   36f38:	7a401800 	ccmp	w0, #0x0, #0x0, ne  // ne = any
   36f3c:	390123e0 	strb	w0, [sp, #72]
   36f40:	540009a0 	b.eq	37074 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x184>  // b.none
   36f44:	f9400040 	ldr	x0, [x2]
   36f48:	f9002be0 	str	x0, [sp, #80]
   36f4c:	39402041 	ldrb	w1, [x2, #8]
   36f50:	390163e1 	strb	w1, [sp, #88]
   36f54:	f100001f 	cmp	x0, #0x0
   36f58:	7a401820 	ccmp	w1, #0x0, #0x0, ne  // ne = any
   36f5c:	54000800 	b.eq	3705c <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x16c>  // b.none
   36f60:	f9400a63 	ldr	x3, [x19, #16]
   36f64:	f9003bff 	str	xzr, [sp, #112]
   36f68:	910183f8 	add	x24, sp, #0x60
   36f6c:	b40000e3 	cbz	x3, 36f88 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x98>
   36f70:	aa1803e0 	mov	x0, x24
   36f74:	aa1303e1 	mov	x1, x19
   36f78:	52800042 	mov	w2, #0x2                   	// #2
   36f7c:	d63f0060 	blr	x3
   36f80:	3dc00660 	ldr	q0, [x19, #16]
   36f84:	3d801fe0 	str	q0, [sp, #112]
   36f88:	2a1703e5 	mov	w5, w23
   36f8c:	aa1603e2 	mov	x2, x22
   36f90:	aa1803e4 	mov	x4, x24
   36f94:	910143e3 	add	x3, sp, #0x50
   36f98:	910103e1 	add	x1, sp, #0x40
   36f9c:	aa1503e0 	mov	x0, x21
   36fa0:	97ffed40 	bl	324a0 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)@plt>
   36fa4:	f9403be3 	ldr	x3, [sp, #112]
   36fa8:	b40000a3 	cbz	x3, 36fbc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xcc>
   36fac:	aa1803e1 	mov	x1, x24
   36fb0:	aa1803e0 	mov	x0, x24
   36fb4:	52800062 	mov	w2, #0x3                   	// #3
   36fb8:	d63f0060 	blr	x3
   36fbc:	f9402be0 	ldr	x0, [sp, #80]
   36fc0:	b4000060 	cbz	x0, 36fcc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xdc>
   36fc4:	394163e1 	ldrb	w1, [sp, #88]
   36fc8:	34000361 	cbz	w1, 37034 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x144>
   36fcc:	f94023e0 	ldr	x0, [sp, #64]
   36fd0:	b4000060 	cbz	x0, 36fdc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xec>
   36fd4:	394123e1 	ldrb	w1, [sp, #72]
   36fd8:	340001a1 	cbz	w1, 3700c <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x11c>
   36fdc:	f9451694 	ldr	x20, [x20, #2600]
   36fe0:	f94047e0 	ldr	x0, [sp, #136]
   36fe4:	f9400281 	ldr	x1, [x20]
   36fe8:	eb010000 	subs	x0, x0, x1
   36fec:	d2800001 	mov	x1, #0x0                   	// #0
   36ff0:	540004e1 	b.ne	3708c <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x19c>  // b.any
   36ff4:	aa1503e0 	mov	x0, x21
   36ff8:	a94153f3 	ldp	x19, x20, [sp, #16]
   36ffc:	a9425bf5 	ldp	x21, x22, [sp, #32]
   37000:	a94363f7 	ldp	x23, x24, [sp, #48]
   37004:	a8c97bfd 	ldp	x29, x30, [sp], #144
   37008:	d65f03c0 	ret
   3700c:	91002001 	add	x1, x0, #0x8
   37010:	885ffc22 	ldaxr	w2, [x1]
   37014:	51000442 	sub	w2, w2, #0x1
   37018:	8803fc22 	stlxr	w3, w2, [x1]
   3701c:	35ffffa3 	cbnz	w3, 37010 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x120>
   37020:	35fffde2 	cbnz	w2, 36fdc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xec>
   37024:	f9400001 	ldr	x1, [x0]
   37028:	f9400821 	ldr	x1, [x1, #16]
   3702c:	d63f0020 	blr	x1
   37030:	17ffffeb 	b	36fdc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xec>
   37034:	91002001 	add	x1, x0, #0x8
   37038:	885ffc22 	ldaxr	w2, [x1]
   3703c:	51000442 	sub	w2, w2, #0x1
   37040:	8803fc22 	stlxr	w3, w2, [x1]
   37044:	35ffffa3 	cbnz	w3, 37038 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x148>
   37048:	35fffc22 	cbnz	w2, 36fcc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xdc>
   3704c:	f9400001 	ldr	x1, [x0]
   37050:	f9400821 	ldr	x1, [x1, #16]
   37054:	d63f0020 	blr	x1
   37058:	17ffffdd 	b	36fcc <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xdc>
   3705c:	91002000 	add	x0, x0, #0x8
   37060:	885ffc01 	ldaxr	w1, [x0]
   37064:	11000421 	add	w1, w1, #0x1
   37068:	8802fc01 	stlxr	w2, w1, [x0]
   3706c:	35ffffa2 	cbnz	w2, 37060 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x170>
   37070:	17ffffbc 	b	36f60 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x70>
   37074:	910020a5 	add	x5, x5, #0x8
   37078:	885ffca0 	ldaxr	w0, [x5]
   3707c:	11000400 	add	w0, w0, #0x1
   37080:	8801fca0 	stlxr	w1, w0, [x5]
   37084:	35ffffa1 	cbnz	w1, 37078 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x188>
   37088:	17ffffaf 	b	36f44 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x54>
   3708c:	97ffedcd 	bl	327c0 <__stack_chk_fail@plt>
   37090:	f9403be3 	ldr	x3, [sp, #112]
   37094:	aa0003f3 	mov	x19, x0
   37098:	b40000a3 	cbz	x3, 370ac <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1bc>
   3709c:	aa1803e1 	mov	x1, x24
   370a0:	aa1803e0 	mov	x0, x24
   370a4:	52800062 	mov	w2, #0x3                   	// #3
   370a8:	d63f0060 	blr	x3
   370ac:	f9402be0 	ldr	x0, [sp, #80]
   370b0:	b4000080 	cbz	x0, 370c0 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1d0>
   370b4:	394163e1 	ldrb	w1, [sp, #88]
   370b8:	35000041 	cbnz	w1, 370c0 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1d0>
   370bc:	97ffef19 	bl	32d20 <icraft::xir::Object::decref()@plt>
   370c0:	f94023e0 	ldr	x0, [sp, #64]
   370c4:	b4000080 	cbz	x0, 370d4 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1e4>
   370c8:	394123e1 	ldrb	w1, [sp, #72]
   370cc:	35000041 	cbnz	w1, 370d4 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1e4>
   370d0:	97ffef14 	bl	32d20 <icraft::xir::Object::decref()@plt>
   370d4:	aa1303e0 	mov	x0, x19
   370d8:	97fff59a 	bl	34740 <_Unwind_Resume@plt>
   370dc:	f9403be3 	ldr	x3, [sp, #112]
   370e0:	aa0003f3 	mov	x19, x0
   370e4:	b4fffe43 	cbz	x3, 370ac <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1bc>
   370e8:	aa1803e1 	mov	x1, x24
   370ec:	aa1803e0 	mov	x0, x24
   370f0:	52800062 	mov	w2, #0x3                   	// #3
   370f4:	d63f0060 	blr	x3
   370f8:	17ffffed 	b	370ac <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1bc>
   370fc:	d503201f 	nop

0000000000037100 <icraft::xrt::MemChunk::free()>:
   37100:	f9400000 	ldr	x0, [x0]
   37104:	17ffeeb7 	b	32be0 <icraft::xrt::MemChunkNode::free()@plt>

0000000000037108 <icraft::xrt::MemChunk::isOn(icraft::xrt::MemRegion const&) const>:
   37108:	a9be7bfd 	stp	x29, x30, [sp, #-32]!
   3710c:	910003fd 	mov	x29, sp
   37110:	f9000bf3 	str	x19, [sp, #16]
   37114:	aa0103f3 	mov	x19, x1
   37118:	97fff60e 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3711c:	9100a000 	add	x0, x0, #0x28
   37120:	aa1303e1 	mov	x1, x19
   37124:	f9400bf3 	ldr	x19, [sp, #16]
   37128:	a8c27bfd 	ldp	x29, x30, [sp], #32
   3712c:	17fff6a9 	b	34bd0 <icraft::xir::ObjectRef::same_as(icraft::xir::ObjectRef const&) const@plt>

0000000000037130 <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const>:
   37130:	a9ba7bfd 	stp	x29, x30, [sp, #-96]!
   37134:	910003fd 	mov	x29, sp
   37138:	a9025bf5 	stp	x21, x22, [sp, #32]
   3713c:	900004f5 	adrp	x21, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   37140:	f94516a2 	ldr	x2, [x21, #2600]
   37144:	a90153f3 	stp	x19, x20, [sp, #16]
   37148:	f9400823 	ldr	x3, [x1, #16]
   3714c:	f9400044 	ldr	x4, [x2]
   37150:	f9002fe4 	str	x4, [sp, #88]
   37154:	d2800004 	mov	x4, #0x0                   	// #0
   37158:	f90023ff 	str	xzr, [sp, #64]
   3715c:	f9400013 	ldr	x19, [x0]
   37160:	b40003a3 	cbz	x3, 371d4 <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const+0xa4>
   37164:	9100c3f6 	add	x22, sp, #0x30
   37168:	aa0103f4 	mov	x20, x1
   3716c:	aa1603e0 	mov	x0, x22
   37170:	52800042 	mov	w2, #0x2                   	// #2
   37174:	d63f0060 	blr	x3
   37178:	a9410283 	ldp	x3, x0, [x20, #16]
   3717c:	a9448664 	ldp	x4, x1, [x19, #72]
   37180:	a9048263 	stp	x3, x0, [x19, #72]
   37184:	a9431fe6 	ldp	x6, x7, [sp, #48]
   37188:	a90407e4 	stp	x4, x1, [sp, #64]
   3718c:	a9438e62 	ldp	x2, x3, [x19, #56]
   37190:	a9030fe2 	stp	x2, x3, [sp, #48]
   37194:	a9039e66 	stp	x6, x7, [x19, #56]
   37198:	b40000a4 	cbz	x4, 371ac <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const+0x7c>
   3719c:	9100c3e1 	add	x1, sp, #0x30
   371a0:	52800062 	mov	w2, #0x3                   	// #3
   371a4:	aa0103e0 	mov	x0, x1
   371a8:	d63f0080 	blr	x4
   371ac:	f94516b5 	ldr	x21, [x21, #2600]
   371b0:	f9402fe0 	ldr	x0, [sp, #88]
   371b4:	f94002a1 	ldr	x1, [x21]
   371b8:	eb010000 	subs	x0, x0, x1
   371bc:	d2800001 	mov	x1, #0x0                   	// #0
   371c0:	540000e1 	b.ne	371dc <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const+0xac>  // b.any
   371c4:	a94153f3 	ldp	x19, x20, [sp, #16]
   371c8:	a9425bf5 	ldp	x21, x22, [sp, #32]
   371cc:	a8c67bfd 	ldp	x29, x30, [sp], #96
   371d0:	d65f03c0 	ret
   371d4:	f94027e0 	ldr	x0, [sp, #72]
   371d8:	17ffffe9 	b	3717c <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const+0x4c>
   371dc:	97ffed79 	bl	327c0 <__stack_chk_fail@plt>
   371e0:	f94023e3 	ldr	x3, [sp, #64]
   371e4:	aa0003f3 	mov	x19, x0
   371e8:	b40000a3 	cbz	x3, 371fc <icraft::xrt::MemChunk::setDeleter(std::function<void (icraft::xrt::MemPtr const&)>) const+0xcc>
   371ec:	aa1603e1 	mov	x1, x22
   371f0:	aa1603e0 	mov	x0, x22
   371f4:	52800062 	mov	w2, #0x3                   	// #3
   371f8:	d63f0060 	blr	x3
   371fc:	aa1303e0 	mov	x0, x19
   37200:	97fff550 	bl	34740 <_Unwind_Resume@plt>
   37204:	d503201f 	nop

0000000000037208 <icraft::xrt::MemChunk::setAutoFree(bool) const>:
   37208:	f9400000 	ldr	x0, [x0]
   3720c:	39016001 	strb	w1, [x0, #88]
   37210:	d65f03c0 	ret
   37214:	d503201f 	nop

0000000000037218 <icraft::xrt::RegRegion::init()>:
   37218:	f9400000 	ldr	x0, [x0]
   3721c:	f9400001 	ldr	x1, [x0]
   37220:	f9401821 	ldr	x1, [x1, #48]
   37224:	aa0103f0 	mov	x16, x1
   37228:	d61f0200 	br	x16
   3722c:	d503201f 	nop

0000000000037230 <icraft::xrt::RegRegion::deinit()>:
   37230:	f9400000 	ldr	x0, [x0]
   37234:	f9400001 	ldr	x1, [x0]
   37238:	f9401c21 	ldr	x1, [x1, #56]
   3723c:	aa0103f0 	mov	x16, x1
   37240:	d61f0200 	br	x16
   37244:	d503201f 	nop

0000000000037248 <icraft::xrt::RegRegion::read(unsigned long, bool) const>:
   37248:	a9be7bfd 	stp	x29, x30, [sp, #-32]!
   3724c:	910003fd 	mov	x29, sp
   37250:	a90153f3 	stp	x19, x20, [sp, #16]
   37254:	12001c54 	and	w20, w2, #0xff
   37258:	aa0103f3 	mov	x19, x1
   3725c:	97fff5bd 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   37260:	f9400003 	ldr	x3, [x0]
   37264:	aa1303e1 	mov	x1, x19
   37268:	2a1403e2 	mov	w2, w20
   3726c:	a94153f3 	ldp	x19, x20, [sp, #16]
   37270:	a8c27bfd 	ldp	x29, x30, [sp], #32
   37274:	f9402063 	ldr	x3, [x3, #64]
   37278:	aa0303f0 	mov	x16, x3
   3727c:	d61f0200 	br	x16

0000000000037280 <icraft::xrt::RegRegion::write(unsigned long, unsigned long, bool) const>:
   37280:	a9bd7bfd 	stp	x29, x30, [sp, #-48]!
   37284:	910003fd 	mov	x29, sp
   37288:	a90153f3 	stp	x19, x20, [sp, #16]
   3728c:	aa0103f3 	mov	x19, x1
   37290:	aa0203f4 	mov	x20, x2
   37294:	f90013f5 	str	x21, [sp, #32]
   37298:	12001c75 	and	w21, w3, #0xff
   3729c:	97fff5ad 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   372a0:	f9400004 	ldr	x4, [x0]
   372a4:	aa1403e2 	mov	x2, x20
   372a8:	aa1303e1 	mov	x1, x19
   372ac:	2a1503e3 	mov	w3, w21
   372b0:	a94153f3 	ldp	x19, x20, [sp, #16]
   372b4:	f94013f5 	ldr	x21, [sp, #32]
   372b8:	a8c37bfd 	ldp	x29, x30, [sp], #48
   372bc:	f9402484 	ldr	x4, [x4, #72]
   372c0:	aa0403f0 	mov	x16, x4
   372c4:	d61f0200 	br	x16

00000000000372c8 <icraft::xrt::RegRegion::device() const>:
   372c8:	a9be7bfd 	stp	x29, x30, [sp, #-32]!
   372cc:	910003fd 	mov	x29, sp
   372d0:	f9000bf3 	str	x19, [sp, #16]
   372d4:	aa0803f3 	mov	x19, x8
   372d8:	97fff59e 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   372dc:	f9400801 	ldr	x1, [x0, #16]
   372e0:	b40000c1 	cbz	x1, 372f8 <icraft::xrt::RegRegion::device() const+0x30>
   372e4:	91002020 	add	x0, x1, #0x8
   372e8:	885ffc02 	ldaxr	w2, [x0]
   372ec:	11000442 	add	w2, w2, #0x1
   372f0:	8803fc02 	stlxr	w3, w2, [x0]
   372f4:	35ffffa3 	cbnz	w3, 372e8 <icraft::xrt::RegRegion::device() const+0x20>
   372f8:	f9000261 	str	x1, [x19]
   372fc:	aa1303e0 	mov	x0, x19
   37300:	3900227f 	strb	wzr, [x19, #8]
   37304:	f9400bf3 	ldr	x19, [sp, #16]
   37308:	a8c27bfd 	ldp	x29, x30, [sp], #32
   3730c:	d65f03c0 	ret

0000000000037310 <icraft::xrt::RegRegion::_bindDevice(icraft::xrt::DeviceNode const*)>:
   37310:	f9400002 	ldr	x2, [x0]
   37314:	f9000841 	str	x1, [x2, #16]
   37318:	d65f03c0 	ret
   3731c:	d503201f 	nop

0000000000037320 <icraft::xrt::Device::defaultMemRegion() const>:
   37320:	a9bf7bfd 	stp	x29, x30, [sp, #-16]!
   37324:	910003fd 	mov	x29, sp
   37328:	97fff58a 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3732c:	91020000 	add	x0, x0, #0x80
   37330:	a8c17bfd 	ldp	x29, x30, [sp], #16
   37334:	d65f03c0 	ret

0000000000037338 <icraft::xrt::Device::malloc(unsigned long) const>:
   37338:	a9bc7bfd 	stp	x29, x30, [sp, #-64]!
   3733c:	910003fd 	mov	x29, sp
