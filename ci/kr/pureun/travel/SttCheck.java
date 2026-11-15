package kr.pureun.travel;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;

/** PC·빌드 서버에서 앱의 음성 인식 핵심(SttCore)을 실제 모델과 녹음 파일로 시험한다.
 *  사용: SttCheck <vad.onnx> <whisper|sensevoice> <언어 또는 auto> <모델 파일들,쉼표> <wav...> */
public class SttCheck {
    public static void main(String[] a) throws Exception {
        final int[] finals = {0}, silentFinals = {0, 0};
        final java.util.List<float[]> clips = new java.util.ArrayList<>();
        final java.util.List<long[]> places = new java.util.ArrayList<>();
        final float[] secs = new float[64];
        SttCore core = new SttCore(a[0], a[1], a[3].split(","), 2, 0.45f, new SttCore.Listener() {
            @Override public void onPartial(String t) { System.out.println("   (중간) " + t); }
            @Override public void onFinal(String t, String lang, float db, float hz, float sec, long[] at) {
                if (t.isEmpty()) { silentFinals[0]++; if (at == null) silentFinals[1]++; System.out.printf("   [소리만] %.1f초 저장 %s%n", sec, at == null ? "없음" : String.format("%.1f~%.1f초", at[0] / 16000f, at[1] / 16000f)); return; }
                if (finals[0] < secs.length) secs[finals[0]] = sec;
                finals[0]++;
                if (at != null) synchronized (places) { places.add(at); }
                System.out.printf("   [확정] lang=%s %.1fdB %.0fHz %.1f초 저장 %s → %s%n", lang, db, hz, sec,
                        at == null ? "없음" : String.format("%.1f~%.1f초", at[0] / 16000f, at[1] / 16000f), t);
            }
        });
        core.setLanguage("auto".equals(a[2]) ? "" : a[2]);
        // 들은 소리 저장 시험: 긴 무음만 빼고 저장되는지, 문장마다 저장된 자리가 맞는지
        File recFile = File.createTempFile("sttcheck", ".pcm");
        AudioStore store = new AudioStore(recFile);
        core.setStore(store);
        long t0 = System.currentTimeMillis(), fedTotal = 0;
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
            clips.add(s);
            System.out.println("▶ " + new File(a[i]).getName() + " (" + rate + "Hz, " + String.format("%.1f", n / 16000f) + "초)");
            total += n / 16000f;
            // 마이크처럼 0.1초씩 넣고, 파일 사이에 1초 쉼
            float[] buf = new float[1600];
            for (int p = 0; p < n; p += 1600) { int c = Math.min(1600, n - p); System.arraycopy(s, p, buf, 0, c); core.accept(buf, c); }
            float[] sil = new float[1600];
            for (int k = 0; k < (i == 4 ? 60 : 10); k++) core.accept(sil, 1600);   // 첫 파일 뒤에는 6초 쉼 (긴 무음이 빠지는지 보려고)
            fedTotal += n + 1600L * (i == 4 ? 60 : 10);
        }
        core.flush();
        while (core.busy()) Thread.sleep(50);
        long ms = System.currentTimeMillis() - t0;
        // 저장된 소리 받아 적기 시험: 첫 녹음을 통째로 넘겨 글이 나오는지 (Gemini가 실패했을 때 쓰는 길)
        final String[] fileText = {null, null};
        core.transcribe(clips.get(0), "auto".equals(a[2]) ? "" : a[2], new SttCore.TextCallback() {
            @Override public void done(String text, String error) { fileText[0] = text; fileText[1] = error; }
        });
        while (core.busy()) Thread.sleep(50);
        System.out.println("저장된 소리 받아 적기 → " + fileText[0] + (fileText[1] == null ? "" : " (오류 " + fileText[1] + ")"));
        boolean fileOk = fileText[1] == null && fileText[0] != null && fileText[0].length() >= 4;
        if (!fileOk) System.out.println("FAIL: 저장된 소리를 받아 적지 못함");
        // 받아 적지 않는 방식 시험: 말소리 구간만 찾아 소리 자리를 알려 줘야 함 (글은 비어 있음)
        core.setNoDecode(true);
        int before = finals[0];
        { float[] s2 = clips.get(clips.size() - 1), buf2 = new float[1600];
          for (int p = 0; p < s2.length; p += 1600) { int c = Math.min(1600, s2.length - p); System.arraycopy(s2, p, buf2, 0, c); core.accept(buf2, c); }
          float[] sil2 = new float[1600]; for (int k = 0; k < 10; k++) core.accept(sil2, 1600);
          fedTotal += s2.length + 16000L; }
        core.flush();
        while (core.busy()) Thread.sleep(50);
        core.setNoDecode(false);
        boolean quietOk = silentFinals[0] >= 1 && silentFinals[1] == 0 && finals[0] == before;
        System.out.println(quietOk ? "받아 적지 않는 방식: 정상 (소리 자리 " + silentFinals[0] + "개)" : "FAIL: 받아 적지 않는 방식이 맞지 않음 (" + silentFinals[0] + "," + silentFinals[1] + "," + (finals[0] - before) + ")");
        System.out.printf("문장 %d개 · 소리 %.1f초를 %.1f초에 처리%n", finals[0], total, ms / 1000f);
        core.release();
        store.close();
        // 저장 확인
        long saved = recFile.length() / 2;
        System.out.printf("저장: 받은 소리 %.1f초 → 파일 %.1f초 (긴 무음 %.1f초 뺌)%n", fedTotal / 16000f, saved / 16000f, (fedTotal - saved) / 16000f);
        boolean ok = saved > 0 && saved < fedTotal;
        if (!ok) System.out.println("FAIL: 저장된 길이가 이상함");
        long prev = -1; int k = 0;
        for (long[] p : places) {
            float len = (p[1] - p[0]) / 16000f, want = k < secs.length ? secs[k] : len;
            if (p[0] < 0 || p[1] > saved || p[1] <= p[0] || p[0] < prev || Math.abs(len - want) > 0.3f || p[3] < p[2]) {
                ok = false; System.out.printf("FAIL: 문장 %d의 저장 자리가 맞지 않음 (%d~%d, 파일 %d, 말한 길이 %.1f초)%n", k + 1, p[0], p[1], saved, want);
            }
            prev = p[0]; k++;
        }
        if (places.size() != finals[0]) { ok = false; System.out.println("FAIL: 저장 자리가 없는 문장이 있음"); }
        // 저장된 소리에서 그 자리를 꺼내 보면 실제로 소리가 있어야 함 (무음이 아니어야 함)
        byte[] rb = Files.readAllBytes(recFile.toPath());
        ByteBuffer rbb = ByteBuffer.wrap(rb).order(ByteOrder.LITTLE_ENDIAN);
        k = 0;
        for (long[] p : places) {
            double e = 0; long cnt = p[1] - p[0];
            for (long q = p[0]; q < p[1]; q++) { double v = rbb.getShort((int) (q * 2)) / 32768.0; e += v * v; }
            double db = 10 * Math.log10(Math.max(e / Math.max(1, cnt), 1e-12));
            if (db < -50) { ok = false; System.out.printf("FAIL: 문장 %d의 저장 자리에 소리가 없음 (%.1fdB)%n", k + 1, db); }
            k++;
        }
        recFile.delete();
        System.out.println(ok ? "저장 자리 확인: 정상" : "저장 자리 확인: 실패");
        if (!ok || !fileOk || !quietOk) System.exit(1);
        if (finals[0] == 0) { System.out.println("FAIL: 인식된 문장이 없음"); System.exit(1); }
        System.exit(0);
    }
}
