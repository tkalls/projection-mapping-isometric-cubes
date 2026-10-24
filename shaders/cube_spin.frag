// cube_spin: a real 3D cube, rendered through the same 2D "lens" the aligned rig defines.
// The rig's three arms a, b, c are the screen images of the cube's three edge directions, so the
// 2x3 matrix P = [a b c] is the projection. At rotation 0 (or any multiple of 90 on the turntable)
// this render lands exactly on the rig, so on the real creases.
// Inputs: 0 ceiling clip (top face), 1 left clip (y faces), 2 = pack: left half right clip (x faces), right half 4th clip (bottom face).
uniform vec4 uV;    // xy vertex (px)
uniform vec4 uAng;  // arm angles (deg)
uniform vec4 uLen;  // arm lengths (px)
uniform vec4 uS;    // x angle (deg), y axis (0 turntable, 1 corner hinge, 2 tumble), z shading, w ceiling upright
uniform vec4 uK;    // x kick, y punch, z flash
uniform vec4 uR0, uR1, uR2;   // rotation matrix columns, from the Python motion engine (spin_rot)
uniform vec4 uPv;   // xyz pivot, w scale
out vec4 fragColor;

mat3 axisAngle(vec3 ax, float a){
  ax = normalize(ax); float s = sin(a), c = cos(a), oc = 1.0 - c;
  return mat3(oc*ax.x*ax.x + c,       oc*ax.x*ax.y + ax.z*s,  oc*ax.z*ax.x - ax.y*s,
              oc*ax.x*ax.y - ax.z*s,  oc*ax.y*ax.y + c,       oc*ax.y*ax.z + ax.x*s,
              oc*ax.z*ax.x + ax.y*s,  oc*ax.y*ax.z - ax.x*s,  oc*ax.z*ax.z + c);
}

void main(){
  vec2 p = (vUV.st - 0.5)*vec2(1280.0, 720.0);
  // --- seat-corrected projection ---------------------------------------------------------
  // The aligned rig tells us how the three real surfaces appear in the projector: arms a, b, c
  // from the vertex. From the filming seat those same three faces read as a PERFECT isometric
  // hexagon. So: (1) find which surface this projector pixel lands on and where on it (the sector
  // between two arms, solved as a 2x2 system), (2) move to that spot in the ideal isometric "seat
  // view" (arms at 150, 30 and 270 degrees, equal length), (3) render the object there with a true
  // orthographic isometric camera. A sphere is then a perfect circle from the seat.
  vec2 a = vec2(cos(radians(uAng.x)), sin(radians(uAng.x)))*uLen.x;
  vec2 b = vec2(cos(radians(uAng.y)), sin(radians(uAng.y)))*uLen.y;
  vec2 c = vec2(cos(radians(uAng.z)), sin(radians(uAng.z)))*uLen.z;
  float Ls = (uLen.x + uLen.y + uLen.z)/3.0;
  vec2 a2 = vec2(cos(radians(150.0)), sin(radians(150.0)))*Ls;
  vec2 b2 = vec2(cos(radians(30.0)),  sin(radians(30.0)))*Ls;
  vec2 c2 = vec2(0.0, -1.0)*Ls;
  vec2 qp = p - uV.xy;
  vec2 s;
  {
    float d1 = a.x*b.y - a.y*b.x;  vec2 k1 = vec2(qp.x*b.y - qp.y*b.x, a.x*qp.y - a.y*qp.x)/d1;   // ceiling
    float d2 = a.x*c.y - a.y*c.x;  vec2 k2 = vec2(qp.x*c.y - qp.y*c.x, a.x*qp.y - a.y*qp.x)/d2;   // left wall
    float d3 = b.x*c.y - b.y*c.x;  vec2 k3 = vec2(qp.x*c.y - qp.y*c.x, b.x*qp.y - b.y*qp.x)/d3;   // right wall
    if (k1.x >= 0.0 && k1.y >= 0.0)      s = k1.x*a2 + k1.y*b2;
    else if (k2.x >= 0.0 && k2.y >= 0.0) s = k2.x*a2 + k2.y*c2;
    else                                 s = k3.x*b2 + k3.y*c2;
  }
  // render in the seat view: P' = [a2 b2 c2] is an exact orthographic isometric projection
  float grow = 1.0 + uK.y*uK.x;
  vec3 r1 = vec3(a2.x, b2.x, c2.x)*grow, r2 = vec3(a2.y, b2.y, c2.y)*grow;
  vec3 n = normalize(cross(r1, r2));
  if (dot(n, vec3(1.0)) < 0.0) n = -n;
  vec2 q = s;
  float m11 = dot(r1, r1), m12 = dot(r1, r2), m22 = dot(r2, r2), det = m11*m22 - m12*m12;
  vec2 w = vec2(m22*q.x - m12*q.y, -m12*q.x + m11*q.y)/det;
  vec3 X0 = r1*w.x + r2*w.y;


  // orientation from the motion engine: any rotation the Python side can describe
  mat3 R = mat3(uR0.xyz, uR1.xyz, uR2.xyz);
  mat3 Ri = transpose(R);
  vec3 piv = uPv.xyz;
  float sc = max(uPv.w, 0.05);
  vec3 o = Ri*(X0 - piv)/sc + piv, d = Ri*n/sc;

  // ray / box [0,1]^3 (slab method)
  vec3 inv = 1.0/d;
  vec3 t0 = (vec3(0.0) - o)*inv, t1 = (vec3(1.0) - o)*inv;
  vec3 tmn = min(t0, t1), tmx = max(t0, t1);
  float tin = max(max(tmn.x, tmn.y), tmn.z), tout = min(min(tmx.x, tmx.y), tmx.z);
  vec3 col = vec3(0.0);
  if (tout >= tin){
    vec3 h = clamp(o + d*tin, 0.0, 1.0);
    vec3 N; vec2 st; int tex;
    if (tin == tmn.x){ bool lo = d.x > 0.0; N = vec3(lo ? -1.0 : 1.0, 0, 0); tex = 2; st = lo ? vec2(h.y, 1.0 - h.z) : vec2(1.0 - h.y, 1.0 - h.z); }
    else if (tin == tmn.y){ bool lo = d.y > 0.0; N = vec3(0, lo ? -1.0 : 1.0, 0); tex = 1; st = lo ? vec2(1.0 - h.x, 1.0 - h.z) : vec2(h.x, 1.0 - h.z); }
    else { bool lo = d.z > 0.0; N = vec3(0, 0, lo ? -1.0 : 1.0); tex = lo ? 0 : 3;   // the bottom gets its own clip
           vec2 uv = lo ? h.xy : vec2(h.y, h.x);
           st = (uS.w > 0.5) ? vec2((uv.y - uv.x + 1.0)*0.5, (uv.x + uv.y)*0.5) : uv; }
    st = clamp(st, 0.0008, 0.9992);
    if (tex == 0) col = texture(sTD2DInputs[0], st).rgb;
    else if (tex == 1) col = texture(sTD2DInputs[1], st).rgb;
    else if (tex == 2) col = texture(sTD2DInputs[2], vec2(clamp(st.x, 0.0016, 0.9984)*0.5, st.y)).rgb;
    else col = texture(sTD2DInputs[2], vec2(0.5 + clamp(st.x, 0.0016, 0.9984)*0.5, st.y)).rgb;
    // shade by how squarely the face turns toward the viewer (equal for all three at rest)
    vec3 Nw = R*N;
    float facing = clamp(dot(Nw, -n)/0.57735, 0.0, 1.4);
    col *= mix(1.0, facing, uS.z);
    col *= 1.0 + uK.z*uK.x;
  }
  fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
