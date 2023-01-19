# Owner(s): ["module: onnx"]
import unittest

import onnx_test_common
import torch
from torch import nn
from torch.nn import functional as F
from torch.testing._internal import common_utils


class TestFxToOnnxWithOnnxRuntime(onnx_test_common._TestONNXRuntime):
    def test_simple_function(self):
        def func(x):
            y = x + 1
            z = y.relu()
            return (y, z)

        tensor_x = torch.randn(1, 1, 2, dtype=torch.float32)

        self.run_test_with_fx_to_onnx_exporter(func, (tensor_x,))

    @unittest.skip("TypeError: export() got an unexpected keyword argument 'b'")
    def test_func_with_args_and_kwargs(self):
        def func(x, b=1.0):
            y = x + b
            z = y.relu()
            return (y, z)

        tensor_x = torch.randn(1, 1, 2, dtype=torch.float32)

        self.run_test_with_fx_to_onnx_exporter(func, (tensor_x,), {"b": 500.0})

    def test_mnist(self):
        class MNISTModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(1, 32, 3, 1, bias=True)
                self.conv2 = nn.Conv2d(32, 64, 3, 1, bias=True)
                self.fc1 = nn.Linear(9216, 128, bias=True)
                self.fc2 = nn.Linear(128, 10, bias=True)

            def forward(self, tensor_x: torch.Tensor):
                tensor_x = self.conv1(tensor_x)
                tensor_x = torch.sigmoid(tensor_x)
                tensor_x = self.conv2(tensor_x)
                tensor_x = torch.sigmoid(tensor_x)
                tensor_x = F.max_pool2d(tensor_x, 2)
                tensor_x = torch.flatten(tensor_x, 1)
                tensor_x = self.fc1(tensor_x)
                tensor_x = torch.sigmoid(tensor_x)
                output = self.fc2(tensor_x)
                return output

        tensor_x = torch.rand((64, 1, 28, 28), dtype=torch.float32)
        self.run_test_with_fx_to_onnx_exporter(MNISTModel(), (tensor_x,))

    # test single op with no kwargs
    def test_sigmoid(self):
        x = torch.randn(1, 4, 2, 3)

        class SigmoidModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.sigmoid = torch.nn.Sigmoid()

            def forward(self, x):
                return self.sigmoid(x)

        self.run_test_with_fx_to_onnx_exporter(SigmoidModel(), (x,))

    # test single op with no kwargs
    def test_sigmoid_add(self):
        x = torch.randn(1, 4, 2, 3)

        class SigmoidAddModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.sigmoid = torch.nn.Sigmoid()

            def forward(self, x):
                x = torch.ops.aten.add(x, 1, alpha=2)
                return self.sigmoid(x)

        self.run_test_with_fx_to_onnx_exporter(SigmoidAddModel(), (x,))


if __name__ == "__main__":
    common_utils.run_tests()
