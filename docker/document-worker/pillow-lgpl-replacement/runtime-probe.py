
import ctypes, hashlib, io, json, os, pathlib
from PIL import Image, ImageDraw, ImageFont, _imagingft, features
path = pathlib.Path(_imagingft.__file__)
library = ctypes.CDLL(str(path))
getter = library.plwc_g3_modified_shim_marker
getter.restype = ctypes.c_char_p
# No direct load_fribidi invocation: this must have run through Pillow import.
marker = getter().decode('ascii')
assert marker == 'PLwC modified LGPL shim executed', marker
font = ImageFont.truetype('/usr/local/lib/python3.12/site-packages/reportlab/fonts/Vera.ttf', 28, layout_engine=ImageFont.Layout.BASIC)
image = Image.new('RGB', (560, 90), 'white')
ImageDraw.Draw(image).text((12, 12), 'PLwC LGPL replacement 2026', fill='black', font=font)
assert image.getextrema()[0][0] < 255
assert font.getmask('PLwC').getbbox() is not None
buf = io.BytesIO(); image.save(buf, format='PNG')
assert buf.getvalue().startswith(b'\x89PNG\r\n\x1a\n')
maps = pathlib.Path('/proc/self/maps').read_text()
assert str(path) in maps
versions = {name: features.version(name) for name in ['freetype2','harfbuzz','raqm','fribidi']}
assert versions['freetype2'] == '2.14.3', versions
result = {'uid': os.getuid(), 'gid': os.getgid(), 'extension_path': str(path),
          'extension_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'marker': marker,
          'marker_read_after_normal_pillow_import': True, 'direct_load_fribidi_invoked': False,
          'font_layout': 'BASIC', 'font_mask_nonempty': True, 'png_bytes': len(buf.getvalue()),
          'png_sha256': hashlib.sha256(buf.getvalue()).hexdigest(), 'versions': versions,
          'have_raqm': bool(_imagingft.HAVE_RAQM), 'replacement_path_in_loaded_memory_maps': True}
assert result['uid'] == result['gid'] == 10001
print(json.dumps(result))
