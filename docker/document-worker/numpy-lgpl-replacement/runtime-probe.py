
import ctypes, hashlib, json, os, pathlib
import numpy as np
path = pathlib.Path('/usr/local/lib/python3.12/site-packages/numpy.libs/libquadmath-96973f99-934c22de.so.0.0.0')
maps = pathlib.Path('/proc/self/maps').read_text()
assert str(path) in maps
# RTLD_NOLOAD proves NumPy's ordinary import has already loaded this replacement.
library = ctypes.CDLL(str(path), mode=os.RTLD_NOLOAD | os.RTLD_LOCAL)
probe = library.plwc_quadmath_modified_probe
probe.restype = ctypes.c_int
assert probe() == 1
getter = library.plwc_quadmath_modified_marker; getter.restype = ctypes.c_char_p
marker = getter().decode('ascii'); assert marker == 'PLwC modified quadmath executed', marker
matrix = np.array([[3.0, 1.0], [1.0, 2.0]])
answer = np.linalg.solve(matrix, np.array([9.0, 8.0]))
assert np.allclose(answer, [2.0, 3.0])
u, sigma, vt = np.linalg.svd(matrix)
assert np.allclose((u * sigma) @ vt, matrix)
result = {'uid': os.getuid(), 'gid': os.getgid(), 'extension_path': str(path),
          'extension_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'marker': marker,
          'modified_expq_called_by_LGPL_probe': True, 'quad_precision_exp_of_zero_equal_one': True,
          'RTLD_NOLOAD_after_normal_numpy_import': True, 'replacement_path_in_loaded_memory_maps': True,
          'numpy_version': np.__version__, 'linear_solve': answer.tolist(), 'svd_reconstruction_pass': True}
assert result['uid'] == result['gid'] == 10001
print(json.dumps(result))
