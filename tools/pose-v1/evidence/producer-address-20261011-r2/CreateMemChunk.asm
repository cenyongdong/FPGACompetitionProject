
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

00000000000379d0 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const>:
   379d0:	a9b77bfd 	stp	x29, x30, [sp, #-144]!
   379d4:	910003fd 	mov	x29, sp
   379d8:	a90153f3 	stp	x19, x20, [sp, #16]
   379dc:	900004f4 	adrp	x20, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   379e0:	f9451685 	ldr	x5, [x20, #2600]
   379e4:	a9025bf5 	stp	x21, x22, [sp, #32]
   379e8:	aa0803f5 	mov	x21, x8
   379ec:	f9400813 	ldr	x19, [x0, #16]
   379f0:	f94000a0 	ldr	x0, [x5]
   379f4:	f90047e0 	str	x0, [sp, #136]
   379f8:	d2800000 	mov	x0, #0x0                   	// #0
   379fc:	a90363f7 	stp	x23, x24, [sp, #48]
   37a00:	aa0103e0 	mov	x0, x1
   37a04:	aa0203f6 	mov	x22, x2
   37a08:	12001c98 	and	w24, w4, #0xff
   37a0c:	aa0303e1 	mov	x1, x3
   37a10:	b4000ad3 	cbz	x19, 37b68 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x198>
   37a14:	91002262 	add	x2, x19, #0x8
   37a18:	885ffc43 	ldaxr	w3, [x2]
   37a1c:	11000463 	add	w3, w3, #0x1
   37a20:	8804fc43 	stlxr	w4, w3, [x2]
   37a24:	35ffffa4 	cbnz	w4, 37a18 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x48>
   37a28:	f9400003 	ldr	x3, [x0]
   37a2c:	f90027e3 	str	x3, [sp, #72]
   37a30:	39402000 	ldrb	w0, [x0, #8]
   37a34:	390143e0 	strb	w0, [sp, #80]
   37a38:	b4000043 	cbz	x3, 37a40 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x70>
   37a3c:	34000a80 	cbz	w0, 37b8c <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1bc>
   37a40:	f9002ff3 	str	x19, [sp, #88]
   37a44:	390183ff 	strb	wzr, [sp, #96]
   37a48:	885ffc40 	ldaxr	w0, [x2]
   37a4c:	11000400 	add	w0, w0, #0x1
   37a50:	8803fc40 	stlxr	w3, w0, [x2]
   37a54:	35ffffa3 	cbnz	w3, 37a48 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x78>
   37a58:	9101a3f7 	add	x23, sp, #0x68
   37a5c:	aa1703e0 	mov	x0, x23
   37a60:	97fff274 	bl	34430 <std::function<void (icraft::xrt::MemPtr const&)>::function(std::function<void (icraft::xrt::MemPtr const&)> const&)@plt>
   37a64:	aa1503e8 	mov	x8, x21
   37a68:	2a1803e4 	mov	w4, w24
   37a6c:	aa1703e3 	mov	x3, x23
   37a70:	aa1603e1 	mov	x1, x22
   37a74:	910163e2 	add	x2, sp, #0x58
   37a78:	910123e0 	add	x0, sp, #0x48
   37a7c:	97ffeff5 	bl	33a50 <icraft::xrt::MemRegionNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)@plt>
   37a80:	f9403fe3 	ldr	x3, [sp, #120]
   37a84:	b40000a3 	cbz	x3, 37a98 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xc8>
   37a88:	aa1703e1 	mov	x1, x23
   37a8c:	aa1703e0 	mov	x0, x23
   37a90:	52800062 	mov	w2, #0x3                   	// #3
   37a94:	d63f0060 	blr	x3
   37a98:	f9402fe0 	ldr	x0, [sp, #88]
   37a9c:	b4000060 	cbz	x0, 37aa8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xd8>
   37aa0:	394183e1 	ldrb	w1, [sp, #96]
   37aa4:	340004e1 	cbz	w1, 37b40 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x170>
   37aa8:	f94027e0 	ldr	x0, [sp, #72]
   37aac:	b4000060 	cbz	x0, 37ab8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xe8>
   37ab0:	394143e1 	ldrb	w1, [sp, #80]
   37ab4:	34000321 	cbz	w1, 37b18 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x148>
   37ab8:	b40000f3 	cbz	x19, 37ad4 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x104>
   37abc:	91002260 	add	x0, x19, #0x8
   37ac0:	885ffc01 	ldaxr	w1, [x0]
   37ac4:	51000421 	sub	w1, w1, #0x1
   37ac8:	8802fc01 	stlxr	w2, w1, [x0]
   37acc:	35ffffa2 	cbnz	w2, 37ac0 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xf0>
   37ad0:	340001a1 	cbz	w1, 37b04 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x134>
   37ad4:	f9451694 	ldr	x20, [x20, #2600]
   37ad8:	f94047e0 	ldr	x0, [sp, #136]
   37adc:	f9400281 	ldr	x1, [x20]
   37ae0:	eb010000 	subs	x0, x0, x1
   37ae4:	d2800001 	mov	x1, #0x0                   	// #0
   37ae8:	540006a1 	b.ne	37bbc <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1ec>  // b.any
   37aec:	aa1503e0 	mov	x0, x21
   37af0:	a94153f3 	ldp	x19, x20, [sp, #16]
   37af4:	a9425bf5 	ldp	x21, x22, [sp, #32]
   37af8:	a94363f7 	ldp	x23, x24, [sp, #48]
   37afc:	a8c97bfd 	ldp	x29, x30, [sp], #144
   37b00:	d65f03c0 	ret
   37b04:	f9400261 	ldr	x1, [x19]
   37b08:	aa1303e0 	mov	x0, x19
   37b0c:	f9400821 	ldr	x1, [x1, #16]
   37b10:	d63f0020 	blr	x1
   37b14:	17fffff0 	b	37ad4 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x104>
   37b18:	91002001 	add	x1, x0, #0x8
   37b1c:	885ffc22 	ldaxr	w2, [x1]
   37b20:	51000442 	sub	w2, w2, #0x1
   37b24:	8803fc22 	stlxr	w3, w2, [x1]
   37b28:	35ffffa3 	cbnz	w3, 37b1c <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x14c>
   37b2c:	35fffc62 	cbnz	w2, 37ab8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xe8>
   37b30:	f9400001 	ldr	x1, [x0]
   37b34:	f9400821 	ldr	x1, [x1, #16]
   37b38:	d63f0020 	blr	x1
   37b3c:	17ffffdf 	b	37ab8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xe8>
   37b40:	91002001 	add	x1, x0, #0x8
   37b44:	885ffc22 	ldaxr	w2, [x1]
   37b48:	51000442 	sub	w2, w2, #0x1
   37b4c:	8803fc22 	stlxr	w3, w2, [x1]
   37b50:	35ffffa3 	cbnz	w3, 37b44 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x174>
   37b54:	35fffaa2 	cbnz	w2, 37aa8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xd8>
   37b58:	f9400001 	ldr	x1, [x0]
   37b5c:	f9400821 	ldr	x1, [x1, #16]
   37b60:	d63f0020 	blr	x1
   37b64:	17ffffd1 	b	37aa8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0xd8>
   37b68:	f9400002 	ldr	x2, [x0]
   37b6c:	f90027e2 	str	x2, [sp, #72]
   37b70:	39402000 	ldrb	w0, [x0, #8]
   37b74:	390143e0 	strb	w0, [sp, #80]
   37b78:	b4000042 	cbz	x2, 37b80 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1b0>
   37b7c:	34000140 	cbz	w0, 37ba4 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1d4>
   37b80:	f9002fff 	str	xzr, [sp, #88]
   37b84:	390183ff 	strb	wzr, [sp, #96]
   37b88:	17ffffb4 	b	37a58 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x88>
   37b8c:	91002063 	add	x3, x3, #0x8
   37b90:	885ffc60 	ldaxr	w0, [x3]
   37b94:	11000400 	add	w0, w0, #0x1
   37b98:	8804fc60 	stlxr	w4, w0, [x3]
   37b9c:	35ffffa4 	cbnz	w4, 37b90 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1c0>
   37ba0:	17ffffa8 	b	37a40 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x70>
   37ba4:	91002042 	add	x2, x2, #0x8
   37ba8:	885ffc40 	ldaxr	w0, [x2]
   37bac:	11000400 	add	w0, w0, #0x1
   37bb0:	8803fc40 	stlxr	w3, w0, [x2]
   37bb4:	35ffffa3 	cbnz	w3, 37ba8 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1d8>
   37bb8:	17fffff2 	b	37b80 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x1b0>
   37bbc:	97ffeb01 	bl	327c0 <__stack_chk_fail@plt>
   37bc0:	f9403fe3 	ldr	x3, [sp, #120]
   37bc4:	aa0003f4 	mov	x20, x0
   37bc8:	b40000a3 	cbz	x3, 37bdc <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x20c>
   37bcc:	aa1703e1 	mov	x1, x23
   37bd0:	aa1703e0 	mov	x0, x23
   37bd4:	52800062 	mov	w2, #0x3                   	// #3
   37bd8:	d63f0060 	blr	x3
   37bdc:	f9402fe0 	ldr	x0, [sp, #88]
   37be0:	b4000080 	cbz	x0, 37bf0 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x220>
   37be4:	394183e1 	ldrb	w1, [sp, #96]
   37be8:	35000041 	cbnz	w1, 37bf0 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x220>
   37bec:	97ffec4d 	bl	32d20 <icraft::xir::Object::decref()@plt>
   37bf0:	f94027e0 	ldr	x0, [sp, #72]
   37bf4:	b4000080 	cbz	x0, 37c04 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x234>
   37bf8:	394143e1 	ldrb	w1, [sp, #80]
   37bfc:	35000041 	cbnz	w1, 37c04 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x234>
   37c00:	97ffec48 	bl	32d20 <icraft::xir::Object::decref()@plt>
   37c04:	b4000073 	cbz	x19, 37c10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x240>
   37c08:	aa1303e0 	mov	x0, x19
   37c0c:	97ffec45 	bl	32d20 <icraft::xir::Object::decref()@plt>
   37c10:	aa1403e0 	mov	x0, x20
   37c14:	97fff2cb 	bl	34740 <_Unwind_Resume@plt>
   37c18:	aa0003f4 	mov	x20, x0
   37c1c:	17fffff0 	b	37bdc <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const+0x20c>
