
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

000000000003aee8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)>:
   3aee8:	a9ad7bfd 	stp	x29, x30, [sp, #-304]!
   3aeec:	b00004c4 	adrp	x4, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3aef0:	910003fd 	mov	x29, sp
   3aef4:	f9451484 	ldr	x4, [x4, #2600]
   3aef8:	a90573fb 	stp	x27, x28, [sp, #80]
   3aefc:	b00004dc 	adrp	x28, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3af00:	a90153f3 	stp	x19, x20, [sp, #16]
   3af04:	aa0003f3 	mov	x19, x0
   3af08:	f9400085 	ldr	x5, [x4]
   3af0c:	f90097e5 	str	x5, [sp, #296]
   3af10:	d2800005 	mov	x5, #0x0                   	// #0
   3af14:	f9462b80 	ldr	x0, [x28, #3152]
   3af18:	a9025bf5 	stp	x21, x22, [sp, #32]
   3af1c:	aa0103f5 	mov	x21, x1
   3af20:	12001c41 	and	w1, w2, #0xff
   3af24:	a90363f7 	stp	x23, x24, [sp, #48]
   3af28:	9102427b 	add	x27, x19, #0x90
   3af2c:	a9046bf9 	stp	x25, x26, [sp, #64]
   3af30:	aa0303f8 	mov	x24, x3
   3af34:	aa0803f9 	mov	x25, x8
   3af38:	b9007be1 	str	w1, [sp, #120]
   3af3c:	b4000080 	cbz	x0, 3af4c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x64>
   3af40:	aa1b03e0 	mov	x0, x27
   3af44:	97ffdde3 	bl	326d0 <pthread_mutex_lock@plt>
   3af48:	35004ae0 	cbnz	w0, 3b8a4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9bc>
   3af4c:	b4001f55 	cbz	x21, 3b334 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x44c>
   3af50:	f9401660 	ldr	x0, [x19, #40]
   3af54:	eb15001f 	cmp	x0, x21
   3af58:	54000fa3 	b.cc	3b14c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x264>  // b.lo, b.ul, b.last
   3af5c:	f9400e61 	ldr	x1, [x19, #24]
   3af60:	9100c263 	add	x3, x19, #0x30
   3af64:	f9401a77 	ldr	x23, [x19, #48]
   3af68:	f100003f 	cmp	x1, #0x0
   3af6c:	39408262 	ldrb	w2, [x19, #32]
   3af70:	91006264 	add	x4, x19, #0x18
   3af74:	f90033e3 	str	x3, [sp, #96]
   3af78:	1a9f17e0 	cset	w0, eq  // eq = none
   3af7c:	f9003be4 	str	x4, [sp, #112]
   3af80:	eb17007f 	cmp	x3, x23
   3af84:	f9005be1 	str	x1, [sp, #176]
   3af88:	2a000040 	orr	w0, w2, w0
   3af8c:	54001360 	b.eq	3b1f8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x310>  // b.none
   3af90:	3902e3e2 	strb	w2, [sp, #184]
   3af94:	910042fa 	add	x26, x23, #0x10
   3af98:	34003820 	cbz	w0, 3b69c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7b4>
   3af9c:	9102c3f4 	add	x20, sp, #0xb0
   3afa0:	910203f6 	add	x22, sp, #0x80
   3afa4:	aa1403e0 	mov	x0, x20
   3afa8:	aa1603e8 	mov	x8, x22
   3afac:	aa1803e1 	mov	x1, x24
   3afb0:	97fffda2 	bl	3a638 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]>
   3afb4:	f9405be0 	ldr	x0, [sp, #176]
   3afb8:	b4000060 	cbz	x0, 3afc4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc>
   3afbc:	3942e3e1 	ldrb	w1, [sp, #184]
   3afc0:	340037a1 	cbz	w1, 3b6b4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7cc>
   3afc4:	aa1603e0 	mov	x0, x22
   3afc8:	aa1403e8 	mov	x8, x20
   3afcc:	aa1503e1 	mov	x1, x21
   3afd0:	97ffe6cc 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3afd4:	aa1a03e1 	mov	x1, x26
   3afd8:	aa1403e0 	mov	x0, x20
   3afdc:	97ffdf79 	bl	32dc0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)@plt>
   3afe0:	f9405be1 	ldr	x1, [sp, #176]
   3afe4:	12001c16 	and	w22, w0, #0xff
   3afe8:	b4000061 	cbz	x1, 3aff4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x10c>
   3afec:	3942e3e0 	ldrb	w0, [sp, #184]
   3aff0:	34001d20 	cbz	w0, 3b394 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x4ac>
   3aff4:	34001d76 	cbz	w22, 3b3a0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x4b8>
   3aff8:	f94043f6 	ldr	x22, [sp, #128]
   3affc:	394223f8 	ldrb	w24, [sp, #136]
   3b000:	f10002df 	cmp	x22, #0x0
   3b004:	1a9f17fa 	cset	w26, eq  // eq = none
   3b008:	2a1a031a 	orr	w26, w24, w26
   3b00c:	34003c1a 	cbz	w26, 3b78c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8a4>
   3b010:	d2800500 	mov	x0, #0x28                  	// #40
   3b014:	f9401a77 	ldr	x23, [x19, #48]
   3b018:	97ffe18a 	bl	33640 <operator new(unsigned long)@plt>
   3b01c:	f9000816 	str	x22, [x0, #16]
   3b020:	aa1703e1 	mov	x1, x23
   3b024:	39006018 	strb	w24, [x0, #24]
   3b028:	f9001015 	str	x21, [x0, #32]
   3b02c:	97ffdcbd 	bl	32320 <std::__detail::_List_node_base::_M_hook(std::__detail::_List_node_base*)@plt>
   3b030:	f9402260 	ldr	x0, [x19, #64]
   3b034:	f94043e1 	ldr	x1, [sp, #128]
   3b038:	91000400 	add	x0, x0, #0x1
   3b03c:	394223e2 	ldrb	w2, [sp, #136]
   3b040:	f9002260 	str	x0, [x19, #64]
   3b044:	f100003f 	cmp	x1, #0x0
   3b048:	f90053e1 	str	x1, [sp, #160]
   3b04c:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   3b050:	3902a3e2 	strb	w2, [sp, #168]
   3b054:	54003a80 	b.eq	3b7a4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8bc>  // b.none
   3b058:	3941e3e4 	ldrb	w4, [sp, #120]
   3b05c:	910423f6 	add	x22, sp, #0x108
   3b060:	910283fa 	add	x26, sp, #0xa0
   3b064:	aa1503e2 	mov	x2, x21
   3b068:	aa1603e3 	mov	x3, x22
   3b06c:	aa1a03e1 	mov	x1, x26
   3b070:	aa1403e8 	mov	x8, x20
   3b074:	aa1303e0 	mov	x0, x19
   3b078:	f9008fff 	str	xzr, [sp, #280]
   3b07c:	97ffe6a5 	bl	34b10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const@plt>
   3b080:	f9408fe3 	ldr	x3, [sp, #280]
   3b084:	b40000a3 	cbz	x3, 3b098 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x1b0>
   3b088:	aa1603e1 	mov	x1, x22
   3b08c:	aa1603e0 	mov	x0, x22
   3b090:	52800062 	mov	w2, #0x3                   	// #3
   3b094:	d63f0060 	blr	x3
   3b098:	f94053e0 	ldr	x0, [sp, #160]
   3b09c:	b4000060 	cbz	x0, 3b0a8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x1c0>
   3b0a0:	3942a3e1 	ldrb	w1, [sp, #168]
   3b0a4:	34002bc1 	cbz	w1, 3b61c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x734>
   3b0a8:	91012273 	add	x19, x19, #0x48
   3b0ac:	aa1403e0 	mov	x0, x20
   3b0b0:	97ffe628 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3b0b4:	aa0003e2 	mov	x2, x0
   3b0b8:	aa1a03e1 	mov	x1, x26
   3b0bc:	aa1303e0 	mov	x0, x19
   3b0c0:	f90053e2 	str	x2, [sp, #160]
   3b0c4:	97ffdf7f 	bl	32ec0 <icraft::xrt::MemChunkNode const*& std::vector<icraft::xrt::MemChunkNode const*, std::allocator<icraft::xrt::MemChunkNode const*> >::emplace_back<icraft::xrt::MemChunkNode const*>(icraft::xrt::MemChunkNode const*&&)@plt>
   3b0c8:	f9405be0 	ldr	x0, [sp, #176]
   3b0cc:	f9000320 	str	x0, [x25]
   3b0d0:	3942e3e1 	ldrb	w1, [sp, #184]
   3b0d4:	39002321 	strb	w1, [x25, #8]
   3b0d8:	f100001f 	cmp	x0, #0x0
   3b0dc:	7a401820 	ccmp	w1, #0x0, #0x0, ne  // ne = any
   3b0e0:	54002900 	b.eq	3b600 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x718>  // b.none
   3b0e4:	b4000060 	cbz	x0, 3b0f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x208>
   3b0e8:	3942e3e1 	ldrb	w1, [sp, #184]
   3b0ec:	34002861 	cbz	w1, 3b5f8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x710>
   3b0f0:	f94043e0 	ldr	x0, [sp, #128]
   3b0f4:	b4000060 	cbz	x0, 3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b0f8:	394223e1 	ldrb	w1, [sp, #136]
   3b0fc:	34001181 	cbz	w1, 3b32c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x444>
   3b100:	f9462b80 	ldr	x0, [x28, #3152]
   3b104:	b4000060 	cbz	x0, 3b110 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x228>
   3b108:	aa1b03e0 	mov	x0, x27
   3b10c:	97ffdf29 	bl	32db0 <pthread_mutex_unlock@plt>
   3b110:	900004c0 	adrp	x0, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3b114:	f9451400 	ldr	x0, [x0, #2600]
   3b118:	f94097e1 	ldr	x1, [sp, #296]
   3b11c:	f9400002 	ldr	x2, [x0]
   3b120:	eb020021 	subs	x1, x1, x2
   3b124:	d2800002 	mov	x2, #0x0                   	// #0
   3b128:	54004521 	b.ne	3b9cc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xae4>  // b.any
   3b12c:	aa1903e0 	mov	x0, x25
   3b130:	a94153f3 	ldp	x19, x20, [sp, #16]
   3b134:	a9425bf5 	ldp	x21, x22, [sp, #32]
   3b138:	a94363f7 	ldp	x23, x24, [sp, #48]
   3b13c:	a9446bf9 	ldp	x25, x26, [sp, #64]
   3b140:	a94573fb 	ldp	x27, x28, [sp, #80]
   3b144:	a8d37bfd 	ldp	x29, x30, [sp], #304
   3b148:	d65f03c0 	ret
   3b14c:	52855f61 	mov	w1, #0x2afb                	// #11003
   3b150:	52805320 	mov	w0, #0x299                 	// #665
   3b154:	97ffea3f 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3b158:	97ffdca6 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3b15c:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3b160:	aa0003f4 	mov	x20, x0
   3b164:	91356021 	add	x1, x1, #0xd58
   3b168:	d28006e2 	mov	x2, #0x37                  	// #55
   3b16c:	97ffe1ed 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3b170:	9103a3f7 	add	x23, sp, #0xe8
   3b174:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3b178:	910042e4 	add	x4, x23, #0x10
   3b17c:	b0000342 	adrp	x2, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3b180:	aa1703e0 	mov	x0, x23
   3b184:	91364021 	add	x1, x1, #0xd90
   3b188:	9136d842 	add	x2, x2, #0xdb6
   3b18c:	52800003 	mov	w3, #0x0                   	// #0
   3b190:	f90077e4 	str	x4, [sp, #232]
   3b194:	97ffddeb 	bl	32940 <void std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >::_M_construct<char const*>(char const*, char const*, std::forward_iterator_tag)@plt>
   3b198:	a94e87e0 	ldp	x0, x1, [sp, #232]
   3b19c:	910423f6 	add	x22, sp, #0x108
   3b1a0:	f9401664 	ldr	x4, [x19, #40]
   3b1a4:	aa1603e8 	mov	x8, x22
   3b1a8:	910303e3 	add	x3, sp, #0xc0
   3b1ac:	d2800882 	mov	x2, #0x44                  	// #68
   3b1b0:	f90063f5 	str	x21, [sp, #192]
   3b1b4:	f9006be4 	str	x4, [sp, #208]
   3b1b8:	97ffe62a 	bl	34a60 <fmt::v8::vformat[abi:cxx11](fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3b1bc:	a9508be1 	ldp	x1, x2, [sp, #264]
   3b1c0:	aa1403e0 	mov	x0, x20
   3b1c4:	97ffe1d7 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3b1c8:	f94087e0 	ldr	x0, [sp, #264]
   3b1cc:	910042d6 	add	x22, x22, #0x10
   3b1d0:	eb16001f 	cmp	x0, x22
   3b1d4:	54000040 	b.eq	3b1dc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x2f4>  // b.none
   3b1d8:	97ffe0de 	bl	33550 <operator delete(void*)@plt>
   3b1dc:	f94077e0 	ldr	x0, [sp, #232]
   3b1e0:	910042f7 	add	x23, x23, #0x10
   3b1e4:	eb17001f 	cmp	x0, x23
   3b1e8:	54000040 	b.eq	3b1f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x308>  // b.none
   3b1ec:	97ffe0d9 	bl	33550 <operator delete(void*)@plt>
   3b1f0:	97ffe9fc 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3b1f4:	17ffff5a 	b	3af5c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x74>
   3b1f8:	3902e3e2 	strb	w2, [sp, #184]
   3b1fc:	34003140 	cbz	w0, 3b824 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x93c>
   3b200:	9102c3f4 	add	x20, sp, #0xb0
   3b204:	aa1803e1 	mov	x1, x24
   3b208:	aa1403e0 	mov	x0, x20
   3b20c:	910243e8 	add	x8, sp, #0x90
   3b210:	97fffd0a 	bl	3a638 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]>
   3b214:	f9405be0 	ldr	x0, [sp, #176]
   3b218:	b4000060 	cbz	x0, 3b224 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x33c>
   3b21c:	3942e3e1 	ldrb	w1, [sp, #184]
   3b220:	34002ce1 	cbz	w1, 3b7bc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8d4>
   3b224:	f9404bf6 	ldr	x22, [sp, #144]
   3b228:	394263f8 	ldrb	w24, [sp, #152]
   3b22c:	f10002df 	cmp	x22, #0x0
   3b230:	1a9f17fa 	cset	w26, eq  // eq = none
   3b234:	2a1a031a 	orr	w26, w24, w26
   3b238:	34002eba 	cbz	w26, 3b80c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x924>
   3b23c:	d2800500 	mov	x0, #0x28                  	// #40
   3b240:	f9401a77 	ldr	x23, [x19, #48]
   3b244:	97ffe0ff 	bl	33640 <operator new(unsigned long)@plt>
   3b248:	f9000816 	str	x22, [x0, #16]
   3b24c:	aa1703e1 	mov	x1, x23
   3b250:	39006018 	strb	w24, [x0, #24]
   3b254:	f9001015 	str	x21, [x0, #32]
   3b258:	97ffdc32 	bl	32320 <std::__detail::_List_node_base::_M_hook(std::__detail::_List_node_base*)@plt>
   3b25c:	f9402260 	ldr	x0, [x19, #64]
   3b260:	f9404be1 	ldr	x1, [sp, #144]
   3b264:	91000400 	add	x0, x0, #0x1
   3b268:	394263e2 	ldrb	w2, [sp, #152]
   3b26c:	f9002260 	str	x0, [x19, #64]
   3b270:	f100003f 	cmp	x1, #0x0
   3b274:	f90053e1 	str	x1, [sp, #160]
   3b278:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   3b27c:	3902a3e2 	strb	w2, [sp, #168]
   3b280:	54002aa0 	b.eq	3b7d4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8ec>  // b.none
   3b284:	3941e3e4 	ldrb	w4, [sp, #120]
   3b288:	910423f6 	add	x22, sp, #0x108
   3b28c:	910283fa 	add	x26, sp, #0xa0
   3b290:	aa1503e2 	mov	x2, x21
   3b294:	aa1603e3 	mov	x3, x22
   3b298:	aa1a03e1 	mov	x1, x26
   3b29c:	aa1403e8 	mov	x8, x20
   3b2a0:	aa1303e0 	mov	x0, x19
   3b2a4:	f9008fff 	str	xzr, [sp, #280]
   3b2a8:	97ffe61a 	bl	34b10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const@plt>
   3b2ac:	f9408fe3 	ldr	x3, [sp, #280]
   3b2b0:	b40000a3 	cbz	x3, 3b2c4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x3dc>
   3b2b4:	aa1603e1 	mov	x1, x22
   3b2b8:	aa1603e0 	mov	x0, x22
   3b2bc:	52800062 	mov	w2, #0x3                   	// #3
   3b2c0:	d63f0060 	blr	x3
   3b2c4:	f94053e0 	ldr	x0, [sp, #160]
   3b2c8:	b4000060 	cbz	x0, 3b2d4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x3ec>
   3b2cc:	3942a3e1 	ldrb	w1, [sp, #168]
   3b2d0:	340027a1 	cbz	w1, 3b7c4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8dc>
   3b2d4:	91012273 	add	x19, x19, #0x48
   3b2d8:	aa1403e0 	mov	x0, x20
   3b2dc:	97ffe59d 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3b2e0:	aa0003e2 	mov	x2, x0
   3b2e4:	aa1a03e1 	mov	x1, x26
   3b2e8:	aa1303e0 	mov	x0, x19
   3b2ec:	f90053e2 	str	x2, [sp, #160]
   3b2f0:	97ffdef4 	bl	32ec0 <icraft::xrt::MemChunkNode const*& std::vector<icraft::xrt::MemChunkNode const*, std::allocator<icraft::xrt::MemChunkNode const*> >::emplace_back<icraft::xrt::MemChunkNode const*>(icraft::xrt::MemChunkNode const*&&)@plt>
   3b2f4:	f9405be0 	ldr	x0, [sp, #176]
   3b2f8:	f9000320 	str	x0, [x25]
   3b2fc:	3942e3e1 	ldrb	w1, [sp, #184]
   3b300:	39002321 	strb	w1, [x25, #8]
   3b304:	f100001f 	cmp	x0, #0x0
   3b308:	7a401820 	ccmp	w1, #0x0, #0x0, ne  // ne = any
   3b30c:	54002700 	b.eq	3b7ec <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x904>  // b.none
   3b310:	b4000060 	cbz	x0, 3b31c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x434>
   3b314:	3942e3e1 	ldrb	w1, [sp, #184]
   3b318:	340025a1 	cbz	w1, 3b7cc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8e4>
   3b31c:	f9404be0 	ldr	x0, [sp, #144]
   3b320:	b4ffef00 	cbz	x0, 3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b324:	394263e1 	ldrb	w1, [sp, #152]
   3b328:	35ffeec1 	cbnz	w1, 3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b32c:	97ffde7d 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b330:	17ffff74 	b	3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b334:	9102c3f4 	add	x20, sp, #0xb0
   3b338:	aa1403e8 	mov	x8, x20
   3b33c:	97ffe5dd 	bl	34ab0 <icraft::xrt::MemPtr::NullPtr()@plt>
   3b340:	910423f6 	add	x22, sp, #0x108
   3b344:	aa1403e1 	mov	x1, x20
   3b348:	aa1303e0 	mov	x0, x19
   3b34c:	aa1603e3 	mov	x3, x22
   3b350:	aa1903e8 	mov	x8, x25
   3b354:	52800004 	mov	w4, #0x0                   	// #0
   3b358:	d2800002 	mov	x2, #0x0                   	// #0
   3b35c:	f9008fff 	str	xzr, [sp, #280]
   3b360:	97ffe5ec 	bl	34b10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const@plt>
   3b364:	f9408fe3 	ldr	x3, [sp, #280]
   3b368:	b40000a3 	cbz	x3, 3b37c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x494>
   3b36c:	aa1603e1 	mov	x1, x22
   3b370:	aa1603e0 	mov	x0, x22
   3b374:	52800062 	mov	w2, #0x3                   	// #3
   3b378:	d63f0060 	blr	x3
   3b37c:	f9405be0 	ldr	x0, [sp, #176]
   3b380:	b4ffec00 	cbz	x0, 3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b384:	3942e3e1 	ldrb	w1, [sp, #184]
   3b388:	35ffebc1 	cbnz	w1, 3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b38c:	97ffde65 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b390:	17ffff5c 	b	3b100 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x218>
   3b394:	aa0103e0 	mov	x0, x1
   3b398:	97ffde62 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b39c:	35ffe2f6 	cbnz	w22, 3aff8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x110>
   3b3a0:	f94012e1 	ldr	x1, [x23, #32]
   3b3a4:	aa1a03e0 	mov	x0, x26
   3b3a8:	aa1403e8 	mov	x8, x20
   3b3ac:	97ffe5d5 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b3b0:	910243e0 	add	x0, sp, #0x90
   3b3b4:	aa1803e1 	mov	x1, x24
   3b3b8:	aa0003e8 	mov	x8, x0
   3b3bc:	f90037e0 	str	x0, [sp, #104]
   3b3c0:	aa1403e0 	mov	x0, x20
   3b3c4:	97fffc9d 	bl	3a638 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]>
   3b3c8:	f9405be0 	ldr	x0, [sp, #176]
   3b3cc:	b4000060 	cbz	x0, 3b3d8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x4f0>
   3b3d0:	3942e3e1 	ldrb	w1, [sp, #184]
   3b3d4:	340026a1 	cbz	w1, 3b8a8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9c0>
   3b3d8:	f9401a60 	ldr	x0, [x19, #48]
   3b3dc:	910283f7 	add	x23, sp, #0xa0
   3b3e0:	f9400016 	ldr	x22, [x0]
   3b3e4:	f94033e0 	ldr	x0, [sp, #96]
   3b3e8:	eb16001f 	cmp	x0, x22
   3b3ec:	54002ec0 	b.eq	3b9c4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xadc>  // b.none
   3b3f0:	f94037e0 	ldr	x0, [sp, #104]
   3b3f4:	910042da 	add	x26, x22, #0x10
   3b3f8:	aa1403e8 	mov	x8, x20
   3b3fc:	aa1503e1 	mov	x1, x21
   3b400:	97ffe5c0 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b404:	aa1a03e1 	mov	x1, x26
   3b408:	aa1403e0 	mov	x0, x20
   3b40c:	97ffde6d 	bl	32dc0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)@plt>
   3b410:	f9405be2 	ldr	x2, [sp, #176]
   3b414:	12001c01 	and	w1, w0, #0xff
   3b418:	b4000062 	cbz	x2, 3b424 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x53c>
   3b41c:	3942e3e0 	ldrb	w0, [sp, #184]
   3b420:	34001020 	cbz	w0, 3b624 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x73c>
   3b424:	350014c1 	cbnz	w1, 3b6bc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7d4>
   3b428:	f94012c1 	ldr	x1, [x22, #32]
   3b42c:	aa1a03e0 	mov	x0, x26
   3b430:	aa1703e8 	mov	x8, x23
   3b434:	aa1703fa 	mov	x26, x23
   3b438:	97ffe5b2 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b43c:	aa1703e0 	mov	x0, x23
   3b440:	97ffe57c 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3b444:	7100041f 	cmp	w0, #0x1
   3b448:	aa1703e0 	mov	x0, x23
   3b44c:	54001040 	b.eq	3b654 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x76c>  // b.none
   3b450:	97ffe578 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3b454:	340011e0 	cbz	w0, 3b690 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7a8>
   3b458:	3942a3e1 	ldrb	w1, [sp, #168]
   3b45c:	3902e3e1 	strb	w1, [sp, #184]
   3b460:	f94053e2 	ldr	x2, [sp, #160]
   3b464:	f90053ff 	str	xzr, [sp, #160]
   3b468:	f9404be0 	ldr	x0, [sp, #144]
   3b46c:	f9004be2 	str	x2, [sp, #144]
   3b470:	f9005bff 	str	xzr, [sp, #176]
   3b474:	f100001f 	cmp	x0, #0x0
   3b478:	7a401820 	ccmp	w1, #0x0, #0x0, ne  // ne = any
   3b47c:	54000de0 	b.eq	3b638 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x750>  // b.none
   3b480:	f94053e0 	ldr	x0, [sp, #160]
   3b484:	b4000060 	cbz	x0, 3b490 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x5a8>
   3b488:	3942a3e1 	ldrb	w1, [sp, #168]
   3b48c:	34000fe1 	cbz	w1, 3b688 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7a0>
   3b490:	f94002d6 	ldr	x22, [x22]
   3b494:	f94033e0 	ldr	x0, [sp, #96]
   3b498:	eb16001f 	cmp	x0, x22
   3b49c:	54fffaa1 	b.ne	3b3f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x508>  // b.any
   3b4a0:	f94037e0 	ldr	x0, [sp, #104]
   3b4a4:	aa1a03e8 	mov	x8, x26
   3b4a8:	aa1503e1 	mov	x1, x21
   3b4ac:	97ffe595 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b4b0:	f9401661 	ldr	x1, [x19, #40]
   3b4b4:	aa1403e8 	mov	x8, x20
   3b4b8:	f9403be0 	ldr	x0, [sp, #112]
   3b4bc:	97ffe591 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b4c0:	aa1403e1 	mov	x1, x20
   3b4c4:	aa1a03e0 	mov	x0, x26
   3b4c8:	97ffde3e 	bl	32dc0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)@plt>
   3b4cc:	f9405be1 	ldr	x1, [sp, #176]
   3b4d0:	12001c16 	and	w22, w0, #0xff
   3b4d4:	b4000061 	cbz	x1, 3b4e0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x5f8>
   3b4d8:	3942e3e0 	ldrb	w0, [sp, #184]
   3b4dc:	34001c20 	cbz	w0, 3b860 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x978>
   3b4e0:	f94053e0 	ldr	x0, [sp, #160]
   3b4e4:	b4000060 	cbz	x0, 3b4f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x608>
   3b4e8:	3942a3e1 	ldrb	w1, [sp, #168]
   3b4ec:	34001b61 	cbz	w1, 3b858 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x970>
   3b4f0:	34001e56 	cbz	w22, 3b8b8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9d0>
   3b4f4:	f9404bf6 	ldr	x22, [sp, #144]
   3b4f8:	394263f7 	ldrb	w23, [sp, #152]
   3b4fc:	f10002df 	cmp	x22, #0x0
   3b500:	1a9f17f8 	cset	w24, eq  // eq = none
   3b504:	2a1802f8 	orr	w24, w23, w24
   3b508:	34001c38 	cbz	w24, 3b88c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9a4>
   3b50c:	d2800500 	mov	x0, #0x28                  	// #40
   3b510:	97ffe04c 	bl	33640 <operator new(unsigned long)@plt>
   3b514:	f94033e1 	ldr	x1, [sp, #96]
   3b518:	f9000816 	str	x22, [x0, #16]
   3b51c:	39006017 	strb	w23, [x0, #24]
   3b520:	f9001015 	str	x21, [x0, #32]
   3b524:	97ffdb7f 	bl	32320 <std::__detail::_List_node_base::_M_hook(std::__detail::_List_node_base*)@plt>
   3b528:	f9402260 	ldr	x0, [x19, #64]
   3b52c:	f9404be1 	ldr	x1, [sp, #144]
   3b530:	91000400 	add	x0, x0, #0x1
   3b534:	394263e2 	ldrb	w2, [sp, #152]
   3b538:	f9002260 	str	x0, [x19, #64]
   3b53c:	f100003f 	cmp	x1, #0x0
   3b540:	f90053e1 	str	x1, [sp, #160]
   3b544:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   3b548:	3902a3e2 	strb	w2, [sp, #168]
   3b54c:	54001940 	b.eq	3b874 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x98c>  // b.none
   3b550:	3941e3e4 	ldrb	w4, [sp, #120]
   3b554:	910423f6 	add	x22, sp, #0x108
   3b558:	aa1503e2 	mov	x2, x21
   3b55c:	aa1603e3 	mov	x3, x22
   3b560:	aa1403e8 	mov	x8, x20
   3b564:	aa1a03e1 	mov	x1, x26
   3b568:	aa1303e0 	mov	x0, x19
   3b56c:	f9008fff 	str	xzr, [sp, #280]
   3b570:	97ffe568 	bl	34b10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const@plt>
   3b574:	f9408fe3 	ldr	x3, [sp, #280]
   3b578:	b40000a3 	cbz	x3, 3b58c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x6a4>
   3b57c:	aa1603e1 	mov	x1, x22
   3b580:	aa1603e0 	mov	x0, x22
   3b584:	52800062 	mov	w2, #0x3                   	// #3
   3b588:	d63f0060 	blr	x3
   3b58c:	f94053e0 	ldr	x0, [sp, #160]
   3b590:	b4000080 	cbz	x0, 3b5a0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x6b8>
   3b594:	3942a3e1 	ldrb	w1, [sp, #168]
   3b598:	35000041 	cbnz	w1, 3b5a0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x6b8>
   3b59c:	97ffdde1 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b5a0:	91012273 	add	x19, x19, #0x48
   3b5a4:	aa1403e0 	mov	x0, x20
   3b5a8:	97ffe4ea 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3b5ac:	aa0003e2 	mov	x2, x0
   3b5b0:	aa1a03e1 	mov	x1, x26
   3b5b4:	aa1303e0 	mov	x0, x19
   3b5b8:	f90053e2 	str	x2, [sp, #160]
   3b5bc:	97ffde41 	bl	32ec0 <icraft::xrt::MemChunkNode const*& std::vector<icraft::xrt::MemChunkNode const*, std::allocator<icraft::xrt::MemChunkNode const*> >::emplace_back<icraft::xrt::MemChunkNode const*>(icraft::xrt::MemChunkNode const*&&)@plt>
   3b5c0:	f9405be0 	ldr	x0, [sp, #176]
   3b5c4:	3942e3e1 	ldrb	w1, [sp, #184]
   3b5c8:	f9000320 	str	x0, [x25]
   3b5cc:	f100001f 	cmp	x0, #0x0
   3b5d0:	39002321 	strb	w1, [x25, #8]
   3b5d4:	7a401820 	ccmp	w1, #0x0, #0x0, ne  // ne = any
   3b5d8:	54001320 	b.eq	3b83c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x954>  // b.none
   3b5dc:	b4000060 	cbz	x0, 3b5e8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x700>
   3b5e0:	3942e3e1 	ldrb	w1, [sp, #184]
   3b5e4:	34001661 	cbz	w1, 3b8b0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9c8>
   3b5e8:	f9404be0 	ldr	x0, [sp, #144]
   3b5ec:	b4ffd820 	cbz	x0, 3b0f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x208>
   3b5f0:	394263e1 	ldrb	w1, [sp, #152]
   3b5f4:	35ffd7e1 	cbnz	w1, 3b0f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x208>
   3b5f8:	97ffddca 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b5fc:	17fffebd 	b	3b0f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x208>
   3b600:	91002000 	add	x0, x0, #0x8
   3b604:	885ffc01 	ldaxr	w1, [x0]
   3b608:	11000421 	add	w1, w1, #0x1
   3b60c:	8802fc01 	stlxr	w2, w1, [x0]
   3b610:	35ffffa2 	cbnz	w2, 3b604 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x71c>
   3b614:	f9405be0 	ldr	x0, [sp, #176]
   3b618:	17fffeb3 	b	3b0e4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x1fc>
   3b61c:	97ffddc1 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b620:	17fffea2 	b	3b0a8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x1c0>
   3b624:	aa0203e0 	mov	x0, x2
   3b628:	b9007fe1 	str	w1, [sp, #124]
   3b62c:	97ffddbd 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b630:	b9407fe1 	ldr	w1, [sp, #124]
   3b634:	17ffff7c 	b	3b424 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x53c>
   3b638:	97ffddba 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b63c:	f9405be0 	ldr	x0, [sp, #176]
   3b640:	b4fff200 	cbz	x0, 3b480 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x598>
   3b644:	3942e3e1 	ldrb	w1, [sp, #184]
   3b648:	35fff1c1 	cbnz	w1, 3b480 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x598>
   3b64c:	97ffddb5 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b650:	17ffff8c 	b	3b480 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x598>
   3b654:	97ffdb3f 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3b658:	aa0003e2 	mov	x2, x0
   3b65c:	aa1403e8 	mov	x8, x20
   3b660:	aa1703e0 	mov	x0, x23
   3b664:	9ad80841 	udiv	x1, x2, x24
   3b668:	9b188821 	msub	x1, x1, x24, x2
   3b66c:	f100003f 	cmp	x1, #0x0
   3b670:	cb010302 	sub	x2, x24, x1
   3b674:	9a811041 	csel	x1, x2, x1, ne  // ne = any
   3b678:	97ffe522 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3b67c:	3942e3e1 	ldrb	w1, [sp, #184]
   3b680:	f9405be2 	ldr	x2, [sp, #176]
   3b684:	17ffff79 	b	3b468 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x580>
   3b688:	97ffdda6 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b68c:	17ffff81 	b	3b490 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x5a8>
   3b690:	aa1703e0 	mov	x0, x23
   3b694:	97ffe2e7 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3b698:	17fffff0 	b	3b658 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x770>
   3b69c:	91002021 	add	x1, x1, #0x8
   3b6a0:	885ffc20 	ldaxr	w0, [x1]
   3b6a4:	11000400 	add	w0, w0, #0x1
   3b6a8:	8802fc20 	stlxr	w2, w0, [x1]
   3b6ac:	35ffffa2 	cbnz	w2, 3b6a0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7b8>
   3b6b0:	17fffe3b 	b	3af9c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb4>
   3b6b4:	97ffdd9b 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b6b8:	17fffe43 	b	3afc4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc>
   3b6bc:	f9404bf7 	ldr	x23, [sp, #144]
   3b6c0:	394263f8 	ldrb	w24, [sp, #152]
   3b6c4:	f10002ff 	cmp	x23, #0x0
   3b6c8:	1a9f17fa 	cset	w26, eq  // eq = none
   3b6cc:	2a1a031a 	orr	w26, w24, w26
   3b6d0:	3400163a 	cbz	w26, 3b994 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xaac>
   3b6d4:	d2800500 	mov	x0, #0x28                  	// #40
   3b6d8:	97ffdfda 	bl	33640 <operator new(unsigned long)@plt>
   3b6dc:	f9000817 	str	x23, [x0, #16]
   3b6e0:	aa1603e1 	mov	x1, x22
   3b6e4:	39006018 	strb	w24, [x0, #24]
   3b6e8:	f9001015 	str	x21, [x0, #32]
   3b6ec:	97ffdb0d 	bl	32320 <std::__detail::_List_node_base::_M_hook(std::__detail::_List_node_base*)@plt>
   3b6f0:	f9402260 	ldr	x0, [x19, #64]
   3b6f4:	f9404be1 	ldr	x1, [sp, #144]
   3b6f8:	91000400 	add	x0, x0, #0x1
   3b6fc:	394263e2 	ldrb	w2, [sp, #152]
   3b700:	f9002260 	str	x0, [x19, #64]
   3b704:	f100003f 	cmp	x1, #0x0
   3b708:	f90053e1 	str	x1, [sp, #160]
   3b70c:	7a401840 	ccmp	w2, #0x0, #0x0, ne  // ne = any
   3b710:	3902a3e2 	strb	w2, [sp, #168]
   3b714:	540014c0 	b.eq	3b9ac <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xac4>  // b.none
   3b718:	3941e3e4 	ldrb	w4, [sp, #120]
   3b71c:	910423f6 	add	x22, sp, #0x108
   3b720:	910283fa 	add	x26, sp, #0xa0
   3b724:	aa1503e2 	mov	x2, x21
   3b728:	aa1603e3 	mov	x3, x22
   3b72c:	aa1a03e1 	mov	x1, x26
   3b730:	aa1403e8 	mov	x8, x20
   3b734:	aa1303e0 	mov	x0, x19
   3b738:	f9008fff 	str	xzr, [sp, #280]
   3b73c:	97ffe4f5 	bl	34b10 <icraft::xrt::MemManagerNode::CreateMemChunk(icraft::xrt::MemPtr, unsigned long, std::function<void (icraft::xrt::MemPtr const&)>, bool) const@plt>
   3b740:	f9408fe3 	ldr	x3, [sp, #280]
   3b744:	b40000a3 	cbz	x3, 3b758 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x870>
   3b748:	aa1603e1 	mov	x1, x22
   3b74c:	aa1603e0 	mov	x0, x22
   3b750:	52800062 	mov	w2, #0x3                   	// #3
   3b754:	d63f0060 	blr	x3
   3b758:	f94053e0 	ldr	x0, [sp, #160]
   3b75c:	b4000060 	cbz	x0, 3b768 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x880>
   3b760:	3942a3e1 	ldrb	w1, [sp, #168]
   3b764:	34000841 	cbz	w1, 3b86c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x984>
   3b768:	91012273 	add	x19, x19, #0x48
   3b76c:	aa1403e0 	mov	x0, x20
   3b770:	97ffe478 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3b774:	aa0003e2 	mov	x2, x0
   3b778:	aa1a03e1 	mov	x1, x26
   3b77c:	aa1303e0 	mov	x0, x19
   3b780:	f90053e2 	str	x2, [sp, #160]
   3b784:	97ffddcf 	bl	32ec0 <icraft::xrt::MemChunkNode const*& std::vector<icraft::xrt::MemChunkNode const*, std::allocator<icraft::xrt::MemChunkNode const*> >::emplace_back<icraft::xrt::MemChunkNode const*>(icraft::xrt::MemChunkNode const*&&)@plt>
   3b788:	17ffff8e 	b	3b5c0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x6d8>
   3b78c:	910022c0 	add	x0, x22, #0x8
   3b790:	885ffc01 	ldaxr	w1, [x0]
   3b794:	11000421 	add	w1, w1, #0x1
   3b798:	8802fc01 	stlxr	w2, w1, [x0]
   3b79c:	35ffffa2 	cbnz	w2, 3b790 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8a8>
   3b7a0:	17fffe1c 	b	3b010 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x128>
   3b7a4:	91002021 	add	x1, x1, #0x8
   3b7a8:	885ffc20 	ldaxr	w0, [x1]
   3b7ac:	11000400 	add	w0, w0, #0x1
   3b7b0:	8802fc20 	stlxr	w2, w0, [x1]
   3b7b4:	35ffffa2 	cbnz	w2, 3b7a8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8c0>
   3b7b8:	17fffe28 	b	3b058 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x170>
   3b7bc:	97ffdd59 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b7c0:	17fffe99 	b	3b224 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x33c>
   3b7c4:	97ffdd57 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b7c8:	17fffec3 	b	3b2d4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x3ec>
   3b7cc:	97ffdd55 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b7d0:	17fffed3 	b	3b31c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x434>
   3b7d4:	91002021 	add	x1, x1, #0x8
   3b7d8:	885ffc20 	ldaxr	w0, [x1]
   3b7dc:	11000400 	add	w0, w0, #0x1
   3b7e0:	8802fc20 	stlxr	w2, w0, [x1]
   3b7e4:	35ffffa2 	cbnz	w2, 3b7d8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x8f0>
   3b7e8:	17fffea7 	b	3b284 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x39c>
   3b7ec:	91002000 	add	x0, x0, #0x8
   3b7f0:	885ffc01 	ldaxr	w1, [x0]
   3b7f4:	11000421 	add	w1, w1, #0x1
   3b7f8:	8802fc01 	stlxr	w2, w1, [x0]
   3b7fc:	35ffffa2 	cbnz	w2, 3b7f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x908>
   3b800:	f9405be0 	ldr	x0, [sp, #176]
   3b804:	b5ffd880 	cbnz	x0, 3b314 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x42c>
   3b808:	17fffec5 	b	3b31c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x434>
   3b80c:	910022c0 	add	x0, x22, #0x8
   3b810:	885ffc01 	ldaxr	w1, [x0]
   3b814:	11000421 	add	w1, w1, #0x1
   3b818:	8802fc01 	stlxr	w2, w1, [x0]
   3b81c:	35ffffa2 	cbnz	w2, 3b810 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x928>
   3b820:	17fffe87 	b	3b23c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x354>
   3b824:	91002021 	add	x1, x1, #0x8
   3b828:	885ffc20 	ldaxr	w0, [x1]
   3b82c:	11000400 	add	w0, w0, #0x1
   3b830:	8802fc20 	stlxr	w2, w0, [x1]
   3b834:	35ffffa2 	cbnz	w2, 3b828 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x940>
   3b838:	17fffe72 	b	3b200 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x318>
   3b83c:	91002000 	add	x0, x0, #0x8
   3b840:	885ffc01 	ldaxr	w1, [x0]
   3b844:	11000421 	add	w1, w1, #0x1
   3b848:	8802fc01 	stlxr	w2, w1, [x0]
   3b84c:	35ffffa2 	cbnz	w2, 3b840 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x958>
   3b850:	f9405be0 	ldr	x0, [sp, #176]
   3b854:	17ffff62 	b	3b5dc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x6f4>
   3b858:	97ffdd32 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b85c:	17ffff25 	b	3b4f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x608>
   3b860:	aa0103e0 	mov	x0, x1
   3b864:	97ffdd2f 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b868:	17ffff1e 	b	3b4e0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x5f8>
   3b86c:	97ffdd2d 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b870:	17ffffbe 	b	3b768 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x880>
   3b874:	91002021 	add	x1, x1, #0x8
   3b878:	885ffc20 	ldaxr	w0, [x1]
   3b87c:	11000400 	add	w0, w0, #0x1
   3b880:	8802fc20 	stlxr	w2, w0, [x1]
   3b884:	35ffffa2 	cbnz	w2, 3b878 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x990>
   3b888:	17ffff32 	b	3b550 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x668>
   3b88c:	910022c0 	add	x0, x22, #0x8
   3b890:	885ffc01 	ldaxr	w1, [x0]
   3b894:	11000421 	add	w1, w1, #0x1
   3b898:	8802fc01 	stlxr	w2, w1, [x0]
   3b89c:	35ffffa2 	cbnz	w2, 3b890 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x9a8>
   3b8a0:	17ffff1b 	b	3b50c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x624>
   3b8a4:	97ffddd3 	bl	32ff0 <std::__throw_system_error(int)@plt>
   3b8a8:	97ffdd1e 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b8ac:	17fffecb 	b	3b3d8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x4f0>
   3b8b0:	97ffdd1c 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3b8b4:	17ffff4d 	b	3b5e8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x700>
   3b8b8:	52855f61 	mov	w1, #0x2afb                	// #11003
   3b8bc:	52805800 	mov	w0, #0x2c0                 	// #704
   3b8c0:	97ffe864 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3b8c4:	97ffdacb 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3b8c8:	9103a3f7 	add	x23, sp, #0xe8
   3b8cc:	d2800664 	mov	x4, #0x33                  	// #51
   3b8d0:	910042e3 	add	x3, x23, #0x10
   3b8d4:	aa0003f3 	mov	x19, x0
   3b8d8:	aa1403e1 	mov	x1, x20
   3b8dc:	aa1703e0 	mov	x0, x23
   3b8e0:	d2800002 	mov	x2, #0x0                   	// #0
   3b8e4:	f9005be4 	str	x4, [sp, #176]
   3b8e8:	f90077e3 	str	x3, [sp, #232]
   3b8ec:	97ffe3a5 	bl	34780 <std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >::_M_create(unsigned long&, unsigned long)@plt>
   3b8f0:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3b8f4:	9136e021 	add	x1, x1, #0xdb8
   3b8f8:	f9405be2 	ldr	x2, [sp, #176]
   3b8fc:	f9007fe2 	str	x2, [sp, #248]
   3b900:	a9420c22 	ldp	x2, x3, [x1, #32]
   3b904:	f90077e0 	str	x0, [sp, #232]
   3b908:	a9401424 	ldp	x4, x5, [x1]
   3b90c:	a9001404 	stp	x4, x5, [x0]
   3b910:	910423f6 	add	x22, sp, #0x108
   3b914:	a9020c02 	stp	x2, x3, [x0, #32]
   3b918:	aa1603e8 	mov	x8, x22
   3b91c:	b842f023 	ldur	w3, [x1, #47]
   3b920:	a9411424 	ldp	x4, x5, [x1, #16]
   3b924:	a9011404 	stp	x4, x5, [x0, #16]
   3b928:	d2800082 	mov	x2, #0x4                   	// #4
   3b92c:	b802f003 	stur	w3, [x0, #47]
   3b930:	910303e3 	add	x3, sp, #0xc0
   3b934:	f9405be0 	ldr	x0, [sp, #176]
   3b938:	f9007be0 	str	x0, [sp, #240]
   3b93c:	f94077e1 	ldr	x1, [sp, #232]
   3b940:	3820683f 	strb	wzr, [x1, x0]
   3b944:	f90063f5 	str	x21, [sp, #192]
   3b948:	a94e87e0 	ldp	x0, x1, [sp, #232]
   3b94c:	97ffe445 	bl	34a60 <fmt::v8::vformat[abi:cxx11](fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3b950:	a9508be1 	ldp	x1, x2, [sp, #264]
   3b954:	aa1303e0 	mov	x0, x19
   3b958:	97ffdff2 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3b95c:	f94087e0 	ldr	x0, [sp, #264]
   3b960:	910042d6 	add	x22, x22, #0x10
   3b964:	eb16001f 	cmp	x0, x22
   3b968:	54000040 	b.eq	3b970 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xa88>  // b.none
   3b96c:	97ffdef9 	bl	33550 <operator delete(void*)@plt>
   3b970:	f94077e0 	ldr	x0, [sp, #232]
   3b974:	910042f7 	add	x23, x23, #0x10
   3b978:	eb17001f 	cmp	x0, x23
   3b97c:	54000040 	b.eq	3b984 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xa9c>  // b.none
   3b980:	97ffdef4 	bl	33550 <operator delete(void*)@plt>
   3b984:	97ffe817 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3b988:	f900033f 	str	xzr, [x25]
   3b98c:	3900233f 	strb	wzr, [x25, #8]
   3b990:	17ffff16 	b	3b5e8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x700>
   3b994:	910022e0 	add	x0, x23, #0x8
   3b998:	885ffc01 	ldaxr	w1, [x0]
   3b99c:	11000421 	add	w1, w1, #0x1
   3b9a0:	8802fc01 	stlxr	w2, w1, [x0]
   3b9a4:	35ffffa2 	cbnz	w2, 3b998 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xab0>
   3b9a8:	17ffff4b 	b	3b6d4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x7ec>
   3b9ac:	91002021 	add	x1, x1, #0x8
   3b9b0:	885ffc20 	ldaxr	w0, [x1]
   3b9b4:	11000400 	add	w0, w0, #0x1
   3b9b8:	8802fc20 	stlxr	w2, w0, [x1]
   3b9bc:	35ffffa2 	cbnz	w2, 3b9b0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xac8>
   3b9c0:	17ffff56 	b	3b718 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x830>
   3b9c4:	aa1703fa 	mov	x26, x23
   3b9c8:	17fffeb6 	b	3b4a0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0x5b8>
   3b9cc:	97ffdb7d 	bl	327c0 <__stack_chk_fail@plt>
   3b9d0:	f94087e1 	ldr	x1, [sp, #264]
   3b9d4:	910042d6 	add	x22, x22, #0x10
   3b9d8:	aa0003f3 	mov	x19, x0
   3b9dc:	eb16003f 	cmp	x1, x22
   3b9e0:	54000060 	b.eq	3b9ec <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb04>  // b.none
   3b9e4:	aa0103e0 	mov	x0, x1
   3b9e8:	97ffdeda 	bl	33550 <operator delete(void*)@plt>
   3b9ec:	f94077e0 	ldr	x0, [sp, #232]
   3b9f0:	910042f7 	add	x23, x23, #0x10
   3b9f4:	eb17001f 	cmp	x0, x23
   3b9f8:	54000281 	b.ne	3ba48 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb60>  // b.any
   3b9fc:	97ffe7f9 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3ba00:	f9404be0 	ldr	x0, [sp, #144]
   3ba04:	b4000080 	cbz	x0, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3ba08:	394263e1 	ldrb	w1, [sp, #152]
   3ba0c:	35000041 	cbnz	w1, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3ba10:	97ffdcc4 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ba14:	f94043e0 	ldr	x0, [sp, #128]
   3ba18:	b4000080 	cbz	x0, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3ba1c:	394223e1 	ldrb	w1, [sp, #136]
   3ba20:	35000041 	cbnz	w1, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3ba24:	97ffdcbf 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ba28:	f9462b80 	ldr	x0, [x28, #3152]
   3ba2c:	b4000060 	cbz	x0, 3ba38 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb50>
   3ba30:	aa1b03e0 	mov	x0, x27
   3ba34:	97ffdcdf 	bl	32db0 <pthread_mutex_unlock@plt>
   3ba38:	aa1303e0 	mov	x0, x19
   3ba3c:	97ffe341 	bl	34740 <_Unwind_Resume@plt>
   3ba40:	aa0003f3 	mov	x19, x0
   3ba44:	17ffffea 	b	3b9ec <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb04>
   3ba48:	97ffdec2 	bl	33550 <operator delete(void*)@plt>
   3ba4c:	17ffffec 	b	3b9fc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb14>
   3ba50:	aa0003f3 	mov	x19, x0
   3ba54:	35fffd7a 	cbnz	w26, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3ba58:	aa1703e0 	mov	x0, x23
   3ba5c:	97ffdcb1 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ba60:	17ffffe8 	b	3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3ba64:	f9405be1 	ldr	x1, [sp, #176]
   3ba68:	aa0003f3 	mov	x19, x0
   3ba6c:	b4fffca1 	cbz	x1, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3ba70:	3942e3e0 	ldrb	w0, [sp, #184]
   3ba74:	35fffc60 	cbnz	w0, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3ba78:	aa0103e0 	mov	x0, x1
   3ba7c:	97ffdca9 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ba80:	17ffffe0 	b	3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3ba84:	aa0003f3 	mov	x19, x0
   3ba88:	17ffffdd 	b	3b9fc <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb14>
   3ba8c:	f9405be1 	ldr	x1, [sp, #176]
   3ba90:	aa0003f3 	mov	x19, x0
   3ba94:	b40000a1 	cbz	x1, 3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3ba98:	3942e3e0 	ldrb	w0, [sp, #184]
   3ba9c:	35000060 	cbnz	w0, 3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3baa0:	aa0103e0 	mov	x0, x1
   3baa4:	97ffdc9f 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3baa8:	f94053e0 	ldr	x0, [sp, #160]
   3baac:	b4fffaa0 	cbz	x0, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bab0:	3942a3e1 	ldrb	w1, [sp, #168]
   3bab4:	35fffa61 	cbnz	w1, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bab8:	97ffdc9a 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3babc:	17ffffd1 	b	3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bac0:	aa0003f3 	mov	x19, x0
   3bac4:	17fffff9 	b	3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3bac8:	f94053e1 	ldr	x1, [sp, #160]
   3bacc:	aa0003f3 	mov	x19, x0
   3bad0:	b4fff981 	cbz	x1, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bad4:	3942a3e0 	ldrb	w0, [sp, #168]
   3bad8:	35fff940 	cbnz	w0, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3badc:	aa0103e0 	mov	x0, x1
   3bae0:	17ffffe7 	b	3ba7c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb94>
   3bae4:	17ffffe0 	b	3ba64 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb7c>
   3bae8:	aa0003f3 	mov	x19, x0
   3baec:	17ffffc5 	b	3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3baf0:	aa0003f3 	mov	x19, x0
   3baf4:	17ffffcd 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3baf8:	17ffffdb 	b	3ba64 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb7c>
   3bafc:	aa0003f3 	mov	x19, x0
   3bb00:	97ffe7b8 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3bb04:	17ffffc9 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bb08:	f9408fe3 	ldr	x3, [sp, #280]
   3bb0c:	aa0003f3 	mov	x19, x0
   3bb10:	b40000a3 	cbz	x3, 3bb24 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xc3c>
   3bb14:	aa1603e1 	mov	x1, x22
   3bb18:	aa1603e0 	mov	x0, x22
   3bb1c:	52800062 	mov	w2, #0x3                   	// #3
   3bb20:	d63f0060 	blr	x3
   3bb24:	f94053e0 	ldr	x0, [sp, #160]
   3bb28:	b4fff760 	cbz	x0, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bb2c:	3942a3e1 	ldrb	w1, [sp, #168]
   3bb30:	35fff721 	cbnz	w1, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bb34:	97ffdc7b 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bb38:	17ffffb7 	b	3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bb3c:	f9408fe3 	ldr	x3, [sp, #280]
   3bb40:	aa0003f3 	mov	x19, x0
   3bb44:	b4fffb23 	cbz	x3, 3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3bb48:	aa1603e1 	mov	x1, x22
   3bb4c:	aa1603e0 	mov	x0, x22
   3bb50:	52800062 	mov	w2, #0x3                   	// #3
   3bb54:	d63f0060 	blr	x3
   3bb58:	17ffffd4 	b	3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3bb5c:	f9408fe3 	ldr	x3, [sp, #280]
   3bb60:	aa0003f3 	mov	x19, x0
   3bb64:	b4fffa23 	cbz	x3, 3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3bb68:	aa1603e1 	mov	x1, x22
   3bb6c:	aa1603e0 	mov	x0, x22
   3bb70:	52800062 	mov	w2, #0x3                   	// #3
   3bb74:	d63f0060 	blr	x3
   3bb78:	17ffffcc 	b	3baa8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xbc0>
   3bb7c:	aa0003f3 	mov	x19, x0
   3bb80:	35fff418 	cbnz	w24, 3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bb84:	aa1603e0 	mov	x0, x22
   3bb88:	97ffdc66 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bb8c:	17ffff9d 	b	3ba00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb18>
   3bb90:	f9405be1 	ldr	x1, [sp, #176]
   3bb94:	aa0003f3 	mov	x19, x0
   3bb98:	b4fff3e1 	cbz	x1, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bb9c:	3942e3e0 	ldrb	w0, [sp, #184]
   3bba0:	35fff3a0 	cbnz	w0, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bba4:	aa0103e0 	mov	x0, x1
   3bba8:	97ffdc5e 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bbac:	17ffff9a 	b	3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bbb0:	17fffff8 	b	3bb90 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xca8>
   3bbb4:	f94087e1 	ldr	x1, [sp, #264]
   3bbb8:	910042d6 	add	x22, x22, #0x10
   3bbbc:	aa0003f3 	mov	x19, x0
   3bbc0:	eb16003f 	cmp	x1, x22
   3bbc4:	54000060 	b.eq	3bbd0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xce8>  // b.none
   3bbc8:	aa0103e0 	mov	x0, x1
   3bbcc:	97ffde61 	bl	33550 <operator delete(void*)@plt>
   3bbd0:	f94077e0 	ldr	x0, [sp, #232]
   3bbd4:	910042f7 	add	x23, x23, #0x10
   3bbd8:	eb17001f 	cmp	x0, x23
   3bbdc:	54fff920 	b.eq	3bb00 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xc18>  // b.none
   3bbe0:	97ffde5c 	bl	33550 <operator delete(void*)@plt>
   3bbe4:	97ffe77f 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3bbe8:	17ffff90 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bbec:	aa0003f3 	mov	x19, x0
   3bbf0:	35fff13a 	cbnz	w26, 3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bbf4:	aa1603e0 	mov	x0, x22
   3bbf8:	97ffdc4a 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bbfc:	17ffff86 	b	3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bc00:	aa0003f3 	mov	x19, x0
   3bc04:	17fffff3 	b	3bbd0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xce8>
   3bc08:	f9408fe3 	ldr	x3, [sp, #280]
   3bc0c:	aa0003f3 	mov	x19, x0
   3bc10:	b40000a3 	cbz	x3, 3bc24 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xd3c>
   3bc14:	aa1603e1 	mov	x1, x22
   3bc18:	aa1603e0 	mov	x0, x22
   3bc1c:	52800062 	mov	w2, #0x3                   	// #3
   3bc20:	d63f0060 	blr	x3
   3bc24:	f9405be0 	ldr	x0, [sp, #176]
   3bc28:	b4fff000 	cbz	x0, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc2c:	3942e3e1 	ldrb	w1, [sp, #184]
   3bc30:	35ffefc1 	cbnz	w1, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc34:	97ffdc3b 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bc38:	17ffff7c 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc3c:	aa0003f3 	mov	x19, x0
   3bc40:	3500035a 	cbnz	w26, 3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bc44:	aa1603e0 	mov	x0, x22
   3bc48:	97ffdc36 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bc4c:	14000017 	b	3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bc50:	aa0003f3 	mov	x19, x0
   3bc54:	17ffff70 	b	3ba14 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb2c>
   3bc58:	f9405be1 	ldr	x1, [sp, #176]
   3bc5c:	aa0003f3 	mov	x19, x0
   3bc60:	b4ffee41 	cbz	x1, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc64:	3942e3e0 	ldrb	w0, [sp, #184]
   3bc68:	35ffee00 	cbnz	w0, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc6c:	aa0103e0 	mov	x0, x1
   3bc70:	97ffdc2c 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bc74:	17ffff6d 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bc78:	f9408fe3 	ldr	x3, [sp, #280]
   3bc7c:	aa0003f3 	mov	x19, x0
   3bc80:	b40000a3 	cbz	x3, 3bc94 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdac>
   3bc84:	aa1603e1 	mov	x1, x22
   3bc88:	aa1603e0 	mov	x0, x22
   3bc8c:	52800062 	mov	w2, #0x3                   	// #3
   3bc90:	d63f0060 	blr	x3
   3bc94:	f94053e0 	ldr	x0, [sp, #160]
   3bc98:	b4000080 	cbz	x0, 3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bc9c:	3942a3e1 	ldrb	w1, [sp, #168]
   3bca0:	35000041 	cbnz	w1, 3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bca4:	97ffdc1f 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bca8:	f9404be0 	ldr	x0, [sp, #144]
   3bcac:	b4ffebe0 	cbz	x0, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bcb0:	394263e1 	ldrb	w1, [sp, #152]
   3bcb4:	35ffeba1 	cbnz	w1, 3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bcb8:	97ffdc1a 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3bcbc:	17ffff5b 	b	3ba28 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xb40>
   3bcc0:	17ffffb4 	b	3bb90 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xca8>
   3bcc4:	f9405be1 	ldr	x1, [sp, #176]
   3bcc8:	aa0003f3 	mov	x19, x0
   3bccc:	b4fffee1 	cbz	x1, 3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bcd0:	3942e3e0 	ldrb	w0, [sp, #184]
   3bcd4:	35fffea0 	cbnz	w0, 3bca8 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdc0>
   3bcd8:	aa0103e0 	mov	x0, x1
   3bcdc:	17fffff2 	b	3bca4 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xdbc>
   3bce0:	17ffffde 	b	3bc58 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)+0xd70>
   3bce4:	d503201f 	nop

000000000003bce8 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)>:
   3bce8:	d11003ff 	sub	sp, sp, #0x400
   3bcec:	a9007bfd 	stp	x29, x30, [sp]
   3bcf0:	910003fd 	mov	x29, sp
   3bcf4:	a90153f3 	stp	x19, x20, [sp, #16]
   3bcf8:	900004d3 	adrp	x19, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3bcfc:	aa0103f4 	mov	x20, x1
   3bd00:	f9451661 	ldr	x1, [x19, #2600]
   3bd04:	a9025bf5 	stp	x21, x22, [sp, #32]
   3bd08:	aa0003f5 	mov	x21, x0
   3bd0c:	f9400022 	ldr	x2, [x1]
   3bd10:	f901ffe2 	str	x2, [sp, #1016]
   3bd14:	d2800002 	mov	x2, #0x0                   	// #0
   3bd18:	f9001bf7 	str	x23, [sp, #48]
   3bd1c:	97ffe345 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3bd20:	2a0003f6 	mov	w22, w0
   3bd24:	aa1403e0 	mov	x0, x20
   3bd28:	97ffe342 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3bd2c:	6b0002df 	cmp	w22, w0
   3bd30:	54000320 	b.eq	3bd94 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0xac>  // b.none
   3bd34:	52856081 	mov	w1, #0x2b04                	// #11012
   3bd38:	52801120 	mov	w0, #0x89                  	// #137
   3bd3c:	97ffe745 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3bd40:	97ffd9ac 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3bd44:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3bd48:	aa0003f6 	mov	x22, x0
   3bd4c:	912f8021 	add	x1, x1, #0xbe0
   3bd50:	d2800682 	mov	x2, #0x34                  	// #52
   3bd54:	97ffdef3 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3bd58:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3bd5c:	aa1603e0 	mov	x0, x22
   3bd60:	91306021 	add	x1, x1, #0xc18
   3bd64:	d2800402 	mov	x2, #0x20                  	// #32
   3bd68:	97ffdeee 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3bd6c:	97ffd9a1 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3bd70:	910783f6 	add	x22, sp, #0x1e0
   3bd74:	aa1603e8 	mov	x8, x22
   3bd78:	97ffdc92 	bl	32fc0 <icraft::detail::LogExcept::Entry::finalize()@plt>
   3bd7c:	900004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3bd80:	aa1603e0 	mov	x0, x22
   3bd84:	f9453021 	ldr	x1, [x1, #2656]
   3bd88:	91004021 	add	x1, x1, #0x10
   3bd8c:	f900f3e1 	str	x1, [sp, #480]
   3bd90:	97ffdeb8 	bl	33870 <std::runtime_error::~runtime_error()@plt>
   3bd94:	aa1503e0 	mov	x0, x21
   3bd98:	97ffe326 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3bd9c:	7100041f 	cmp	w0, #0x1
   3bda0:	54000e80 	b.eq	3bf70 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x288>  // b.none
   3bda4:	721e781f 	tst	w0, #0xfffffffd
   3bda8:	54000bc0 	b.eq	3bf20 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x238>  // b.none
   3bdac:	910183f4 	add	x20, sp, #0x60
   3bdb0:	900004d6 	adrp	x22, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3bdb4:	9101c280 	add	x0, x20, #0x70
   3bdb8:	97ffda3a 	bl	326a0 <std::ios_base::ios_base()@plt>
   3bdbc:	900004c0 	adrp	x0, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3bdc0:	910803e3 	add	x3, sp, #0x200
   3bdc4:	4f000400 	movi	v0.4s, #0x0
   3bdc8:	790363ff 	strh	wzr, [sp, #432]
   3bdcc:	f9467000 	ldr	x0, [x0, #3296]
   3bdd0:	d2800001 	mov	x1, #0x0                   	// #0
   3bdd4:	f944a6c2 	ldr	x2, [x22, #2376]
   3bdd8:	3c9b8060 	stur	q0, [x3, #-72]
   3bddc:	a940dc15 	ldp	x21, x23, [x0, #8]
   3bde0:	3c9c8060 	stur	q0, [x3, #-56]
   3bde4:	91004042 	add	x2, x2, #0x10
   3bde8:	f85e82a3 	ldur	x3, [x21, #-24]
   3bdec:	f90033f5 	str	x21, [sp, #96]
   3bdf0:	f9006be2 	str	x2, [sp, #208]
   3bdf4:	f900d7ff 	str	xzr, [sp, #424]
   3bdf8:	8b030280 	add	x0, x20, x3
   3bdfc:	f8236a97 	str	x23, [x20, x3]
   3be00:	97ffdfe4 	bl	33d90 <std::basic_ios<char, std::char_traits<char> >::init(std::basic_streambuf<char, std::char_traits<char> >*)@plt>
   3be04:	900004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3be08:	900004c2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3be0c:	91010280 	add	x0, x20, #0x40
   3be10:	a9077fff 	stp	xzr, xzr, [sp, #112]
   3be14:	f9465421 	ldr	x1, [x1, #3240]
   3be18:	a9087fff 	stp	xzr, xzr, [sp, #128]
   3be1c:	f945a842 	ldr	x2, [x2, #2896]
   3be20:	91006023 	add	x3, x1, #0x18
   3be24:	91010021 	add	x1, x1, #0x40
   3be28:	a9097fff 	stp	xzr, xzr, [sp, #144]
   3be2c:	91004042 	add	x2, x2, #0x10
   3be30:	a9060be3 	stp	x3, x2, [sp, #96]
   3be34:	f9006be1 	str	x1, [sp, #208]
   3be38:	97ffe382 	bl	34c40 <std::locale::locale()@plt>
   3be3c:	900004c2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3be40:	91018283 	add	x3, x20, #0x60
   3be44:	52800204 	mov	w4, #0x10                  	// #16
   3be48:	91002281 	add	x1, x20, #0x8
   3be4c:	f947e842 	ldr	x2, [x2, #4048]
   3be50:	9101c280 	add	x0, x20, #0x70
   3be54:	b900abe4 	str	w4, [sp, #168]
   3be58:	91004042 	add	x2, x2, #0x10
   3be5c:	f90037e2 	str	x2, [sp, #104]
   3be60:	f9005be3 	str	x3, [sp, #176]
   3be64:	f9005fff 	str	xzr, [sp, #184]
   3be68:	390303ff 	strb	wzr, [sp, #192]
   3be6c:	97ffdfc9 	bl	33d90 <std::basic_ios<char, std::char_traits<char> >::init(std::basic_streambuf<char, std::char_traits<char> >*)@plt>
   3be70:	900004d5 	adrp	x21, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3be74:	900004c6 	adrp	x6, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3be78:	910783f6 	add	x22, sp, #0x1e0
   3be7c:	d2803e88 	mov	x8, #0x1f4                 	// #500
   3be80:	f944eea7 	ldr	x7, [x21, #2520]
   3be84:	910082c9 	add	x9, x22, #0x20
   3be88:	f94678c6 	ldr	x6, [x6, #3312]
   3be8c:	910040e7 	add	x7, x7, #0x10
   3be90:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3be94:	aa1603e0 	mov	x0, x22
   3be98:	91310021 	add	x1, x1, #0xc40
   3be9c:	910103e4 	add	x4, sp, #0x40
   3bea0:	d2800005 	mov	x5, #0x0                   	// #0
   3bea4:	d2800003 	mov	x3, #0x0                   	// #0
   3bea8:	d28000a2 	mov	x2, #0x5                   	// #5
   3beac:	a9047fff 	stp	xzr, xzr, [sp, #64]
   3beb0:	a91e27e7 	stp	x7, x9, [sp, #480]
   3beb4:	a91f23ff 	stp	xzr, x8, [sp, #496]
   3beb8:	f94000d7 	ldr	x23, [x6]
   3bebc:	97ffe259 	bl	34820 <void fmt::v8::detail::vformat_to<char>(fmt::v8::detail::buffer<char>&, fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<std::conditional<std::is_same<fmt::v8::type_identity<char>::type, char>::value, fmt::v8::appender, std::back_insert_iterator<fmt::v8::detail::buffer<fmt::v8::type_identity<char>::type> > >::type, fmt::v8::type_identity<char>::type> >, fmt::v8::detail::locale_ref)@plt>
   3bec0:	aa1703e3 	mov	x3, x23
   3bec4:	d2800021 	mov	x1, #0x1                   	// #1
   3bec8:	a95edfe0 	ldp	x0, x23, [sp, #488]
   3becc:	aa1703e2 	mov	x2, x23
   3bed0:	97ffe214 	bl	34720 <fwrite@plt>
   3bed4:	eb0002ff 	cmp	x23, x0
   3bed8:	54000908 	b.hi	3bff8 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x310>  // b.pmore
   3bedc:	f944eeb5 	ldr	x21, [x21, #2520]
   3bee0:	910082c1 	add	x1, x22, #0x20
   3bee4:	f940f7e0 	ldr	x0, [sp, #488]
   3bee8:	910042b5 	add	x21, x21, #0x10
   3beec:	f900f3f5 	str	x21, [sp, #480]
   3bef0:	eb01001f 	cmp	x0, x1
   3bef4:	54000040 	b.eq	3befc <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x214>  // b.none
   3bef8:	97ffdd96 	bl	33550 <operator delete(void*)@plt>
   3befc:	b0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3bf00:	aa1403e0 	mov	x0, x20
   3bf04:	9137c021 	add	x1, x1, #0xdf0
   3bf08:	d28003a2 	mov	x2, #0x1d                  	// #29
   3bf0c:	97ffde85 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3bf10:	aa1403e0 	mov	x0, x20
   3bf14:	97ffdf6b 	bl	33cc0 <icraft::detail::LogMsg<(icraft::LogLevel)4>::~LogMsg()@plt>
   3bf18:	52800000 	mov	w0, #0x0                   	// #0
   3bf1c:	14000009 	b	3bf40 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x258>
   3bf20:	aa1503e0 	mov	x0, x21
   3bf24:	97ffe0c3 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3bf28:	aa0003e1 	mov	x1, x0
   3bf2c:	aa1403e0 	mov	x0, x20
   3bf30:	aa0103f4 	mov	x20, x1
   3bf34:	97ffe0bf 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3bf38:	eb00029f 	cmp	x20, x0
   3bf3c:	1a9f37e0 	cset	w0, cs  // cs = hs, nlast
   3bf40:	f9451673 	ldr	x19, [x19, #2600]
   3bf44:	f941ffe1 	ldr	x1, [sp, #1016]
   3bf48:	f9400262 	ldr	x2, [x19]
   3bf4c:	eb020021 	subs	x1, x1, x2
   3bf50:	d2800002 	mov	x2, #0x0                   	// #0
   3bf54:	54000201 	b.ne	3bf94 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x2ac>  // b.any
   3bf58:	a9407bfd 	ldp	x29, x30, [sp]
   3bf5c:	a94153f3 	ldp	x19, x20, [sp, #16]
   3bf60:	a9425bf5 	ldp	x21, x22, [sp, #32]
   3bf64:	f9401bf7 	ldr	x23, [sp, #48]
   3bf68:	911003ff 	add	sp, sp, #0x400
   3bf6c:	d65f03c0 	ret
   3bf70:	aa1503e0 	mov	x0, x21
   3bf74:	97ffd8f7 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3bf78:	aa0003e1 	mov	x1, x0
   3bf7c:	aa1403e0 	mov	x0, x20
   3bf80:	aa0103f4 	mov	x20, x1
   3bf84:	97ffd8f3 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3bf88:	eb00029f 	cmp	x20, x0
   3bf8c:	1a9f37e0 	cset	w0, cs  // cs = hs, nlast
   3bf90:	17ffffec 	b	3bf40 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x258>
   3bf94:	97ffda0b 	bl	327c0 <__stack_chk_fail@plt>
   3bf98:	aa0003f3 	mov	x19, x0
   3bf9c:	97ffe691 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3bfa0:	aa1303e0 	mov	x0, x19
   3bfa4:	97ffe1e7 	bl	34740 <_Unwind_Resume@plt>
   3bfa8:	aa0003f3 	mov	x19, x0
   3bfac:	14000029 	b	3c050 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x368>
   3bfb0:	aa0003f3 	mov	x19, x0
   3bfb4:	aa1403e0 	mov	x0, x20
   3bfb8:	97ffdf42 	bl	33cc0 <icraft::detail::LogMsg<(icraft::LogLevel)4>::~LogMsg()@plt>
   3bfbc:	aa1303e0 	mov	x0, x19
   3bfc0:	97ffe1e0 	bl	34740 <_Unwind_Resume@plt>
   3bfc4:	aa0003f3 	mov	x19, x0
   3bfc8:	91002280 	add	x0, x20, #0x8
   3bfcc:	97ffe13d 	bl	344c0 <std::__cxx11::basic_stringbuf<char, std::char_traits<char>, std::allocator<char> >::~basic_stringbuf()@plt>
   3bfd0:	f85e82a0 	ldur	x0, [x21, #-24]
   3bfd4:	f90033f5 	str	x21, [sp, #96]
   3bfd8:	f8206a97 	str	x23, [x20, x0]
   3bfdc:	f944a6c1 	ldr	x1, [x22, #2376]
   3bfe0:	9101c280 	add	x0, x20, #0x70
   3bfe4:	91004021 	add	x1, x1, #0x10
   3bfe8:	f9006be1 	str	x1, [sp, #208]
   3bfec:	97ffd9e9 	bl	32790 <std::ios_base::~ios_base()@plt>
   3bff0:	aa1303e0 	mov	x0, x19
   3bff4:	97ffe1d3 	bl	34740 <_Unwind_Resume@plt>
   3bff8:	d2800400 	mov	x0, #0x20                  	// #32
   3bffc:	97ffdae1 	bl	32b80 <__cxa_allocate_exception@plt>
   3c000:	aa0003f7 	mov	x23, x0
   3c004:	97ffdf1b 	bl	33c70 <__errno_location@plt>
   3c008:	b9400000 	ldr	w0, [x0]
   3c00c:	90000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3c010:	aa1703e8 	mov	x8, x23
   3c014:	91312021 	add	x1, x1, #0xc48
   3c018:	910143e4 	add	x4, sp, #0x50
   3c01c:	d2800003 	mov	x3, #0x0                   	// #0
   3c020:	d2800282 	mov	x2, #0x14                  	// #20
   3c024:	a9057fff 	stp	xzr, xzr, [sp, #80]
   3c028:	97ffe012 	bl	34070 <fmt::v8::vsystem_error(int, fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3c02c:	f00004a2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3c030:	f00004a1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3c034:	aa1703e0 	mov	x0, x23
   3c038:	f9466c42 	ldr	x2, [x2, #3288]
   3c03c:	f944bc21 	ldr	x1, [x1, #2424]
   3c040:	97ffe17c 	bl	34630 <__cxa_throw@plt>
   3c044:	aa0003f3 	mov	x19, x0
   3c048:	aa1703e0 	mov	x0, x23
   3c04c:	97ffdc25 	bl	330e0 <__cxa_free_exception@plt>
   3c050:	f944eea2 	ldr	x2, [x21, #2520]
   3c054:	910082c1 	add	x1, x22, #0x20
   3c058:	f940f7e0 	ldr	x0, [sp, #488]
   3c05c:	91004042 	add	x2, x2, #0x10
   3c060:	f900f3e2 	str	x2, [sp, #480]
   3c064:	eb01001f 	cmp	x0, x1
   3c068:	54000040 	b.eq	3c070 <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x388>  // b.none
   3c06c:	97ffdd39 	bl	33550 <operator delete(void*)@plt>
   3c070:	aa1403e0 	mov	x0, x20
   3c074:	97ffd943 	bl	32580 <std::__cxx11::basic_ostringstream<char, std::char_traits<char>, std::allocator<char> >::~basic_ostringstream()@plt>
   3c078:	aa1303e0 	mov	x0, x19
   3c07c:	97ffe1b1 	bl	34740 <_Unwind_Resume@plt>
   3c080:	aa0003f3 	mov	x19, x0
   3c084:	17ffffd6 	b	3bfdc <icraft::xrt::operator>=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x2f4>
