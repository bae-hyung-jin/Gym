import bpy, math
from mathutils import Vector

# 1. Inspect Player_Bomio bone world axes in rest pose
bpy.ops.wm.open_mainfile(filepath=r"G:\Unity_Gym\AI-Gym\_blender\Bomio_Exercises\01_Avatar\Player_Bomio.blend")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
print("=== BOMIO REST POSE BONE WORLD AXES ===")
mw = arm.matrix_world
for bn in ["Hips", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot",
           "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"]:
    pb = arm.pose.bones[f"mixamorig:{bn}"]
    M = (mw @ pb.matrix).to_3x3().normalized()
    head = mw @ pb.head
    tail = mw @ pb.tail
    print(f"{bn:13s} | head={tuple(round(v,3) for v in head)} tail={tuple(round(v,3) for v in tail)} | X={tuple(round(v,2) for v in M.col[0])} Y={tuple(round(v,2) for v in M.col[1])} Z={tuple(round(v,2) for v in M.col[2])}")

# 2. Inspect key mesh world bounding-box centers in each of the 5 machine .blend files
SRC = {
    "HipAdduction": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\hip_adduction (1).blend",
    "LyingLegCurl": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\lying_leg_curl.blend",
    "BenchPress":   r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\plate_loaded_bench_press (2).blend",
    "StairClimber": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\stair_climber.blend",
    "VSquat":       r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\v_squat.blend",
}

def bbox_world(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx, (mn + mx) * 0.5

for tag, path in SRC.items():
    bpy.ops.wm.open_mainfile(filepath=path)
    print(f"\n=== {tag} KEY OBJECTS ===")
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if any(k in ob.name for k in ["Pivot", "Pad", "Grip", "Handle", "Seat", "Foot", "Roller", "Back", "Shoulder", "Bench", "Deck"]):
            if ob.type == 'MESH':
                mn, mx, ctr = bbox_world(ob)
                print(f"  MESH  {ob.name:32s} ctr={tuple(round(v,3) for v in ctr)} min={tuple(round(v,3) for v in mn)} max={tuple(round(v,3) for v in mx)}")
            elif ob.type == 'EMPTY':
                loc = ob.matrix_world.translation
                print(f"  EMPTY {ob.name:32s} loc={tuple(round(v,3) for v in loc)}")
