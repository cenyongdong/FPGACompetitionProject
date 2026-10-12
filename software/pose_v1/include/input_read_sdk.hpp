#pragma once
#include <icraft-xrt/core/tensor.h>
namespace pose::input_read {
void intoHost(const icraft::xrt::Tensor& source,icraft::xrt::Tensor& destination);
}
