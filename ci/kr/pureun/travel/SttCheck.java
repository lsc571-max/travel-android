package kr.pureun.travel;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;

/** PC·빌드 서버에서 앱의 음성 인식 핵심(SttCore)을 실제 모델과 녹음 파일로 시험한다.
 *  사용: SttCheck <vad.onnx> <whisper|sensevoice> <언어 또는 auto> <모델 파일들,쉼표> <wav...> */
public class SttCheck {
    public static void main(String[] a) throws Exception {
        final int[] finals = {0};
        SttCore core = new SttCore(a[0], a[1], a[3].split(","), 2, 0.45f, new SttCore.Listener() {
            @Override public void onPartial(String t) { System.out.println("   (중간) " + t); }
            @Override public void onFinal(String t, String lang, float db, float hz, float sec) {
                finals[0]++;
                System.out.printf("   [확정] lang=%s %.1fdB %.0fHz %.1f초 → %s%n", lang, db, hz, sec, t);
            }
        });
        core.setLanguage("auto".equals(a[2]) ? "" : a[2]);
        long t0 = System.currentTimeMillis();
        float total = 0;
        for (int i = 4; i < a.length; i++) {
            byte[] b = Files.readAllBytes(new File(a[i]).toPath());
            ByteBuffer bb = ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN);
            int rate = bb.getInt(24), ch = bb.getShort(22), pos = 12;
            while (pos + 8 <= b.length && !(b[pos] == 'd' && b[pos + 1] == 'a' && b[pos + 2] == 't' && b[pos + 3] == 'a')) pos += 8 + bb.getInt(pos + 4);
            int len = Math.min(bb.getInt(pos + 4), b.length - pos - 8); pos += 8;
            int n = len / 2 / ch;
            float[] s = new float[n];
            for (int k = 0; k < n; k++) s[k] = bb.getShort(pos + k * 2 * ch) / 32768f;
            if (rate != 16000) { // 간단한 다시 표본화
                int m = (int) ((long) n * 16000 / rate); float[] r = new float[m];
                for (int k = 0; k < m; k++) r[k] = s[Math.min(n - 1, (int) ((long) k * rate / 16000))];
                s = r; n = m;
            }
            System.out.println("▶ " + new File(a[i]).getName() + " (" + rate + "Hz, " + String.format("%.1f", n / 16000f) + "초)");
            total += n / 16000f;
            // 마이크처럼 0.1초씩 넣고, 파일 사이에 1초 쉼
            float[] buf = new float[1600];
            for (int p = 0; p < n; p += 1600) { int c = Math.min(1600, n - p); System.arraycopy(s, p, buf, 0, c); core.accept(buf, c); }
            float[] sil = new float[1600];
            for (int k = 0; k < 10; k++) core.accept(sil, 1600);
        }
        core.flush();
        while (core.busy()) Thread.sleep(50);
        long ms = System.currentTimeMillis() - t0;
        System.out.printf("문장 %d개 · 소리 %.1f초를 %.1f초에 처리%n", finals[0], total, ms / 1000f);
        core.release();
        if (finals[0] == 0) { System.out.println("FAIL: 인식된 문장이 없음"); System.exit(1); }
        System.exit(0);
    }
}
