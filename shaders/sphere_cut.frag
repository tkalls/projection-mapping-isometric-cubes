// sphere_cut: a sphere with one eighth removed. The notch exposes three quarter-disc faces that
// meet at 90 degrees, a miniature of the room corner. Same projection and motion engine as cube_spin.
// Inputs: 0 ceiling clip, 1 left clip, 2 = packed image: left half right-wall clip, right half outer-skin clip.
uniform vec4 uV;    // xy vertex (px)
uniform vec4 uAng;  // arm angles (deg)
uniform vec4 uLen;  // arm lengths (px)
uniform vec4 uS;    // z shading
uniform vec4 uK;    // x kick, y punch, z flash
uniform vec4 uR0, uR1, uR2;   // rotation (motion engine)
uniform vec4 uPv;   // xyz pivot, w scale
uniform vec4 uSp;   // x radius (cube units), y rim glow, z inner shade, w notch on/off
out vec4 fragColor;
const float PI = 3.14159265;

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


  mat3 R = mat3(uR0.xyz, uR1.xyz, uR2.xyz), Ri = transpose(R);
  vec3 C = vec3(0.5);
  float sc = max(uPv.w, 0.05);
  vec3 o = Ri*(X0 - C)/sc + C, d = Ri*n/sc;
  float rad = uSp.x;

  // ray vs sphere
  vec3 oc = o - C;
  float A = dot(d, d), B = dot(oc, d), Cc = dot(oc, oc) - rad*rad, disc = B*B - A*Cc;
  vec3 col = vec3(0.0);
  if (disc > 0.0){
    float sq = sqrt(disc);
    float t0 = (-B - sq)/A, t1 = (-B + sq)/A;
    vec3 p0 = o + d*t0;
    // the removed eighth: the octant on the viewer's side of the centre (x, y, z all below the centre)
    bool inNotch = uSp.w > 0.5 && all(lessThan(p0, C));
    bool hit = false; vec3 h; int face = -1;
    if (!inNotch){ hit = true; h = p0; face = 3; }
    else {
      // inside the notch: the ray meets the first cut plane it crosses (leaving the octant)
      float tq = 1e9; int ax = -1;
      for (int i = 0; i < 3; i++){
        if (d[i] > 0.0){ float ti = (C[i] - o[i])/d[i]; if (ti < tq){ tq = ti; ax = i; } }
      }
      if (ax >= 0 && tq < t1){ hit = true; h = o + d*tq; face = ax; }
    }
    if (hit){
      if (face == 3){
        // outer skin: latitude/longitude wrap of the 4th clip
        vec3 s = normalize(h - C);
        vec2 st = vec2(atan(s.y, s.x)/(2.0*PI) + 0.5, acos(clamp(s.z, -1.0, 1.0))/PI);
        st = clamp(st, 0.0016, 0.9984); col = texture(sTD2DInputs[2], vec2(0.5 + st.x*0.5, st.y)).rgb;
        vec3 Nw = normalize(R*s);
        float facing = clamp(dot(Nw, -n), 0.0, 1.0);
        col *= mix(1.0, 0.35 + 0.75*facing, uS.z);
        col += vec3(1.0)*pow(1.0 - facing, 6.0)*uSp.y;                 // rim light: keeps the round silhouette
      } else {
        // inner quarter-disc faces, each with its own clip; uv runs from the centre outward
        vec3 e = (C - h)/rad;                                           // 0 at the centre, 1 at the rim
        vec2 st = (face == 0) ? vec2(e.y, e.z) : ((face == 1) ? vec2(e.x, e.z) : vec2(e.x, e.y));
        st = clamp(vec2(st.x, 1.0 - st.y), 0.0008, 0.9992);
        if (face == 2) col = texture(sTD2DInputs[0], st).rgb;          // z-cut  -> ceiling clip
        else if (face == 1) col = texture(sTD2DInputs[1], st).rgb;     // y-cut  -> left clip
        else col = texture(sTD2DInputs[2], vec2(clamp(st.x, 0.0016, 0.9984)*0.5, st.y)).rgb;   // x-cut -> right clip (left half of the pack)
        float ao = smoothstep(0.0, 0.25, min(min(e.x + e.y, e.y + e.z), e.x + e.z));
        col *= uSp.z*(0.75 + 0.25*ao);
      }
      col *= 1.0 + uK.z*uK.x;
    }
  }
  fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
