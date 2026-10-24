// pack_rs: two square clips side by side (left half = right-wall clip, right half = sphere skin),
// because the sphere shader only gets three input slots here.
out vec4 fragColor;
void main(){
  vec2 uv = vUV.st;
  vec4 c = (uv.x < 0.5) ? texture(sTD2DInputs[0], vec2(uv.x*2.0, uv.y)) : texture(sTD2DInputs[1], vec2(uv.x*2.0 - 1.0, uv.y));
  fragColor = c;
}
