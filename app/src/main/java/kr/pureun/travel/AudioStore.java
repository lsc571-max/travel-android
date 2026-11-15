package kr.pureun.travel;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.ArrayList;

/**
 * 들은 소리를 휴대폰에 저장한다 (안드로이드 기능을 쓰지 않는 순수 자바 → PC에서도 시험 가능).
 * 마이크 소리는 끊김 없이 계속 받고, 긴 무음만 빼고 적는다: 말소리 앞 1초·뒤 1초는 남기므로 짧은 쉼은 그대로 남는다.
 * 파일은 머리글 없는 16kHz·모노·16비트 소리(PCM). "소리 전체에서 몇 번째 표본인지"를 "파일의 몇 번째 표본인지"로 바꿔 주는 표를 함께 갖고 있어,
 * 문장마다 그 문장의 소리가 파일 어디에 있는지 알 수 있다.
 */
class AudioStore {
    static final int RATE = 16000;
    private static final int PRE = RATE, HANG = RATE;       // 말소리 앞·뒤로 남기는 길이 (1초씩)

    private final File file;
    private OutputStream out;
    private final float[] pre = new float[PRE];              // 아직 적지 않은 최근 소리 (말이 시작되면 앞에 붙임)
    private int preLen = 0, prePos = 0, hang = 0;
    private long streamPos = 0, filePos = 0, wall0 = 0, lastFlush = 0;
    private boolean writing = false, failed = false;
    private final ArrayList<long[]> runs = new ArrayList<>();   // {소리 전체에서의 시작, 파일에서의 시작, 길이}
    private final byte[] bytes = new byte[2 * 2048];

    AudioStore(File f) { file = f; }

    String name() { return file.getName(); }
    synchronized long streamPos() { return streamPos; }
    synchronized long fileSamples() { return filePos; }

    /** 소리 조각을 넣음. speech: 지금 말소리 구간인지 */
    synchronized void write(float[] w, int n, boolean speech) {
        if (wall0 == 0) wall0 = System.currentTimeMillis();
        if (speech) {
            if (!writing) {                                  // 말이 시작됨 → 앞에 모아 둔 소리부터 적음
                long start = streamPos - preLen;
                runs.add(new long[]{start, filePos, 0});
                writing = true;
                if (preLen > 0) {
                    float[] o = new float[preLen];
                    int first = (prePos - preLen + PRE) % PRE;
                    for (int i = 0; i < preLen; i++) o[i] = pre[(first + i) % PRE];
                    put(o, preLen);
                    preLen = 0;
                }
            }
            put(w, n);
            hang = HANG;
        } else if (writing && hang > 0) {                    // 말이 끝난 뒤 1초까지는 계속 적음
            put(w, n);
            hang -= n;
            if (hang <= 0) writing = false;
        } else {                                             // 무음: 적지 않고 최근 1초만 기억
            writing = false;
            for (int i = 0; i < n; i++) { pre[prePos] = w[i]; prePos = (prePos + 1) % PRE; }
            preLen = Math.min(PRE, preLen + n);
        }
        streamPos += n;
    }

    private void put(float[] s, int n) {
        if (failed) { grow(n); return; }
        try {
            if (out == null) {
                File dir = file.getParentFile();
                if (dir != null) dir.mkdirs();
                out = new BufferedOutputStream(new FileOutputStream(file, false), 1 << 16);
            }
            int off = 0;
            while (off < n) {
                int c = Math.min(n - off, bytes.length / 2);
                for (int i = 0; i < c; i++) {
                    int v = Math.round(Math.max(-1f, Math.min(1f, s[off + i])) * 32767f);
                    bytes[i * 2] = (byte) v; bytes[i * 2 + 1] = (byte) (v >> 8);
                }
                out.write(bytes, 0, c * 2);
                off += c;
            }
            long now = System.currentTimeMillis();
            if (now - lastFlush > 2000) { out.flush(); lastFlush = now; }   // 앱이 갑자기 꺼져도 2초 전까지는 남게
        } catch (Throwable t) { failed = true; }
        grow(n);
    }

    private void grow(int n) {
        filePos += n;
        if (!runs.isEmpty()) runs.get(runs.size() - 1)[2] += n;
    }

    /** 소리 전체에서의 위치 → 파일에서의 위치 (빠진 무음 구간에 있으면 바로 다음에 적힌 곳) */
    synchronized long map(long stream) {
        long best = 0;
        for (int i = 0; i < runs.size(); i++) {
            long[] r = runs.get(i);
            if (stream < r[0]) return r[1];
            best = r[1] + Math.min(stream - r[0], r[2]);
        }
        return best;
    }

    /** 그 위치의 소리가 들린 시각 (ms) */
    synchronized long wallAt(long stream) { return (wall0 == 0 ? System.currentTimeMillis() : wall0) + stream * 1000 / RATE; }

    /** 잠깐 듣지 않다가 다시 들을 때: 지금부터의 소리가 "지금" 들린 것으로 시각을 다시 맞춤 */
    synchronized void resync() { wall0 = System.currentTimeMillis() - streamPos * 1000 / RATE; }

    /** 지금까지 받은 소리를 파일에 내려 적음 */
    synchronized void flush() { try { if (out != null) out.flush(); } catch (Throwable ignored) { } }

    synchronized void close() {
        try { if (out != null) { out.flush(); out.close(); } } catch (Throwable ignored) { }
        out = null;
        if (filePos == 0 || failed) { try { file.delete(); } catch (Throwable ignored) { } }
    }
}
