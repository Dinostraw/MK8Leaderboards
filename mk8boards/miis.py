from anynet.streams import StreamIn, StreamOut
from nintendo.miis import MiiData


class MiiDataWiiU(MiiData):
    def decode(self, stream: StreamIn):
        super().decode(stream)
        self.mac_address = self.mii_id[4:]
        self.mii_id = self.mii_id[:4]

    def encode(self, outstream: StreamOut):
        self.mii_id = self.mii_id.extend(self.mac_address)
        super().encode(outstream)
        self.mii_id = self.mii_id[:4]

    @classmethod
    def parse(cls, data: bytes):
        return super().parse(data)

    # References:
    # https://github.com/kazuki-4ys/kazuki-4ys.github.io/blob/master/web_apps/MiiInfoEditorCTR/mii.js#L108
    # https://github.com/HEYimHeroic/mii2studio/blob/master/mii2studio.py#L186
    def to_studio_api(self) -> bytes:
        if not self.glass_color:
            glasses_color = 8
        elif self.glass_color < 6:
            glasses_color = self.glass_color + 13
        else:
            glasses_color = 0

        studio_bytes = bytes([
            self.beard_color if self.beard_color else 8,
            self.beard_type,
            self.fatness,

            self.eye_thickness,
            self.eye_color + 8,
            self.eye_rotation,
            self.eye_scale,
            self.eye_type,
            self.eye_distance,
            self.eye_height,

            self.eyebrow_thickness,
            self.eyebrow_color if self.eyebrow_color else 8,
            self.eyebrow_rotation,
            self.eyebrow_scale,
            self.eyebrow_type,
            self.eyebrow_distance,
            self.eyebrow_height,

            self.face_color,
            self.blush_type,
            self.face_type,
            self.face_style,

            self.color,
            self.gender,

            glasses_color,
            self.glass_scale,
            self.glass_type,
            self.glass_height,

            self.hair_color if self.hair_color else 8,
            self.hair_mirrored,
            self.hair_type,

            self.size,
            self.mole_scale,
            self.mole_enabled,
            self.mole_xpos,
            self.mole_ypos,

            self.mouth_thickness,
            self.mouth_color + 19 if self.mouth_color < 4 else 0,
            self.mouth_scale,
            self.mouth_type,
            self.mouth_height,

            self.mustache_scale,
            self.mustache_type,
            self.mustache_height,

            self.nose_scale,
            self.nose_type,
            self.nose_height
        ])

        def gen_bytes():
            n = 0x42
            yield n
            for x in studio_bytes:
                n = (7 + (x ^ n)) & 0xFF
                yield n

        return bytes(gen_bytes())

    def __init__(self):
        self.mac_address = None
        self.mii_id = None
