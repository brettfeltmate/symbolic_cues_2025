# type: ignore
from construct import this, Float32l, Int16sl, Struct, Computed, Int32ul, CString

def decodeMarkerID(obj, _):
    return obj.encoded_id & 0x0000FFFF


def decodeModelID(obj, _):
    return obj.encoded_id >> 16


def trackingValid(obj, _):
    return (obj.error & 0x01) != 0


unlabeled_marker = Struct(
    "pos_x" / Float32l,
    "pos_y" / Float32l,
    "pos_z" / Float32l,
)

labeled_marker = Struct(
    "id" / Int32ul,
    "marker_id" / Computed(this.id * decodeMarkerID),
    "model_id" / Computed(this.id * decodeModelID),
    "pos_x" / Float32l,
    "pos_y" / Float32l,
    "pos_z" / Float32l,
    "size" / Float32l,
    "param" / Int16sl,
    "residual" / Float32l,
)

rigid_body = Struct(
    "id" / Int32ul,
    "pos_x" / Float32l,
    "pos_y" / Float32l,
    "pos_z" / Float32l,
    "rot_w" / Float32l,
    "rot_x" / Float32l,
    "rot_y" / Float32l,
    "rot_z" / Float32l,
    "error" / Float32l,
    "tracking" / Int16sl,
    "is_valid" / Computed(lambda ctx: (ctx.tracking & 0x01) != 0),
)

packet_structs = {
    "label": CString("utf8"),
    "size": Int32ul,
    "count": Int32ul,
    "frame_number": Int32ul,
    "unlabeled_marker": unlabeled_marker,
    "labeled_marker": labeled_marker,
    "rigid_body": rigid_body,
}
