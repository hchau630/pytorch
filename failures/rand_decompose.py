import torch
from torch.utils._python_dispatch import TorchDispatchMode
import functorch
from functorch.compile import aot_function, aot_module, draw_graph, print_compile

# aten = torch.ops.aten
# class FunctionalizeRandomOps(TorchDispatchMode):
#     """
#     This class keeps track of seed and offset.
#     """

#     def __init__(self):
#         # If initial_seed changes, it means that somebody has called
#         # set_rng_state in between and we will have to get the updated seed and offset.
#         self._seed = torch.initial_seed()
#         # TODO - In future, this needs to be a tensor of offsets if we want to
#         # support splittable RNG
#         self._offset = 0
#         self._random_aten_ops = [aten.randn.default]
        
#         # TODO - this is only for prototype. We should remove this in future with an aten-level op
#         self._use_inductor_op = True
    

#     def get_offset(self, shape):
#         # TODO - Specific to PyTorch CUDA impl. It calculates the total number
#         # of randoms generated by CUDA. If everything fits nicely in the
#         # stride-loop CUDA kernel, this is equal to the number of elements. But,
#         # when a thread block has some unusable threads, it can be a different
#         # number.

#         # For impl, look at calc_execution_policy


#         # std::tuple<uint64_t, dim3, dim3> calc_execution_policy(int64_t total_elements) {
#         # const uint64_t numel = static_cast<uint64_t>(total_elements);
#         # const uint32_t block_size = block_size_bound;
#         # const uint32_t unroll = curand4_engine_calls;
#         # dim3 dim_block(block_size);
#         # dim3 grid((numel + block_size - 1) / block_size);
#         # uint32_t blocks_per_sm = at::cuda::getCurrentDeviceProperties()->maxThreadsPerMultiProcessor / block_size;
#         # grid.x = std::min(
#         #     static_cast<uint32_t>(at::cuda::getCurrentDeviceProperties()->multiProcessorCount) * blocks_per_sm,
#         #     grid.x);
#         # //number of times random will be generated per thread, to offset philox counter in thc random state
#         # uint64_t counter_offset = ((numel - 1) / (block_size * grid.x * unroll) + 1)
#         #                               * curand4_engine_calls;
#         # return std::make_tuple(counter_offset, grid, dim_block);

#         numel = 1
#         for dim_size in shape:
#             numel *= dim_size

#         block_size = 256
#         unroll = 4
#         curand4_engine_calls = 4
#         device_property = torch.cuda.get_device_properties(torch.cuda.current_device())
#         blocks_per_sm = int(device_property.max_threads_per_multi_processor / block_size)
#         grid_size = int((numel + block_size - 1) / block_size)
#         grid_size = min(grid_size, device_property.multi_processor_count * blocks_per_sm)
#         offset = int((numel - 1) / (block_size * grid_size * unroll) + 1) * curand4_engine_calls
#         return offset

#     def get_seed(self):
#         current_seed = torch.initial_seed()
#         if current_seed != self._seed:
#             # Getting the seed is acutally easy, its the offset that is hard to get
#             raise NotImplementedError("torch.set_rng_state/manual_seed has been called in between and changes state. Unimplemented")
#         if self._use_inductor_op:
#             # TODO - Triton seems to need the seed to be 32 bits
#             return self._seed % (2**32)
#         return self._seed
 


        

#     def __torch_dispatch__(self, func, types, args=..., kwargs=None):
        
#         import torch._inductor
#         from torch._inductor.overrides import philox_rand_like
#         if func in self._random_aten_ops:
#             # get seed and offset to be used for the op
#             new_seed = self.get_seed()
#             new_offset = self._offset

#             # Set the new offset for the future randn op
#             shape = args[0]
#             device = kwargs["device"]
#             self._offset += self.get_offset(shape)

#             # Call the functionalized rng op
#             if self._use_inductor_op:
#                 TO_BE_REMOVED_tensor_to_make_inductor_api_happy = torch.empty(shape, device=device)
#                 return philox_rand_like(TO_BE_REMOVED_tensor_to_make_inductor_api_happy, new_seed, new_offset)
#             else:
#                 raise NotImplementedError("aten level functional op not implemeted yet")

#         return func(*args, **kwargs)

# class HelloContextManager:
#     def __enter__(self):
#         print("Entering the context...")
#         return "Hello, World!"
#     def __exit__(self, exc_type, exc_value, exc_tb):
#         print("Leaving the context...")
#         print(exc_type, exc_value, exc_tb, sep="\n")

# class HelloContextManager2:
#     def __enter__(self):
#         print("Entering the context2...")
#         return "Hello, World2!"
#     def __exit__(self, exc_type, exc_value, exc_tb):
#         print("Leaving the context2...")
#         print(exc_type, exc_value, exc_tb, sep="\n")

# with HelloContextManager(), HelloContextManager2():
#     print("AAA")

class MockModule(torch.nn.Module):
    def __init__(self):
        super().__init__()
    
    def forward(self, x):
        a = torch.rand(1024, device="cuda") + torch.sin(x)
        a = torch.rand(4, 1024, device="cuda").sum(axis=0) + torch.sin(a)
        a = torch.rand(1024, device="cuda") + torch.sin(a)
        a = torch.nn.functional.dropout(a)
        return a

mod = MockModule()

x = torch.randn(1024, device="cuda", requires_grad=True)

# with FunctionalizeRandomOps():
#     z = mod(x)
#     print(z)


# aot_mod = aot_module(mod, print_compile)
# aot_mod(x)

opt_mod = torch.compile(mod, backend="aot_eager_decomp_partition")
opt_mod(x).sum().backward()