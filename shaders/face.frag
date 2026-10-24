// corner face. Mode 0 = test pattern (for lining up the cube), 1 = clip playback.
// In test mode the big white dot marks uv (0,0): put that corner of every face on the room vertex.
uniform vec4 uM;   // x mode, y twist 0..1, z gain, w time
uniform vec4 uC;   // rgb test colour, w face id
uniform vec4 uA;   // x bass, y level, z black crush
uniform vec4 uB;   // x boost (gain), y lift (gamma < 1 brightens mids), z saturation
out vec4 fragColor;
void main(){
  vec2 uv = vUV.st;
  float e = min(min(uv.x, 1.0-uv.x), min(uv.y, 1.0-uv.y));
  vec3 c;
  if (uM.x < 0.5){
    c = uC.rgb*0.55;
    vec2 f = fract(uv*4.0);
    float grid = step(min(min(f.x, 1.0-f.x), min(f.y, 1.0-f.y)), 0.015);
    c += vec3(0.22)*grid;
    c += vec3(1.0)*smoothstep(0.01, 0.003, e);                      // outline
    c = mix(c, vec3(1.0), smoothstep(0.075, 0.06, length(uv)));      // vertex dot at uv (0,0)
    float diag = abs(uv.x - uv.y);                                   // diagonal from the vertex
    c += vec3(0.35)*smoothstep(0.006, 0.0, diag);
  } else {
    vec3 raw = texture(sTD2DInputs[0], uv).rgb;
    vec2 o = vec2(0.003 + 0.02*uA.y, 0.0);
    vec3 split = vec3(texture(sTD2DInputs[0], uv + o).r, raw.g, texture(sTD2DInputs[0], uv - o).b);
    c = mix(raw, split, uM.y);
    c = max(c - uA.z, 0.0)/(1.0 - uA.z);                            // crush near-black to true black
    c = pow(c, vec3(uB.y));                                          // lift the mids
    float l = dot(c, vec3(0.299, 0.587, 0.114));
    c = mix(vec3(l), c, uB.z);                                       // saturation
    c *= uB.x*(1.0 + 0.25*uA.x*uM.y);                                // boost
  }
  c *= uM.z;
  // no seam: faces run edge to edge
  fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
