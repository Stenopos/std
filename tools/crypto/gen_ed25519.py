import sys
sys.path.insert(0, sys.argv[2])
import ref_ed25519 as r
out = sys.argv[1]
def fe_table(name, vals):
    body = "\n".join(f"    t.push({v})" for v in vals)
    return f"func {name}() -> List[int64] {{\n    List[int64] t = list_new()\n{body}\n    return t\n}}"
def byte_table(name, vals):
    body = "\n".join(f"    t.push({v})" for v in vals)
    return f"func {name}() -> List[int32] {{\n    List[int32] t = list_new()\n{body}\n    return t\n}}"
tables = "\n\n".join([fe_table("fe_d", r.C["D"]), fe_table("fe_d2", r.C["D2"]), fe_table("fe_base_x", r.C["X"]),
                      fe_table("fe_base_y", r.C["Y"]), fe_table("fe_sqrtm1", r.C["I"]), byte_table("order_l", r.Lb)])
src = open(sys.argv[3]).read().replace("@TABLES@", tables)
open(f"{out}/ed25519.sten", "w").write(src)
