package kr.pureun.travel;

/**
 * 폰에서 나오는 소리(48kHz·스테레오)를 음성 인식이 쓰는 16kHz·모노로 바꾼다 (순수 자바 → PC에서도 시험 가능).
 * 두 채널을 평균 낸 뒤, 8kHz 위의 소리를 걸러 내고(겹침 방지) 세 개 중 하나씩만 남긴다.
 */
class Down48 {
    private static final int TAPS = 63;
    private static final float[] H = design();
    private final float[] hist = new float[TAPS];
    private int pos = 0, phase = 0;

    private static float[] design() {
        double fc = 7400.0 / 48000.0, sum = 0;
        float[] h = new float[TAPS];
        int mid = (TAPS - 1) / 2;
        for (int i = 0; i < TAPS; i++) {
            double x = i - mid;
            double sinc = x == 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * x) / (Math.PI * x);
            double win = 0.54 - 0.46 * Math.cos(2 * Math.PI * i / (TAPS - 1));
            h[i] = (float) (sinc * win);
            sum += h[i];
        }
        for (int i = 0; i < TAPS; i++) h[i] /= (float) sum;
        return h;
    }

    /** in: 왼쪽·오른쪽이 번갈아 든 16비트 소리, n = 값의 개수. out에는 n/6+1개 넣을 자리가 있어야 함. 돌려주는 값 = 만든 16kHz 표본 수 */
    int push(short[] in, int n, float[] out) {
        int m = 0;
        for (int i = 0; i + 1 < n; i += 2) {
            hist[pos] = (in[i] + in[i + 1]) / 65536f;
            pos = (pos + 1) % TAPS;
            if (++phase == 3) {
                phase = 0;
                float acc = 0;
                int k = pos;
                for (int t = 0; t < TAPS; t++) { acc += H[t] * hist[k]; k = (k + 1) % TAPS; }
                out[m++] = acc;
            }
        }
        return m;
    }
}
