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


class MiiDataSwitch:
    # Reference:
    # https://github.com/HEYimHeroic/mii2studio/blob/master/gen3_switchgame.ksy
    def decode(self, stream: StreamIn):
        data = stream.read(0x58)
        stream = StreamIn(data, "<")

        self.mii_id = stream.repeat(stream.u8, 16)
        self.mii_name = stream.wchars(11).split("\0", 1)[0]
        self.font_region = stream.u8()

        self.color = stream.u8()
        self.gender = stream.u8()
        self.size = stream.u8()
        self.fatness = stream.u8()
        self.special = stream.u8()
        self.unknown = stream.u8()

        self.face_type = stream.u8()
        self.face_color = stream.u8()
        self.face_style = stream.u8()
        self.blush_type = stream.u8()

        self.hair_type = stream.u8()
        self.hair_color = stream.u8()
        self.hair_mirrored = stream.u8()

        self.eye_type = stream.u8()
        self.eye_color = stream.u8()
        self.eye_scale = stream.u8()
        self.eye_thickness = stream.u8()
        self.eye_rotation = stream.u8()
        self.eye_distance = stream.u8()
        self.eye_height = stream.u8()

        self.eyebrow_type = stream.u8()
        self.eyebrow_color = stream.u8()
        self.eyebrow_scale = stream.u8()
        self.eyebrow_thickness = stream.u8()
        self.eyebrow_rotation = stream.u8()
        self.eyebrow_distance = stream.u8()
        self.eyebrow_height = stream.u8()

        self.nose_type = stream.u8()
        self.nose_scale = stream.u8()
        self.nose_height = stream.u8()

        self.mouth_type = stream.u8()
        self.mouth_color = stream.u8()
        self.mouth_scale = stream.u8()
        self.mouth_thickness = stream.u8()
        self.mouth_height = stream.u8()

        self.beard_color = stream.u8()
        self.beard_type = stream.u8()
        self.mustache_type = stream.u8()
        self.mustache_scale = stream.u8()
        self.mustache_height = stream.u8()

        self.glass_type = stream.u8()
        self.glass_color = stream.u8()
        self.glass_scale = stream.u8()
        self.glass_height = stream.u8()

        self.mole_enabled = stream.u8()
        self.mole_scale = stream.u8()
        self.mole_xpos = stream.u8()
        self.mole_ypos = stream.u8()

        self.always_zero = stream.u8()

    def encode(self, outstream: StreamOut):
        pass

    @classmethod
    def parse(cls, data: bytes):
        instance = cls()
        instance.decode(StreamIn(data, "<"))
        return instance

    # References:
    # https://github.com/kazuki-4ys/kazuki-4ys.github.io/blob/master/web_apps/MiiInfoEditorCTR/mii.js#L108
    # https://github.com/HEYimHeroic/mii2studio/blob/master/mii2studio.py#L186
    def to_studio_api(self) -> bytes:
        studio_bytes = bytes([
            self.beard_color,
            self.beard_type,
            self.fatness,

            self.eye_thickness,
            self.eye_color,
            self.eye_rotation,
            self.eye_scale,
            self.eye_type,
            self.eye_distance,
            self.eye_height,

            self.eyebrow_thickness,
            self.eyebrow_color,
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

            self.glass_color,
            self.glass_scale,
            self.glass_type,
            self.glass_height,

            self.hair_color,
            self.hair_mirrored,
            self.hair_type,

            self.size,
            self.mole_scale,
            self.mole_enabled,
            self.mole_xpos,
            self.mole_ypos,

            self.mouth_thickness,
            self.mouth_color,
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
        self.mii_id = b"\x6A\xB8\x5D\x53\x8E\x86\xE8\x86\xB4\x2F\x5C\x26\xCB\x23\x43\x3A"
        self.mii_name = "みんな、みていてくれ"
        self.font_region = 0

        self.color = 0
        self.gender = 0
        self.size = 64
        self.fatness = 64
        self.special = 0
        self.unknown = 0

        self.face_type = 0
        self.face_color = 0
        self.face_style = 0
        self.blush_type = 0

        self.hair_type = 33
        self.hair_color = 1
        self.hair_mirrored = 0

        self.eye_type = 2
        self.eye_color = 8
        self.eye_scale = 4
        self.eye_thickness = 3
        self.eye_rotation = 4
        self.eye_distance = 2
        self.eye_height = 12

        self.eyebrow_type = 6
        self.eyebrow_color = 1
        self.eyebrow_scale = 4
        self.eyebrow_thickness = 3
        self.eyebrow_rotation = 6
        self.eyebrow_distance = 2
        self.eyebrow_height = 10

        self.nose_type = 1
        self.nose_scale = 4
        self.nose_height = 9

        self.mouth_type = 23
        self.mouth_color = 19
        self.mouth_scale = 4
        self.mouth_thickness = 3
        self.mouth_height = 13

        self.beard_color = 8
        self.beard_type = 0
        self.mustache_type = 0
        self.mustache_scale = 4
        self.mustache_height = 10

        self.glass_type = 0
        self.glass_color = 8
        self.glass_scale = 4
        self.glass_height = 10

        self.mole_enabled = 0
        self.mole_scale = 4
        self.mole_xpos = 2
        self.mole_ypos = 20

        self.always_zero = 0
