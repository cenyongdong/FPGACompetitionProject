
/usr/lib/aarch64-linux-gnu/libicraft_xrt.so:     file format elf64-littleaarch64


Disassembly of section .text:

000000000003a638 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]>:
   3a638:	a9bc7bfd 	stp	x29, x30, [sp, #-64]!
   3a63c:	910003fd 	mov	x29, sp
   3a640:	a9025bf5 	stp	x21, x22, [sp, #32]
   3a644:	b00004d6 	adrp	x22, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3a648:	aa0803f5 	mov	x21, x8
   3a64c:	f94516c2 	ldr	x2, [x22, #2600]
   3a650:	a90153f3 	stp	x19, x20, [sp, #16]
   3a654:	aa0103f4 	mov	x20, x1
   3a658:	f9400041 	ldr	x1, [x2]
   3a65c:	f9001fe1 	str	x1, [sp, #56]
   3a660:	d2800001 	mov	x1, #0x0                   	// #0
   3a664:	aa0003f3 	mov	x19, x0
   3a668:	97ffe8f2 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3a66c:	7100041f 	cmp	w0, #0x1
   3a670:	aa1303e0 	mov	x0, x19
   3a674:	540003e0 	b.eq	3a6f0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]+0xb8>  // b.none
   3a678:	97ffe8ee 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3a67c:	34000220 	cbz	w0, 3a6c0 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]+0x88>
   3a680:	f9400260 	ldr	x0, [x19]
   3a684:	f90002a0 	str	x0, [x21]
   3a688:	39402260 	ldrb	w0, [x19, #8]
   3a68c:	f900027f 	str	xzr, [x19]
   3a690:	390022a0 	strb	w0, [x21, #8]
   3a694:	f94516c0 	ldr	x0, [x22, #2600]
   3a698:	f9401fe1 	ldr	x1, [sp, #56]
   3a69c:	f9400002 	ldr	x2, [x0]
   3a6a0:	eb020021 	subs	x1, x1, x2
   3a6a4:	d2800002 	mov	x2, #0x0                   	// #0
   3a6a8:	540003a1 	b.ne	3a71c <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]+0xe4>  // b.any
   3a6ac:	aa1503e0 	mov	x0, x21
   3a6b0:	a94153f3 	ldp	x19, x20, [sp, #16]
   3a6b4:	a9425bf5 	ldp	x21, x22, [sp, #32]
   3a6b8:	a8c47bfd 	ldp	x29, x30, [sp], #64
   3a6bc:	d65f03c0 	ret
   3a6c0:	aa1303e0 	mov	x0, x19
   3a6c4:	97ffe6db 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3a6c8:	aa0003e2 	mov	x2, x0
   3a6cc:	aa1503e8 	mov	x8, x21
   3a6d0:	aa1303e0 	mov	x0, x19
   3a6d4:	9ad40841 	udiv	x1, x2, x20
   3a6d8:	9b148821 	msub	x1, x1, x20, x2
   3a6dc:	f100003f 	cmp	x1, #0x0
   3a6e0:	cb010294 	sub	x20, x20, x1
   3a6e4:	9a811281 	csel	x1, x20, x1, ne  // ne = any
   3a6e8:	97ffe906 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3a6ec:	17ffffea 	b	3a694 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]+0x5c>
   3a6f0:	97ffdf18 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3a6f4:	aa0003e1 	mov	x1, x0
   3a6f8:	aa1503e8 	mov	x8, x21
   3a6fc:	aa1303e0 	mov	x0, x19
   3a700:	9ad40822 	udiv	x2, x1, x20
   3a704:	9b148442 	msub	x2, x2, x20, x1
   3a708:	f100005f 	cmp	x2, #0x0
   3a70c:	cb020281 	sub	x1, x20, x2
   3a710:	9a821021 	csel	x1, x1, x2, ne  // ne = any
   3a714:	97ffe8fb 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3a718:	17ffffdf 	b	3a694 <icraft::xrt::DefaultMemManagerNode::malloc(unsigned long, bool, unsigned long)::{lambda(icraft::xrt::MemPtr, unsigned long)#1}::operator()(icraft::xrt::MemPtr, unsigned long) const [clone .isra.0]+0x5c>
   3a71c:	97ffe029 	bl	327c0 <__stack_chk_fail@plt>

000000000003a720 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const>:
   3a720:	a9b07bfd 	stp	x29, x30, [sp, #-256]!
   3a724:	910003fd 	mov	x29, sp
   3a728:	a90363f7 	stp	x23, x24, [sp, #48]
   3a72c:	b00004d8 	adrp	x24, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3a730:	aa0003f7 	mov	x23, x0
   3a734:	f9451705 	ldr	x5, [x24, #2600]
   3a738:	a9025bf5 	stp	x21, x22, [sp, #32]
   3a73c:	aa0103f6 	mov	x22, x1
   3a740:	f94000a1 	ldr	x1, [x5]
   3a744:	f9007fe1 	str	x1, [sp, #248]
   3a748:	d2800001 	mov	x1, #0x0                   	// #0
   3a74c:	aa0303f5 	mov	x21, x3
   3a750:	a90153f3 	stp	x19, x20, [sp, #16]
   3a754:	aa0403f3 	mov	x19, x4
   3a758:	aa0203f4 	mov	x20, x2
   3a75c:	a9046bf9 	stp	x25, x26, [sp, #64]
   3a760:	97ffe87c 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a764:	8b1302c1 	add	x1, x22, x19
   3a768:	f9401000 	ldr	x0, [x0, #32]
   3a76c:	eb00003f 	cmp	x1, x0
   3a770:	54001068 	b.hi	3a97c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x25c>  // b.pmore
   3a774:	aa1403e0 	mov	x0, x20
   3a778:	97ffe876 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a77c:	f9401000 	ldr	x0, [x0, #32]
   3a780:	8b150261 	add	x1, x19, x21
   3a784:	eb00003f 	cmp	x1, x0
   3a788:	54000888 	b.hi	3a898 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x178>  // b.pmore
   3a78c:	aa1703e0 	mov	x0, x23
   3a790:	97ffe870 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a794:	910183fa 	add	x26, sp, #0x60
   3a798:	9100a019 	add	x25, x0, #0x28
   3a79c:	aa1703e0 	mov	x0, x23
   3a7a0:	97ffe86c 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a7a4:	aa1603e1 	mov	x1, x22
   3a7a8:	aa1a03e8 	mov	x8, x26
   3a7ac:	91004000 	add	x0, x0, #0x10
   3a7b0:	97ffe8d4 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3a7b4:	aa1403e0 	mov	x0, x20
   3a7b8:	97ffe866 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a7bc:	aa0003e1 	mov	x1, x0
   3a7c0:	aa1403e0 	mov	x0, x20
   3a7c4:	9100a034 	add	x20, x1, #0x28
   3a7c8:	97ffe862 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a7cc:	9101c3f6 	add	x22, sp, #0x70
   3a7d0:	91004000 	add	x0, x0, #0x10
   3a7d4:	aa1503e1 	mov	x1, x21
   3a7d8:	aa1603e8 	mov	x8, x22
   3a7dc:	97ffe8c9 	bl	34b00 <icraft::xrt::operator+(icraft::xrt::MemPtr const&, unsigned long)@plt>
   3a7e0:	aa1303e4 	mov	x4, x19
   3a7e4:	aa1603e3 	mov	x3, x22
   3a7e8:	aa1403e2 	mov	x2, x20
   3a7ec:	aa1a03e1 	mov	x1, x26
   3a7f0:	aa1903e0 	mov	x0, x25
   3a7f4:	97ffe3cf 	bl	33730 <icraft::xrt::MemRegion::memcpy(icraft::xrt::MemPtr const&, icraft::xrt::MemRegion const&, icraft::xrt::MemPtr const&, unsigned long) const@plt>
   3a7f8:	f9403be0 	ldr	x0, [sp, #112]
   3a7fc:	b4000060 	cbz	x0, 3a808 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xe8>
   3a800:	3941e3e1 	ldrb	w1, [sp, #120]
   3a804:	34000361 	cbz	w1, 3a870 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x150>
   3a808:	f94033e0 	ldr	x0, [sp, #96]
   3a80c:	b4000060 	cbz	x0, 3a818 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xf8>
   3a810:	3941a3e1 	ldrb	w1, [sp, #104]
   3a814:	340001a1 	cbz	w1, 3a848 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x128>
   3a818:	f9451718 	ldr	x24, [x24, #2600]
   3a81c:	f9407fe0 	ldr	x0, [sp, #248]
   3a820:	f9400301 	ldr	x1, [x24]
   3a824:	eb010000 	subs	x0, x0, x1
   3a828:	d2800001 	mov	x1, #0x0                   	// #0
   3a82c:	540011a1 	b.ne	3aa60 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x340>  // b.any
   3a830:	a94153f3 	ldp	x19, x20, [sp, #16]
   3a834:	a9425bf5 	ldp	x21, x22, [sp, #32]
   3a838:	a94363f7 	ldp	x23, x24, [sp, #48]
   3a83c:	a9446bf9 	ldp	x25, x26, [sp, #64]
   3a840:	a8d07bfd 	ldp	x29, x30, [sp], #256
   3a844:	d65f03c0 	ret
   3a848:	91002001 	add	x1, x0, #0x8
   3a84c:	885ffc22 	ldaxr	w2, [x1]
   3a850:	51000442 	sub	w2, w2, #0x1
   3a854:	8803fc22 	stlxr	w3, w2, [x1]
   3a858:	35ffffa3 	cbnz	w3, 3a84c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x12c>
   3a85c:	35fffde2 	cbnz	w2, 3a818 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xf8>
   3a860:	f9400001 	ldr	x1, [x0]
   3a864:	f9400821 	ldr	x1, [x1, #16]
   3a868:	d63f0020 	blr	x1
   3a86c:	17ffffeb 	b	3a818 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xf8>
   3a870:	91002001 	add	x1, x0, #0x8
   3a874:	885ffc22 	ldaxr	w2, [x1]
   3a878:	51000442 	sub	w2, w2, #0x1
   3a87c:	8803fc22 	stlxr	w3, w2, [x1]
   3a880:	35ffffa3 	cbnz	w3, 3a874 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x154>
   3a884:	35fffc22 	cbnz	w2, 3a808 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xe8>
   3a888:	f9400001 	ldr	x1, [x0]
   3a88c:	f9400821 	ldr	x1, [x1, #16]
   3a890:	d63f0020 	blr	x1
   3a894:	17ffffdd 	b	3a808 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0xe8>
   3a898:	52855f61 	mov	w1, #0x2afb                	// #11003
   3a89c:	528025e0 	mov	w0, #0x12f                 	// #303
   3a8a0:	a90573fb 	stp	x27, x28, [sp, #80]
   3a8a4:	97ffec6b 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3a8a8:	97ffded2 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3a8ac:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a8b0:	aa0003fc 	mov	x28, x0
   3a8b4:	91328021 	add	x1, x1, #0xca0
   3a8b8:	d2800802 	mov	x2, #0x40                  	// #64
   3a8bc:	97ffe419 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3a8c0:	910203f9 	add	x25, sp, #0x80
   3a8c4:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a8c8:	91004324 	add	x4, x25, #0x10
   3a8cc:	d0000342 	adrp	x2, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a8d0:	aa1903e0 	mov	x0, x25
   3a8d4:	9133a021 	add	x1, x1, #0xce8
   3a8d8:	9134c842 	add	x2, x2, #0xd32
   3a8dc:	52800003 	mov	w3, #0x0                   	// #0
   3a8e0:	f90043e4 	str	x4, [sp, #128]
   3a8e4:	97ffe017 	bl	32940 <void std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >::_M_construct<char const*>(char const*, char const*, std::forward_iterator_tag)@plt>
   3a8e8:	aa1403e0 	mov	x0, x20
   3a8ec:	97ffe819 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a8f0:	f9401004 	ldr	x4, [x0, #32]
   3a8f4:	910303fb 	add	x27, sp, #0xc0
   3a8f8:	a94807e0 	ldp	x0, x1, [sp, #128]
   3a8fc:	910283fa 	add	x26, sp, #0xa0
   3a900:	aa1b03e3 	mov	x3, x27
   3a904:	aa1a03e8 	mov	x8, x26
   3a908:	d2808882 	mov	x2, #0x444                 	// #1092
   3a90c:	f90063f5 	str	x21, [sp, #192]
   3a910:	f9006bf3 	str	x19, [sp, #208]
   3a914:	f90073e4 	str	x4, [sp, #224]
   3a918:	97ffe852 	bl	34a60 <fmt::v8::vformat[abi:cxx11](fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3a91c:	a94a0be1 	ldp	x1, x2, [sp, #160]
   3a920:	aa1c03e0 	mov	x0, x28
   3a924:	97ffe3ff 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3a928:	f94053e0 	ldr	x0, [sp, #160]
   3a92c:	9100435a 	add	x26, x26, #0x10
   3a930:	eb1a001f 	cmp	x0, x26
   3a934:	54000040 	b.eq	3a93c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x21c>  // b.none
   3a938:	97ffe306 	bl	33550 <operator delete(void*)@plt>
   3a93c:	f94043e0 	ldr	x0, [sp, #128]
   3a940:	91004339 	add	x25, x25, #0x10
   3a944:	eb19001f 	cmp	x0, x25
   3a948:	54000040 	b.eq	3a950 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x230>  // b.none
   3a94c:	97ffe301 	bl	33550 <operator delete(void*)@plt>
   3a950:	97ffdea8 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3a954:	aa1b03e8 	mov	x8, x27
   3a958:	97ffe19a 	bl	32fc0 <icraft::detail::LogExcept::Entry::finalize()@plt>
   3a95c:	b00004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3a960:	aa1b03e0 	mov	x0, x27
   3a964:	f9453021 	ldr	x1, [x1, #2656]
   3a968:	91004021 	add	x1, x1, #0x10
   3a96c:	f90063e1 	str	x1, [sp, #192]
   3a970:	97ffe3c0 	bl	33870 <std::runtime_error::~runtime_error()@plt>
   3a974:	a94573fb 	ldp	x27, x28, [sp, #80]
   3a978:	17ffff85 	b	3a78c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x6c>
   3a97c:	52855f61 	mov	w1, #0x2afb                	// #11003
   3a980:	528025e0 	mov	w0, #0x12f                 	// #303
   3a984:	a90573fb 	stp	x27, x28, [sp, #80]
   3a988:	97ffec32 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3a98c:	97ffde99 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3a990:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a994:	aa0003fc 	mov	x28, x0
   3a998:	91328021 	add	x1, x1, #0xca0
   3a99c:	d2800802 	mov	x2, #0x40                  	// #64
   3a9a0:	97ffe3e0 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3a9a4:	910203f9 	add	x25, sp, #0x80
   3a9a8:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a9ac:	91004324 	add	x4, x25, #0x10
   3a9b0:	d0000342 	adrp	x2, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3a9b4:	aa1903e0 	mov	x0, x25
   3a9b8:	9133a021 	add	x1, x1, #0xce8
   3a9bc:	9134c842 	add	x2, x2, #0xd32
   3a9c0:	52800003 	mov	w3, #0x0                   	// #0
   3a9c4:	f90043e4 	str	x4, [sp, #128]
   3a9c8:	97ffdfde 	bl	32940 <void std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >::_M_construct<char const*>(char const*, char const*, std::forward_iterator_tag)@plt>
   3a9cc:	aa1703e0 	mov	x0, x23
   3a9d0:	97ffe7e0 	bl	34950 <icraft::xir::ObjectRef::get() const@plt>
   3a9d4:	f9401004 	ldr	x4, [x0, #32]
   3a9d8:	910303fb 	add	x27, sp, #0xc0
   3a9dc:	a94807e0 	ldp	x0, x1, [sp, #128]
   3a9e0:	910283fa 	add	x26, sp, #0xa0
   3a9e4:	aa1b03e3 	mov	x3, x27
   3a9e8:	aa1a03e8 	mov	x8, x26
   3a9ec:	d2808882 	mov	x2, #0x444                 	// #1092
   3a9f0:	f90063f6 	str	x22, [sp, #192]
   3a9f4:	f9006bf3 	str	x19, [sp, #208]
   3a9f8:	f90073e4 	str	x4, [sp, #224]
   3a9fc:	97ffe819 	bl	34a60 <fmt::v8::vformat[abi:cxx11](fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3aa00:	a94a0be1 	ldp	x1, x2, [sp, #160]
   3aa04:	aa1c03e0 	mov	x0, x28
   3aa08:	97ffe3c6 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3aa0c:	f94053e0 	ldr	x0, [sp, #160]
   3aa10:	9100435a 	add	x26, x26, #0x10
   3aa14:	eb1a001f 	cmp	x0, x26
   3aa18:	54000040 	b.eq	3aa20 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x300>  // b.none
   3aa1c:	97ffe2cd 	bl	33550 <operator delete(void*)@plt>
   3aa20:	f94043e0 	ldr	x0, [sp, #128]
   3aa24:	91004339 	add	x25, x25, #0x10
   3aa28:	eb19001f 	cmp	x0, x25
   3aa2c:	54000040 	b.eq	3aa34 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x314>  // b.none
   3aa30:	97ffe2c8 	bl	33550 <operator delete(void*)@plt>
   3aa34:	97ffde6f 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3aa38:	aa1b03e8 	mov	x8, x27
   3aa3c:	97ffe161 	bl	32fc0 <icraft::detail::LogExcept::Entry::finalize()@plt>
   3aa40:	b00004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3aa44:	aa1b03e0 	mov	x0, x27
   3aa48:	f9453021 	ldr	x1, [x1, #2656]
   3aa4c:	91004021 	add	x1, x1, #0x10
   3aa50:	f90063e1 	str	x1, [sp, #192]
   3aa54:	97ffe387 	bl	33870 <std::runtime_error::~runtime_error()@plt>
   3aa58:	a94573fb 	ldp	x27, x28, [sp, #80]
   3aa5c:	17ffff46 	b	3a774 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x54>
   3aa60:	a90573fb 	stp	x27, x28, [sp, #80]
   3aa64:	97ffdf57 	bl	327c0 <__stack_chk_fail@plt>
   3aa68:	aa0003f3 	mov	x19, x0
   3aa6c:	f94043e0 	ldr	x0, [sp, #128]
   3aa70:	91004339 	add	x25, x25, #0x10
   3aa74:	eb19001f 	cmp	x0, x25
   3aa78:	54000040 	b.eq	3aa80 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x360>  // b.none
   3aa7c:	97ffe2b5 	bl	33550 <operator delete(void*)@plt>
   3aa80:	97ffebd8 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3aa84:	aa1303e0 	mov	x0, x19
   3aa88:	97ffe72e 	bl	34740 <_Unwind_Resume@plt>
   3aa8c:	f94053e1 	ldr	x1, [sp, #160]
   3aa90:	9100435a 	add	x26, x26, #0x10
   3aa94:	aa0003f3 	mov	x19, x0
   3aa98:	eb1a003f 	cmp	x1, x26
   3aa9c:	54fffe80 	b.eq	3aa6c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x34c>  // b.none
   3aaa0:	aa0103e0 	mov	x0, x1
   3aaa4:	97ffe2ab 	bl	33550 <operator delete(void*)@plt>
   3aaa8:	17fffff1 	b	3aa6c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x34c>
   3aaac:	aa0003f3 	mov	x19, x0
   3aab0:	17fffff4 	b	3aa80 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x360>
   3aab4:	f94053e1 	ldr	x1, [sp, #160]
   3aab8:	9100435a 	add	x26, x26, #0x10
   3aabc:	aa0003f3 	mov	x19, x0
   3aac0:	eb1a003f 	cmp	x1, x26
   3aac4:	54000060 	b.eq	3aad0 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3b0>  // b.none
   3aac8:	aa0103e0 	mov	x0, x1
   3aacc:	97ffe2a1 	bl	33550 <operator delete(void*)@plt>
   3aad0:	f94043e0 	ldr	x0, [sp, #128]
   3aad4:	91004339 	add	x25, x25, #0x10
   3aad8:	eb19001f 	cmp	x0, x25
   3aadc:	54000040 	b.eq	3aae4 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3c4>  // b.none
   3aae0:	97ffe29c 	bl	33550 <operator delete(void*)@plt>
   3aae4:	97ffebbf 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3aae8:	aa1303e0 	mov	x0, x19
   3aaec:	97ffe715 	bl	34740 <_Unwind_Resume@plt>
   3aaf0:	aa0003f3 	mov	x19, x0
   3aaf4:	17fffffc 	b	3aae4 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3c4>
   3aaf8:	aa0003f3 	mov	x19, x0
   3aafc:	17fffff5 	b	3aad0 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3b0>
   3ab00:	f9403be1 	ldr	x1, [sp, #112]
   3ab04:	aa0003f3 	mov	x19, x0
   3ab08:	b40000a1 	cbz	x1, 3ab1c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3fc>
   3ab0c:	3941e3e0 	ldrb	w0, [sp, #120]
   3ab10:	35000060 	cbnz	w0, 3ab1c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3fc>
   3ab14:	aa0103e0 	mov	x0, x1
   3ab18:	97ffe082 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ab1c:	f94033e0 	ldr	x0, [sp, #96]
   3ab20:	a90573fb 	stp	x27, x28, [sp, #80]
   3ab24:	b4000080 	cbz	x0, 3ab34 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x414>
   3ab28:	3941a3e1 	ldrb	w1, [sp, #104]
   3ab2c:	35000041 	cbnz	w1, 3ab34 <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x414>
   3ab30:	97ffe07c 	bl	32d20 <icraft::xir::Object::decref()@plt>
   3ab34:	aa1303e0 	mov	x0, x19
   3ab38:	97ffe702 	bl	34740 <_Unwind_Resume@plt>
   3ab3c:	aa0003f3 	mov	x19, x0
   3ab40:	17fffff7 	b	3ab1c <icraft::xrt::MemChunk::copyFrom(unsigned long, icraft::xrt::MemChunk const&, unsigned long, unsigned long) const+0x3fc>
   3ab44:	d503201f 	nop

000000000003ab48 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)>:
   3ab48:	d11003ff 	sub	sp, sp, #0x400
   3ab4c:	a9007bfd 	stp	x29, x30, [sp]
   3ab50:	910003fd 	mov	x29, sp
   3ab54:	a90153f3 	stp	x19, x20, [sp, #16]
   3ab58:	b00004d3 	adrp	x19, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ab5c:	aa0103f4 	mov	x20, x1
   3ab60:	f9451661 	ldr	x1, [x19, #2600]
   3ab64:	a9025bf5 	stp	x21, x22, [sp, #32]
   3ab68:	aa0003f5 	mov	x21, x0
   3ab6c:	f9400022 	ldr	x2, [x1]
   3ab70:	f901ffe2 	str	x2, [sp, #1016]
   3ab74:	d2800002 	mov	x2, #0x0                   	// #0
   3ab78:	f9001bf7 	str	x23, [sp, #48]
   3ab7c:	97ffe7ad 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3ab80:	2a0003f6 	mov	w22, w0
   3ab84:	aa1403e0 	mov	x0, x20
   3ab88:	97ffe7aa 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3ab8c:	6b0002df 	cmp	w22, w0
   3ab90:	54000320 	b.eq	3abf4 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0xac>  // b.none
   3ab94:	52856081 	mov	w1, #0x2b04                	// #11012
   3ab98:	52800e20 	mov	w0, #0x71                  	// #113
   3ab9c:	97ffebad 	bl	35a50 <icraft::detail::LogExcept::LogExcept(char const*, int, int) [clone .constprop.1]>
   3aba0:	97ffde14 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3aba4:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3aba8:	aa0003f6 	mov	x22, x0
   3abac:	912f8021 	add	x1, x1, #0xbe0
   3abb0:	d2800682 	mov	x2, #0x34                  	// #52
   3abb4:	97ffe35b 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3abb8:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3abbc:	aa1603e0 	mov	x0, x22
   3abc0:	91306021 	add	x1, x1, #0xc18
   3abc4:	d2800402 	mov	x2, #0x20                  	// #32
   3abc8:	97ffe356 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3abcc:	97ffde09 	bl	323f0 <icraft::detail::LogExcept::GetEntry()@plt>
   3abd0:	910783f6 	add	x22, sp, #0x1e0
   3abd4:	aa1603e8 	mov	x8, x22
   3abd8:	97ffe0fa 	bl	32fc0 <icraft::detail::LogExcept::Entry::finalize()@plt>
   3abdc:	b00004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3abe0:	aa1603e0 	mov	x0, x22
   3abe4:	f9453021 	ldr	x1, [x1, #2656]
   3abe8:	91004021 	add	x1, x1, #0x10
   3abec:	f900f3e1 	str	x1, [sp, #480]
   3abf0:	97ffe320 	bl	33870 <std::runtime_error::~runtime_error()@plt>
   3abf4:	aa1503e0 	mov	x0, x21
   3abf8:	97ffe78e 	bl	34a30 <icraft::xrt::MemPtr::ptype() const@plt>
   3abfc:	7100041f 	cmp	w0, #0x1
   3ac00:	54000e80 	b.eq	3add0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x288>  // b.none
   3ac04:	721e781f 	tst	w0, #0xfffffffd
   3ac08:	54000bc0 	b.eq	3ad80 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x238>  // b.none
   3ac0c:	910183f4 	add	x20, sp, #0x60
   3ac10:	b00004d6 	adrp	x22, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ac14:	9101c280 	add	x0, x20, #0x70
   3ac18:	97ffdea2 	bl	326a0 <std::ios_base::ios_base()@plt>
   3ac1c:	b00004c0 	adrp	x0, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ac20:	910803e3 	add	x3, sp, #0x200
   3ac24:	4f000400 	movi	v0.4s, #0x0
   3ac28:	790363ff 	strh	wzr, [sp, #432]
   3ac2c:	f9467000 	ldr	x0, [x0, #3296]
   3ac30:	d2800001 	mov	x1, #0x0                   	// #0
   3ac34:	f944a6c2 	ldr	x2, [x22, #2376]
   3ac38:	3c9b8060 	stur	q0, [x3, #-72]
   3ac3c:	a940dc15 	ldp	x21, x23, [x0, #8]
   3ac40:	3c9c8060 	stur	q0, [x3, #-56]
   3ac44:	91004042 	add	x2, x2, #0x10
   3ac48:	f85e82a3 	ldur	x3, [x21, #-24]
   3ac4c:	f90033f5 	str	x21, [sp, #96]
   3ac50:	f9006be2 	str	x2, [sp, #208]
   3ac54:	f900d7ff 	str	xzr, [sp, #424]
   3ac58:	8b030280 	add	x0, x20, x3
   3ac5c:	f8236a97 	str	x23, [x20, x3]
   3ac60:	97ffe44c 	bl	33d90 <std::basic_ios<char, std::char_traits<char> >::init(std::basic_streambuf<char, std::char_traits<char> >*)@plt>
   3ac64:	b00004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ac68:	b00004c2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ac6c:	91010280 	add	x0, x20, #0x40
   3ac70:	a9077fff 	stp	xzr, xzr, [sp, #112]
   3ac74:	f9465421 	ldr	x1, [x1, #3240]
   3ac78:	a9087fff 	stp	xzr, xzr, [sp, #128]
   3ac7c:	f945a842 	ldr	x2, [x2, #2896]
   3ac80:	91006023 	add	x3, x1, #0x18
   3ac84:	91010021 	add	x1, x1, #0x40
   3ac88:	a9097fff 	stp	xzr, xzr, [sp, #144]
   3ac8c:	91004042 	add	x2, x2, #0x10
   3ac90:	a9060be3 	stp	x3, x2, [sp, #96]
   3ac94:	f9006be1 	str	x1, [sp, #208]
   3ac98:	97ffe7ea 	bl	34c40 <std::locale::locale()@plt>
   3ac9c:	b00004c2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3aca0:	91018283 	add	x3, x20, #0x60
   3aca4:	52800204 	mov	w4, #0x10                  	// #16
   3aca8:	91002281 	add	x1, x20, #0x8
   3acac:	f947e842 	ldr	x2, [x2, #4048]
   3acb0:	9101c280 	add	x0, x20, #0x70
   3acb4:	b900abe4 	str	w4, [sp, #168]
   3acb8:	91004042 	add	x2, x2, #0x10
   3acbc:	f90037e2 	str	x2, [sp, #104]
   3acc0:	f9005be3 	str	x3, [sp, #176]
   3acc4:	f9005fff 	str	xzr, [sp, #184]
   3acc8:	390303ff 	strb	wzr, [sp, #192]
   3accc:	97ffe431 	bl	33d90 <std::basic_ios<char, std::char_traits<char> >::init(std::basic_streambuf<char, std::char_traits<char> >*)@plt>
   3acd0:	b00004d5 	adrp	x21, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3acd4:	b00004c6 	adrp	x6, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3acd8:	910783f6 	add	x22, sp, #0x1e0
   3acdc:	d2803e88 	mov	x8, #0x1f4                 	// #500
   3ace0:	f944eea7 	ldr	x7, [x21, #2520]
   3ace4:	910082c9 	add	x9, x22, #0x20
   3ace8:	f94678c6 	ldr	x6, [x6, #3312]
   3acec:	910040e7 	add	x7, x7, #0x10
   3acf0:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3acf4:	aa1603e0 	mov	x0, x22
   3acf8:	91310021 	add	x1, x1, #0xc40
   3acfc:	910103e4 	add	x4, sp, #0x40
   3ad00:	d2800005 	mov	x5, #0x0                   	// #0
   3ad04:	d2800003 	mov	x3, #0x0                   	// #0
   3ad08:	d28000a2 	mov	x2, #0x5                   	// #5
   3ad0c:	a9047fff 	stp	xzr, xzr, [sp, #64]
   3ad10:	a91e27e7 	stp	x7, x9, [sp, #480]
   3ad14:	a91f23ff 	stp	xzr, x8, [sp, #496]
   3ad18:	f94000d7 	ldr	x23, [x6]
   3ad1c:	97ffe6c1 	bl	34820 <void fmt::v8::detail::vformat_to<char>(fmt::v8::detail::buffer<char>&, fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<std::conditional<std::is_same<fmt::v8::type_identity<char>::type, char>::value, fmt::v8::appender, std::back_insert_iterator<fmt::v8::detail::buffer<fmt::v8::type_identity<char>::type> > >::type, fmt::v8::type_identity<char>::type> >, fmt::v8::detail::locale_ref)@plt>
   3ad20:	aa1703e3 	mov	x3, x23
   3ad24:	d2800021 	mov	x1, #0x1                   	// #1
   3ad28:	a95edfe0 	ldp	x0, x23, [sp, #488]
   3ad2c:	aa1703e2 	mov	x2, x23
   3ad30:	97ffe67c 	bl	34720 <fwrite@plt>
   3ad34:	eb0002ff 	cmp	x23, x0
   3ad38:	54000908 	b.hi	3ae58 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x310>  // b.pmore
   3ad3c:	f944eeb5 	ldr	x21, [x21, #2520]
   3ad40:	910082c1 	add	x1, x22, #0x20
   3ad44:	f940f7e0 	ldr	x0, [sp, #488]
   3ad48:	910042b5 	add	x21, x21, #0x10
   3ad4c:	f900f3f5 	str	x21, [sp, #480]
   3ad50:	eb01001f 	cmp	x0, x1
   3ad54:	54000040 	b.eq	3ad5c <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x214>  // b.none
   3ad58:	97ffe1fe 	bl	33550 <operator delete(void*)@plt>
   3ad5c:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3ad60:	aa1403e0 	mov	x0, x20
   3ad64:	9134e021 	add	x1, x1, #0xd38
   3ad68:	d28003a2 	mov	x2, #0x1d                  	// #29
   3ad6c:	97ffe2ed 	bl	33920 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   3ad70:	aa1403e0 	mov	x0, x20
   3ad74:	97ffe3d3 	bl	33cc0 <icraft::detail::LogMsg<(icraft::LogLevel)4>::~LogMsg()@plt>
   3ad78:	52800000 	mov	w0, #0x0                   	// #0
   3ad7c:	14000009 	b	3ada0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x258>
   3ad80:	aa1503e0 	mov	x0, x21
   3ad84:	97ffe52b 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3ad88:	aa0003e1 	mov	x1, x0
   3ad8c:	aa1403e0 	mov	x0, x20
   3ad90:	aa0103f4 	mov	x20, x1
   3ad94:	97ffe527 	bl	34230 <icraft::xrt::MemPtr::cptr() const@plt>
   3ad98:	eb00029f 	cmp	x20, x0
   3ad9c:	1a9f87e0 	cset	w0, ls  // ls = plast
   3ada0:	f9451673 	ldr	x19, [x19, #2600]
   3ada4:	f941ffe1 	ldr	x1, [sp, #1016]
   3ada8:	f9400262 	ldr	x2, [x19]
   3adac:	eb020021 	subs	x1, x1, x2
   3adb0:	d2800002 	mov	x2, #0x0                   	// #0
   3adb4:	54000201 	b.ne	3adf4 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x2ac>  // b.any
   3adb8:	a9407bfd 	ldp	x29, x30, [sp]
   3adbc:	a94153f3 	ldp	x19, x20, [sp, #16]
   3adc0:	a9425bf5 	ldp	x21, x22, [sp, #32]
   3adc4:	f9401bf7 	ldr	x23, [sp, #48]
   3adc8:	911003ff 	add	sp, sp, #0x400
   3adcc:	d65f03c0 	ret
   3add0:	aa1503e0 	mov	x0, x21
   3add4:	97ffdd5f 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3add8:	aa0003e1 	mov	x1, x0
   3addc:	aa1403e0 	mov	x0, x20
   3ade0:	aa0103f4 	mov	x20, x1
   3ade4:	97ffdd5b 	bl	32350 <icraft::xrt::MemPtr::addr() const@plt>
   3ade8:	eb00029f 	cmp	x20, x0
   3adec:	1a9f87e0 	cset	w0, ls  // ls = plast
   3adf0:	17ffffec 	b	3ada0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x258>
   3adf4:	97ffde73 	bl	327c0 <__stack_chk_fail@plt>
   3adf8:	aa0003f3 	mov	x19, x0
   3adfc:	97ffeaf9 	bl	359e0 <icraft::detail::LogExcept::~LogExcept() [clone .constprop.0]>
   3ae00:	aa1303e0 	mov	x0, x19
   3ae04:	97ffe64f 	bl	34740 <_Unwind_Resume@plt>
   3ae08:	aa0003f3 	mov	x19, x0
   3ae0c:	14000029 	b	3aeb0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x368>
   3ae10:	aa0003f3 	mov	x19, x0
   3ae14:	aa1403e0 	mov	x0, x20
   3ae18:	97ffe3aa 	bl	33cc0 <icraft::detail::LogMsg<(icraft::LogLevel)4>::~LogMsg()@plt>
   3ae1c:	aa1303e0 	mov	x0, x19
   3ae20:	97ffe648 	bl	34740 <_Unwind_Resume@plt>
   3ae24:	aa0003f3 	mov	x19, x0
   3ae28:	91002280 	add	x0, x20, #0x8
   3ae2c:	97ffe5a5 	bl	344c0 <std::__cxx11::basic_stringbuf<char, std::char_traits<char>, std::allocator<char> >::~basic_stringbuf()@plt>
   3ae30:	f85e82a0 	ldur	x0, [x21, #-24]
   3ae34:	f90033f5 	str	x21, [sp, #96]
   3ae38:	f8206a97 	str	x23, [x20, x0]
   3ae3c:	f944a6c1 	ldr	x1, [x22, #2376]
   3ae40:	9101c280 	add	x0, x20, #0x70
   3ae44:	91004021 	add	x1, x1, #0x10
   3ae48:	f9006be1 	str	x1, [sp, #208]
   3ae4c:	97ffde51 	bl	32790 <std::ios_base::~ios_base()@plt>
   3ae50:	aa1303e0 	mov	x0, x19
   3ae54:	97ffe63b 	bl	34740 <_Unwind_Resume@plt>
   3ae58:	d2800400 	mov	x0, #0x20                  	// #32
   3ae5c:	97ffdf49 	bl	32b80 <__cxa_allocate_exception@plt>
   3ae60:	aa0003f7 	mov	x23, x0
   3ae64:	97ffe383 	bl	33c70 <__errno_location@plt>
   3ae68:	b9400000 	ldr	w0, [x0]
   3ae6c:	d0000341 	adrp	x1, a4000 <icraft::xrt::utils::Ftmp2Tensor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, icraft::xir::Value const&)+0x58>
   3ae70:	aa1703e8 	mov	x8, x23
   3ae74:	91312021 	add	x1, x1, #0xc48
   3ae78:	910143e4 	add	x4, sp, #0x50
   3ae7c:	d2800003 	mov	x3, #0x0                   	// #0
   3ae80:	d2800282 	mov	x2, #0x14                  	// #20
   3ae84:	a9057fff 	stp	xzr, xzr, [sp, #80]
   3ae88:	97ffe47a 	bl	34070 <fmt::v8::vsystem_error(int, fmt::v8::basic_string_view<char>, fmt::v8::basic_format_args<fmt::v8::basic_format_context<fmt::v8::appender, char> >)@plt>
   3ae8c:	b00004c2 	adrp	x2, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ae90:	b00004c1 	adrp	x1, d3000 <typeinfo for icraft::xir::NodeBase<icraft::xrt::CacheSyncHostMemRegionNode, icraft::xrt::MemRegionNode>@@Base+0x28>
   3ae94:	aa1703e0 	mov	x0, x23
   3ae98:	f9466c42 	ldr	x2, [x2, #3288]
   3ae9c:	f944bc21 	ldr	x1, [x1, #2424]
   3aea0:	97ffe5e4 	bl	34630 <__cxa_throw@plt>
   3aea4:	aa0003f3 	mov	x19, x0
   3aea8:	aa1703e0 	mov	x0, x23
   3aeac:	97ffe08d 	bl	330e0 <__cxa_free_exception@plt>
   3aeb0:	f944eea2 	ldr	x2, [x21, #2520]
   3aeb4:	910082c1 	add	x1, x22, #0x20
   3aeb8:	f940f7e0 	ldr	x0, [sp, #488]
   3aebc:	91004042 	add	x2, x2, #0x10
   3aec0:	f900f3e2 	str	x2, [sp, #480]
   3aec4:	eb01001f 	cmp	x0, x1
   3aec8:	54000040 	b.eq	3aed0 <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x388>  // b.none
   3aecc:	97ffe1a1 	bl	33550 <operator delete(void*)@plt>
   3aed0:	aa1403e0 	mov	x0, x20
   3aed4:	97ffddab 	bl	32580 <std::__cxx11::basic_ostringstream<char, std::char_traits<char>, std::allocator<char> >::~basic_ostringstream()@plt>
   3aed8:	aa1303e0 	mov	x0, x19
   3aedc:	97ffe619 	bl	34740 <_Unwind_Resume@plt>
   3aee0:	aa0003f3 	mov	x19, x0
   3aee4:	17ffffd6 	b	3ae3c <icraft::xrt::operator<=(icraft::xrt::MemPtr const&, icraft::xrt::MemPtr const&)+0x2f4>
