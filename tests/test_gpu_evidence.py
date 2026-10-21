import unittest
from source_normalization import gpu_details


class GpuEvidenceTests(unittest.TestCase):
    def test_gpu_model_alone_does_not_classify_or_supply_memory(self):
        self.assertEqual(gpu_details('NVIDIA RTX 4060'), {'gpu_kind':'unknown','vram_gb':None})
        self.assertEqual(gpu_details('Intel Arc Graphics'), {'gpu_kind':'unknown','vram_gb':None})

    def test_explicit_memory_type_and_bounded_graphics_capacity(self):
        self.assertEqual(gpu_details('NVIDIA GeForce RTX 5060 Laptop GPU 8GB GDDR7', bounded=True),
                         {'gpu_kind':'discrete','vram_gb':8})
        self.assertEqual(gpu_details('NVIDIA GeForce RTX 4050 Laptop GPU 6GB', bounded=True)['vram_gb'],6)
        self.assertIsNone(gpu_details('Laptop RTX 4050 16GB DDR5 RAM')['vram_gb'])

    def test_shared_conflicting_and_alternative_memory_stays_unknown(self):
        self.assertEqual(gpu_details('Integrated Intel Graphics shared 16GB', bounded=True),
                         {'gpu_kind':'integrated','vram_gb':None})
        self.assertIsNone(gpu_details('RTX 4060 8GB GDDR6 or 12GB GDDR6', bounded=True)['vram_gb'])
        self.assertEqual(gpu_details('Integrated discrete 8GB GDDR6', bounded=True),
                         {'gpu_kind':'unknown','vram_gb':None})
        self.assertIsNone(gpu_details('RTX 4060 up to 8GB GDDR6', bounded=True)['vram_gb'])
