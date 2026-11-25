import bpy

SRC = {
    "HipAdduction": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\hip_adduction (1).blend",
    "LyingLegCurl": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\lying_leg_curl.blend",
    "BenchPress":   r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\plate_loaded_bench_press (2).blend",
    "StairClimber": r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\stair_climber.blend",
    "VSquat":       r"e:\내 드라이브\굿노트백업\3-2\창업프로젝트\Unity(서원대학교)\1125\한도윤\v_squat.blend",
}

for tag, path in SRC.items():
    bpy.ops.wm.open_mainfile(filepath=path)
    print(f"\n=== {tag} MATERIALS ===")
    for mat in sorted(bpy.data.materials, key=lambda m: m.name):
        if mat.users == 0:
            continue
        col = (0.5, 0.5, 0.5, 1.0)
        met = 0.0
        rough = 0.5
        tex = None
        if mat.use_nodes and mat.node_tree:
            bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if bsdf:
                bc_in = bsdf.inputs.get("Base Color")
                if bc_in:
                    col = tuple(round(v, 3) for v in bc_in.default_value)
                    if bc_in.is_linked:
                        # Trace back to Image Texture
                        visited = set()
                        stack = [bc_in.links[0].from_node]
                        while stack:
                            nd = stack.pop()
                            if nd in visited: continue
                            visited.add(nd)
                            if nd.type == 'TEX_IMAGE' and nd.image:
                                tex = nd.image.name
                                break
                            for inp in nd.inputs:
                                for lk in inp.links:
                                    stack.append(lk.from_node)
                met_in = bsdf.inputs.get("Metallic")
                if met_in: met = round(met_in.default_value, 3)
                r_in = bsdf.inputs.get("Roughness")
                if r_in: rough = round(r_in.default_value, 3)
        print(f"  {mat.name:36s} | col={col} met={met} rough={rough} tex={tex}")
