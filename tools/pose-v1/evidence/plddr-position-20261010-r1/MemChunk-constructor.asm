
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000036c30 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)>:
   36c30:	a9b87bfd 	stp	x29, x30, [sp, #-128]!
   36c34:	910003fd 	mov	x29, sp
   36c38:	a9025bf5 	stp	x21, x22, [sp, #32]
   36c3c:	b00004f6 	adrp	x22, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   36c40:	aa0403f5 	mov	x21, x4
   36c44:	a90153f3 	stp	x19, x20, [sp, #16]
   36c48:	aa0003f4 	mov	x20, x0
   36c4c:	f94516c0 	ldr	x0, [x22, #2600]
   36c50:	a90363f7 	stp	x23, x24, [sp, #48]
   36c54:	aa0103f8 	mov	x24, x1
   36c58:	f9400001 	ldr	x1, [x0]
   36c5c:	f9003fe1 	str	x1, [sp, #120]
   36c60:	d2800001 	mov	x1, #0x0                   	// #0
   36c64:	a9046bf9 	stp	x25, x26, [sp, #64]
   36c68:	aa0303f7 	mov	x23, x3
   36c6c:	f900029f 	str	xzr, [x20]
   36c70:	aa0203f9 	mov	x25, x2
   36c74:	3900229f 	strb	wzr, [x20, #8]
   36c78:	12001cba 	and	w26, w5, #0xff
   36c7c:	d2800c00 	mov	x0, #0x60                  	// #96
   36c80:	97fff270 	bl	33640 <operator new(unsigned long)@plt>
   36c84:	b00004e4 	adrp	x4, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   36c88:	a9007c1f 	stp	xzr, xzr, [x0]
   36c8c:	aa0003f3 	mov	x19, x0
   36c90:	f944f484 	ldr	x4, [x4, #2536]
   36c94:	a9017c1f 	stp	xzr, xzr, [x0, #16]
   36c98:	91004084 	add	x4, x4, #0x10
   36c9c:	a9027c1f 	stp	xzr, xzr, [x0, #32]
   36ca0:	a9037c1f 	stp	xzr, xzr, [x0, #48]
   36ca4:	a9047c1f 	stp	xzr, xzr, [x0, #64]
   36ca8:	a9057c1f 	stp	xzr, xzr, [x0, #80]
   36cac:	f8008404 	str	x4, [x0], #8
   36cb0:	885ffc01 	ldaxr	w1, [x0]
   36cb4:	11000421 	add	w1, w1, #0x1
   36cb8:	8802fc01 	stlxr	w2, w1, [x0]
   36cbc:	35ffffa2 	cbnz	w2, 36cb0 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x80>
   36cc0:	f9400301 	ldr	x1, [x24]
   36cc4:	39402302 	ldrb	w2, [x24, #8]
   36cc8:	b4000bc1 	cbz	x1, 36e40 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x210>
   36ccc:	34000662 	cbz	w2, 36d98 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x168>
   36cd0:	f9000a61 	str	x1, [x19, #16]
   36cd4:	f94002e1 	ldr	x1, [x23]
   36cd8:	f9001279 	str	x25, [x19, #32]
   36cdc:	394022e2 	ldrb	w2, [x23, #8]
   36ce0:	b4000881 	cbz	x1, 36df0 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1c0>
   36ce4:	34000ba2 	cbz	w2, 36e58 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x228>
   36ce8:	f9001661 	str	x1, [x19, #40]
   36cec:	f9400aa3 	ldr	x3, [x21, #16]
   36cf0:	f90033ff 	str	xzr, [sp, #96]
   36cf4:	b4000a23 	cbz	x3, 36e38 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x208>
   36cf8:	910143f7 	add	x23, sp, #0x50
   36cfc:	aa1503e1 	mov	x1, x21
   36d00:	aa1703e0 	mov	x0, x23
   36d04:	52800042 	mov	w2, #0x2                   	// #2
   36d08:	d63f0060 	blr	x3
   36d0c:	a94102a3 	ldp	x3, x0, [x21, #16]
   36d10:	a9448664 	ldp	x4, x1, [x19, #72]
   36d14:	a9048263 	stp	x3, x0, [x19, #72]
   36d18:	a9438e62 	ldp	x2, x3, [x19, #56]
   36d1c:	a90607e4 	stp	x4, x1, [sp, #96]
   36d20:	a9451fe6 	ldp	x6, x7, [sp, #80]
   36d24:	a9039e66 	stp	x6, x7, [x19, #56]
   36d28:	a9050fe2 	stp	x2, x3, [sp, #80]
   36d2c:	b40000a4 	cbz	x4, 36d40 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x110>
   36d30:	910143e1 	add	x1, sp, #0x50
   36d34:	52800062 	mov	w2, #0x3                   	// #3
   36d38:	aa0103e0 	mov	x0, x1
   36d3c:	d63f0080 	blr	x4
   36d40:	f9400280 	ldr	x0, [x20]
   36d44:	f9000293 	str	x19, [x20]
   36d48:	3901627a 	strb	w26, [x19, #88]
   36d4c:	b40000e0 	cbz	x0, 36d68 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x138>
   36d50:	91002001 	add	x1, x0, #0x8
   36d54:	885ffc22 	ldaxr	w2, [x1]
   36d58:	51000442 	sub	w2, w2, #0x1
   36d5c:	8803fc22 	stlxr	w3, w2, [x1]
   36d60:	35ffffa3 	cbnz	w3, 36d54 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x124>
   36d64:	34000982 	cbz	w2, 36e94 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x264>
   36d68:	f94516d6 	ldr	x22, [x22, #2600]
   36d6c:	f9403fe0 	ldr	x0, [sp, #120]
   36d70:	f94002c1 	ldr	x1, [x22]
   36d74:	eb010000 	subs	x0, x0, x1
   36d78:	d2800001 	mov	x1, #0x0                   	// #0
   36d7c:	54000941 	b.ne	36ea4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x274>  // b.any
   36d80:	a94153f3 	ldp	x19, x20, [sp, #16]
   36d84:	a9425bf5 	ldp	x21, x22, [sp, #32]
   36d88:	a94363f7 	ldp	x23, x24, [sp, #48]
   36d8c:	a9446bf9 	ldp	x25, x26, [sp, #64]
   36d90:	a8c87bfd 	ldp	x29, x30, [sp], #128
   36d94:	d65f03c0 	ret
   36d98:	91002020 	add	x0, x1, #0x8
   36d9c:	885ffc02 	ldaxr	w2, [x0]
   36da0:	11000442 	add	w2, w2, #0x1
   36da4:	8803fc02 	stlxr	w3, w2, [x0]
   36da8:	35ffffa3 	cbnz	w3, 36d9c <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x16c>
   36dac:	f9400a60 	ldr	x0, [x19, #16]
   36db0:	f9000a61 	str	x1, [x19, #16]
   36db4:	b4fff900 	cbz	x0, 36cd4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xa4>
   36db8:	91002001 	add	x1, x0, #0x8
   36dbc:	885ffc22 	ldaxr	w2, [x1]
   36dc0:	51000442 	sub	w2, w2, #0x1
   36dc4:	8803fc22 	stlxr	w3, w2, [x1]
   36dc8:	35ffffa3 	cbnz	w3, 36dbc <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x18c>
   36dcc:	35fff842 	cbnz	w2, 36cd4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xa4>
   36dd0:	f9400001 	ldr	x1, [x0]
   36dd4:	f9400821 	ldr	x1, [x1, #16]
   36dd8:	d63f0020 	blr	x1
   36ddc:	f9001279 	str	x25, [x19, #32]
   36de0:	f94002e1 	ldr	x1, [x23]
   36de4:	394022e2 	ldrb	w2, [x23, #8]
   36de8:	b5fff7e1 	cbnz	x1, 36ce4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xb4>
   36dec:	d503201f 	nop
   36df0:	f9401660 	ldr	x0, [x19, #40]
   36df4:	f900167f 	str	xzr, [x19, #40]
   36df8:	f100001f 	cmp	x0, #0x0
   36dfc:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   36e00:	54fff761 	b.ne	36cec <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xbc>  // b.any
   36e04:	91002001 	add	x1, x0, #0x8
   36e08:	885ffc22 	ldaxr	w2, [x1]
   36e0c:	51000442 	sub	w2, w2, #0x1
   36e10:	8803fc22 	stlxr	w3, w2, [x1]
   36e14:	35ffffa3 	cbnz	w3, 36e08 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1d8>
   36e18:	35fff6a2 	cbnz	w2, 36cec <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xbc>
   36e1c:	f9400001 	ldr	x1, [x0]
   36e20:	f9400821 	ldr	x1, [x1, #16]
   36e24:	d63f0020 	blr	x1
   36e28:	f90033ff 	str	xzr, [sp, #96]
   36e2c:	f9400aa3 	ldr	x3, [x21, #16]
   36e30:	b5fff643 	cbnz	x3, 36cf8 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xc8>
   36e34:	d503201f 	nop
   36e38:	f94037e0 	ldr	x0, [sp, #104]
   36e3c:	17ffffb5 	b	36d10 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xe0>
   36e40:	f9400a60 	ldr	x0, [x19, #16]
   36e44:	f9000a7f 	str	xzr, [x19, #16]
   36e48:	f100001f 	cmp	x0, #0x0
   36e4c:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   36e50:	54fff421 	b.ne	36cd4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xa4>  // b.any
   36e54:	17ffffd9 	b	36db8 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x188>
   36e58:	91002020 	add	x0, x1, #0x8
   36e5c:	885ffc02 	ldaxr	w2, [x0]
   36e60:	11000442 	add	w2, w2, #0x1
   36e64:	8803fc02 	stlxr	w3, w2, [x0]
   36e68:	35ffffa3 	cbnz	w3, 36e5c <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x22c>
   36e6c:	f9401660 	ldr	x0, [x19, #40]
   36e70:	f9001661 	str	x1, [x19, #40]
   36e74:	b4fff3c0 	cbz	x0, 36cec <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xbc>
   36e78:	91002001 	add	x1, x0, #0x8
   36e7c:	885ffc22 	ldaxr	w2, [x1]
   36e80:	51000442 	sub	w2, w2, #0x1
   36e84:	8803fc22 	stlxr	w3, w2, [x1]
   36e88:	35ffffa3 	cbnz	w3, 36e7c <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x24c>
   36e8c:	35fff302 	cbnz	w2, 36cec <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0xbc>
   36e90:	17ffffe3 	b	36e1c <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x1ec>
   36e94:	f9400001 	ldr	x1, [x0]
   36e98:	f9400821 	ldr	x1, [x1, #16]
   36e9c:	d63f0020 	blr	x1
   36ea0:	17ffffb2 	b	36d68 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x138>
   36ea4:	97ffee47 	bl	327c0 <__stack_chk_fail@plt>
   36ea8:	aa0003f5 	mov	x21, x0
   36eac:	f9400280 	ldr	x0, [x20]
   36eb0:	b4000080 	cbz	x0, 36ec0 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x290>
   36eb4:	39402281 	ldrb	w1, [x20, #8]
   36eb8:	35000041 	cbnz	w1, 36ec0 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x290>
   36ebc:	97ffef99 	bl	32d20 <icraft::xir::Object::decref()@plt>
   36ec0:	aa1503e0 	mov	x0, x21
   36ec4:	97fff61f 	bl	34740 <_Unwind_Resume@plt>
   36ec8:	f94033e3 	ldr	x3, [sp, #96]
   36ecc:	aa0003f5 	mov	x21, x0
   36ed0:	b40000a3 	cbz	x3, 36ee4 <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x2b4>
   36ed4:	aa1703e1 	mov	x1, x23
   36ed8:	aa1703e0 	mov	x0, x23
   36edc:	52800062 	mov	w2, #0x3                   	// #3
   36ee0:	d63f0060 	blr	x3
   36ee4:	aa1303e0 	mov	x0, x19
   36ee8:	97ffef8e 	bl	32d20 <icraft::xir::Object::decref()@plt>
   36eec:	17fffff0 	b	36eac <icraft::xrt::MemChunk::MemChunk(icraft::xrt::MemPtr, unsigned long, icraft::xrt::MemRegion, std::function<void (icraft::xrt::MemPtr const&)>, bool)+0x27c>
