// cube_rig: three faces of a cube built from FOUR points, so their shared edges are always the creases.
// V = the room vertex; A, B, C = points along the left-ceiling, right-ceiling and vertical creases.
// Canvas pixels, origin at the centre of the projector frame, y up.
// Inputs: 0 ceiling face, 1 left wall face, 2 right wall face. uv (0,0) of every face sits on V.
uniform vec4 uV;    // xy vertex, z guides on/off, w guide brightness
uniform vec4 uAng;  // x left-crease angle, y right-crease angle, z down-crease angle (degrees)
uniform vec4 uLen;  // x left arm, y right arm, z down arm (px)
uniform vec4 uF1;   // far-corner nudges: xy ceiling, zw left wall
uniform vec4 uF2;   // xy right wall
uniform vec4 uO;    // x orient on (clips mode), y ceiling upright
uniform vec4 uK;    // x kick envelope 0..1, y punch (size), z brightness flash, w crease flash
out vec4 fragColor;

float cross2(vec2 a, vec2 b){ return a.x*b.y - a.y*b.x; }
// inverse bilinear (Inigo Quilez): where inside quad abcd is point p? a=(0,0) b=(1,0) c=(1,1) d=(0,1)
vec2 invBilinear(vec2 p, vec2 a, vec2 b, vec2 c, vec2 d){
  vec2 e = b-a, f = d-a, g = a-b+c-d, h = p-a;
  float k2 = cross2(g, f), k1 = cross2(e, f) + cross2(h, g), k0 = cross2(h, e);
  if (abs(k2) < 0.001) return vec2((h.x*k1 + f.x*k0)/(e.x*k1 - g.x*k0), -k0/k1);
  float w = k1*k1 - 4.0*k0*k2; if (w < 0.0) return vec2(-1.0);
  w = sqrt(w); float ik2 = 0.5/k2;
  float v = (-k1 - w)*ik2, u = (h.x - f.x*v)/(e.x + g.x*v);
  if (u < 0.0 || u > 1.0 || v < 0.0 || v > 1.0){ v = (-k1 + w)*ik2; u = (h.x - f.x*v)/(e.x + g.x*v); }
  return vec2(u, v);
}
// faces overlap by a hair at shared edges so no pixel on a crease is ever left unpainted;
// the uv is clamped so the overlap repeats the face's own edge pixels
bool inside(vec2 uv){ return all(greaterThanEqual(uv, vec2(-0.004))) && all(lessThanEqual(uv, vec2(1.004))); }
float lineDist(vec2 p, vec2 o, vec2 dir){ return abs(cross2(p - o, dir)); }   // distance to the infinite line

void main(){
  vec2 p = (vUV.st - 0.5)*vec2(1280.0, 720.0);
  vec2 V = uV.xy;
  vec2 dA = vec2(cos(radians(uAng.x)), sin(radians(uAng.x)));
  vec2 dB = vec2(cos(radians(uAng.y)), sin(radians(uAng.y)));
  vec2 dC = vec2(cos(radians(uAng.z)), sin(radians(uAng.z)));
  float grow = 1.0 + uK.y*uK.x;                       // the cube punches out from the vertex on each kick
  vec2 A = V + dA*uLen.x*grow, B = V + dB*uLen.y*grow, C = V + dC*uLen.z*grow;

  // Orientation: every face is anchored with uv (0,0) on the vertex, which leaves the left wall
  // rotated 180 degrees, the right wall flipped top-to-bottom, and the ceiling running along the
  // cube's diagonal. In clips mode each face is turned so the picture reads upright.
  vec3 col = vec3(0.0);
  vec2 uv, st;
  bool orient = uO.x > 0.5;
  uv = invBilinear(p, V, A, A + B - V + uF1.xy, B);
  if (inside(uv)){
    st = (orient && uO.y > 0.5) ? vec2((uv.y - uv.x + 1.0)*0.5, (uv.x + uv.y)*0.5) : uv;   // ceiling: up = away from the vertex
    col = texture(sTD2DInputs[0], clamp(st, 0.0008, 0.9992)).rgb;
  }
  uv = invBilinear(p, V, A, A + C - V + uF1.zw, C);
  if (inside(uv)){
    st = orient ? vec2(1.0 - uv.x, 1.0 - uv.y) : uv;                                      // left wall: undo the 180
    col = texture(sTD2DInputs[1], clamp(st, 0.0008, 0.9992)).rgb;
  }
  uv = invBilinear(p, V, B, B + C - V + uF2.xy, C);
  if (inside(uv)){
    st = orient ? vec2(uv.x, 1.0 - uv.y) : uv;                                            // right wall: undo the flip
    col = texture(sTD2DInputs[2], clamp(st, 0.0008, 0.9992)).rgb;
  }

  // kick: whole cube flashes brighter, and the three creases light up white
  col *= 1.0 + uK.z*uK.x;
  float e = 0.0;
  e = max(e, smoothstep(2.5, 0.0, lineDist(p, V, dA)) * step(0.0, dot(p - V, dA)) * step(dot(p - V, dA), uLen.x*grow));
  e = max(e, smoothstep(2.5, 0.0, lineDist(p, V, dB)) * step(0.0, dot(p - V, dB)) * step(dot(p - V, dB), uLen.y*grow));
  e = max(e, smoothstep(2.5, 0.0, lineDist(p, V, dC)) * step(0.0, dot(p - V, dC)) * step(dot(p - V, dC), uLen.z*grow));
  col += vec3(1.0)*e*uK.w*uK.x;

  if (uV.z > 0.5){
    // alignment guides: the three crease lines drawn right across the frame, and a ring on the vertex
    float g = 0.0;
    g = max(g, smoothstep(1.5, 0.0, lineDist(p, V, dA)) * step(0.0, dot(p - V, dA)));
    g = max(g, smoothstep(1.5, 0.0, lineDist(p, V, dB)) * step(0.0, dot(p - V, dB)));
    g = max(g, smoothstep(1.5, 0.0, lineDist(p, V, dC)) * step(0.0, dot(p - V, dC)));
    float ring = smoothstep(2.0, 0.0, abs(length(p - V) - 14.0));
    col = max(col, vec3(1.0, 1.0, 0.2)*max(g, ring)*uV.w);
  }
  fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
